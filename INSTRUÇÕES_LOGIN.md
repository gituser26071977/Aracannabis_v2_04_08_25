# 🔐 Instruções para Login no Sistema Aracannabis

## ✅ Status dos Serviços
- **Backend Flask**: ✅ Rodando na porta 5000
- **Frontend React**: ✅ Rodando na porta 3000
- **Usuário Admin**: ✅ Criado e disponível

## 🌐 Acesso ao Sistema

### 1. Abrir o Sistema
- **URL**: http://localhost:3000
- **Navegador**: Firefox (já aberto) ou qualquer navegador moderno

### 2. Credenciais de Login
```
Usuário: admin
Senha: Aracannabis@2025
```

### 3. Passos para Login
1. **Acesse** http://localhost:3000 no navegador
2. **Digite** o usuário: `admin`
3. **Digite** a senha: `Aracannabis@2025`
4. **Clique** em "Entrar" ou pressione Enter

### 4. Após o Login
1. **Navegue** até a seção "Pacientes"
2. **Selecione** um paciente existente
3. **Clique** na nova aba "Import/Export & IA"
4. **Explore** as funcionalidades:
   - Exportação de dados (JSON/CSV)
   - Importação inteligente com IA
   - Chat com IA sobre dados do paciente

## 🚨 Solução de Problemas

### Se o login não funcionar:
1. **Verifique** se ambos os serviços estão rodando:
   ```bash
   ps aux | grep -E "(python|node)" | grep -v grep
   ```

2. **Teste** a API diretamente:
   ```bash
   curl http://localhost:5000/api/status
   ```

3. **Verifique** o console do navegador (F12) para erros

4. **Recarregue** a página (Ctrl+F5)

### Se ainda houver problemas:
1. **Reinicie** o backend:
   ```bash
   # Pare o processo atual (Ctrl+C)
   python app.py
   ```

2. **Reinicie** o frontend:
   ```bash
   cd frontend
   npm start
   ```

## 🎯 Funcionalidades Implementadas

### 📊 Exportação
- **JSON Completo**: Todos os dados do paciente
- **CSV Específico**: Por tipo (evoluções, dosagens, sintomas)

### 📥 Importação Inteligente
- **Formatos**: JSON, CSV, TXT
- **IA Automática**: Análise e estruturação de dados
- **Criação**: Registros automáticos no sistema

### 🤖 Chat com IA
- **Perguntas**: Sobre evolução, dosagens, sintomas
- **Análise**: Contextual baseada no histórico
- **Insights**: Sugestões personalizadas

## 📞 Suporte
Se precisar de ajuda adicional, verifique os logs do sistema ou consulte a documentação técnica.
