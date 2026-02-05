#!/usr/bin/env python3
"""
FastAPI backend para processamento de screenshots e PDFs.
Endpoints HTTP rápidos que enfileiram jobs para processamento em background.
"""

import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from redis import Redis
from rq import Queue
from rq.job import Job

app = FastAPI(title="Screenshot & PDF Generator API")

# CORS para permitir requisições do frontend Lovable
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especifique o domínio do Lovable
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuração Redis e Queue
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_conn = Redis.from_url(REDIS_URL)
queue = Queue("screenshot-jobs", connection=redis_conn)

# Diretórios
UPLOAD_DIR = Path("/tmp/uploads")
OUTPUT_DIR = Path("/tmp/outputs")
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "Screenshot & PDF Generator API",
        "queue_length": len(queue),
    }


@app.post("/api/upload")
async def upload_csv(
    file: UploadFile = File(...),
    viewport_width: int = Form(1280),
    viewport_height: int = Form(800),
    pdf_format: str = Form("A4"),
    landscape: bool = Form(False),
    delimiter: str = Form(";"),
):
    """
    Recebe upload do CSV e enfileira job de processamento.
    Retorna job_id imediatamente (< 1 segundo).
    """
    # Validação do arquivo
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Arquivo deve ser CSV")
    
    # Gera ID único para o job
    job_id = str(uuid.uuid4())
    
    # Salva arquivo CSV
    csv_path = UPLOAD_DIR / f"{job_id}.csv"
    content = await file.read()
    csv_path.write_bytes(content)
    
    # Output path para o ZIP
    output_path = OUTPUT_DIR / job_id
    output_path.mkdir(exist_ok=True)
    
    # Enfileira job para processamento em background
    job = queue.enqueue(
        "worker.process_screenshots",
        csv_path=str(csv_path),
        output_dir=str(output_path),
        job_id=job_id,
        viewport_width=viewport_width,
        viewport_height=viewport_height,
        pdf_format=pdf_format,
        landscape=landscape,
        delimiter=delimiter,
        job_timeout="2h",  # Timeout de 2 horas
        job_id=job_id,
    )
    
    return {
        "job_id": job_id,
        "status": "queued",
        "message": "Job enfileirado para processamento",
    }


@app.get("/api/status/{job_id}")
async def get_status(job_id: str):
    """
    Consulta status do job de processamento.
    Retorna progresso em tempo real.
    """
    try:
        job = Job.fetch(job_id, connection=redis_conn)
    except Exception:
        raise HTTPException(status_code=404, detail="Job não encontrado")
    
    status = job.get_status()
    meta = job.meta
    
    response = {
        "job_id": job_id,
        "status": status,  # queued, started, finished, failed
        "progress": meta.get("progress", 0),
        "total": meta.get("total", 0),
        "current_url": meta.get("current_url", ""),
        "errors": meta.get("errors", []),
    }
    
    # Adiciona informações extras baseado no status
    if status == "finished":
        response["zip_ready"] = True
        response["download_url"] = f"/api/download/{job_id}"
    elif status == "failed":
        response["error"] = job.exc_info
    
    return response


@app.get("/api/download/{job_id}")
async def download_result(job_id: str):
    """
    Download do arquivo ZIP com screenshots e PDFs.
    """
    zip_path = OUTPUT_DIR / f"{job_id}.zip"
    
    if not zip_path.exists():
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return FileResponse(
        path=str(zip_path),
        filename=f"capturas_{timestamp}.zip",
        media_type="application/zip",
    )


@app.delete("/api/jobs/{job_id}")
async def delete_job(job_id: str):
    """
    Remove job e arquivos associados (limpeza).
    """
    try:
        job = Job.fetch(job_id, connection=redis_conn)
        job.delete()
    except Exception:
        pass
    
    # Remove arquivos
    csv_path = UPLOAD_DIR / f"{job_id}.csv"
    zip_path = OUTPUT_DIR / f"{job_id}.zip"
    output_dir = OUTPUT_DIR / job_id
    
    if csv_path.exists():
        csv_path.unlink()
    if zip_path.exists():
        zip_path.unlink()
    if output_dir.exists():
        import shutil
        shutil.rmtree(output_dir)
    
    return {"message": "Job e arquivos removidos"}


@app.get("/api/queue/stats")
async def queue_stats():
    """
    Estatísticas da fila de processamento.
    """
    return {
        "queued": len(queue),
        "started": queue.started_job_registry.count,
        "finished": queue.finished_job_registry.count,
        "failed": queue.failed_job_registry.count,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
