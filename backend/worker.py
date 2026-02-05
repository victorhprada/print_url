#!/usr/bin/env python3
"""
Background worker para processar screenshots e PDFs.
Roda em background no Render sem timeout de processamento.
"""

import os
import sys
import zipfile
from pathlib import Path
from typing import Optional

from redis import Redis
from rq import Worker, Queue, Connection

# Adiciona o diretório parent ao path para importar screenshot_pdf
sys.path.insert(0, str(Path(__file__).parent.parent))

from screenshot_pdf import (
    read_urls_from_file,
    capture_many,
    _parse_headers,
)


def process_screenshots(
    csv_path: str,
    output_dir: str,
    job_id: str,
    viewport_width: int = 1280,
    viewport_height: int = 800,
    pdf_format: str = "A4",
    landscape: bool = False,
    delimiter: str = ";",
):
    """
    Processa todas as URLs do CSV e gera screenshots/PDFs.
    Atualiza progresso no job.meta durante o processamento.
    """
    from rq import get_current_job
    
    job = get_current_job()
    output_path = Path(output_dir)
    
    try:
        # Lê URLs do CSV
        urls = read_urls_from_file(
            Path(csv_path),
            csv_col=None,
            delimiter=delimiter,
        )
        
        total = len(urls)
        job.meta["total"] = total
        job.meta["progress"] = 0
        job.meta["errors"] = []
        job.save_meta()
        
        # Callback para atualizar progresso
        def update_progress(index: int, url: str, error: Optional[str] = None):
            job.meta["progress"] = index + 1
            job.meta["current_url"] = url
            if error:
                job.meta["errors"].append({"url": url, "error": error})
            job.save_meta()
        
        # Processa URLs (modificado para incluir callback)
        results = capture_many_with_progress(
            urls=urls,
            output_dir=output_path,
            base_prefix=f"captura_{job_id[:8]}",
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
            progress_callback=update_progress,
        )
        
        # Cria ZIP com estrutura de pastas
        zip_path = Path(output_dir).parent / f"{job_id}.zip"
        create_zip(output_path, zip_path)
        
        # Marca como completo
        job.meta["status"] = "completed"
        job.meta["zip_path"] = str(zip_path)
        job.save_meta()
        
        return {
            "status": "success",
            "total_processed": len(results),
            "errors": len(job.meta["errors"]),
            "zip_path": str(zip_path),
        }
        
    except Exception as e:
        job.meta["status"] = "failed"
        job.meta["error"] = str(e)
        job.save_meta()
        raise


def capture_many_with_progress(
    urls,
    output_dir,
    base_prefix,
    viewport_width,
    viewport_height,
    wait_until,
    timeout_ms,
    pdf_format,
    landscape,
    scale,
    user_agent,
    accept_language,
    timezone_id,
    extra_headers,
    headless,
    proxy,
    post_wait_ms,
    progress_callback,
):
    """
    Versão modificada de capture_many que chama callback de progresso.
    """
    from playwright.sync_api import sync_playwright
    from screenshot_pdf import (
        ensure_output_dir,
        filename_for_url,
        _locale_from_accept_language,
    )
    
    output_dir = ensure_output_dir(output_dir)
    results = []
    
    with sync_playwright() as p:
        launch_kwargs = {"headless": headless}
        if proxy:
            launch_kwargs["proxy"] = {"server": proxy}
        
        browser = p.chromium.launch(**launch_kwargs)
        headers = dict(extra_headers)
        if accept_language:
            headers.setdefault("Accept-Language", accept_language)
        
        context = browser.new_context(
            viewport={"width": viewport_width, "height": viewport_height},
            device_scale_factor=1,
            user_agent=user_agent,
            locale=_locale_from_accept_language(accept_language),
            timezone_id=timezone_id,
            extra_http_headers=headers or None,
        )
        
        page = context.new_page()
        page.add_init_script(
            """
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'languages', { get: () => ['pt-BR','pt','en-US','en'] });
            Object.defineProperty(navigator, 'plugins', { get: () => [1,2,3,4,5] });
            """
        )
        
        for i, (url, tipo) in enumerate(urls):
            error = None
            try:
                # Determina diretório baseado no tipo
                if tipo in ["plataforma", "aplicativo"]:
                    target_dir = ensure_output_dir(output_dir / tipo)
                else:
                    target_dir = output_dir
                
                base_name = filename_for_url(base_prefix, url, i)
                screenshot_path = target_dir / f"{base_name}.png"
                pdf_path = target_dir / f"{base_name}.pdf"
                
                response = page.goto(url, wait_until=wait_until, timeout=timeout_ms)
                
                if post_wait_ms > 0:
                    page.wait_for_timeout(post_wait_ms)
                
                page.screenshot(path=str(screenshot_path), full_page=True)
                page.emulate_media(media="screen")
                page.pdf(
                    path=str(pdf_path),
                    format=pdf_format,
                    print_background=True,
                    scale=scale,
                    landscape=landscape,
                )
                
                results.append((url, screenshot_path, pdf_path))
                
            except Exception as e:
                error = str(e)
                print(f"Erro ao processar {url}: {error}")
            
            finally:
                # Atualiza progresso
                progress_callback(i, url, error)
        
        context.close()
        browser.close()
    
    return results


def create_zip(source_dir: Path, zip_path: Path):
    """
    Cria arquivo ZIP mantendo a estrutura de pastas.
    """
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for file_path in source_dir.rglob("*"):
            if file_path.is_file():
                arcname = file_path.relative_to(source_dir)
                zipf.write(file_path, arcname)


def main():
    """
    Inicia o worker RQ que processa jobs da fila.
    """
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    with Connection(Redis.from_url(REDIS_URL)):
        worker = Worker(["screenshot-jobs"])
        print("🚀 Worker iniciado. Aguardando jobs...")
        worker.work()


if __name__ == "__main__":
    main()
