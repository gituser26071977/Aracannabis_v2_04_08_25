# 🚀 Como Iniciar o Software Aracannabis (Versão Sem IA)

## Pré-requisitos

Certifique-se de que você tem instalado:
- Python 3.8+
- Node.js 16+
- PostgreSQL 14+
- Git

## 📋 Passo a Passo para Iniciar

### 1. **Preparar o Ambiente**

```bash
# Navegar para o diretório do projeto
cd /home/mint/Desktop/Projetos&Clientes/Aracannabis/aracannabis_project/ARACANNABIS_PRONTUARIO_NO_AI

# Criar e ativar ambiente virtual Python (opcional)
python -m venv venv
source venv/bin/activate

# Instalar dependências Python
pip install -r requirements.txt
```

### 2. **Configurar Banco de Dados**

```bash
# Iniciar PostgreSQL
sudo systemctl start postgresql

# Criar banco de dados (se necessário)
createdb aracannabis
```

### 3. **Iniciar o Backend**

```bash
# Executar o servidor Flask com CORS livre
python app_cors_livre.py
```

O backend estará disponível em: `http://localhost:5002`

### 4. **Iniciar o Frontend**

```bash
# Navegar para o diretório do frontend
cd frontend

# Instalar dependências (primeira vez)
npm install

# Iniciar o servidor de desenvolvimento
npm start
```

O frontend estará disponível em: `http://localhost:3000`

## 🔐 Credenciais de Acesso

**Usuário Admin:**
- **Usuário:** `admin`
- **Senha:** `Aracannabis@2025`

## 🌐 URLs de Acesso

- **Frontend:** http://localhost:3000
- **Backend:** http://localhost:5002
- **Documentação da API:** http://localhost:5002 (página inicial)

## ⚡ Início Rápido

### Terminal 1 - Backend:
```bash
cd /home/mint/Desktop/Projetos&Clientes/Aracannabis/aracannabis_project/ARACANNABIS_PRONTUARIO_NO_AI
python app_cors_livre.py
```

### Terminal 2 - Frontend:
```bash
cd /home/mint/Desktop/Projetos&Clientes/Aracannabis/aracannabis_project/ARACANNABIS_PRONTUARIO_NO_AI/frontend
npm start
```

## 🔧 Solução de Problemas Comuns

### Backend não inicia:
```bash
# Verificar dependências
pip install -r requirements.txt

# Verificar conexão com PostgreSQL
psql -h localhost -U postgres -d aracannabis
```

### Frontend não inicia:
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm start
```

### Erro "Nenhuma resposta do servidor":
Verifique o arquivo `frontend/src/services/api.js`:
```javascript
// Configuração correta:
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:5002/api', // Porta 5002
});
```

## 🏗️ Estrutura do Projeto Atualizada

```
ARACANNABIS_PRONTUARIO_NO_AI/
├── frontend/             # Aplicação React (porta 3000)
│   ├── public/           # Assets estáticos
│   ├── src/              # Código fonte
│   └── package.json      # Dependências Node.js
├── routes/               # Endpoints da API
│   ├── auth.py           # Autenticação
│   ├── pacientes.py      # Gestão de pacientes
│   └── ...               # Outros endpoints
├── services/             # Lógica de negócios
├── app_cors_livre.py     # Ponto de entrada do backend (porta 5002)
├── config.py             # Configurações
├── .env                  # Variáveis de ambiente
└── requirements.txt      # Dependências Python
```

## 📝 Notas Importantes

1. O servidor backend usa CORS livre para desenvolvimento (não usar em produção)
2. O arquivo `.env` deve ser configurado com as credenciais do banco de dados
3. Para produção, use o arquivo `aracannabis.service` com systemd

## 🆘 Suporte Técnico

Para problemas:
1. Verifique os logs nos terminais do backend e frontend
2. Confirme se o PostgreSQL está rodando (`sudo systemctl status postgresql`)
3. Teste a conexão com o banco:
```bash
psql -h localhost -U postgres -d aracannabis
```

Atualizado em: 14/Jul/2025
