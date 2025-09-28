# 🔐 Instruções Detalhadas para Login no Sistema Aracannabis

## ✅ Status do Sistema

### Backend (API)
- ✅ **Funcionando**: http://localhost:5000
- ✅ **Autenticação**: Testada e funcionando
- ✅ **Usuário criado**: admin / Aracannabis@2025
- ✅ **Todas as funcionalidades**: Import/Export/Chat IA operacionais

### Frontend
- ✅ **Rodando**: http://localhost:3000
- ⚠️ **Login**: Precisa ser testado no navegador

## 🚀 Como Testar o Login

### 1. Abrir o Sistema
```
1. Abra seu navegador (Chrome, Firefox, Edge)
2. Vá para: http://localhost:3000
3. Você deve ver a página de login do Aracannabis
```

### 2. Credenciais de Login
```
Usuário: admin
Senha: Aracannabis@2025
```

### 3. Verificar Problemas (F12)
```
1. Pressione F12 para abrir o Developer Tools
2. Vá para a aba "Console"
3. Tente fazer login
4. Verifique se há erros no console
```

### 4. Verificar Requisições de Rede
```
1. No Developer Tools, vá para aba "Network"
2. Tente fazer login novamente
3. Verifique as requisições:
   - GET /api/csrf-token (deve retornar 200)
   - POST /api/auth/login (deve retornar 200)
```

## 🔍 Possíveis Problemas e Soluções

### Problema 1: Erro de CORS
**Sintomas**: Erro no console sobre CORS
**Solução**: 
```bash
# Reiniciar o backend
Ctrl+C no terminal do backend
python app.py
```

### Problema 2: Cache do Navegador
**Sintomas**: Página não carrega corretamente
**Solução**:
```
1. Pressione Ctrl+F5 (hard refresh)
2. Ou limpe o cache:
   - Chrome: Ctrl+Shift+Delete
   - Firefox: Ctrl+Shift+Delete
```

### Problema 3: Frontend não conecta com Backend
**Sintomas**: Erro de conexão
**Solução**:
```bash
# Verificar se ambos estão rodando:
# Terminal 1: python app.py
# Terminal 2: cd frontend && npm start
```

### Problema 4: Token CSRF
**Sintomas**: Erro 403 - CSRF token inválido
**Solução**: O sistema deve obter automaticamente, mas se não:
```javascript
// No console do navegador, execute:
localStorage.clear()
// Depois recarregue a página
```

## 🛠️ Comandos de Diagnóstico

### Verificar se Backend está funcionando:
```bash
curl http://localhost:5000/api/status
```

### Verificar se Frontend está funcionando:
```bash
curl http://localhost:3000
```

### Testar login via terminal:
```bash
python test_frontend_login.py
```

## 📋 Checklist de Verificação

- [ ] Backend rodando em http://localhost:5000
- [ ] Frontend rodando em http://localhost:3000
- [ ] Página de login carrega sem erros
- [ ] Console do navegador sem erros JavaScript
- [ ] Requisição CSRF retorna token
- [ ] Requisição de login com credenciais corretas

## 🎯 Se Tudo Falhar

### Reiniciar Completamente:
```bash
# Terminal 1 - Parar backend
Ctrl+C

# Terminal 2 - Parar frontend  
Ctrl+C

# Aguardar 5 segundos

# Terminal 1 - Reiniciar backend
python app.py

# Terminal 2 - Reiniciar frontend
cd frontend && npm start

# Aguardar carregar completamente
# Tentar login novamente
```

### Verificar Logs:
```bash
# Logs do backend aparecem no terminal onde rodou python app.py
# Logs do frontend aparecem no console do navegador (F12)
```

## 🔧 Informações Técnicas

### URLs da API:
- Status: http://localhost:5000/api/status
- CSRF: http://localhost:5000/api/csrf-token  
- Login: http://localhost:5000/api/auth/login

### Estrutura de Login:
```json
{
  "usuario": "admin",
  "senha": "Aracannabis@2025"
}
```

### Headers Necessários:
```
Content-Type: application/json
X-CSRF-Token: [token obtido da API]
```

## 📞 Próximos Passos

1. **Teste manual no navegador** seguindo as instruções acima
2. **Verifique o console** para erros específicos
3. **Relate o erro exato** se ainda não funcionar
4. **Teste as funcionalidades** após login bem-sucedido:
   - Listar pacientes
   - Importar/Exportar dados
   - Chat com IA

---

## ✅ Funcionalidades Disponíveis Após Login

### 📤 Exportação
- JSON completo do paciente
- CSV por categoria (evoluções, dosagens, sintomas)

### 📥 Importação  
- Suporte a 15+ formatos
- Processamento automático com IA
- Análise inteligente de conteúdo

### 🤖 Chat com IA
- Perguntas sobre dados do paciente
- Insights automáticos
- Sugestões de tratamento

**Data**: 24/05/2025  
**Versão**: 2.0.0 - Sistema Completo com IA
