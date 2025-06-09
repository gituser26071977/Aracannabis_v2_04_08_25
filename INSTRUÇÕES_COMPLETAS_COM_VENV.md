# 🚀 Instruções Completas - Aracannabis com Ambiente Virtual

## ⚠️ **IMPORTANTE: USAR AMBIENTE VIRTUAL**

Sim, é **NECESSÁRIO** ativar o ambiente virtual antes de executar o sistema!

---

## 🔧 **Como Iniciar o Sistema Corretamente**

### **Passo 1: Ativar o Ambiente Virtual**
```bash
# SEMPRE execute este comando primeiro:
source venv/bin/activate

# Você verá (venv) no início do prompt:
# (venv) mint@computer:~/path$
```

### **Passo 2: Verificar se está ativo**
```bash
# Verificar se o ambiente virtual está ativo
which python3
# Deve mostrar: /caminho/para/venv/bin/python3

# Verificar versão
python3 --version
```

### **Passo 3: Instalar/Atualizar Dependências (se necessário)**
```bash
# Com o venv ativo, instalar dependências
pip3 install -r requirements.txt

# Para funcionalidades de IA (opcional)
pip3 install requests python-dotenv
```

---

## 🚀 **Comandos Corretos para Iniciar**

### **Versão SEM IA (Recomendada para começar)**
```bash
# Terminal 1 - Backend SEM IA
source venv/bin/activate
python3 app_sem_ia.py

# Terminal 2 - Frontend
cd frontend
npm start
```
**Acesso:** http://localhost:5010 (backend) + http://localhost:3000 (frontend)

### **Versão COM IA (Após configurar IA)**
```bash
# Terminal 1 - Backend COM IA
source venv/bin/activate
python3 app.py

# Terminal 2 - Frontend
cd frontend
npm start
```
**Acesso:** http://localhost:5000 (backend) + http://localhost:3000 (frontend)

---

## 🤖 **Configurar IA (Opcional)**

### **Passo 1: Copiar Configurações**
```bash
# Com venv ativo
source venv/bin/activate
cp .env.ai_example .env
```

### **Passo 2: Obter Chave Groq (GRATUITA)**
1. Acesse: https://console.groq.com/
2. Crie conta gratuita
3. Gere API key
4. Edite o arquivo `.env`:
```bash
nano .env
# Adicione:
DEFAULT_LLM_PROVIDER=groq
DEFAULT_LLM_MODEL=llama-3.1-70b-versatile
GROQ_API_KEY=GROQ_KEY_REDACTED-chave-aqui
```

### **Passo 3: Testar IA**
```bash
# Com venv ativo
source venv/bin/activate
python3 test_ai_optimized.py
```

---

## 🔍 **Verificar se Tudo Está Funcionando**

### **1. Verificar Ambiente Virtual**
```bash
source venv/bin/activate
which python3
# Deve mostrar caminho do venv
```

### **2. Verificar Dependências**
```bash
# Com venv ativo
pip3 list | grep -i flask
pip3 list | grep -i requests
```

### **3. Testar Backend**
```bash
# Com venv ativo
source venv/bin/activate

# Testar versão SEM IA
python3 app_sem_ia.py
# Deve iniciar na porta 5010

# OU testar versão COM IA (se configurada)
python3 app.py
# Deve iniciar na porta 5000
```

### **4. Testar Frontend**
```bash
# Em outro terminal
cd frontend
npm start
# Deve iniciar na porta 3000
```

---

## 🚨 **Solução de Problemas Comuns**

### **Erro: "python3: command not found"**
```bash
# Ativar o ambiente virtual primeiro
source venv/bin/activate
```

### **Erro: "ModuleNotFoundError"**
```bash
# Com venv ativo, reinstalar dependências
source venv/bin/activate
pip3 install -r requirements.txt
```

### **Erro: "Port already in use"**
```bash
# Verificar processos rodando
netstat -tlnp | grep :500

# Matar processo se necessário
kill -9 PID_DO_PROCESSO
```

### **Frontend não conecta com backend**
- Verifique se o backend está rodando
- Verifique se está na porta correta (5000 ou 5010)
- Verifique se não há firewall bloqueando

---

## 📋 **Resumo dos Comandos Essenciais**

### **Iniciar Sistema (Versão Estável)**
```bash
# Terminal 1
source venv/bin/activate
python3 app_sem_ia.py

# Terminal 2
cd frontend
npm start
```

### **Parar Sistema**
```bash
# Em cada terminal, pressione:
Ctrl + C
```

### **Desativar Ambiente Virtual**
```bash
deactivate
```

---

## 🎯 **Credenciais de Login**

- **Usuário:** `admin`
- **Senha:** `Aracannabis@2025`

---

## 📊 **URLs de Acesso**

| Versão | Backend | Frontend | Descrição |
|---|---|---|---|
| **SEM IA** | http://localhost:5010 | http://localhost:3000 | Estável, sempre funciona |
| **COM IA** | http://localhost:5000 | http://localhost:3000 | Recursos avançados de IA |

---

## ✅ **Checklist de Verificação**

Antes de usar o sistema, verifique:

- [ ] Ambiente virtual ativado (`source venv/bin/activate`)
- [ ] Dependências instaladas (`pip3 install -r requirements.txt`)
- [ ] PostgreSQL rodando (`sudo systemctl status postgresql`)
- [ ] Backend iniciado (porta 5000 ou 5010)
- [ ] Frontend iniciado (porta 3000)
- [ ] Login funcionando (admin / Aracannabis@2025)

---

## 🎉 **Pronto para Usar!**

Com o ambiente virtual ativado e os comandos corretos, o sistema funcionará perfeitamente.

**Recomendação:** Comece sempre com a versão SEM IA para garantir que tudo está funcionando, depois configure a IA se precisar dos recursos avançados.
