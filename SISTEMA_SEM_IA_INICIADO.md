# Sistema Aracannabis - Versão SEM IA Iniciado

## ✅ Status do Sistema
- **Backend (API)**: Rodando em http://localhost:5010
- **Frontend (React)**: Rodando em http://localhost:3000
- **Banco de Dados**: PostgreSQL configurado
- **Ambiente Virtual**: Ativado

## 🔧 Configurações Aplicadas

### Backend (app_sem_ia.py)
- Porta alterada para 5010 (para não conflitar com versão com IA)
- Funcionalidades de IA removidas:
  - ❌ Import/Export com IA
  - ❌ Configuração de IA
  - ❌ Rotas de IA
- Funcionalidades mantidas:
  - ✅ Autenticação e autorização
  - ✅ Gerenciamento de pacientes
  - ✅ Registro de sintomas
  - ✅ Controle de dosagens
  - ✅ Histórico de evolução
  - ✅ Agendamento de consultas
  - ✅ Gerenciamento de exames
  - ✅ Conformidade com LGPD
  - ✅ Cadastro de profissionais
  - ✅ Integração com Mercado Pago
  - ✅ Sistema de anúncios

### Frontend
- Proxy corrigido para porta 5010
- Interface completa disponível
- Todas as funcionalidades não-IA funcionando

## 🌐 URLs de Acesso

### Backend API
- **Principal**: http://localhost:5010
- **Status**: http://localhost:5010/api/status
- **CSRF Token**: http://localhost:5010/api/csrf-token

### Frontend
- **Principal**: http://localhost:3000

## 📋 Funcionalidades Disponíveis

### Módulos Principais
1. **Autenticação**
   - Login/logout seguro
   - Controle de sessão
   - Rate limiting

2. **Pacientes**
   - Cadastro completo
   - Edição de dados
   - Histórico médico
   - Compartilhamento de dados

3. **Sintomas**
   - Registro detalhado
   - Acompanhamento temporal
   - Gráficos e relatórios

4. **Dosagens**
   - Controle de medicamentos
   - Histórico de doses
   - Alertas e lembretes

5. **Evoluções**
   - Registro de progresso
   - Anotações médicas
   - Timeline de evolução

6. **Consultas**
   - Agendamento
   - Calendário integrado
   - Notificações

7. **Exames**
   - Upload de arquivos
   - Organização por data
   - Visualização de resultados

8. **LGPD**
   - Consentimento de dados
   - Política de privacidade
   - Direitos do titular

9. **Profissionais**
   - Cadastro de médicos
   - Solicitações de acesso
   - Gerenciamento de permissões

10. **Pagamentos**
    - Integração Mercado Pago
    - Planos de assinatura
    - Controle financeiro

## 🔒 Segurança

### Medidas Implementadas
- ✅ CORS configurado
- ✅ Rate limiting ativo
- ✅ Headers de segurança
- ✅ Proteção CSRF
- ✅ JWT para autenticação
- ✅ Conformidade LGPD

### Configurações de Rate Limit
- Login: Limitado por IP
- Endpoints sensíveis: Proteção extra
- APIs de busca: Limites otimizados

## 🚀 Como Usar

### Para Desenvolvedores
1. Backend já está rodando na porta 5010
2. Frontend já está rodando na porta 3000
3. Acesse http://localhost:3000 para usar o sistema

### Para Usuários
1. Acesse http://localhost:3000
2. Faça login com suas credenciais
3. Use todas as funcionalidades disponíveis (exceto IA)

## 📝 Diferenças da Versão com IA

### Removido
- ❌ Chat com IA para análise de dados
- ❌ Import/Export automático com IA
- ❌ Sugestões inteligentes
- ❌ Análise automática de padrões
- ❌ Configurações de modelos de IA

### Mantido
- ✅ Todas as funcionalidades manuais
- ✅ Interface completa
- ✅ Segurança total
- ✅ Performance otimizada
- ✅ Conformidade regulatória

## 🔄 Para Alternar Entre Versões

### Para usar versão COM IA:
```bash
# Parar versão sem IA (Ctrl+C nos terminais)
# Iniciar versão com IA
source venv/bin/activate
python app.py  # Porta 5000
```

### Para usar versão SEM IA (atual):
```bash
# Já está rodando
# Backend: porta 5010
# Frontend: porta 3000
```

## 📊 Monitoramento

### Logs do Sistema
- Conexões de banco de dados
- Tentativas de login
- Requisições da API
- Erros e exceções

### Performance
- Sistema otimizado sem overhead de IA
- Resposta mais rápida
- Menor uso de recursos

---

**Sistema iniciado com sucesso em:** 30/05/2025 21:36
**Versão:** SEM IA
**Status:** ✅ FUNCIONANDO
