# 🚀 Como Iniciar o Software Aracannabis

## Pré-requisitos

Certifique-se de que você tem instalado:
- Python 3.8+
- Node.js 14+
- PostgreSQL
- Git

## 📋 Passo a Passo Simplificado

### 1. **Executar Script de Configuração**

```bash
# Navegar para o diretório do projeto
cd /home/mint/Desktop/Projetos&Clientes/Aracannabis/aracannabis_project/Manus_PRONTUARIO

# Dar permissão de execução ao script
chmod +x setup.sh

# Executar configuração automatizada
./setup.sh
```

### 2. **Iniciar Serviços**

**Terminal 1 - Backend:**
```bash
source venv/bin/activate
python app.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm start
```

## 🔐 Credenciais de Acesso

**Usuário Admin:**
- **Usuário:** `admin`
- **Senha:** `Aracannabis@2025`

## 🌐 URLs de Acesso

- **Frontend (Interface do Usuário):** http://localhost:3000
- **Backend (API):** http://localhost:5000
- **Documentação da API:** http://localhost:5000 (página inicial)

## ⚡ Início Rápido (Comandos Resumidos)

### Terminal 1 - Backend:
```bash
cd /home/mint/Desktop/Projetos&Clientes/Aracannabis/aracannabis_project/Manus_PRONTUARIO
python app.py
```

### Terminal 2 - Frontend:
```bash
cd /home/mint/Desktop/Projetos&Clientes/Aracannabis/aracannabis_project/Manus_PRONTUARIO/frontend
npm start
```

## 🔧 Script de Configuração Automatizada (setup.sh)

Introduzimos um script de configuração automatizada para simplificar a instalação:

- Verifica e instala dependências do sistema (Python, Node.js, PostgreSQL, Git)
- Configura ambiente virtual Python
- Instala dependências Python
- Configura banco de dados

### Se o backend não iniciar:
```bash
# Verificar dependências (executar dentro do venv)
source venv/bin/activate
pip install -r requirements.txt

# Verificar PostgreSQL
sudo systemctl status postgresql

# Verificar arquivo .env
cat .env
```

### Se o frontend não iniciar:
```bash
# Reinstalar dependências
cd frontend
rm -rf node_modules package-lock.json
npm install
npm start
```

### Se houver erro de banco de dados:
```bash
# Executar migração
python migrate_dosagens.py

# Criar usuário admin se necessário
python reset_admin_password.py
```

## 📱 Como Usar o Sistema

1. **Acesse:** http://localhost:3000
2. **Faça login** com as credenciais admin
3. **Navegue pelas funcionalidades:**
   - Gerenciar Pacientes
   - Registrar Dosagens
   - Acompanhar Sintomas
   - Visualizar Gráficos
   - Evoluções Médicas

## 🧪 Testar o Sistema

```bash
# Executar testes automatizados
python test_dosagens.py
```

## 📊 Status dos Serviços

Para verificar se tudo está funcionando:

1. **Backend:** Acesse http://localhost:5000 - deve mostrar página de status
2. **Endpoint de Saúde:** Acesse http://localhost:5000/api/health - deve retornar status "healthy"
3. **Frontend:** Acesse http://localhost:3000 - deve mostrar tela de login
4. **Banco:** Execute `python test_dosagens.py` - todos os testes devem passar

## 🔄 Parar os Serviços

- **Backend:** Pressione `Ctrl+C` no terminal do backend
- **Frontend:** Pressione `Ctrl+C` no terminal do frontend

## 📝 Logs e Debugging

- **Backend:** Logs aparecem no terminal onde executou `python app.py`
- **Frontend:** Logs aparecem no terminal onde executou `npm start`
- **Browser:** Abra DevTools (F12) para ver logs do frontend

---

## ⚠️ Importante

- Mantenha ambos os serviços (backend e frontend) rodando simultaneamente
- O frontend depende do backend para funcionar
- Use sempre as credenciais corretas para login
- Em caso de problemas, execute o script setup.sh novamente
- Verifique os logs nos terminais para diagnóstico
