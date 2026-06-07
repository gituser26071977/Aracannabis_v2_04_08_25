# Especificação Técnica — Agentes Paralelos Fase 1

> **Projeto:** SIAP Health (Rebranding + SaaS-fication)
> **Fase:** 1 — Dinheiro Entrando
> **Data:** 2026-06-07
> **Arquitetura:** Multi-agente paralelo com contratos de interface

---

## 🏗️ Visão Geral da Arquitetura

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FASE 1 — SQUADS                             │
├─────────────────┬─────────────────┬─────────────────┬───────────────┤
│   SQUAD A       │   SQUAD B       │   SQUAD C       │   SQUAD D     │
│   BILLING       │   SEGURANÇA     │   ONBOARDING    │   SGA INTEGRAÇÃO│
│   & PAGAMENTOS  │   & ACESSO      │   & UX          │   CATÁLOGO    │
├─────────────────┼─────────────────┼─────────────────┼───────────────┤
│ A1: Refatorar   │ B1: Middleware  │ C1: Verificação │ D1: Serviço   │
│     billing     │     assinatura  │     de email    │     extração  │
│                 │                 │                 │               │
│ A2: Recorrência │ B2: Decorator   │ C2: Wizard      │ D2: Frontend  │
│     MP          │     rotas       │     onboarding  │     import    │
│                 │                 │                 │               │
│ A3: Webhook     │ B3: Rate limit  │ C3: Redirect    │ D3: Adaptação │
│     unificado   │     tenant      │     trial→pay   │     modelos   │
└─────────────────┴─────────────────┴─────────────────┴───────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  BANCO SIAP      │
                    │  PostgreSQL      │
                    └──────────────────┘
```

**Princípio:** Cada Squad trabalha em paralelo usando **contratos de interface** predefinidos. Quando um Squad precisa de dados de outro, usa a interface — não a implementação.

---

## 📋 CONTRATOS DE INTERFACE (APIs Internas)

### Contrato `IBillingService`

```python
class IBillingService:
    """Interface que o Squad A implementa. Outros squads usam esta interface."""
    
    def create_subscription(self, user_id: int, plan_id: int, 
                           period: str, payment_method: str) -> dict:
        """
        Cria assinatura (trial ou paga).
        Returns: {subscription_id, status, next_billing_date, payment_url}
        """
        pass
    
    def get_subscription_status(self, user_id: int) -> dict:
        """
        Retorna status da assinatura do usuário.
        Returns: {status: 'trial'|'active'|'expired'|'cancelled', 
                  expires_at, plan_id, is_blocked}
        """
        pass
    
    def process_recurring_payment(self, subscription_id: int) -> bool:
        """
        Executa cobrança recorrente. Chamado pelo cron job.
        Returns: True se cobrança gerada com sucesso
        """
        pass
    
    def cancel_subscription(self, user_id: int) -> bool:
        """Cancela assinatura."""
        pass
    
    def handle_webhook(self, provider: str, payload: dict) -> bool:
        """
        Processa webhook de qualquer provedor de pagamento.
        provider: 'mercadopago' | 'stripe' | 'asaas'
        """
        pass
```

### Contrato `IAccessControl`

```python
class IAccessControl:
    """Interface que o Squad B implementa."""
    
    def check_access(self, user_id: int, resource: str) -> dict:
        """
        Verifica se usuário tem acesso ao recurso.
        resource: 'login'|'api'|'feature_ia'|'feature_patient'
        Returns: {allowed: bool, reason: str|null, remaining_quota: dict}
        """
        pass
    
    def enforce_plan_limits(self, user_id: int, action: str, 
                           quantity: int = 1) -> bool:
        """
        Verifica se ação está dentro dos limites do plano.
        action: 'create_patient'|'use_ai_agent'|'upload_file'
        """
        pass
```

---

## 👥 SQUAD A — BILLING & PAGAMENTOS

### Objetivo
Transformar o billing de "mock em memória" para "sistema de cobrança real com recorrência automática".

### Estado Atual
- `services/payment_service.py` → MOCK (UUID fake, perde dados no restart)
- `services/billing_service.py` → depende do mock
- `services/mercadopago_service.py` → SDK real, mas só pagamentos únicos (preference)
- `routes/mercadopago.py` → webhook funciona, mas desconectado do billing

### Estado Desejado
- Cobrança recorrente via Mercado Pago (Subscriptions API / Preapproval)
- Faturas reais no banco
- Webhook unificado que atualiza billing
- Suporte a múltiplos provedores (MP, Stripe, Asaas)

### Sub-agentes

#### A1 — Refatorar BillingService
**Responsabilidade:** Eliminar o mock e unificar billing com Mercado Pago real.

**Tarefas:**
1. Criar `services/billing_service_v2.py` (nova implementação)
2. Implementar `IBillingService` interface
3. Substituir chamadas ao `PaymentService` (mock) por integração real com `MercadoPagoService`
4. Garantir que `Fatura` e `PagamentoRegistro` sejam persistidos no PostgreSQL
5. Criar migration Alembic para novos campos necessários

**Arquivos:**
- `services/billing_service_v2.py` (novo)
- `services/payment_service.py` (deprecar, não deletar ainda)
- `models.py` (novos campos se necessário)
- `routes/billing.py` (atualizar para usar v2)

**Critérios de Aceitação:**
- [ ] `POST /api/billing/subscribe` cria assinatura real no Mercado Pago
- [ ] `GET /api/billing/status` retorna status real da assinatura
- [ ] Não há mais "mock" em memória — tudo persiste no PostgreSQL
- [ ] Fatura é criada no banco com status real (pendente/pago)

---

#### A2 — Implementar Cobrança Recorrente
**Responsabilidade:** Implementar assinatura automática mensal via Mercado Pago.

**Tarefas:**
1. Integrar Mercado Pago Subscriptions API (ou Preapproval)
2. Criar endpoint `POST /api/billing/recurring/create` 
3. Implementar cálculo de próxima cobrança (mensal/trimestral/semestral/anual)
4. Criar script `cron_billing.py` que roda diariamente:
   - Busca assinaturas com `next_billing_date <= hoje`
   - Gera nova fatura
   - Se MP recurring: cobrança automática
   - Se não: envia PIX/boleto por email
5. Atualizar `subscription_expiration_service.py` para usar dados reais

**Arquivos:**
- `services/recurring_service.py` (novo)
- `scripts/cron_billing.py` (novo)
- `routes/billing.py` (adicionar endpoints)

**Critérios de Aceitação:**
- [ ] Assinatura mensal cobra automaticamente todo mês
- [ ] Usuário recebe email com PIX/boleto 3 dias antes do vencimento
- [ ] Pagamento aprovado → assinatura renovada automaticamente
- [ ] Pagamento recusado → assinatura entra em `grace_period` (7 dias)

---

#### A3 — Webhook Unificado
**Responsabilidade:** Criar um único webhook handler para todos os provedores de pagamento.

**Tarefas:**
1. Criar `services/webhook_handler.py`
2. Implementar handlers para:
   - Mercado Pago (`payment.updated`, `preapproval`)
   - Futuro: Stripe, Asaas
3. Garantir idempotência (mesmo webhook 2x não duplica fatura)
4. Log de todos os webhooks recebidos (tabela `WebhookLog`)
5. Atualizar `routes/mercadopago.py` para delegar ao handler unificado

**Arquivos:**
- `services/webhook_handler.py` (novo)
- `models_extra.py` (tabela `WebhookLog`)
- `routes/webhooks.py` (novo — endpoint único `/api/webhooks/{provider}`)

**Critérios de Aceitação:**
- [ ] Webhook do MP processado corretamente
- [ ] Webhook duplicado não gera fatura duplicada
- [ ] Log de webhook acessível no admin

---

## 👥 SQUAD B — SEGURANÇA & ACESSO

### Objetivo
Garantir que apenas usuários pagantes acessem o sistema, respeitando os limites do plano.

### Estado Atual
- `data_expiracao` existe em `Profissional` mas não é verificado
- `Assinatura.status` existe mas não bloqueia acesso
- Rate limit por IP (básico), não por tenant/plano
- Sem enforcement de limites de pacientes/agentes IA

### Estado Desejado
- Middleware que bloqueia login/API se assinatura expirou
- Decorator `@require_active_subscription`
- Rate limit por tenant no Redis
- Enforcement de limites do plano

### Sub-agentes

#### B1 — Middleware de Verificação de Assinatura
**Responsabilidade:** Bloquear acesso quando assinatura não está ativa.

**Tarefas:**
1. Criar `middleware/subscription_middleware.py`
2. Implementar verificação em 3 camadas:
   - **Login:** Impede autenticação se `status != 'active'` ou `trial_ends_at < now`
   - **API:** Retorna `403` com mensagem "Assinatura expirada. Renove em /planos"
   - **Frontend:** Redireciona para página de renovação
3. Tratar grace period (7 dias após expiração → avisos, não bloqueio total)
4. Exceções: rotas públicas (`/`, `/planos`, `/api/webhooks/*`, `/api/status`)

**Arquivos:**
- `middleware/subscription_middleware.py` (novo)
- `routes/auth.py` (adicionar verificação no login)
- `app_cors_livre.py` (registrar middleware)

**Critérios de Aceitação:**
- [ ] Usuário com assinatura expirada não consegue fazer login
- [ ] Usuário em trial consegue login normalmente
- [ ] API retorna 403 com JSON informativo para assinatura expirada
- [ ] Grace period de 7 dias permite acesso com avisos

---

#### B2 — Decorator de Rotas Protegidas
**Responsabilidade:** Proteger rotas específicas que exigem plano pago.

**Tarefas:**
1. Criar `routes/auth_decorators.py` (expandir existente)
2. Implementar decorators:
   - `@require_plan('com_ia')` — bloqueia se plano não inclui IA
   - `@require_feature('unlimited_patients')` — bloqueia se excedeu limite
   - `@require_active_subscription` — verifica assinatura ativa
3. Aplicar decorators nas rotas:
   - IA clínica → `@require_plan('com_ia')`
   - Cadastro de paciente → `@require_feature('unlimited_patients')` (ou contar)
   - Relatórios avançados → `@require_plan('com_ia')`

**Arquivos:**
- `routes/auth_decorators.py` (expandir)
- Todas as rotas em `routes/` (adicionar decorators)

**Critérios de Aceitação:**
- [ ] Rota de IA retorna 403 para plano "Sem IA"
- [ ] Rota de paciente bloqueia quando atinge limite do plano
- [ ] Decorator funciona tanto em rotas Flask tradicionais quanto Blueprints

---

#### B3 — Rate Limit por Tenant/Plano
**Responsabilidade:** Limitar requisições e uso de recursos por tenant.

**Tarefas:**
1. Configurar Flask-Limiter para usar Redis (em vez de memória)
2. Implementar limites por `tenant_id`:
   - Plano "Sem IA": 0 requisições/min para rotas IA
   - Plano "Com IA": limite_agentes_ia requisições/min
   - Geral: limite baseado no plano
3. Implementar contadores de uso no Redis:
   - `tenant:{id}:patients:count` — contador de pacientes
   - `tenant:{id}:ai:requests` — contador de requisições IA
   - `tenant:{id}:storage:bytes` — uso de armazenamento
4. Criar endpoint `GET /api/usage` para o frontend mostrar quota usada

**Arquivos:**
- `middleware/rate_limit_middleware.py` (novo)
- `services/quota_service.py` (novo)
- `routes/admin.py` (endpoint de uso)

**Critérios de Aceitação:**
- [ ] Rate limit funciona com Redis (persiste entre restarts)
- [ ] Tenant do plano "Sem IA" é bloqueado ao usar IA
- [ ] Endpoint `/api/usage` retorna quota usada/total

---

## 👥 SQUAD C — ONBOARDING & UX

### Objetivo
Criar um fluxo de onboarding que converta trial em pagamento.

### Estado Atual
- Cadastro simples (`/register`) — sem verificação de email
- Não há wizard de configuração
- Trial é criado automaticamente mas não redireciona para pagamento
- Não há tour guiado

### Estado Desejado
- Verificação de email obrigatória
- Wizard de onboarding (especialidade, clínica, logo)
- Contador regressivo de trial visível no dashboard
- Redirecionamento automático para pagamento quando trial acaba

### Sub-agentes

#### C1 — Verificação de Email
**Responsabilidade:** Garantir que emails sejam válidos antes de ativar conta.

**Tarefas:**
1. Criar tabela `EmailVerification` (token, expiração)
2. Modificar `routes/auth.py`:
   - `POST /register` → cria usuário como `status='pending_email'`
   - Envia email com link de verificação
   - `GET /verify-email/{token}` → ativa conta, inicia trial
3. Modificar `POST /login` → rejeita login se `status != 'active'`
4. Criar endpoint `POST /resend-verification`

**Arquivos:**
- `models_extra.py` (tabela `EmailVerification`)
- `routes/auth.py` (modificar register/login)
- `services/email_service.py` (novo template de verificação)

**Critérios de Aceitação:**
- [ ] Registro cria conta com status "pending_email"
- [ ] Email de verificação enviado automaticamente
- [ ] Link de verificação ativa conta e inicia trial
- [ ] Login bloqueado até verificar email

---

#### C2 — Wizard de Onboarding
**Responsabilidade:** Guiar novo usuário na configuração inicial.

**Tarefas:**
1. Criar endpoint `GET/POST /api/onboarding` (multi-step)
2. Passos do wizard:
   - **Step 1:** Dados pessoais (nome, CPF, CRM, especialidade)
   - **Step 2:** Dados da clínica (nome, CNPJ, endereço, telefone)
   - **Step 3:** Configuração inicial (timezone, logo, cor tema)
   - **Step 4:** Escolha do plano (mostra trial + opções pagas)
3. Persistir progresso no banco (`OnboardingProgress`)
4. Criar frontend: página `/onboarding` com stepper
5. Redirecionar usuário novo para `/onboarding` após primeiro login

**Arquivos:**
- `routes/onboarding.py` (novo)
- `models_extra.py` (tabela `OnboardingProgress`)
- `frontend/src/pages/OnboardingPage.js` (novo)
- `frontend/src/components/OnboardingStepper.js` (novo)

**Critérios de Aceitação:**
- [ ] Usuário novo é redirecionado para /onboarding no primeiro login
- [ ] Wizard tem 4 passos com validação
- [ ] Progresso é salvo (usuário pode sair e voltar)
- [ ] Após completar, redireciona para dashboard

---

#### C3 — Redirecionamento Trial → Pagamento
**Responsabilidade:** Converter trial em pagamento.

**Tarefas:**
1. Criar componente `TrialBanner` visível no topo do dashboard
   - Mostra: "X dias restantes no trial"
   - Botão: "Escolher plano"
   - Cor muda: verde (>3 dias), amarelo (3 dias), vermelho (<1 dia)
2. Criar página `/trial-ending` com:
   - Resumo do que o usuário usou (pacientes, consultas, IA)
   - CTA forte para pagamento
   - Depoimentos / social proof
3. Bloqueio suave: quando trial acaba:
   - Permite login
   - Mostra modal de pagamento (não permite usar sistema)
   - Mantém dados salvos por 30 dias
4. Email automatizado:
   - 3 dias antes do fim: lembrete
   - 1 dia antes: urgência
   - No dia: último aviso
   - 1 dia depois: "Seus dados estão seguros, renove agora"

**Arquivos:**
- `frontend/src/components/TrialBanner.js` (novo)
- `frontend/src/pages/TrialEndingPage.js` (novo)
- `services/subscription_expiration_service.py` (expandir emails)
- `cron_check_expirations.py` (adicionar lógica de bloqueio suave)

**Critérios de Aceitação:**
- [ ] Banner de trial visível em todas as páginas internas
- [ ] Cores mudam conforme proximidade do fim
- [ ] Email automático enviado nos dias -3, -1, 0, +1
- [ ] Após trial, modal de pagamento bloqueia uso mas mantém login

---

## 👥 SQUAD D — SGA INTEGRAÇÃO (CATÁLOGO)

### Objetivo
Trazer o módulo de extração de produtos por IA do SGA para o SIAP.

### Estado Atual no SGA
- `InventoryIntelligentService` extrai produtos de PDF/catálogo
- Usa LLM multimodal (Gemini) para ler o arquivo
- Retorna JSON com nome, categoria, descrição, unidade
- Frontend em React com modal de upload

### Estado Desejado no SIAP
- Endpoint `POST /api/catalogo/importar-ia` no SIAP
- Aceita PDF, imagem ou planilha
- Extrai produtos e salva em `Produto` + `InventoryItem`
- Frontend no SIAP com preview e confirmação

### Sub-agentes

#### D1 — Serviço de Extração de Catálogo
**Responsabilidade:** Portar o serviço do SGA para o SIAP.

**Tarefas:**
1. Criar `services/catalogo_extraction_service.py`
2. Portar lógica do `InventoryIntelligentService` (SGA):
   - Prompt de sistema para extração de produtos
   - Suporte a múltiplos provedores de LLM
   - Parse de resposta JSON
3. Adaptar para modelos do SIAP:
   - Mapear campos extraídos → `Produto` (nome, descricao, categoria)
   - Mapear → `InventoryItem` (quantidade, lote, validade)
4. Suportar tipos de arquivo: PDF, PNG, JPG, XLSX
5. Limitar por plano (extração IA pode ser feature do plano "Com IA")

**Arquivos:**
- `services/catalogo_extraction_service.py` (novo)
- `routes/catalogo_routes.py` (adicionar endpoint)

**Critérios de Aceitação:**
- [ ] Upload de PDF de catálogo extrai produtos corretamente
- [ ] Resposta em JSON com array de produtos
- [ ] Funciona com Gemini, OpenAI, Anthropic (fallback)
- [ ] Rate limit por tenant (máximo 10 extrações/dia no trial)

---

#### D2 — Frontend de Importação IA
**Responsabilidade:** Criar interface no SIAP para upload e confirmação.

**Tarefas:**
1. Criar componente `ImportCatalogoIA.js`
2. Funcionalidades:
   - Dropzone para upload de arquivo
   - Loading state com animação "IA analisando..."
   - Preview de produtos extraídos em tabela
   - Checkbox para selecionar quais importar
   - Botão "Importar selecionados" → salva no banco
3. Integrar com endpoint `POST /api/catalogo/importar-ia`
4. Integrar com endpoint `POST /api/inventory/` (salvar)
5. Adicionar no menu: "Catálogo → Importar por IA"

**Arquivos:**
- `frontend/src/components/ImportCatalogoIA.js` (novo)
- `frontend/src/pages/CatalogoPage.js` (modificar)

**Critérios de Aceitação:**
- [ ] Upload funciona via drag-and-drop
- [ ] Preview mostra produtos extraídos com edição inline
- [ ] Importação salva produtos selecionados no estoque
- [ ] Feedback de sucesso/erro claro

---

#### D3 — Adaptação de Modelos SIAP
**Responsabilidade:** Garantir compatibilidade entre dados extraídos e schema SIAP.

**Tarefas:**
1. Mapear categorias SGA → SIAP:
   - SGA: óleo, flor, pomada, gummy, pet, vaporizador
   - SIAP: Produto.categoria (verificar schema atual)
2. Adicionar campos faltantes em `Produto` se necessário:
   - `concentracao` (mg/ml ou %)
   - `fabricante`
   - `codigo_barras`
3. Criar migration para novos campos
4. Criar `CatalogoImportLog` para auditoria:
   - quem importou, quando, arquivo, quantos produtos, erros

**Arquivos:**
- `models.py` (novos campos em Produto)
- `models_extra.py` (tabela `CatalogoImportLog`)
- `migrations/` (alembic migration)

**Critérios de Aceitação:**
- [ ] Produtos extraídos salvos corretamente no schema SIAP
- [ ] Campos novos disponíveis na API
- [ ] Log de importação acessível no admin

---

## 🔗 DEPENDÊNCIAS E ORDEM DE EXECUÇÃO

### Paralelização Máxima

```
Semana 1
├── Squad A: A1 (Refatorar billing) [BLOQUEANTE]
├── Squad B: B1, B2, B3 [INDEPENDENTE]
├── Squad C: C1, C2, C3 [INDEPENDENTE]
└── Squad D: D1, D2, D3 [INDEPENDENTE]

Semana 2
├── Squad A: A2 (Recorrência) + A3 (Webhook)
├── Squad B: Integrar com A1 (testar bloqueio com billing real)
├── Squad C: Integrar com A1 (testar trial→pagamento)
└── Squad D: Testes e ajustes
```

**Regra de ouro:** Squad A (A1) é o único bloqueante. Todos os outros podem começar imediatamente usando interfaces mock/stub.

---

## 🧪 ESTRATÉGIA DE TESTES

### Testes por Squad
- **A:** Simular webhook MP, verificar fatura criada, testar recorrência
- **B:** Criar usuário com assinatura expirada, tentar login e API
- **C:** Fluxo completo: register → verify email → onboarding → trial → pagamento
- **D:** Upload PDF catálogo, verificar produtos extraídos, importar

### Teste Integrado (Semana 2)
1. Usuário novo se registra
2. Verifica email
3. Completa onboarding
4. Usa trial por 6 dias
5. Recebe email "faltam 1 dia"
6. Trial acaba → modal de pagamento
7. Paga via PIX (MP real)
8. Assinatura ativa → acesso liberado
9. Usa extração de catálogo IA
10. Importa 50 produtos

---

## 📁 ENTREGÁVEIS FINAIS

| Entregável | Responsável | Formato |
|------------|-------------|---------|
| Código fonte (PR no GitHub) | Todos | Python + React |
| Migration Alembic | A1, D3 | `.py` |
| Documentação API | Todos | Swagger atualizado |
| Testes | Todos | pytest + manual |
| Deploy no VPS | A (coordena) | docker-compose |

---

## ⚠️ RISCOS E MITIGAÇÕES

| Risco | Probabilidade | Impacto | Mitigação |
|-------|--------------|---------|-----------|
| Mercado Pago recusar preapproval | Média | Alto | Ter Stripe/Asaas como fallback |
| Middleware bloquear rotas erradas | Baixa | Alto | Testar rotas públicas exaustivamente |
| Wizard onboarding quebrar cadastro existente | Baixa | Médio | Feature flag para novo onboarding |
| Extração IA não funcionar com PDFs complexos | Média | Médio | Fallback para extração manual |
| Merge conflicts entre squads | Média | Médio | Cada squad trabalha em arquivos diferentes |

---

## ✅ CHECKLIST DE APROVAÇÃO

Antes de iniciar, confirmar:
- [ ] Usuário aprovou especificação
- [ ] Novo nome do produto definido (para branding no onboarding)
- [ ] Provedor de pagamento escolhido (MP é prioridade, fallback?)
- [ ] Emissor de NF escolhido (Focus NFe, PlugNotas, etc.) — Fase 2
- [ ] Domínio de webhook configurado no VPS
- [ ] Redis já funcional no VPS (verificar)

---

*Documento gerado em 2026-06-07. Sujeito a revisão após feedback do usuário.*

---

## 📌 DECISÕES DO CLIENTE (2026-06-07)

| Item | Decisão |
|------|---------|
| Especificação | ✅ **APROVADA** |
| Nome do produto | Em definição — usar placeholder genérico nas interfaces |
| Provedores de pagamento | **3 pré-instalados**: Mercado Pago, Stripe, Asaas. Gestor escolhe nas configurações |
| Feature Flags | **OBRIGATÓRIO** para todas as novas funcionalidades |

### Sistema de Feature Flags Implementado

Arquivo: `services/feature_flag_service.py`

Features registradas:
- `new_billing_v2` — Novo billing
- `recurring_payments` — Cobrança recorrente
- `subscription_block` — Bloqueio por inadimplência
- `plan_enforcement` — Enforcement de limites
- `email_verification` — Verificação de email
- `onboarding_wizard` — Wizard de onboarding
- `trial_banner` — Banner de trial
- `sga_catalog_extraction` — Extração SGA
- `multi_payment_provider` — Múltiplos provedores de pagamento

Uso no código:
```python
from services.feature_flag_service import FeatureFlagService, feature_required

# Verificar
if FeatureFlagService.is_enabled('new_billing_v2', tenant_id=1):
    # usar novo billing

# Decorator
@feature_required('sga_catalog_extraction')
def import_catalog():
    pass
```

---
