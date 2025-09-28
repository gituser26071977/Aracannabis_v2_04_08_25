# Dockerfile para a aplicação Flask com Gunicorn

# 1. Usar uma imagem base do Python
FROM python:3.11-slim

# 2. Definir o diretório de trabalho
WORKDIR /app

# 3. Copiar o arquivo de dependências
COPY requirements.txt .

# 4. Instalar as dependências
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copiar todo o código da aplicação
COPY . .

# 6. Expor a porta que a aplicação usa
EXPOSE 5011

# 7. Comando para iniciar a aplicação com Gunicorn
#    - 'app:create_app()' aponta para a função factory no arquivo 'app.py'
#    - '--bind 0.0.0.0:5011' faz o Gunicorn ouvir na porta correta
#    - '--workers 3' é um bom ponto de partida para o número de processos
#    - '--log-level=info' para vermos os logs
CMD ["gunicorn", "--bind", "0.0.0.0:5011", "--workers", "3", "--log-level=info", "app:create_app()"]
