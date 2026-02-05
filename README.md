# 🤖 WiipoPrint - Captura de Documentos para Ingestão de IA

> Ferramenta automatizada para capturar screenshots e PDFs de bases de conhecimento, preparando documentos para serem ingeridos em bancos vetoriais e consumidos por agentes de IA.

## 🎯 Propósito

Esta ferramenta foi desenvolvida para **automatizar a captura e organização de documentos** de plataformas web e aplicativos, preparando-os para:

- 🧠 **Ingestão em bancos vetoriais** (embeddings)
- 🤖 **Treinamento de agentes de IA conversacionais**
- 📚 **Criação de datasets de conhecimento**
- 🔄 **Backup e versionamento de documentação**

Os documentos são automaticamente organizados em pastas `plataforma/` e `aplicativo/`, facilitando o processamento downstream.

---

## 🚀 Formas de Uso

### 🌐 Interface Web (Recomendado)

**Acesse:** [https://seu-app.lovable.app](https://seu-app.lovable.app)

Ideal para usuários não-técnicos. Interface moderna com:
- ✅ Upload simples via drag-and-drop
- ✅ Processamento em nuvem (sem instalação local)
- ✅ Progresso em tempo real
- ✅ Download automático de todos os lotes
- ✅ Organização automática por tipo

**Como usar:**
1. Faça upload do arquivo CSV com URLs
2. Configure parâmetros (opcional)
3. Clique "Processar"
4. Aguarde processamento (~3min por 20 URLs)
5. Download do ZIP com documentos organizados

---

### 💻 Linha de Comando (Para Desenvolvedores)

Para uso local, automação ou integração em pipelines.

#### Requisitos
- Python 3.9+
- macOS, Linux ou Windows

#### Instalação

1. Clone o repositório:
```bash
git clone https://github.com/victorhprada/print_url.git
cd print_url
```

2. Crie e ative um ambiente virtual:
```bash
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Instale o navegador Chromium:
```bash
python -m playwright install chromium
```

#### Uso Básico

**URL única:**
```bash
python screenshot_pdf.py "https://exemplo.com"
```

**Múltiplas URLs:**
```bash
python screenshot_pdf.py \
  "https://exemplo.com" \
  "https://outro-site.com" \
  --out ./capturas \
  --name lote_docs
```

**Arquivo CSV (com tipos):**
```bash
python screenshot_pdf.py \
  --urls-file MapeamentoBase.csv \
  --delimiter ";" \
  --out ./capturas \
  --name documentos_ia
```

#### Formato do CSV

O CSV deve conter as colunas `url` e `tipo`:

```csv
url;tipo
https://exemplo.com/dashboard;plataforma
https://app.exemplo.com;aplicativo
https://docs.exemplo.com;plataforma
```

**Tipos suportados:**
- `plataforma` - Páginas web (sites, dashboards, portais)
- `aplicativo` - Apps web (interfaces de aplicativo)

Os documentos são organizados automaticamente:
```
capturas/
  ├── plataforma/
  │   ├── doc1.png
  │   ├── doc1.pdf
  │   └── doc2.png
  └── aplicativo/
      ├── app1.png
      └── app1.pdf
```

#### Formato TXT (alternativa ao CSV)

Arquivo de texto simples com formato `URL|tipo`:

```txt
# Base de conhecimento
https://exemplo.com/docs|plataforma
https://app.exemplo.com|aplicativo
https://site.com|plataforma
```

```bash
python screenshot_pdf.py \
  --urls-file urls_com_tipo.txt \
  --out ./capturas \
  --name docs
```

#### Opções Avançadas

```bash
python screenshot_pdf.py "https://exemplo.com" \
  --out ./capturas \
  --name relatorio \
  --width 1920 --height 1080 \
  --wait-until networkidle \
  --timeout-ms 45000 \
  --pdf-format A4 \
  --landscape \
  --scale 1.0
```

**Parâmetros disponíveis:**

| Parâmetro | Descrição | Default |
|-----------|-----------|---------|
| `--out` | Diretório de saída | `.` (atual) |
| `--name` | Nome base/prefixo dos arquivos | timestamp |
| `--width` | Largura do viewport (px) | 1280 |
| `--height` | Altura do viewport (px) | 800 |
| `--wait-until` | Momento de espera (`load`, `networkidle`, etc) | `networkidle` |
| `--timeout-ms` | Timeout de navegação (ms) | 30000 |
| `--pdf-format` | Formato do PDF (`A4`, `Letter`, `A3`, etc) | `A4` |
| `--landscape` | Orientação paisagem | `false` |
| `--scale` | Escala do PDF (0.1 a 2.0) | 1.0 |
| `--delimiter` | Delimitador do CSV | `,` |
| `--csv-col` | Coluna do CSV com URLs | `url` (auto) |

---

## 🏗️ Arquitetura

### Interface Web (Lovable + Render)

```
┌─────────────────────────────┐
│   Frontend (Lovable)        │
│   Interface React/TypeScript │
│   - Upload CSV              │
│   - Configuração            │
│   - Progresso em tempo real │
└──────────────┬──────────────┘
               │ HTTPS
┌──────────────▼──────────────┐
│   Backend API (Render)      │
│   FastAPI + Docker          │
│   - Processa em lotes       │
│   - Max 20 URLs por request │
└──────────────┬──────────────┘
               │
┌──────────────▼──────────────┐
│   Playwright + Chromium     │
│   - Screenshots full-page   │
│   - Export PDF              │
│   - Headless browser        │
└──────────────┬──────────────┘
               │
┌──────────────▼──────────────┐
│   ZIP organizado            │
│   plataforma/ + aplicativo/ │
└─────────────────────────────┘
```

**Tecnologias:**
- Frontend: React + TypeScript + Tailwind CSS + shadcn/ui
- Backend: FastAPI + Playwright + Docker
- Deploy: Lovable (frontend) + Render (backend)
- **100% Free Tier**

---

## 🔧 API REST (para integração)

### Endpoints

**Health Check:**
```bash
GET https://screenshot-batch-api-t4o9.onrender.com/health
```

**Processar Lote:**
```bash
POST https://screenshot-batch-api-t4o9.onrender.com/api/process-batch
Content-Type: multipart/form-data

urls: "URL1|tipo1\nURL2|tipo2" (max 20 URLs)
batch_number: 0
viewport_width: 1280
viewport_height: 800
pdf_format: A4
landscape: false

Response: ZIP file
```

**Preview CSV:**
```bash
POST https://screenshot-batch-api-t4o9.onrender.com/api/process-csv-preview
Content-Type: multipart/form-data

file: arquivo.csv
delimiter: ";"

Response: {
  "total": 164,
  "preview": [...],
  "batches_needed": 9
}
```

Ver documentação completa da API em: [`DEPLOY_RENDER.md`](DEPLOY_RENDER.md)

---

## 📦 Deploy Próprio

Se você quiser fazer deploy da sua própria instância:

1. **Backend:** Ver [`DEPLOY_RENDER.md`](DEPLOY_RENDER.md)
2. **Frontend:** Ver [`LOVABLE_PROMPT.md`](LOVABLE_PROMPT.md)

**Requisitos:**
- Conta GitHub
- Conta Render (free tier)
- Conta Lovable (free tier)

**Custo:** R$ 0/mês (100% free tier)

---

## 🎨 Personalização

### Modificar comportamento do navegador

Edite `screenshot_pdf.py` para ajustar:
- User-Agent
- Headers HTTP customizados
- Timezone
- Locale
- Scripts de inicialização (bypass de detecção)

### Ajustar tempo de processamento

No `api.py`, linha ~157, modifique:
```python
timeout_ms=30000,  # 30 segundos por página
```

### Tamanho dos lotes

Padrão: 20 URLs por lote (~2-3 minutos)

Para reduzir tempo por lote (se der timeout):
- No `api.py`, linha ~106: Ajuste validação de máximo de URLs

---

## 📁 Estrutura do Projeto

```
print_url/
├── api.py                      # Backend FastAPI (processamento em lotes)
├── screenshot_pdf.py           # Script principal de captura
├── requirements.txt            # Dependências Playwright
├── requirements-api.txt        # Dependências API
├── Dockerfile                  # Container Docker para Render
├── render.yaml                 # Configuração Render
├── DEPLOY_RENDER.md            # Guia de deploy completo
├── LOVABLE_PROMPT.md           # Prompt para criar frontend
├── SETUP_RAPIDO.md             # Setup em 5 passos
├── urls_com_tipo.csv           # Exemplo CSV
├── urls_com_tipo.txt           # Exemplo TXT
└── README.md                   # Este arquivo
```

---

## 💡 Casos de Uso

### 1. Captura de Base de Conhecimento para IA

Capture documentação completa de plataformas:
```csv
url;tipo
https://docs.empresa.com/artigo1;plataforma
https://help.empresa.com/artigo2;plataforma
https://app.empresa.com/help;aplicativo
```

Resultado: Documentos organizados prontos para embedding e ingestão em banco vetorial.

### 2. Dataset para Treinamento de Agentes

Crie dataset visual e textual (PDF) de múltiplas fontes para treinar agentes conversacionais com contexto visual.

### 3. Backup Periódico

Automatize via cron/scheduler para manter backup atualizado de documentação crítica.

---

## 🔒 Segurança e Privacidade

- ✅ Arquivos temporários são limpos automaticamente
- ✅ Dados sensíveis no `.gitignore`
- ✅ Sem armazenamento permanente no servidor
- ✅ Processamento isolado por job
- ⚠️ Use HTTPS em produção
- ⚠️ Adicione autenticação para uso público

---

## 🐛 Troubleshooting

### "ModuleNotFoundError: playwright"
```bash
pip install -r requirements.txt
python -m playwright install chromium
```

### "Timeout" ao processar URLs
- Aumentar `--timeout-ms`
- Verificar conectividade
- URLs muito pesadas (reduzir lote)

### Erro 500 no Render
- Ver logs no Render Dashboard
- Verificar se Chromium foi instalado (Docker resolve isso)
- Memória insuficiente (reduzir tamanho do lote)

### Pastas plataforma/aplicativo não criadas
- Verificar se CSV tem coluna `tipo`
- Verificar delimitador (`--delimiter ";"`)
- Ver logs do backend

---

## 📊 Performance

**Tempo de processamento:**
- 1 URL: ~5-10 segundos
- 20 URLs (1 lote): ~2-3 minutos
- 164 URLs (9 lotes): ~18-27 minutos

**Recursos:**
- Memória: ~500MB com Chromium
- CPU: 1 core (free tier)
- Disk: ~100MB por lote (temporário)

---

## 🛠️ Desenvolvimento

### Rodar backend localmente

```bash
# Instalar dependências
pip install -r requirements.txt requirements-api.txt
python -m playwright install chromium

# Rodar API
python api.py
# Acesse: http://localhost:8000
```

### Rodar testes

```bash
# Teste simples com 1 URL
curl -X POST http://localhost:8000/api/process-batch \
  -F "urls=https://www.google.com" \
  -F "batch_number=0" \
  -o teste.zip
```

---

## 📚 Documentação Adicional

- **[DEPLOY_RENDER.md](DEPLOY_RENDER.md)** - Guia completo de deploy no Render
- **[SETUP_RAPIDO.md](SETUP_RAPIDO.md)** - Setup em 5 passos
- **[LOVABLE_PROMPT.md](LOVABLE_PROMPT.md)** - Prompt para criar frontend

---

## 🤝 Contribuindo

Esta é uma ferramenta interna da Wiipo, mas sugestões são bem-vindas:

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/melhoria`)
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

---

## 📝 Changelog

### v2.0.0 (2026-02-05)
- ✨ Interface web com Lovable
- ✨ Backend FastAPI com processamento em lotes
- ✨ Deploy no Render (free tier)
- ✨ Organização automática por tipo (plataforma/aplicativo)
- ✨ Docker para deploy confiável

### v1.0.0 (2026-01-XX)
- 🎉 Versão inicial CLI
- ✅ Suporte a CSV e TXT
- ✅ Screenshots e PDFs via Playwright
- ✅ Coluna `tipo` para organização

---

## 📄 Licença

Este projeto é de uso interno da Wiipo.

---

## 👥 Time

Desenvolvido pela equipe de IA da Wiipo para acelerar a ingestão de documentos em agentes conversacionais.

---

## 🆘 Suporte

- **Issues:** Use GitHub Issues para reportar bugs
- **Documentação:** Ver arquivos `.md` no repositório
- **Deploy:** Ver `DEPLOY_RENDER.md`

---

**🚀 Pronto para capturar conhecimento e alimentar sua IA!**
