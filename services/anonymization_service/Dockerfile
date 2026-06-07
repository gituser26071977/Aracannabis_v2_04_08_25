FROM python:3.9-slim

WORKDIR /app

# Instalar dependências de sistema para compilar crypto e postgres
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Baixar o modelo spaCy durante o build (internet necessária apenas aqui)
RUN python -m spacy download pt_core_news_lg || python -m spacy download pt_core_news_sm

# Copiar o código
COPY . .

# Expor porta
EXPOSE 8000

# Rodar com usuario não root (segurança)
RUN useradd -m anonymizer
USER anonymizer

# Rodar uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
