# Auditoria — Conta de Secretária / Equipe & RBAC

**Data:** 2026-06-11
**Escopo:** Fases 1–4 do plano de Secretária (foundation, invite, RBAC runtime, dashboard)
**Status:** ✅ Implementado e testado (104/104 testes backend passando; build frontend com lint 0 erros nos arquivos novos)

---

## 1. Visão Geral

O AraOS precisava de um tipo de conta dedicado para a equipe administrativa
(secretárias, auxiliares, gestores) que:

1. **Não exigisse CRM/UF** — staff não é profissional de saúde.
2. **Fosse convidada pelo gestor** da Associação, sem cadastro público.
3. **Tivesse permissões granulares** — secretária pode agendar consulta
   e ver paciente, mas **não pode prescrever, evoluir prontuário ou
   configurar IA**.
4. **Ficasse estritamente isolada por tenant** — cada staff pertence a
   uma `associacao_id` e não enxerga dados de outras clínicas.

A solução implementa uma conta `secretary` (canônica AraOS) com
alias legado `auxiliar` (preservado para retrocompatibilidade do seed demo),
ancorada no `RoleRegistry` AraOS e decoradores `@require_role` / `@require_permission`.

---

## 2. Modelo de Roles (4 Camadas Alinhadas)

| Camada | Valor | Onde | Função |
|---|---|---|---|
| Identidade global | `Profissional.role` | `models.py` (DB) | Conta pessoal, independente do tenant |
| Vínculo institucional | `UsuarioAssociacao.role` | `models_extra.py` (DB) | Papel do usuário dentro daquela clínica |
| Permissões canônicas | `RoleRegistry.secretary` | `araos/platform/identity/permissions.py:251` | Conjunto de 18 permissões AraOS |
| Resolução por request | `g.user_permissions` | `middleware/permission_middleware.py` | `frozenset` populado em before_request |

### 2.1. Por que `secretary` e não `auxiliar`?

O `RoleRegistry` AraOS já define `secretary` com semântica clara (18
permissões). `auxiliar` era apenas um string sem mapeamento. Migramos a
semântica para `secretary` mantendo `auxiliar` como **alias aceito** em
todas as allow-lists durante 1 release (compatibilidade com seed demo
existente em `scripts/week11c_create_demo_environment.py`).

### 2.2. Permissões do `secretary` (AraOS)

Definidas em `araos/platform/identity/permissions.py:251`:

```
PATIENT_READ, PATIENT_WRITE,
CONSULTATION_READ, CONSULTATION_WRITE, CONSULTATION_SCHEDULE,
DOCUMENT_READ,
VOICE_USE,
SMART_FLOW_CHECKIN, SMART_FLOW_MONITOR,
COMMUNICATION_SEND, COMMUNICATION_READ,
BILLING_READ, BILLING_INVOICE_CREATE,
CLINIC_READ, PROFESSIONAL_READ,
USER_READ, FEATURE_FLAG_READ
```

> **Não inclui** (por design): `EVOLUTION_WRITE`, `PRESCRIPTION_WRITE`,
> `EXAM_REQUEST`, `AI_USE`, `AI_CONFIG_WRITE`, `LGPD_EXPORT`, `MEDICATION_PRESCRIBE`.
> Esses são exclusivos de profissionais clínicos.

---

## 3. Fluxo de Convite de Staff

```
┌─────────────────────┐                              ┌──────────────────────┐
│ Gestor (admin)      │  POST /association/<id>/     │ Sistema              │
│                     │  professional-invites        │                      │
│                     ├─────────────────────────────▶│                      │
│                     │ {nome, email, role:'secretary'│ invite_type='staff'  │
│                     │  invite_type:'staff'}        │ ConviteProfissional..│
│                     │◀─────────────────────────────│ status='pending'     │
│                     │ {convite, invite_link,       │ email_service.send_  │
│                     │  email_sent}                 │  staff_invite_email  │
└─────────────────────┘                              └──────────┬───────────┘
                                                                │
                                                                ▼
                                                       ┌──────────────────────┐
                                                       │ Secretária (email)   │
                                                       │ GET /convite-staff/  │
                                                       │   :token (público)   │
                                                       ├──────────────────────▶
                                                       │ ◀── {assoc_nome,     │
                                                       │      role, expires}  │
                                                       │ POST /solicitar-     │
                                                       │   cadastro-staff     │
                                                       │ {token, nome,        │
                                                       │  email, telefone,    │
                                                       │  senha}              │
                                                       └──────────────────────┘
```

**Validações cabeadas:**

- `invite_type` no body: `'staff' | 'professional'`. Default = `'professional'`
  para manter o fluxo de profissionais inalterado.
- Allow-list por tipo:
  - `professional` → `role='member'` (default)
  - `staff` → `role='secretary' | 'manager' | 'admin'`
- Convite expirado (`expires_at < now`) → **410 Gone**
- Convite revogado (`revoked_at IS NOT NULL`) → **410 Gone**
- Convite já aceito (`accepted_at IS NOT NULL`) → **410 Gone**
- Validação cruzada: convite `staff` **não** pode virar `profissional` e vice-versa
  (testado em `test_staff_invite_flow.py::test_invite_must_be_staff_type`).

**Criação do usuário (rota `solicitar-cadastro-staff`):**

1. Cria `Profissional` com `role='secretary'`, `status_cadastro='aprovado'`,
   `onboarding_completed=True` (o convite já é aprovação do gestor).
2. **NÃO exige CRM/UF** (campos opcionais).
3. Cria `UsuarioAssociacao(role='member', status='active')` para a
   `associacao_id` do convite.
4. Marca convite como `status='accepted'`, `accepted_at=now()`,
   `accepted_by_user_id=novo.id`.
5. Loga em `AuditLog`: `action='invite.accept'`,
   `resource_type='convite'`, `details={role, invite_type, email}`.
6. Email com credenciais (ou retorno da senha definida pelo próprio usuário).

---

## 4. RBAC Runtime

### 4.1. Middleware de Permissões

`middleware/permission_middleware.py` — registrado em `app_cors_livre.py:312`:

```python
register_permission_middleware(app)
```

Roda em `before_request` após `tenant_middleware` e popula:

```python
g.user_permissions = frozenset(
    RoleRegistry.resolve_permissions([profissional_role, association_role])
)
```

### 4.2. Decoradores (`routes/auth_decorators.py`)

**`@require_role(*allowed_roles)`** (linha 309):

- Bypass automático para `admin` e `superadmin`.
- Aceita múltiplas roles: `@require_role('admin', 'manager', 'secretary')`.
- Aceita `'qualquer'` (bypass explícito).
- Aceita callable predicate para lógica custom.
- Retorna **403** com payload estruturado:
  ```json
  {
    "error": "Acesso negado",
    "message": "Sua role (secretary) não tem permissão para este recurso.",
    "required_roles": ["admin", "profissional", "manager", "superadmin"]
  }
  ```

**`@require_permission(permission_name)`** (linha 359):

- Consulta `g.user_permissions`.
- Admin global sempre passa.
- Suporta wildcards: `patient.*` cobre `patient.read` e `patient.write`.
- Validação best-effort contra `PermissionRegistry` (warning em log se
  permissão não registrada, mas não bloqueia — útil durante rollout).

### 4.3. Decoradores Aplicados por Recurso

| Recurso | Endpoint | Roles Permitidas | Bloqueia Secretary? |
|---|---|---|---|
| Prescrição (gerar) | `POST /prescricoes/gerar` | admin, profissional, manager, superadmin | ✅ |
| Prescrição (assistente) | `POST /prescricoes/assistente` | admin, profissional, manager, superadmin | ✅ |
| Evolução (registrar) | `POST /evolucoes` | admin, profissional, manager, superadmin | ✅ |
| Evolução (atualizar) | `PUT /evolucoes/<id>` | admin, profissional, manager, superadmin | ✅ |
| Evolução (excluir) | `DELETE /evolucoes/<id>` | admin, profissional, manager, superadmin | ✅ |
| AI Chat | `POST /ai-chat` | admin, profissional, manager, superadmin | ✅ |
| Consulta (agendar) | `POST /consultas` | admin, profissional, manager, **secretary**, auxiliar, superadmin | ❌ (liberado) |
| Consulta (atualizar) | `PUT /consultas/<id>` | admin, profissional, manager, **secretary**, auxiliar, superadmin | ❌ (liberado) |
| Consulta (cancelar) | `DELETE /consultas/<id>` | admin, profissional, manager, **secretary**, auxiliar, superadmin | ❌ (liberado) |
| Check-in secretária | `POST /secretaria/consultas/<id>/checkin` | admin, manager, **secretary**, auxiliar, superadmin | ❌ (próprio) |
| Dashboard secretária | `GET /secretaria/dashboard` | admin, manager, **secretary**, auxiliar, superadmin | ❌ (próprio) |
| Quick-search pacientes | `GET /secretaria/pacientes` | admin, manager, **secretary**, auxiliar, superadmin | ❌ (próprio) |

### 4.4. Verificação via Teste Automatizado

`tests/test_rbac_runtime.py` — 20 testes cobrindo:
- Secretary tenta prescrever → 403 ✅
- Secretary acessa `/pacientes` (read-only) → 200 ✅
- Secretary faz dispensation → 200 ✅
- Secretary acessa `/ai-chat` → 403 ✅
- Admin acessa tudo → 200 ✅
- Manager acessa gestão de clínica → 200, configuração de IA → 200 ✅

---

## 5. Multi-Tenant (Segregação por Clínica)

Todas as queries do `SecretariaService` filtram por `associacao_id`
obtido de `g.current_association` (populado por `tenant_middleware`):

```python
consultas = Consulta.query.filter(
    Consulta.associacao_id == g.current_association.id,
    func.date(Consulta.data_hora) == hoje,
).all()
```

**Testes de isolamento:**

- `test_tenant_isolation`: Secretária B (assoc 2) NÃO vê consultas da clínica A (assoc 1).
- `test_checkin_blocked_for_other_tenant`: Secretária B NÃO faz check-in em consulta da A.
- `test_tenant_isolation_in_pacientes`: Listagem de pacientes mostra apenas do tenant ativo.

---

## 6. Frontend — Menu & Badge

### 6.1. Filtro de Menu (`components/NavigationMenu.js`)

Cada item de menu tem prop `roles` (array). A lógica de filtro:

```javascript
const isStaffRole = (role) =>
  ['secretary', 'auxiliar', 'manager'].includes(role);

// No filter() dos items:
if (item.roles && item.roles.length > 0) {
  if (!item.roles.includes(currentUser.role)) return false;
}

// Branch: staff vê APENAS seção "PAINEL DA EQUIPE"
if (isStaffRole(currentUser.role)) {
  // mostra apenas secretariaItems, esconde siapItems clínicos
}
```

### 6.2. Badge de Role

Switch statement na renderização do header (linha 251):

```javascript
switch (currentUser.role) {
  case 'superadmin': return '👑 Super Admin';
  case 'admin': return '👑 Admin';
  case 'secretary': return '👩‍💼 Secretária';
  case 'auxiliar': return '👩‍💼 Secretária (legado)';
  case 'manager': return '🏥 Gestor(a) da Clínica';
  case 'profissional': return '👨‍⚕️ Profissional';
  default: return '👤 Usuário';
}
```

### 6.3. Redirect Automático

`App.js:102-105` — quando uma secretária logada tenta acessar `/dashboard`
(dashboard clínico), é redirecionada automaticamente para `/secretaria/dashboard`:

```javascript
if (location.pathname === '/dashboard' &&
    ['secretary', 'auxiliar'].includes(currentUser.role)) {
  return <Navigate to="/secretaria/dashboard" replace />;
}
```

### 6.4. Rotas Protegidas (`RequireRole.jsx`)

HOC de proteção por role aplicado em todas as rotas `/secretaria/*`:

```jsx
<Route path="/secretaria/dashboard" element={
  <ProtectedRoute>
    <RequireRole roles={['secretary', 'auxiliar', 'admin', 'manager', 'superadmin']}>
      <SecretariaDashboardPage />
    </RequireRole>
  </ProtectedRoute>
} />
```

Comportamento do HOC:
- Sem `currentUser` → redirect `/login` (com state `from` para retorno).
- `currentUser.role` não está em `roles` → redirect `/dashboard` com `state.accessDenied`.

---

## 7. LGPD & Auditoria

### 7.1. Princípios Aplicados

- **Princípio da necessidade**: staff só vê dados estritamente necessários
  para atendimento (nome, CPF, data nascimento, status, observação da consulta).
  Não vê prontuário, prescrições, exames ou evoluções.
- **Princípio do menor privilégio**: 18 permissões AraOS, vs 35 do `physician`.
- **Segregação de função**: staff que dispensa não prescreve; staff que
  agenda não evolui prontuário.
- **Rastreabilidade**: cada invite/accept/revoke gera entrada em `AuditLog`.

### 7.2. Eventos Auditados

| Evento | Origem | Payload |
|---|---|---|
| `invite.create` | `POST /association/<id>/professional-invites` | `{role, invite_type, email, expires_at}` |
| `invite.accept` | `POST /solicitar-cadastro-staff` | `{convite_id, profissional_id, role, invite_type}` |
| `invite.revoke` | `POST /professional-invites/<id>/revoke` | `{convite_id, revoked_by_id, motivo}` |
| `invite.resend` | `POST /professional-invites/<id>/resend` | `{convite_id, email_destino}` |
| `secretaria.checkin` | `POST /secretaria/consultas/<id>/checkin` | `{consulta_id, secretaria_id, status_anterior, status_novo}` |

### 7.3. Templates de Email

- `services/email_service.py::send_staff_invite_email` — versão dedicada
  para staff (texto diferente do convite profissional, com copy explicando
  "você foi convidada como secretária/gestor pela clínica X").

---

## 8. Resultados de Testes

### 8.1. Backend (104/104 passando)

| Suite | # testes | Cobertura |
|---|---|---|
| `test_secretary_foundation.py` | 31 | Role validation, permission resolution, decorator 403/200 paths |
| `test_staff_invite_flow.py` | 34 | Invite create/list/revoke/resend/accept, role allow-list, expiração, audit log |
| `test_rbac_runtime.py` | 20 | Secretary bloqueada em prescrição/evolução/AI, liberada em consulta/dispensation |
| `test_secretaria_dashboard.py` | 19 | Dashboard, agenda, checkin, pacientes, multi-tenant isolation |

### 8.2. Frontend (lint 0 erros nos arquivos novos)

| Arquivo | Status |
|---|---|
| `pages/SecretariaDashboardPage.jsx` | 0 erros, 1 warning (IconButton import não usado — não impacta runtime) |
| `pages/SecretariaPacientesPage.jsx` | 0 erros |
| `pages/SecretariaAgendaPage.jsx` | 0 erros |
| `pages/SecretariaDispensacoesPage.jsx` | 0 erros |
| `components/RequireRole.jsx` | 0 erros |
| `services/secretariaService.js` | 0 erros |

---

## 9. Critérios de Sucesso — Checklist

- [x] `secretaria@demo.cannabis` loga e é redirecionada para `/secretaria/dashboard`
- [x] Menu lateral mostra APENAS itens de secretária (esconde IA, prescrição, receituário)
- [x] Badge mostra "👩‍💼 Secretária"
- [x] `POST /prescricoes` retorna 403 com mensagem clara
- [x] `POST /association/<id>/dispense` retorna 200
- [x] Gestor cria convite → email simulado gerado em `emails_simulados/`
- [x] Secretária aceita convite → conta criada, login funciona
- [x] Convite expirado/revogado retorna 410
- [x] Audit log registra `invite.create`, `invite.accept`, `invite.revoke`
- [x] `RoleRegistry.resolve_permissions(['secretary'])` retorna os 18 esperados

---

## 10. Riscos Residuais & Mitigações

| Risco | Mitigação |
|---|---|
| `auxiliar` legacy quebra em release futuro | Manter alias aceito em todas as allow-lists; planejar migração no próximo release |
| Permission engine AraOS muda contrato | Camada de compat: `resolve_effective_permissions` isola chamadas |
| Frontend com cache de `currentUser.role` | AuthContext é recarregado em logout; state sempre vem do JWT |
| Migration irreversível em produção | `downgrade()` bem definido em `migrations/versions/e1f2a3b4c5d6_*` |
| Staff sem CRM — `crm NOT NULL` falharia | Tornar nullable + CHECK constraint no nível da app |
| Multi-tenant: staff vê pacientes de outra clínica | `g.current_association` filtra todas as queries do service |

---

## 11. Próximos Passos (Sugestões)

1. Adicionar métricas de uso de staff (quantas dispensações/mês, etc.)
2. Notificações push para staff (novo paciente agendado, dispensação atrasada)
3. UI para gestor da clínica revogar convites ativos
4. Auto-desativar staff com mais de 90 dias sem login (compliance)
5. Migrar `auxiliar` → `secretary` em release futuro (1 sprint dedicada)
6. Endpoint `/api/secretaria/dashboard/export` para relatórios de produtividade

---

**Documento de auditoria. Manter em conformidade com LGPD Art. 37
(registro de operações de tratamento) e Art. 46 (medidas de segurança).**
