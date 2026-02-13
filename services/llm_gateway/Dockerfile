FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Usuario nao-root
RUN useradd -m llmgateway
USER llmgateway

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
