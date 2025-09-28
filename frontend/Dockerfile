# Dockerfile para o frontend React
FROM node:18-alpine

ARG REACT_APP_API_URL=http://localhost:5005

WORKDIR /app

# Copiar arquivos de dependências
COPY package*.json ./

# Instalar dependências
RUN npm install

# Copiar o restante do código da aplicação
COPY . .

# Set environment variable for build
ENV REACT_APP_API_URL=$REACT_APP_API_URL

# Construir a aplicação React para produção
RUN npm run build

# Instalar servidor HTTP simples para servir a aplicação
RUN npm install -g serve

# Expor a porta que o servidor vai usar
EXPOSE 3000

# Comando para rodar a aplicação
CMD ["serve", "-s", "build", "-l", "3000"]
