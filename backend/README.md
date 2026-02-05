# Backend API - Screenshot & PDF Generator

Backend FastAPI com processamento assíncrono usando RQ (Redis Queue).

## 🏗️ Arquitetura

```
api.py (FastAPI)
  ↓ enfileira jobs
Redis Queue
  ↓ processa
worker.py (Background Worker)
  ↓ gera
Screenshots + PDFs
  ↓ compacta
ZIP File
```

## 📁 Estrutura

```
backend/
├── api.py              # Endpoints HTTP
├── worker.py           # Background worker (processa jobs)
├── requirements.txt    # Dependências do backend
├── .env.example        # Exemplo de configuração
└── README.md           # Este arquivo
```

## 🚀 Rodando Localmente

### 1. Instalar Redis

```bash
# Docker
docker run -d -p 6379:6379 redis:alpine

# Ou via package manager
brew install redis  # Mac
sudo apt install redis-server  # Linux
```

### 2. Instalar dependências

```bash
cd backend
pip install -r requirements.txt
pip install -r ../requirements.txt
python -m playwright install chromium
```

### 3. Configurar variáveis

```bash
cp .env.example .env
# Editar .env se necessário (Redis URL)
```

### 4. Rodar API e Worker

Terminal 1 (API):
```bash
python api.py
# Ou: uvicorn api:app --reload
```

Terminal 2 (Worker):
```bash
python worker.py
```

## 📡 Endpoints

### POST /api/upload
Upload de CSV e criação de job.

**Request:**
```bash
curl -X POST http://localhost:8000/api/upload \
  -F "file=@meu_arquivo.csv" \
  -F "viewport_width=1920" \
  -F "viewport_height=1080" \
  -F "pdf_format=A4" \
  -F "landscape=false" \
  -F "delimiter=;"
```

**Response:**
```json
{
  "job_id": "abc123...",
  "status": "queued",
  "message": "Job enfileirado para processamento"
}
```

### GET /api/status/{job_id}
Consulta status do job.

**Response:**
```json
{
  "job_id": "abc123...",
  "status": "started",
  "progress": 45,
  "total": 164,
  "current_url": "https://exemplo.com",
  "errors": []
}
```

Status possíveis:
- `queued`: Na fila
- `started`: Processando
- `finished`: Completo (ZIP pronto)
- `failed`: Erro

### GET /api/download/{job_id}
Download do ZIP gerado.

**Response:**
Arquivo `capturas_TIMESTAMP.zip`

### DELETE /api/jobs/{job_id}
Remove job e arquivos (limpeza).

### GET /api/queue/stats
Estatísticas da fila.

**Response:**
```json
{
  "queued": 2,
  "started": 1,
  "finished": 10,
  "failed": 0
}
```

## 🔧 Configuração

### Variáveis de Ambiente

- `REDIS_URL`: URL do Redis (default: `redis://localhost:6379`)
- `PORT`: Porta da API (default: 8000)

### Parâmetros de Upload

| Parâmetro | Tipo | Default | Descrição |
|-----------|------|---------|-----------|
| `file` | File | required | Arquivo CSV |
| `viewport_width` | int | 1280 | Largura viewport |
| `viewport_height` | int | 800 | Altura viewport |
| `pdf_format` | str | A4 | Formato PDF (A4, Letter, etc) |
| `landscape` | bool | false | Orientação paisagem |
| `delimiter` | str | ; | Delimitador do CSV |

## 🐛 Debug

### Ver jobs na fila Redis

```bash
# CLI Redis
redis-cli
> KEYS *
> HGETALL rq:job:{job_id}
```

### Logs do worker

O worker imprime logs no stdout:
```
🚀 Worker iniciado. Aguardando jobs...
Processando job abc123...
Progress: 45/164
```

## 📦 Deploy no Render

Ver arquivo `../DEPLOY.md` para instruções completas.

**Quick setup:**
```bash
# Push para GitHub
git push origin main

# No Render: New > Blueprint
# Selecionar repositório
# Render detecta render.yaml automaticamente
```

## 🧪 Testes

```bash
# Upload de teste
curl -X POST http://localhost:8000/api/upload \
  -F "file=@../urls_com_tipo.csv" \
  -F "delimiter=,"

# Verificar status (substitua {job_id})
curl http://localhost:8000/api/status/{job_id}

# Download
curl http://localhost:8000/api/download/{job_id} -o test.zip
```

## ⏱️ Performance

**Tempo de processamento:**
- 1 URL: ~5-10 segundos
- 100 URLs: ~8-15 minutos
- 200 URLs: ~15-30 minutos

**Limitações:**
- Processamento sequencial (1 URL por vez)
- Memory: ~500MB com Chromium
- Disk: ~100MB por job (temporário)

## 🔒 Segurança

**Para produção, adicione:**
- [ ] Autenticação (JWT)
- [ ] Rate limiting
- [ ] Validação de tamanho de arquivo
- [ ] CORS específico (não `*`)
- [ ] Sanitização de inputs
- [ ] Limpeza automática de arquivos antigos

## 📚 Tecnologias

- **FastAPI**: Web framework
- **RQ**: Redis Queue para background jobs
- **Redis**: Fila e cache
- **Playwright**: Automação de browser
- **Uvicorn**: ASGI server

## 🆘 Suporte

Ver troubleshooting em `../DEPLOY.md`
