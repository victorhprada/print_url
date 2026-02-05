# 🚀 Guia de Deploy - Render (Processamento em Lotes)

Este guia mostra como fazer deploy do backend no Render usando **processamento em lotes** (sem workers).

## 🎯 Arquitetura

```
Frontend (Lovable)
    ↓ Divide em lotes de 20 URLs
API Render (Web Service)
    ↓ Processa 1 lote por vez (~2-3 min)
    ↓ Retorna ZIP
Frontend combina resultados
```

**Vantagens:**
- ✅ 100% FREE (Render Free Tier)
- ✅ Sem Redis, sem Workers
- ✅ Simples de manter

**Limitação:**
- ⚠️ Usuário precisa manter aba aberta durante processamento (~30 min para 164 URLs)

---

## 📋 Passo a Passo

### 1️⃣ Commit e Push para GitHub

```bash
cd c:\Users\victor.prada\Documents\Print_url\print_url

# Verificar arquivos
git status

# Adicionar tudo
git add .

# Commit
git commit -m "Refactor: Use batch processing for Render Free Tier compatibility"

# Push
git push origin main
```

### 2️⃣ Deploy no Render

**Opção A: Via Blueprint (Recomendado)**

1. Acesse: https://dashboard.render.com
2. Clique em **"New +"** → **"Blueprint"**
3. Conecte seu repositório GitHub
4. Selecione `print_url`
5. Render detecta `render.yaml` automaticamente
6. Clique em **"Apply"**
7. Aguarde deploy (~10 minutos - instala Chromium)

**Opção B: Manual**

1. **New +** → **Web Service**
2. Conecte repositório GitHub
3. Configurações:
   - **Name**: `screenshot-batch-api`
   - **Runtime**: Python
   - **Build Command**:
     ```bash
     pip install -r requirements.txt && pip install -r requirements-api.txt && python -m playwright install chromium
     ```
   - **Start Command**: `uvicorn api:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Free
4. Deploy

### 3️⃣ Obter URL do Backend

1. No dashboard do Render, clique no serviço `screenshot-batch-api`
2. Copie a URL: `https://screenshot-batch-api-xxxx.onrender.com`
3. Teste no browser: deve retornar `{"status":"ok",...}`

### 4️⃣ Criar Frontend no Lovable

1. Acesse: https://lovable.dev
2. Crie novo projeto
3. Copie o prompt de `LOVABLE_PROMPT.md` (COMPLETO)
4. Cole no Lovable
5. Aguarde gerar

### 5️⃣ Configurar Frontend

No Lovable, em **Settings** → **Environment Variables**:
- `VITE_API_URL` = `https://screenshot-batch-api-xxxx.onrender.com`

### 6️⃣ Testar!

1. Acesse seu frontend: `https://seu-app.lovable.app`
2. Upload de `MapeamentoBase.csv`
3. Veja preview: "164 URLs detectadas (9 lotes)"
4. Configure delimitador: `;`
5. Clique "Processar Tudo"
6. Aguarde processamento (~27-30 minutos)
7. Baixe ZIPs individuais ou todos combinados!

---

## 🧪 Teste Local

### Backend

```bash
# Instalar dependências
pip install -r requirements.txt
pip install -r requirements-api.txt
python -m playwright install chromium

# Rodar API
python api.py
# ou: uvicorn api:app --reload
```

Teste: http://localhost:8000

### Frontend (Lovable local)

No Lovable, configure:
```
VITE_API_URL=http://localhost:8000
```

---

## 📊 Como Funciona

### Fluxo de Processamento:

```
1. Frontend: Upload CSV (164 URLs)
2. Frontend: Preview → "9 lotes necessários"
3. Frontend: Clica "Processar"

Loop para cada lote:
  4. Frontend → API: POST /process-batch
     - Envia 20 URLs
     - batch_number: 0
  5. API: Processa 20 URLs (~2-3 min)
  6. API → Frontend: Retorna lote1.zip
  7. Frontend: Salva ZIP, atualiza progresso
  8. Próximo lote...

9. Frontend: Todos lotes completos
10. Opção: Baixar todos ou individuais
```

### Tempo Estimado:

- **1 lote (20 URLs)**: ~2-3 minutos
- **9 lotes (164 URLs)**: ~18-27 minutos
- **Cada request < 15 min**: ✅ Dentro do limite do Render Free

---

## ⚙️ Render Free Tier - Características

**Inclui:**
- ✅ Web Service gratuito
- ✅ 750h/mês de runtime
- ✅ Sleep após 15min inativo (primeiro request ~30s)
- ✅ 512MB RAM
- ✅ SSL automático

**Limitações:**
- ⚠️ Timeout de 15 minutos por request HTTP (nossos lotes são ~2-3 min ✓)
- ⚠️ Sem background workers no free tier
- ⚠️ Container hiberna após inatividade

---

## 🐛 Troubleshooting

### "Build failed"
- Ver logs no Render
- Comum: timeout ao instalar Chromium (tente rebuild)

### "504 Gateway Timeout"
- Lote com muitas URLs pesadas
- Reduzir tamanho do lote (15 em vez de 20)

### "Connection closed"
- Render hibernou (primeiro request demora)
- Aguarde ~30s e tente novamente

### Chromium não funciona
- Verificar se `playwright install chromium` rodou no build
- Ver logs: "Chromium 129.0.6668.29 downloaded"

---

## 💡 Otimizações Futuras

- [ ] Processar lotes em paralelo (2-3 simultâneos)
- [ ] Cache de screenshots (URLs repetidas)
- [ ] Compressão de imagens
- [ ] Webhook para notificar quando completo
- [ ] Upload direto para S3/Cloud Storage

---

## 💰 Custos

**FREE:** R$ 0/mês
- Render Free Tier: $0
- Lovable: $0

**Se precisar escalar:**
- Render Starter: $7/mês
- Permite workers + mais recursos

---

## 📚 Arquivos Importantes

- `api.py` - Backend FastAPI
- `render.yaml` - Config do Render
- `LOVABLE_PROMPT.md` - Prompt do frontend
- `screenshot_pdf.py` - Script principal (já existente)

---

## ✅ Checklist

- [ ] Código commitado no GitHub
- [ ] Deploy no Render via Blueprint
- [ ] URL do backend obtida e testada
- [ ] Frontend criado no Lovable
- [ ] `VITE_API_URL` configurada
- [ ] Teste completo com CSV real

---

**Pronto! Sua ferramenta está no ar com 100% free tier! 🎉**

**Tempo total de setup: ~15-20 minutos**
