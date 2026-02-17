#!/usr/bin/env python3
"""
FastAPI backend para processamento de screenshots e PDFs em lotes.
Otimizado para Render Free Tier (Web Service apenas, sem workers).
"""

import io
import sys
import zipfile
import traceback
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import tempfile
import shutil

# Configurar logging detalhado
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Adiciona o diretório atual ao path para importar screenshot_pdf
sys.path.insert(0, str(Path(__file__).parent))

# Importa funções do script principal
try:
    from screenshot_pdf import (
        read_urls_from_file,
        capture_many,
        _parse_headers,
    )
    logger.info("✅ Módulo screenshot_pdf importado com sucesso")
except Exception as e:
    logger.error(f"❌ Erro ao importar screenshot_pdf: {e}")
    logger.error(traceback.format_exc())
    raise

app = FastAPI(
    title="Screenshot & PDF Generator API",
    description="Processa screenshots e PDFs em lotes para Render Free Tier",
    version="2.0.0",
)

@app.get("/")
def health_check():
    return {
        "status": "ok",
        "service": "Screenshot & PDF Generator API (Batch Mode)",
        "version": "2.0.0",
        "mode": "batch_processing",
    }

# CORS para permitir requisições do frontend Lovable
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especifique o domínio do Lovable
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "Screenshot & PDF Generator API (Batch Mode)",
        "version": "2.0.0",
        "mode": "batch_processing",
    }


@app.post("/api/process-batch")
def process_batch(
    urls: str = Form(...),  # URLs separadas por newline
    batch_number: int = Form(0),
    viewport_width: int = Form(1280),
    viewport_height: int = Form(800),
    pdf_format: str = Form("A4"),
    landscape: bool = Form(False),
    delimiter: str = Form(";"),
):
    """
    Processa um lote de URLs (máximo 20) e retorna ZIP.
    Cada lote leva ~2-3 minutos (dentro do limite de 15min do Render Free).
    
    Args:
        urls: URLs separadas por newline (máximo 20)
        batch_number: Número do lote (para nomeação)
        viewport_width: Largura do viewport
        viewport_height: Altura do viewport
        pdf_format: Formato do PDF (A4, Letter, etc)
        landscape: Orientação paisagem
        delimiter: Delimitador do CSV (se vier de CSV)
    
    Returns:
        ZIP file com screenshots e PDFs organizados por tipo
    """
    logger.info(f"📥 Recebido request para lote {batch_number}")
    logger.debug(f"Parâmetros: viewport={viewport_width}x{viewport_height}, pdf={pdf_format}, landscape={landscape}")
    
    try:
        # Parse URLs
        url_list = [line.strip() for line in urls.split("\n") if line.strip()]
        logger.info(f"📊 Total de URLs recebidas: {len(url_list)}")
        
        # Validação: máximo 20 URLs por lote
        if len(url_list) > 20:
            logger.warning(f"⚠️ Muitas URLs: {len(url_list)} (máximo 20)")
            raise HTTPException(
                status_code=400,
                detail="Máximo 20 URLs por lote. Divida em lotes menores.",
            )
        
        if not url_list:
            logger.error("❌ Nenhuma URL fornecida")
            raise HTTPException(status_code=400, detail="Nenhuma URL fornecida")
        
        # Cria diretório temporário
        temp_dir = Path(tempfile.mkdtemp())
        output_dir = temp_dir / "output"
        output_dir.mkdir()
        logger.info(f"📁 Diretório temporário criado: {temp_dir}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro na validação inicial: {e}")
        logger.error(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "traceback": traceback.format_exc()}
        )
    
    try:
        # Converte URLs para formato esperado (url, tipo)
        # Se vier do formato "url|tipo", faz parse
        logger.info("🔄 Convertendo URLs para formato (url, tipo)")
        urls_with_type = []
        for i, url in enumerate(url_list):
            if "|" in url:
                parts = url.split("|", 1)
                url_clean = parts[0].strip()
                tipo = parts[1].strip().lower() if len(parts) > 1 else None
                if tipo and tipo not in ["plataforma", "aplicativo"]:
                    logger.warning(f"⚠️ Tipo inválido '{tipo}' para URL {url_clean}")
                    tipo = None
            else:
                url_clean = url
                tipo = None
            urls_with_type.append((url_clean, tipo))
            logger.debug(f"URL {i+1}: {url_clean} (tipo: {tipo})")
        
        # Processa URLs
        base_prefix = f"lote{batch_number:02d}"
        logger.info(f"🚀 Iniciando processamento de {len(urls_with_type)} URLs...")
        
        results = capture_many(
            urls=urls_with_type,
            output_dir=output_dir,
            base_prefix=base_prefix,
            viewport_width=viewport_width,
            viewport_height=viewport_height,
            wait_until="networkidle",
            timeout_ms=30000,
            pdf_format=pdf_format,
            landscape=landscape,
            scale=1.0,
            user_agent=None,
            accept_language="pt-BR,pt;q=0.9",
            timezone_id="America/Sao_Paulo",
            extra_headers={},
            headless=True,
            proxy=None,
            post_wait_ms=0,
        )
        
        logger.info(f"✅ Processamento concluído: {len(results)} URLs processadas")
        
        # Cria ZIP em memória
        logger.info("📦 Criando arquivo ZIP...")
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
            file_count = 0
            for file_path in output_dir.rglob("*"):
                if file_path.is_file():
                    arcname = file_path.relative_to(output_dir)
                    zipf.write(file_path, arcname)
                    file_count += 1
                    logger.debug(f"Adicionado ao ZIP: {arcname}")
        
        logger.info(f"✅ ZIP criado com {file_count} arquivos")
        zip_buffer.seek(0)
        
        # Limpa diretório temporário
        shutil.rmtree(temp_dir, ignore_errors=True)
        logger.info("🧹 Diretório temporário removido")
        
        # Retorna ZIP
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"lote{batch_number:02d}_{timestamp}.zip"
        logger.info(f"📤 Enviando ZIP: {filename}")
        
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "X-Batch-Number": str(batch_number),
                "X-URLs-Processed": str(len(results)),
            },
        )
    
    except HTTPException:
        raise
    except Exception as e:
        # Limpa em caso de erro
        logger.error(f"❌ ERRO FATAL no processamento: {e}")
        logger.error(f"Traceback completo:\n{traceback.format_exc()}")
        shutil.rmtree(temp_dir, ignore_errors=True)
        
        # Retorna erro detalhado
        return JSONResponse(
            status_code=500,
            content={
                "error": str(e),
                "type": type(e).__name__,
                "traceback": traceback.format_exc()
            }
        )


@app.post("/api/process-csv-preview")
def process_csv_preview(
    file: UploadFile = File(...),
    delimiter: str = Form(";"),
):
    """
    Lê CSV e retorna preview das URLs (primeiras 5 linhas) e total.
    Frontend usa isso para mostrar preview antes de processar.
    """
    try:
        content = file.file.read()
        temp_csv = Path(tempfile.mktemp(suffix=".csv"))
        temp_csv.write_bytes(content)
        
        # Lê URLs
        urls = read_urls_from_file(temp_csv, csv_col=None, delimiter=delimiter)
        
        # Limpa
        temp_csv.unlink()
        
        # Retorna preview
        preview = [
            {"url": url, "tipo": tipo} for url, tipo in urls[:5]
        ]
        
        return {
            "total": len(urls),
            "preview": preview,
            "batches_needed": (len(urls) + 19) // 20,  # Divide em lotes de 20
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao ler CSV: {str(e)}")


@app.get("/health")
async def health():
    """Health check para Render"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    uvicorn.run(app, host="0.0.0.0", port=port)
