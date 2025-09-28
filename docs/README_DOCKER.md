# Aracannabis - Executando com Docker

Este guia explica como executar a aplicação Aracannabis usando Docker.

## Pré-requisitos

- Docker instalado
- Docker Compose instalado

## Estrutura do Docker

O projeto utiliza três containers:

1. **db**: PostgreSQL database
2. **backend**: Flask API server
3. **frontend**: React application

## Como executar

1. **Construir e iniciar todos os serviços:**
   ```bash
   docker-compose up --build
   ```

2. **Executar em modo detached (background):**
   ```bash
   docker-compose up --build -d
   ```

## Acesso às aplicações

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:5004
- **Database**: postgresql://postgres:postgres@localhost:5432/aracannabis

## Comandos úteis

- **Parar todos os serviços:**
  ```bash
  docker-compose down
  ```

- **Visualizar logs:**
  ```bash
  docker-compose logs
  ```

- **Visualizar logs de um serviço específico:**
  ```bash
  docker-compose logs backend
  ```

- **Acessar o shell de um container:**
  ```bash
  docker-compose exec backend sh
  docker-compose exec frontend sh
  docker-compose exec db sh
  ```

## Configuração

As variáveis de ambiente podem ser configuradas no arquivo `.env` na raiz do projeto.

## Primeiro acesso

1. Acesse http://localhost:3000
2. Faça login com as credenciais padrão (se houver) ou registre um novo usuário
3. O sistema criará automaticamente as tabelas do banco de dados na primeira execução

## Solução de problemas

- Se houver problemas de permissão com o banco de dados, verifique se o volume do PostgreSQL está limpo:
  ```bash
  docker-compose down -v
  ```

- Se houver problemas de build, tente limpar o cache do Docker:
  ```bash
  docker system prune -af