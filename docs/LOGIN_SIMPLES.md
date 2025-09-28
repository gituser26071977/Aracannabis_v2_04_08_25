# 🔐 INSTRUÇÕES DE LOGIN - SISTEMA ARACANNABIS

## ✅ CREDENCIAIS CONFIRMADAS

### **Login Principal:**
```
Usuário: admin
Senha: Aracannabis@2025
```

### **Login Alternativo:**
```
Usuário: admin3
Senha: Admin@123456
```

## 🚀 COMO FAZER LOGIN

### **1. Acesse a Página:**
- Abra seu navegador
- Digite: **http://localhost:3000**
- Pressione Enter

### **2. Encontre o Botão de Login:**
- Procure por "Login" no canto superior direito
- OU clique no menu hambúrguer (☰) e selecione "Login"

### **3. Digite as Credenciais:**
- **Usuário**: admin
- **Senha**: Aracannabis@2025
- Clique em "Entrar" ou "Login"

## 🔧 SE NÃO CONSEGUIR LOGAR

### **Opção 1 - Limpar Cache:**
1. Pressione Ctrl+Shift+Delete (ou Cmd+Shift+Delete no Mac)
2. Limpe cookies e cache
3. Recarregue a página (F5)
4. Tente novamente

### **Opção 2 - Modo Incógnito:**
1. Abra uma aba incógnita/privada
2. Acesse http://localhost:3000
3. Tente fazer login

### **Opção 3 - Verificar Console:**
1. Pressione F12
2. Vá na aba "Console"
3. Veja se há erros em vermelho
4. Vá na aba "Network"
5. Tente fazer login e veja se as requisições aparecem

## 🎯 TESTE RÁPIDO

Se quiser testar se o backend está funcionando:

1. Abra uma nova aba
2. Digite: **http://localhost:5000/api/status**
3. Deve mostrar uma resposta JSON com "status": "online"

## 📱 ALTERNATIVAS

Se nada funcionar, tente:

1. **Outro navegador** (Chrome, Firefox, Edge)
2. **Reiniciar o frontend**:
   ```bash
   cd frontend
   npm start
   ```
3. **Verificar se os servidores estão rodando**

## ✅ CONFIRMAÇÃO

O backend está funcionando - vejo nos logs que:
- ✅ CSRF tokens sendo gerados
- ✅ Requisições OPTIONS chegando
- ✅ API respondendo normalmente

O problema pode estar no frontend ou no navegador.

## 🏆 APÓS O LOGIN

Quando conseguir logar, você terá acesso a:
- 📊 Gerenciamento de pacientes
- 🤖 Configuração de IA (38+ modelos)
- 📈 Evoluções e análises
- 🏠 Seus modelos locais Ollama
- 📤 Import/Export (após correção)

**Use as credenciais: admin / Aracannabis@2025**
