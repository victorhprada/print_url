# ⚡ Setup Rápido - Processamento em Lotes

## 🎯 O que foi criado:

### ✅ Backend (Render Free Tier)
- `api.py` - FastAPI com endpoint de processamento em lotes
- `requirements-api.txt` - Dependências da API
- `render.yaml` - Configuração simplificada (apenas Web Service)

### ✅ Documentação
- `LOVABLE_PROMPT.md` - Prompt completo para criar frontend
- `DEPLOY_RENDER.md` - Guia de deploy detalhado
- `SETUP_RAPIDO.md` - Este arquivo (referência rápida)

---

## 🚀 Deploy em 5 Passos (15-20 min)

### 1. Commit e Push
```bash
git add .
git commit -m "Add batch processing for Render Free Tier"
git push origin main
```

### 2. Deploy no Render
1. https://dashboard.render.com
2. New + → Blueprint
3. Selecione repositório `print_url`
4. Apply (aguarde ~10 min)
5. **Copie URL**: `https://screenshot-batch-api-xxxx.onrender.com`

### 3. Criar Frontend no Lovable
1. https://lovable.dev → Novo projeto
2. Cole prompt de `LOVABLE_PROMPT.md` (completo!)
3. Aguarde gerar
4. **Anote URL**: `https://seu-app.lovable.app`

### 4. Conectar Frontend ↔ Backend
No Lovable → Settings → Environment Variables:
```
VITE_API_URL=https://screenshot-batch-api-xxxx.onrender.com
```

### 5. Testar
1. Acesse frontend
2. Upload CSV
3. Processe (aguarde ~30 min para 164 URLs)
4. Download!

---

## 📊 Como Funciona

**Arquitetura:**
```
164 URLs → Frontend divide em 9 lotes de 20
↓
Lote 1 (20 URLs) → API Render (~2-3 min) → lote1.zip
Lote 2 (20 URLs) → API Render (~2-3 min) → lote2.zip
...
Lote 9 (4 URLs) → API Render (~1 min) → lote9.zip
↓
Frontend: Download todos ou individuais
```

**Vantagens:**
- ✅ 100% Free (Render + Lovable)
- ✅ Sem timeout (cada lote < 15 min)
- ✅ Simples de manter

**Limitação:**
- ⚠️ Usuário mantém aba aberta (~30 min total)

---

## 🧪 Teste Local

```bash
# Backend
pip install -r requirements.txt requirements-api.txt
python -m playwright install chromium
python api.py
# → http://localhost:8000

# Frontend (Lovable)
VITE_API_URL=http://localhost:8000
```

---

## 📁 Estrutura Final

```
print_url/
├── api.py                    ✅ Backend FastAPI
├── screenshot_pdf.py         ✅ Script principal
├── requirements.txt          ✅ Deps do Playwright
├── requirements-api.txt      ✅ Deps da API
├── render.yaml               ✅ Config Render
├── LOVABLE_PROMPT.md         ✅ Prompt frontend
├── DEPLOY_RENDER.md          ✅ Guia completo
├── SETUP_RAPIDO.md           ✅ Este arquivo
└── README.md                 ✅ Docs original
```

---

## 🔧 Configuração no Render

**Build Command:**
```bash
pip install -r requirements.txt && pip install -r requirements-api.txt && python -m playwright install chromium
```

**Start Command:**
```bash
uvicorn api:app --host 0.0.0.0 --port $PORT
```

---

## 💰 Custo: R$ 0/mês

- Render Web Service: Free
- Lovable: Free
- **Total: Gratuito!**

---

## 📚 Documentação

- **Setup Rápido**: Este arquivo
- **Deploy Detalhado**: `DEPLOY_RENDER.md`
- **Prompt Frontend**: `LOVABLE_PROMPT.md`

---

## 🆘 Problemas Comuns

**"Build failed"**
→ Rebuild no Render (timeout ao baixar Chromium)

**"504 Timeout"**
→ Lote muito grande, reduzir para 15 URLs

**"Connection closed"**
→ Render hibernou, aguarde 30s

---

**Pronto! Siga os 5 passos acima e em 20 minutos está no ar! 🚀**
