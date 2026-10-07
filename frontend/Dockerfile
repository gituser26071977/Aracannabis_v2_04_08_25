# Dockerfile para o frontend React
FROM node:18-alpine

# IMPORTANT: Declare ARG before any RUN commands that need it
ARG REACT_APP_API_URL=http://localhost:5002

WORKDIR /app

# Copiar arquivos de dependências
COPY package*.json ./

# Instalar dependências
RUN npm install

# Copiar o restante do código da aplicação
COPY . .

# CRITICAL: Set ENV before npm run build so React bakes it into the bundle
ENV REACT_APP_API_URL=$REACT_APP_API_URL
# O eslint embutido do CRA quebra o build por causa da config do
# eslint-plugin-jest (env "jest/globals" unknown) em eslint-config-react-app.
# Lint é feito à parte; desabilitamos o plugin eslint apenas no build.
ENV DISABLE_ESLINT_PLUGIN=true

# Construir a aplicação React para produção
RUN npm run build

# Instalar servidor HTTP simples para servir a aplicação
RUN npm install -g serve

# Expor a porta que o servidor vai usar
EXPOSE 3000

# Comando para rodar a aplicação
CMD ["serve", "-s", "build", "-l", "3000"]
