# 🚀 Guia de Deploy - Render + Lovable

Este guia mostra como fazer deploy do backend no Render e conectar com o frontend no Lovable.

## 📋 Pré-requisitos

1. Conta no [Render](https://render.com) (free tier)
2. Conta no [Lovable](https://lovable.dev) (free tier)
3. Repositório GitHub com o código

---

## 🎨 PARTE 1: Deploy do Frontend no Lovable

### 1. Criar projeto no Lovable

1. Acesse https://lovable.dev
2. Crie novo projeto
3. Cole o prompt que foi fornecido
4. Aguarde o Lovable gerar o código
5. Anote a URL do seu app: `https://seu-app.lovable.app`

### 2. Configurar variável de ambiente (DEPOIS do deploy do backend)

No Lovable, adicione a variável de ambiente:
- Nome: `VITE_API_URL`
- Valor: `https://seu-backend.onrender.com` (URL do Render - passo 2)

---

## 🖥️ PARTE 2: Deploy do Backend no Render

### Opção A: Deploy via GitHub (Recomendado)

#### 1. Preparar repositório

```bash
# Certifique-se que o código está commitado
git add .
git commit -m "Add backend for web deployment"
git push origin main
```

#### 2. Criar novo Web Service no Render

1. Acesse https://dashboard.render.com
2. Clique em **"New +"** → **"Blueprint"**
3. Conecte seu repositório GitHub
4. Selecione o repositório `print_url`
5. O Render vai detectar o `render.yaml` automaticamente
6. Clique em **"Apply"**

O Render vai criar automaticamente:
- ✅ Web Service (`screenshot-api`)
- ✅ Background Worker (`screenshot-worker`)
- ✅ Redis database (`screenshot-redis`)

#### 3. Aguardar deploy

- Primeiro deploy leva ~10-15 minutos (instala Chromium)
- Acompanhe os logs em cada serviço
- Aguarde até aparecer "Live" (verde)

#### 4. Obter URL do backend

1. No dashboard do Render, clique em `screenshot-api`
2. Copie a URL: `https://screenshot-api-xxxx.onrender.com`
3. Teste no browser: deve retornar `{"status":"ok",...}`

### Opção B: Deploy Manual (sem render.yaml)

Se preferir criar manualmente:

#### 1. Criar Redis

1. **New +** → **Redis**
2. Nome: `screenshot-redis`
3. Plan: **Free**
4. Criar

#### 2. Criar Web Service

1. **New +** → **Web Service**
2. Conectar repositório GitHub
3. Configurações:
   - **Root Directory**: `backend`
   - **Build Command**:
     ```bash
     pip install -r requirements.txt && pip install -r ../requirements.txt && python -m playwright install chromium && python -m playwright install-deps
     ```
   - **Start Command**: `uvicorn api:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Free
4. **Environment Variables**:
   - `REDIS_URL`: Conectar ao Redis criado no passo 1

#### 3. Criar Worker

1. **New +** → **Background Worker**
2. Mesmo repositório
3. Configurações:
   - **Root Directory**: `backend`
   - **Build Command**: (mesmo do Web Service)
   - **Start Command**: `python worker.py`
   - **Plan**: Free
4. **Environment Variables**:
   - `REDIS_URL`: Mesmo Redis

---

## 🔗 PARTE 3: Conectar Frontend ao Backend

### 1. Atualizar variável no Lovable

No Lovable, vá em Settings → Environment Variables:
- `VITE_API_URL` = `https://screenshot-api-xxxx.onrender.com`

### 2. Testar integração

1. Acesse seu frontend: `https://seu-app.lovable.app`
2. Faça upload de um CSV de teste
3. Clique em "Processar"
4. Deve mostrar progresso em tempo real
5. Após completar, faça download do ZIP

---

## 🧪 Teste Local (Desenvolvimento)

### 1. Instalar Redis localmente

**Windows (WSL/Docker):**
```bash
docker run -d -p 6379:6379 redis:alpine
```

**Mac (Homebrew):**
```bash
brew install redis
brew services start redis
```

**Linux:**
```bash
sudo apt install redis-server
sudo systemctl start redis
```

### 2. Instalar dependências

```bash
cd backend
pip install -r requirements.txt
pip install -r ../requirements.txt
python -m playwright install chromium
```

### 3. Rodar API e Worker

Terminal 1 (API):
```bash
cd backend
uvicorn api:app --reload
```

Terminal 2 (Worker):
```bash
cd backend
python worker.py
```

### 4. Testar

```bash
# Upload
curl -X POST http://localhost:8000/api/upload \
  -F "file=@../MapeamentoBase.csv" \
  -F "delimiter=;"

# Status
curl http://localhost:8000/api/status/{job_id}

# Download
curl http://localhost:8000/api/download/{job_id} -o result.zip
```

---

## 📊 Monitoramento no Render

### Ver logs em tempo real

1. No dashboard do Render
2. Clique no serviço (`screenshot-api` ou `screenshot-worker`)
3. Aba **"Logs"**
4. Veja progresso do processamento

### Métricas

- **Queue stats**: `https://seu-backend.onrender.com/api/queue/stats`
- **Health check**: `https://seu-backend.onrender.com/`

---

## ⚠️ Limitações do Free Tier

### Render Free:
- ✅ Web Service + Worker + Redis = **FREE**
- ⚠️ **Sleep após 15 min inativo** (primeiro request demora ~30s para acordar)
- ✅ Worker processa SEM timeout (pode levar horas)
- ✅ 750h/mês de runtime (suficiente)

### Lovable Free:
- ✅ Hosting frontend = **FREE**
- ✅ Sem limite de requisições
- ⚠️ 1 app por conta no free tier

---

## 🐛 Troubleshooting

### Error: "Job não encontrado"
- Redis pode ter expirado os dados
- Verifique se o worker está rodando

### Error: "Timeout"
- Aumentar `timeout_ms` no upload
- Verificar se URLs são acessíveis

### Worker não processa
- Ver logs do worker no Render
- Verificar se Redis está conectado
- Verificar variável `REDIS_URL`

### Frontend não conecta ao backend
- Verificar CORS no `api.py`
- Verificar `VITE_API_URL` no Lovable
- Testar URL do backend no browser

---

## 🔒 Segurança (Produção)

Para usar em produção, adicione:

1. **Autenticação**: JWT tokens
2. **Rate limiting**: Limit de uploads por IP
3. **Validação**: Tamanho máximo de CSV
4. **CORS específico**: Apenas domínio do Lovable
5. **Limpeza automática**: Deletar arquivos antigos

---

## 💰 Custos

**Free Tier Total: R$ 0/mês**
- Render: Web + Worker + Redis = Free
- Lovable: Frontend = Free

**Se precisar escalar:**
- Render Pro: $7/mês por serviço
- Redis Render: $10/mês (1GB)

---

## 📚 Próximos Passos

1. [ ] Deploy no Render via Blueprint
2. [ ] Criar frontend no Lovable
3. [ ] Conectar `VITE_API_URL`
4. [ ] Testar com CSV real
5. [ ] Configurar limpeza automática de arquivos
6. [ ] Adicionar autenticação (opcional)

**Pronto! Sua ferramenta está no ar! 🎉**
