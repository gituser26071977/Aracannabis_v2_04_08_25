# 🚀 Versões do Sistema Aracannabis

## 📋 Duas Versões Disponíveis

O sistema Aracannabis agora possui **duas versões** para atender diferentes necessidades:

### 1. **Versão COMPLETA (com IA)** 
- **Arquivo:** `app.py`
- **Porta:** 5000
- **URL:** http://localhost:5000

### 2. **Versão SIMPLIFICADA (sem IA)**
- **Arquivo:** `app_sem_ia.py` 
- **Porta:** 5010
- **URL:** http://localhost:5010

---

## 🔍 Comparação das Versões

| Funcionalidade | Versão COM IA | Versão SEM IA |
|---|---|---|
| **Gerenciamento de Pacientes** | ✅ | ✅ |
| **Registro de Sintomas** | ✅ | ✅ |
| **Controle de Dosagens** | ✅ | ✅ |
| **Histórico de Evoluções** | ✅ | ✅ |
| **Agendamento de Consultas** | ✅ | ✅ |
| **Conformidade LGPD** | ✅ | ✅ |
| **Segurança Avançada** | ✅ | ✅ |
| **Import/Export com IA** | ✅ | ❌ |
| **Configuração de IA** | ✅ | ❌ |
| **Análise Inteligente** | ✅ | ❌ |

---

## 🚀 Como Iniciar Cada Versão

### **Versão COMPLETA (com IA)**
```bash
# Terminal 1 - Backend COM IA
cd "/home/mint/Desktop/Projetos&Clientes/Aracannabis/aracannabis_project/Manus_PRONTUARIO"
python3 app.py

# Terminal 2 - Frontend
cd "/home/mint/Desktop/Projetos&Clientes/Aracannabis/aracannabis_project/Manus_PRONTUARIO/frontend"
npm start
```

**Acesso:** 
- Backend: http://localhost:5000
- Frontend: http://localhost:3000

### **Versão SIMPLIFICADA (sem IA)**
```bash
# Terminal 1 - Backend SEM IA
cd "/home/mint/Desktop/Projetos&Clientes/Aracannabis/aracannabis_project/Manus_PRONTUARIO"
python3 app_sem_ia.py

# Terminal 2 - Frontend (mesmo para ambas)
cd "/home/mint/Desktop/Projetos&Clientes/Aracannabis/aracannabis_project/Manus_PRONTUARIO/frontend"
npm start
```

**Acesso:**
- Backend: http://localhost:5010
- Frontend: http://localhost:3000

---

## 🎯 Quando Usar Cada Versão

### **Use a Versão COM IA quando:**
- Precisar de funcionalidades de análise inteligente
- Quiser usar import/export automatizado
- Tiver configurado APIs de IA (OpenAI, etc.)
- Precisar de recursos avançados de processamento

### **Use a Versão SEM IA quando:**
- Quiser um sistema mais simples e estável
- Não precisar de funcionalidades de IA
- Tiver problemas com dependências de IA
- Quiser economia de recursos do servidor

---

## 🔧 Configuração e Dependências

### **Dependências Comuns (ambas versões):**
```bash
pip3 install flask flask-cors flask-jwt-extended flask-sqlalchemy flask-limiter python-dotenv psycopg2-binary
```

### **Dependências Extras (só versão COM IA):**
```bash
pip3 install openai crewai langchain requests beautifulsoup4
```

---

## 📊 Status e Monitoramento

### **Verificar qual versão está rodando:**
```bash
# Verificar porta 5000 (versão COM IA)
curl http://localhost:5000/api/status

# Verificar porta 5010 (versão SEM IA)  
curl http://localhost:5010/api/status
```

### **Verificar processos ativos:**
```bash
# Ver qual versão está rodando
netstat -tlnp | grep :500
```

---

## 🔄 Alternando Entre Versões

### **Para trocar da versão COM IA para SEM IA:**
1. Pare o backend atual: `Ctrl+C`
2. Execute: `python3 app_sem_ia.py`
3. Acesse: http://localhost:5010

### **Para trocar da versão SEM IA para COM IA:**
1. Pare o backend atual: `Ctrl+C`
2. Execute: `python3 app.py`
3. Acesse: http://localhost:5000

---

## 🔐 Credenciais (iguais para ambas)

- **Usuário:** `admin`
- **Senha:** `Aracannabis@2025`

---

## ⚠️ Observações Importantes

1. **Frontend único:** O mesmo frontend funciona com ambas as versões
2. **Banco de dados:** Ambas usam o mesmo banco PostgreSQL
3. **Portas diferentes:** 5000 (com IA) e 5010 (sem IA)
4. **Segurança:** Ambas têm o mesmo nível de segurança
5. **LGPD:** Ambas são totalmente compatíveis com LGPD

---

## 🆘 Solução de Problemas

### **Se a versão COM IA não funcionar:**
- Use a versão SEM IA como alternativa
- Verifique se as dependências de IA estão instaladas
- Verifique as configurações de API no arquivo `.env`

### **Se ambas não funcionarem:**
- Verifique se o PostgreSQL está rodando
- Verifique se as dependências básicas estão instaladas
- Execute: `pip3 install -r requirements.txt`

---

## 📈 Recomendações

- **Para produção:** Use a versão SEM IA (mais estável)
- **Para desenvolvimento:** Use a versão COM IA (mais recursos)
- **Para testes:** Alterne entre as duas conforme necessário
