# Usa imagem oficial do Playwright com Python e Chromium pré-instalado
FROM mcr.microsoft.com/playwright/python:v1.47.0-jammy

# Define diretório de trabalho
WORKDIR /app

# Copia arquivos de dependências
COPY requirements.txt requirements-api.txt ./

# Instala dependências Python
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r requirements-api.txt

# Copia código da aplicação
COPY api.py screenshot_pdf.py ./

# Cria diretórios temporários
RUN mkdir -p /tmp/uploads /tmp/outputs

# Expõe porta
EXPOSE 8000

# Variável de ambiente para porta (Render injeta automaticamente)
ENV PORT=8000

# Comando de inicialização
CMD uvicorn api:app --host 0.0.0.0 --port $PORT
