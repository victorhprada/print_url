#!/usr/bin/env python3

import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from playwright.sync_api import sync_playwright


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(
		description="Capture a full-page screenshot (PNG) and export a PDF from URLs using Playwright (Chromium)."
	)
	parser.add_argument("urls", nargs="*", help="URLs das páginas a serem capturadas")
	parser.add_argument(
		"--urls-file",
		dest="urls_file",
		type=Path,
		default=None,
		help="Arquivo com URLs (txt: uma por linha; csv: ver --csv-col e --delimiter)",
	)
	parser.add_argument(
		"--csv-col",
		dest="csv_col",
		type=str,
		default=None,
		help="Coluna do CSV contendo as URLs (nome da coluna ou índice iniciando em 0)",
	)
	parser.add_argument(
		"--delimiter",
		dest="delimiter",
		type=str,
		default=",",
		help="Delimitador do CSV (default: ,)",
	)
	parser.add_argument(
		"--out",
		dest="output_dir",
		type=Path,
		default=Path.cwd(),
		help="Diretório de saída (default: diretório atual)",
	)
	parser.add_argument(
		"--name",
		dest="base_name",
		type=str,
		default=None,
		help="Nome base do arquivo sem extensão (default: timestamp). Para múltiplas URLs, será usado como prefixo.",
	)
	parser.add_argument(
		"--width",
		dest="viewport_width",
		type=int,
		default=1280,
		help="Largura do viewport em pixels (default: 1280)",
	)
	parser.add_argument(
		"--height",
		dest="viewport_height",
		type=int,
		default=800,
		help="Altura do viewport em pixels (default: 800)",
	)
	parser.add_argument(
		"--wait-until",
		dest="wait_until",
		choices=["load", "domcontentloaded", "networkidle", "commit"],
		default="networkidle",
		help="Espera pela navegação (default: networkidle)",
	)
	parser.add_argument(
		"--timeout-ms",
		dest="timeout_ms",
		type=int,
		default=30000,
		help="Timeout de navegação em ms (default: 30000)",
	)
	parser.add_argument(
		"--pdf-format",
		dest="pdf_format",
		choices=[
			"Letter",
			"Legal",
			"Tabloid",
			"Ledger",
			"A0",
			"A1",
			"A2",
			"A3",
			"A4",
			"A5",
			"A6",
		],
		default="A4",
		help="Formato do PDF (default: A4)",
	)
	parser.add_argument(
		"--landscape",
		action="store_true",
		help="Gera PDF em orientação paisagem (default: retrato)",
	)
	parser.add_argument(
		"--scale",
		dest="scale",
		type=float,
		default=1.0,
		help="Escala do PDF, 0.1 a 2.0 (default: 1.0)",
	)
	# Anti-403 opções
	parser.add_argument(
		"--user-agent",
		dest="user_agent",
		type=str,
		default=(
			"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
			"AppleWebKit/537.36 (KHTML, like Gecko) "
			"Chrome/124.0.0.0 Safari/537.36"
		),
		help="User-Agent customizado (default: Chrome estável)",
	)
	parser.add_argument(
		"--accept-language",
		dest="accept_language",
		type=str,
		default="pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
		help="Header Accept-Language (default: pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7)",
	)
	parser.add_argument(
		"--header",
		dest="headers",
		action="append",
		default=[],
		help="Header extra no formato 'Nome: Valor' (pode repetir)",
	)
	parser.add_argument(
		"--timezone",
		dest="timezone_id",
		type=str,
		default="America/Sao_Paulo",
		help="Timezone para o contexto (default: America/Sao_Paulo)",
	)
	parser.add_argument(
		"--headful",
		action="store_true",
		help="Executa com janela visível (default: headless)",
	)
	parser.add_argument(
		"--proxy",
		dest="proxy",
		type=str,
		default=None,
		help="Proxy ex.: http://usuario:senha@host:porta",
	)
	parser.add_argument(
		"--post-wait-ms",
		dest="post_wait_ms",
		type=int,
		default=0,
		help="Espera extra após navegação antes de capturar (ms)",
	)
	return parser.parse_args()


def ensure_output_dir(path: Path) -> Path:
	path.mkdir(parents=True, exist_ok=True)
	return path


def generate_base_prefix(custom_name: Optional[str]) -> str:
	if custom_name:
		return custom_name
	return datetime.now().strftime("capture_%Y%m%d_%H%M%S")


def sanitize_for_filename(text: str) -> str:
	unsafe = [":", "/", "\\", "?", "*", "\"", "<", ">", "|"]
	result = text
	for ch in unsafe:
		result = result.replace(ch, "-")
	return "".join(c if 32 <= ord(c) < 127 else "-" for c in result)


def filename_for_url(base_prefix: str, url: str, index: int) -> str:
	# Usa host + path simplificado, fallback para índice
	try:
		from urllib.parse import urlparse

		parsed = urlparse(url)
		host = parsed.netloc or "site"
		path = parsed.path.strip("/").replace("/", "-")
		slug_parts = [host]
		if path:
			slug_parts.append(path)
		slug = "_".join(slug_parts)[:80] or f"url{index+1}"
	except Exception:
		slug = f"url{index+1}"
	return sanitize_for_filename(f"{base_prefix}_{slug}")


def read_urls_from_file(file_path: Path, csv_col: Optional[str], delimiter: str) -> list[tuple[str, Optional[str]]]:
	"""Retorna lista de tuplas (url, tipo) onde tipo pode ser 'plataforma', 'aplicativo' ou None"""
	if not file_path.exists():
		raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
	lower = file_path.suffix.lower()
	if lower == ".csv":
		return _read_urls_from_csv(file_path, csv_col, delimiter)
	# Trata como txt: uma URL por linha (ignora vazias e comentários '#')
	# Suporta formato: URL ou URL|tipo
	urls: list[tuple[str, Optional[str]]] = []
	for line in file_path.read_text(encoding="utf-8").splitlines():
		line = line.strip()
		if not line or line.startswith("#"):
			continue
		# Verifica se tem separador | para tipo
		if "|" in line:
			parts = line.split("|", 1)
			url = parts[0].strip()
			tipo = parts[1].strip().lower() if len(parts) > 1 else None
			# Valida tipo
			if tipo and tipo not in ["plataforma", "aplicativo"]:
				print(f"Aviso: tipo '{tipo}' inválido para URL {url}. Usando None.", file=sys.stderr)
				tipo = None
		else:
			url = line
			tipo = None
		urls.append((url, tipo))
	return urls


def _read_urls_from_csv(file_path: Path, csv_col: Optional[str], delimiter: str) -> list[tuple[str, Optional[str]]]:
	"""Lê URLs do CSV e tenta extrair coluna 'tipo' se existir"""
	import csv

	urls: list[tuple[str, Optional[str]]] = []
	with file_path.open("r", encoding="utf-8", newline="") as f:
		# Tenta DictReader primeiro (com cabeçalho)
		reader = csv.DictReader(f, delimiter=delimiter)
		fieldnames = reader.fieldnames or []
		use_dict = bool(fieldnames)
		# Decide coluna alvo
		index_col: Optional[int] = None
		name_col: Optional[str] = None
		if csv_col is not None:
			# Usuário passou nome ou índice
			try:
				index_col = int(csv_col)
			except ValueError:
				name_col = csv_col
		else:
			# Default: coluna 'url' se existir, senão índice 0
			if use_dict and any(n.lower() == "url" for n in fieldnames):
				name_col = next(n for n in fieldnames if n.lower() == "url")
			else:
				index_col = 0
		
		# Verifica se existe coluna 'tipo'
		tipo_col = None
		if use_dict and any(n.lower() == "tipo" for n in fieldnames):
			tipo_col = next(n for n in fieldnames if n.lower() == "tipo")
		
		if use_dict and name_col is not None:
			for row in reader:
				val = (row.get(name_col) or "").strip()
				if val:
					# Tenta pegar o tipo se existir
					tipo = None
					if tipo_col:
						tipo_raw = (row.get(tipo_col) or "").strip().lower()
						if tipo_raw in ["plataforma", "aplicativo"]:
							tipo = tipo_raw
					urls.append((val, tipo))
			return urls
		# Caso sem cabeçalho ou preferiu índice
		f.seek(0)
		simple_reader = csv.reader(f, delimiter=delimiter)
		for row in simple_reader:
			if not row:
				continue
			try:
				val = (row[index_col or 0] or "").strip()
			except IndexError:
				continue
			if val and val.lower() != "url":
				# Sem dict reader, não temos tipo
				urls.append((val, None))
	return urls


def gather_urls(positional_urls: list[str], urls_file: Optional[Path], csv_col: Optional[str], delimiter: str) -> list[tuple[str, Optional[str]]]:
	"""Retorna lista de tuplas (url, tipo) combinando arquivo e argumentos posicionais"""
	file_urls: list[tuple[str, Optional[str]]] = []
	if urls_file is not None:
		file_urls = read_urls_from_file(urls_file, csv_col, delimiter)
	# URLs posicionais não têm tipo
	positional_tuples = [(u, None) for u in positional_urls]
	# Combina, preservando ordem (arquivo primeiro, depois posicionais)
	combined = [*file_urls, *positional_tuples]
	# Remove vazios e espaços
	combined = [(u.strip(), t) for u, t in combined if u and u.strip()]
	if not combined:
		raise ValueError("Nenhuma URL fornecida. Informe URLs posicionais ou --urls-file.")
	return combined


def _parse_headers(headers_list: list[str]) -> dict[str, str]:
	result: dict[str, str] = {}
	for item in headers_list:
		if not item:
			continue
		parts = item.split(":", 1)
		if len(parts) != 2:
			continue
		name, value = parts[0].strip(), parts[1].strip()
		if name and value:
			result[name] = value
	return result


def _locale_from_accept_language(accept_language: Optional[str]) -> Optional[str]:
	if not accept_language:
		return None
	first = accept_language.split(",", 1)[0].strip()
	if ";" in first:
		first = first.split(";", 1)[0].strip()
	return first or None


def capture_many(urls: list[tuple[str, Optional[str]]], output_dir: Path, base_prefix: str, viewport_width: int, viewport_height: int, wait_until: str, timeout_ms: int, pdf_format: str, landscape: bool, scale: float, user_agent: Optional[str], accept_language: Optional[str], timezone_id: Optional[str], extra_headers: dict[str, str], headless: bool, proxy: Optional[str], post_wait_ms: int) -> list[tuple[str, Path, Path]]:
	"""Captura screenshots e PDFs de múltiplas URLs, organizando por tipo (plataforma/aplicativo) se especificado"""
	output_dir = ensure_output_dir(output_dir)
	results: list[tuple[str, Path, Path]] = []
	with sync_playwright() as p:
		launch_kwargs: dict = {"headless": headless}
		if proxy:
			launch_kwargs["proxy"] = {"server": proxy}
		browser = p.chromium.launch(**launch_kwargs)
		# Headers padrão + extras
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
		# Scripts simples para reduzir detecção automatizada
		page.add_init_script(
			"""
			Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
			Object.defineProperty(navigator, 'languages', { get: () => ['pt-BR','pt','en-US','en'] });
			Object.defineProperty(navigator, 'plugins', { get: () => [1,2,3,4,5] });
			"""
		)
		for i, (url, tipo) in enumerate(urls):
			# Determina o diretório de saída baseado no tipo
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
			# Opcional: log simples de status HTTP
			try:
				status = response.status if response else None
				if status and status >= 400:
					print(f"Aviso: status HTTP {status} para {url}", file=sys.stderr)
			except Exception:
				pass
			results.append((url, screenshot_path, pdf_path))
		context.close()
		browser.close()
	return results


def main() -> None:
	args = parse_args()
	base_prefix = generate_base_prefix(args.base_name)
	try:
		urls = gather_urls(args.urls, args.urls_file, args.csv_col, args.delimiter)
		extra_headers = _parse_headers(args.headers)
		results = capture_many(
			urls=urls,
			output_dir=args.output_dir,
			base_prefix=base_prefix,
			viewport_width=args.viewport_width,
			viewport_height=args.viewport_height,
			wait_until=args.wait_until,
			timeout_ms=args.timeout_ms,
			pdf_format=args.pdf_format,
			landscape=args.landscape,
			scale=args.scale,
			user_agent=args.user_agent,
			accept_language=args.accept_language,
			timezone_id=args.timezone_id,
			extra_headers=extra_headers,
			headless=(not args.headful),
			proxy=args.proxy,
			post_wait_ms=args.post_wait_ms,
		)
		for url, screenshot_file, pdf_file in results:
			print(f"URL: {url}")
			print(f"  Screenshot salvo em: {screenshot_file}")
			print(f"  PDF salvo em: {pdf_file}")
	except Exception as exc:  # noqa: BLE001 - propósito é reportar erro ao usuário
		print(f"Erro ao capturar páginas: {exc}", file=sys.stderr)
		sys.exit(1)


if __name__ == "__main__":
	main()
