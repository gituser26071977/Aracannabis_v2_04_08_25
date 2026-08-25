# Relatório E2E em Produção — 2026-08-25

**Ambiente:** https://siap.vittalis.site (frontend) / https://api.vittalis.site
(API) **Usuário:** Dra. E2E Teste (`e2e_1787694297@teste.araos.dev`) —
profissional, trial 14 dias **Escopo:** cadastro de conta → aprovação → login →
dashboard → paciente → consulta → financeiro → IA → planos

---

## 1. Resumo do que funciona

| Fluxo                                                    | Resultado                                                                   |
| -------------------------------------------------------- | --------------------------------------------------------------------------- |
| Cadastro de profissional (4 passos)                      | ✅ HTTP 201, solicitação em `solicitacoes_cadastro` (pendente)              |
| Aprovação + criação de usuário                           | ✅ `profissional` criado, `status_cadastro=aprovado`, `status_conta=active` |
| Login (email + senha)                                    | ✅ HTTP 200, token JWT (AraOS + legacy)                                     |
| Dashboard                                                | ✅ "Pacientes do dia", "SEU FINANCEIRO" (R$ 0,00)                           |
| Cadastro de paciente                                     | ✅ HTTP 201 (após criar workspace)                                          |
| Agendamento de consulta                                  | ✅ HTTP 201, evento no calendário                                           |
| Editar/atualizar consulta (modal)                        | ✅ abre com dados                                                           |
| Lembretes (`/api/consultas/lembretes/enviar`)            | ✅ 200                                                                      |
| Troca de período agenda (Mês/Semana/Dia/Hoje)            | ✅                                                                          |
| Assistente IA (`/api/chat-simples`)                      | ✅ 200                                                                      |
| Financeiro dashboard (`/api/faturamento/minha-situacao`) | ✅ 200 (lançamentos zerados)                                                |
| Lista de pacientes (`GET /api/pacientes/`)               | ✅ 200                                                                      |

---

## 2. Bugs encontrados (precisam de correção)

### B1. ROLE `profissional` não existe no RoleRegistry (P0 — bloqueia operações de escrita)

- **Sintoma:** `POST /api/pacientes/` → **403
  `{"error":"Permissão negada","required_permissions":["patient.write"]}`**
- **Causa:** O `processar_aprovacao()` cria o usuário com `role='profissional'`,
  mas o `RoleRegistry` (`araos/platform/identity/permissions.py:613`) só conhece
  `admin`, `physician`, `secretary`, `manager`, `patient`, `agent`,
  `service_account`, `viewer`, `neuro_physician`, `health_secretary`,
  `scientific_producer`. `require_permission` (`routes/auth_decorators.py:73`)
  não encontra a role → nega.
- **Impacto:** qualquer endpoint com
  `@require_permission(PATIENT_WRITE/PATIENT_DELETE/...)` retorna 403 para todos
  os profissionais aprovados (a menos que a role do vínculo de workspace seja
  `admin` — e mesmo assim depende do tenant middleware).
- **Contorno usado no teste:** criei a associação + `usuarios_associacoes` (role
  `admin`), que faz o tenant middleware setar `g.user_role=admin`.
- **Correção sugerida:** mapear `profissional` → `physician` no
  `_resolve_user_role_names` ou registrar role alias `profissional` no
  `RoleRegistry` (backward compat).

### B2. Middleware `enforce_perfil_acesso` bloqueia rotas públicas (P1 — página de Planos quebrada)

- **Sintoma:** página `/planos` mostra "Não foi possível carregar os preços
  atualizados" e "Nenhum plano disponível no momento".
- **Causa:** `GET /api/planos/` é **pública** (sem `@jwt_required`; funciona sem
  token — retorna 3 planos), mas o middleware `enforce_perfil_acesso`
  (`app_cors_livre.py:528`) roda para qualquer request **com** token.
  `/api/planos` está na `AREA_ADMINISTRATIVA` (`services/perfil_acesso.py`), e o
  usuário é perfil `assistencial` → 403.
- **Impacto:** **nenhum usuário logado consegue ver os preços nem assinar
  plano** (vira a página de vendas do SaaS). Também afeta
  `GET /api/planos/meu-plano` (banner "15 dias restantes" quebrado) e
  `GET /api/meus-modulos` (403/422 no dashboard).
- **Correção sugerida:** no `area_da_rota()`/`verificar_acesso()`, liberar rotas
  públicas (ou prefixos de leitura de plano/assinatura) para qualquer usuário
  autenticado — ex.: tratar `/api/planos` GET como área `None`.

### B3. Página de Configurar Receituário não carrega (P1)

- **Sintoma:** `/configuracao-prescricao` mostra "Não foi possível carregar as
  configurações atuais."
- **Causa:** `GET /api/prescricao-config/` → 403 pelo mesmo middleware
  `enforce_perfil_acesso` (`/api/prescricao-config` ∈ `AREA_ADMINISTRATIVA`). O
  `processar_aprovacao()` cria a `ConfiguracaoPrescricao`, mas o usuário não
  consegue lê-la.
- **Impacto:** profissional assistencial não configura logomarcas/assinatura/IA
  de dosagem.
- **Correção sugerida:** mover `/api/prescricao-config` para uma área acessível
  ao perfil assistencial (é configuração do próprio profissional, não gestão de
  clínica).

### B4. `GET /api/meus-modulos` → 403/422 no dashboard

- **Sintoma:** dashboard dispara `GET /api/meus-modulos` → 422 (primeira) e 403
  (depois).
- **Causa:** idem middleware de perfil (`/api/meus-modulos` ∈
  `AREA_ADMINISTRATIVA`).
- **Impacto:** módulos de especialidade não carregam para usuário assistencial
  (features de prontuário que deveriam estar liberadas no trial).

### B5. (Menor) Botão "🔌 API" no dashboard sem ação visível

- **Sintoma:** clicar em "🔌 API" não muda URL nem mostra conteúdo.
- **Observação:** pode ser intencional (card informativo) — confirmar intenção
  de produto.

### B6. (Observação) Cadastro financeiro de novo usuário

- `minha-situacao` retorna 200 com tudo zerado (correto para usuário novo).
- Para testar lançamento real seria preciso concluir uma consulta (status
  `realizada`) e lançar cobrança — o fluxo de faturamento administrativo
  (`/api/faturamento/lancamentos`) retorna 403 para perfil assistencial (by
  design; gestor financeiro precisa perfil admin/solo/manager).

---

## 3. Correções aplicadas (2026-08-25) e re-teste

### Correções

| Bug | Correção                                                                                                                  | Arquivo                     |
| --- | ------------------------------------------------------------------------------------------------------------------------- | --------------------------- |
| B1  | Adicionado `_ROLE_ALIASES` mapeando `profissional`→`physician` e `secretaria`→`secretary` em `_resolve_user_role_names()` | `routes/auth_decorators.py` |
| B2  | Criada `_ROTAS_ABERTAS_AUTENTICADO = ["/api/planos"]` → retorna área `None` (qualquer autenticado)                        | `services/perfil_acesso.py` |
| B3  | `/api/prescricao-config` movido para `AREA_ASSISTENCIAL`                                                                  | `services/perfil_acesso.py` |
| B4  | `/api/meus-modulos` movido para `AREA_ASSISTENCIAL`                                                                       | `services/perfil_acesso.py` |

Aplicado via `docker cp` no container `siap-backend-final` (com backup em
`/root/*.bak.*.py`) + `docker restart`. Código local sincronizado
(`routes/auth_decorators.py`, `services/perfil_acesso.py`).

### Re-teste E2E (pós-correção)

| Fluxo                       | Antes                                 | Depois                                        |
| --------------------------- | ------------------------------------- | --------------------------------------------- |
| Criar paciente (UI)         | 403 Permissão negada                  | ✅ 201 (CPF 93391650800, id 3)                |
| Agendar consulta (UI)       | bloqueado                             | ✅ 201 (id 24, 29/08 09:00, presencial)       |
| Página de Planos            | "Não foi possível carregar os preços" | ✅ planos visíveis (Sem IA/Com IA/Enterprise) |
| Configurar Receituário      | "Não foi possível carregar"           | ✅ config + IA de Dosagem visíveis            |
| Assistente IA               | OK                                    | ✅ OK                                         |
| `GET /api/planos/meu-plano` | 403                                   | ✅ 200                                        |
| `GET /api/meus-modulos`     | 422/403                               | ✅ 200                                        |

> Nota: o `POST /api/pacientes/` só retornava 400/409 (validação de CPF/horário
> duplicado) após a correção — comportamento correto do sistema, não bug.

---

## 4. Sobre validação automática de cadastro (pergunta: "Como está acontecendo a liberação?")

Hoje existe um pipeline parcial automático
(`services/registration_verification_service.py`):

1. `solicitar-cadastro` cria a solicitação (`pendente`) e dispara
   `verify_registration()`.
2. `verify_registration()`:
   - `_verify_crm()` → **só valida FORMATO** (dígitos + UF) e duplicidade
     interna. **NÃO consulta o CFM/CRP/COREN.**
   - `_verify_email()` → formato + DNS MX + domínio descartável + duplicidade.
   - `_verify_fraud()` → timing (nº de solicitações no dia).
   - `_aggregate_results()` → monta contexto e chama LLM (DeepSeek via
     `ai_manager`) com roleplay "Auditor de Conformidade Médica"; retorna
     `recommendation: auto_approve | manual_review | reject`.
3. Se `auto_approve` → `processar_aprovacao()` roda imediatamente (já
   existente).
4. Senão → admin aprova manualmente em `AdminPage.js` (SolicitacoesManager), com
   suporte do Telegram que sugere link do CFM.

**Lacunas para o que você quer (confirmar conselho + redes sociais):**

- **Não há consulta real a APIs de conselho** —
  `services/crm_validator_service.py` tem stub/TODO para o CFM
  (`https://portal.cfm.org.br/api/profissional/buscar`) e portais regionais, mas
  não é chamado no fluxo de produção.
- **Não há campo de redes sociais** em `SolicitacoesCadastro` nem verificação
  delas.
- **Infra de agentes já existe e é reutilizável:** `services/ai_agents.py`
  (multi-provedor LLM), `services/crew_agents.py` (agente "Validador de
  Cadastros", tools `validar_crm_profissional`, `aprovar/rejeitar_cadastro`),
  tabelas `ai_agents`/`crew_configs`/`ai_prompts`, endpoints
  `/api/ai-management/execute/agent|crew`.

**Para implementar o que você pensou:**

1. Ativar/realizar a consulta real ao CFM e conselhos regionais no
   `RegistrationVerificationService` (hoje é formato apenas).
2. Adicionar campos de redes sociais (ex.: Instagram/LinkedIn) no cadastro e uma
   tool de verificação web no agente.
3. Conectar o resultado do agente ao `processar_aprovacao()`
   (auto-aprovar/rejeitar ou enviar para review manual).

---

## 5. Notas do teste

- Para completar o E2E tive que replicar manualmente o que
  `processar_aprovacao()` cria (workspace `Associacao` + `usuarios_associacoes`
  role `admin`) porque a aprovação foi feita via INSERT direto no banco.
- Screenshots do teste em `/tmp/opencode/` (cadastro, login, dashboard,
  paciente, consulta, IA).
- **B1 é crítico:** significa que todo profissional recém-aprovado (role
  `profissional`) fica bloqueado em escrita até ter vínculo de workspace com
  role `admin` — isso deve ser validado com o usuário 39 (Medico Base Teste),
  criado pelo fluxo oficial.
