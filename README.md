# Aracannabis Prontuário Eletrônico

Sistema de prontuário eletrônico para acompanhamento de pacientes em tratamento com cannabis medicinal.

## Estrutura do Projeto

O projeto está organizado em duas partes principais:

1. **Backend**: API RESTful desenvolvida com Flask
2. **Frontend**: Interface de usuário desenvolvida com React

## Requisitos

### Backend
- Python 3.8+
- PostgreSQL 12+
- Dependências Python listadas em `requirements.txt`

### Frontend
- Node.js 14+
- npm 6+
- Dependências JavaScript listadas em `package.json`

## Configuração do Ambiente de Desenvolvimento

### Backend

1. Crie um ambiente virtual Python:
```bash
python -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Configure as variáveis de ambiente:
```bash
cp .env.example .env
# Edite o arquivo .env com suas configurações
```

4. Inicialize o banco de dados:
```bash
# Certifique-se de que o PostgreSQL está rodando
# Crie o banco de dados 'aracannabis'
flask db init
flask db migrate
flask db upgrade
```

5. Execute o servidor de desenvolvimento:
```bash
flask run
```

### Frontend

1. Instale as dependências:
```bash
npm install
```

2. Execute o servidor de desenvolvimento:
```bash
npm start
```

## Implantação em Produção

Para implantar o aplicativo em um servidor Debian 12, siga as instruções detalhadas no arquivo `deployment_plan.md`.

## Funcionalidades

- Autenticação de profissionais de saúde
- Cadastro e gerenciamento de pacientes
- Registro e acompanhamento de sintomas
- Controle de dosagens de medicamentos
- Registro de evoluções médicas
- Geração de gráficos para visualização da evolução do tratamento
- Conformidade com LGPD (Lei Geral de Proteção de Dados)

## Segurança

- Autenticação via JWT (JSON Web Tokens)
- Senhas armazenadas com hash seguro
- Registro de atividades para auditoria
- Controle de acesso baseado em funções

## Licença

Este projeto é propriedade da Aracannabis e seu uso é restrito conforme os termos acordados.
