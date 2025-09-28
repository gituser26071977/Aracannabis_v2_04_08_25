# Aracannabis Prontuário - Versão Sem IA

Este diretório contém a versão do sistema Aracannabis Prontuário sem as funcionalidades de Inteligência Artificial.

## Estrutura do Projeto

- `backend/`: Contém o código-fonte do backend (API Flask).
- `frontend/`: Contém o código-fonte do frontend (Aplicação React).

## Como Rodar o Projeto

### 1. Backend

1.  **Navegue até o diretório do backend:**
    ```bash
    cd versao_sem_ia/backend
    ```

2.  **Crie e ative um ambiente virtual (recomendado):**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # No Linux/macOS
    # venv\Scripts\activate   # No Windows
    ```

3.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure as variáveis de ambiente:**
    Crie um arquivo `.env` na raiz do diretório `backend` com as seguintes variáveis:
    ```env
    FLASK_ENV=development
    DATABASE_URL=postgresql://user:password@host:port/database_name
    JWT_SECRET_KEY=sua_chave_secreta_jwt
    SECRET_KEY=sua_chave_secreta_flask
    ```
    *Substitua `user`, `password`, `host`, `port` e `database_name` pelos dados do seu banco de dados PostgreSQL.*
    *Gere chaves secretas fortes para `JWT_SECRET_KEY` e `SECRET_KEY`.*

5.  **Execute o backend:**
    ```bash
    flask run --host=0.0.0.0 --port=5011
    ```
    O backend estará disponível em `http://localhost:5011`.

### 2. Frontend

1.  **Navegue até o diretório do frontend:**
    ```bash
    cd versao_sem_ia/frontend
    ```

2.  **Instale as dependências:**
    ```bash
    npm install
    ```

3.  **Execute o frontend:**
    ```bash
    npm start
    ```
    O frontend estará disponível em `http://localhost:3000`.

### Acesso ao Sistema

Após iniciar o backend e o frontend, acesse `http://localhost:3000` no seu navegador para utilizar o sistema.
