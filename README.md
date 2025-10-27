# WiipoPrint - Captura de Screenshot e PDF de uma URL

Este projeto traz um script Python que acessa uma URL, tira um screenshot da página inteira (PNG) e exporta a página em PDF usando Playwright (Chromium).

## Requisitos
- Python 3.9+
- macOS, Linux ou Windows

## Instalação
1. Crie e ative um ambiente virtual (recomendado):
```bash
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
```
2. Instale as dependências:
```bash
pip install -r requirements.txt
```
3. Instale os navegadores do Playwright (necessário apenas uma vez):
```bash
python -m playwright install chromium
```

## Uso
Execute o script passando uma ou várias URLs. Por padrão, os arquivos são salvos no diretório atual com um nome baseado em timestamp.
```bash
python screenshot_pdf.py "https://exemplo.com"
```

Várias URLs de uma vez (o `--name` vira prefixo e cada URL vira um arquivo distinto):
```bash
python screenshot_pdf.py \
  "https://exemplo.com" \
  "https://www.google.com/search?q=wiipo" \
  --out ./capturas \
  --name lote_relatorios
```

### Ler URLs de arquivo
Você pode informar URLs via arquivo de texto (uma por linha) ou CSV.

- TXT (uma URL por linha, linhas vazias e iniciadas com `#` são ignoradas):
```bash
python screenshot_pdf.py --urls-file urls.txt --out ./capturas --name lote_txt
```

- CSV (por padrão usa a coluna `url` ou a primeira coluna se `url` não existir):
```bash
python screenshot_pdf.py --urls-file urls.csv --out ./capturas --name lote_csv
```

- CSV com coluna específica e delimitador customizado:
```bash
python screenshot_pdf.py \
  --urls-file urls.csv \
  --csv-col link \
  --delimiter ";" \
  --out ./capturas \
  --name lote_csv_custom
```

Opções úteis:
```bash
python screenshot_pdf.py "https://exemplo.com" \
  --out ./capturas \
  --name relatorio_home \
  --width 1440 --height 900 \
  --wait-until networkidle \
  --timeout-ms 45000 \
  --pdf-format A4 \
  --landscape \
  --scale 1.0
```

- `--out`: diretório de saída
- `--name`: nome base/prefixo dos arquivos (gera `.png` e `.pdf`)
- `--width`/`--height`: tamanho do viewport
- `--wait-until`: momento de espera da navegação (`load`, `domcontentloaded`, `networkidle`, `commit`)
- `--timeout-ms`: timeout de navegação em ms
- `--pdf-format`: tamanho do PDF (ex.: `A4`)
- `--landscape`: PDF em paisagem
- `--scale`: escala do PDF (0.1 a 2.0)

Nomeação dos arquivos:
- Para múltiplas URLs, o nome segue `PREFIXO_HOST_PATH.(png|pdf)` quando possível, limitado a 80 caracteres no slug. Caracteres inválidos são substituídos por `-`.

Saída esperada:
- Screenshot: `NOME.png`
- PDF: `NOME.pdf`

## Exemplos
- Capturar `google.com` com nome customizado no diretório `./saidas`:
```bash
python screenshot_pdf.py "https://www.google.com" --out ./saidas --name google_home
```
- Capturar várias URLs com prefixo:
```bash
python screenshot_pdf.py "https://www.python.org" "https://pypi.org" --out ./saidas --name python_sites
```
- Ler de TXT:
```bash
python screenshot_pdf.py --urls-file urls.txt --out ./saidas --name lote_txt
```
- Ler de CSV com coluna `link` e `;` como separador:
```bash
python screenshot_pdf.py --urls-file urls.csv --csv-col link --delimiter ";" --out ./saidas --name lote_csv
```

## Dúvidas
Se precisar adaptar (ex.: autenticação, clique antes de exportar, remover cabeçalhos do PDF, etc.), abra um issue ou peça aqui que ajusto o script.
