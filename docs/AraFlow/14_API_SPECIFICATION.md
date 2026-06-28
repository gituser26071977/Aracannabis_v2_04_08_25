# AraFlow — Especificação de API

> **Versão:** 0.1.0
> **Data:** 2026-06-24
> **Owner:** Software Architect + Tech Lead
>
> Esta especificação descreve a **API REST** do AraFlow. A API segue o padrão do AraOS, com autenticação centralizada e padrões de URL/headers consistentes.

---

## Sumário

1. Convenções gerais
2. Autenticação e autorização
3. Versionamento
4. Formato de dados
5. Erros
6. Paginação
7. Filtros e ordenação
8. Rate limiting
9. Endpoints — Paciente
10. Endpoints — Protocolos
11. Endpoints — Prescrições
12. Endpoints — Sessões
13. Endpoints — Escalas
14. Endpoints — IA
15. Endpoints — LGPD
16. Endpoints — Admin
17. Webhooks (futuro)
18. OpenAPI

---

## 1. Convenções gerais

| Aspecto | Padrão |
|---------|--------|
| Base URL | `https://api.araos.com/araflow/v1/` |
| Autenticação | Bearer token (AraOS) |
| Formato | JSON (UTF-8) |
| Datas | ISO 8601 (`2026-06-24T13:30:00Z`) |
| Timezone | UTC no servidor; conversão no cliente |
| IDs | UUIDv4 |
| Headers obrigatórios | `Authorization`, `Accept`, `Content-Type`, `X-Request-ID` |
| Headers recomendados | `X-Idempotency-Key` (mutações) |

---

## 2. Autenticação e autorização

### 2.1 Token

```
Authorization: Bearer <token>
```

- Token emitido pelo AraOS.
- Lifetime: 1h; refresh via AraOS.
- Audience: `araflow`.

### 2.2 Escopos

| Scope | Acesso |
|-------|--------|
| `araflow:patient.read` | Ler próprio perfil |
| `araflow:patient.write` | Editar próprio perfil |
| `araflow:protocol.read` | Ler biblioteca |
| `araflow:session.write` | Criar/editar sessões próprias |
| `araflow:scale.write` | Preencher escalas |
| `araflow:data.export` | Exportar dados |
| `araflow:data.delete` | Excluir conta |
| `araflow:prof.read` | Ler pacientes (profissional) |
| `araflow:prof.write` | Prescrever (profissional) |
| `araflow:ai.read` | Ler recomendações |
| `araflow:admin` | Admin |

### 2.3 Autorização contextual

- Paciente só lê/edita recursos próprios.
- Profissional só vê pacientes com vínculo ativo.
- Toda ação gera `audit_log`.

---

## 3. Versionamento

- Via URL: `/v1/`, `/v2/`.
- Compatibilidade retroativa **mínima 12 meses**.
- Deprecação: aviso 6 meses antes + header `Sunset`.

---

## 4. Formato de dados

### 4.1 Envelope padrão de resposta

```json
{
  "data": { ... },
  "meta": {
    "request_id": "uuid",
    "timestamp": "2026-06-24T13:30:00Z",
    "version": "1.0.0"
  }
}
```

### 4.2 Lista

```json
{
  "data": [ ... ],
  "meta": {
    "request_id": "...",
    "page": 1,
    "per_page": 20,
    "total": 1234,
    "has_next": true
  }
}
```

---

## 5. Erros

### 5.1 Formato

```json
{
  "error": {
    "code": "validation_error",
    "message": "Campo X é obrigatório",
    "details": [
      { "field": "email", "issue": "invalid_format" }
    ],
    "request_id": "uuid"
  }
}
```

### 5.2 Códigos

| HTTP | Code | Significado |
|------|------|-------------|
| 400 | `validation_error` | Dados inválidos |
| 401 | `unauthorized` | Token ausente/inválido |
| 403 | `forbidden` | Sem permissão |
| 404 | `not_found` | Recurso não existe |
| 409 | `conflict` | Estado inconsistente |
| 422 | `unprocessable` | Regra de negócio violada |
| 429 | `rate_limited` | Limite excedido |
| 500 | `internal_error` | Erro interno |
| 503 | `service_unavailable` | Manutenção |

---

## 6. Paginação

- **Cursor-based** (preferido) para listas longas.
- **Offset-based** disponível para admin.

```
?cursor=eyJpZCI6IjEyMyJ9&limit=20
```

Resposta inclui `next_cursor`.

---

## 7. Filtros e ordenação

```
GET /sessions?from=2026-05-01&to=2026-06-01&sort=-started_at
```

Sintaxe:
- `sort=field` (asc)
- `sort=-field` (desc)
- Múltiplos: `sort=-started_at,protocol_id`

---

## 8. Rate limiting

| Recurso | Limite |
|---------|--------|
| Geral | 100 req / minuto / usuário |
| Sessões (write) | 30 / hora / usuário |
| Escalas (write) | 5 / dia / usuário |
| Exportação | 1 / dia / usuário |
| Login | 10 / hora / IP |

Headers de resposta:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1719234600
```

---

## 9. Endpoints — Paciente

### 9.1 GET /me

Retorna perfil do paciente autenticado.

**Resposta:**
```json
{
  "data": {
    "id": "uuid",
    "user_id": "uuid",
    "primary_objective": "anxiety",
    "consent_flags": {
      "clinical": true,
      "analytics": true,
      "research": false,
      "professional_share": true
    },
    "preferences": {
      "visual": "circle",
      "audio_volume": 70,
      "notifications": true
    },
    "locale": "pt-BR",
    "timezone": "America/Sao_Paulo"
  }
}
```

### 9.2 PATCH /me

Atualiza perfil. Campos editáveis: `primary_objective`, `preferences`, `locale`, `timezone`, `birth_date`, `biological_sex`.

### 9.3 GET /me/consents

Lista histórico de consentimentos.

### 9.4 PATCH /me/consents

Atualiza consentimentos. **Gera entrada em `consent_log`.**

### 9.5 GET /me/summary

Retorna sumário de progresso.

```json
{
  "data": {
    "sessions_total": 23,
    "minutes_total": 117,
    "current_streak": 5,
    "longest_streak": 14,
    "last_session_at": "2026-06-23T22:14:00Z",
    "adherence_7d": 0.86,
    "adherence_30d": 0.78
  }
}
```

---

## 10. Endpoints — Protocolos

### 10.1 GET /protocols

Lista protocolos publicados.

**Query params:**
- `domain` (ansiedade, sono, ...)
- `intensity` (soft, moderate, intense)
- `duration_max` (minutos)
- `evidence` (A, B, C, D)
- `q` (busca textual)
- `sort` (popularity, evidence, newest)

**Resposta:**
```json
{
  "data": [
    {
      "id": "uuid",
      "slug": "4-7-8",
      "name": "Respiração 4-7-8",
      "short_description": "...",
      "domain": "anxiety",
      "intensity": "intense",
      "duration_min": 5,
      "evidence_level": "B",
      "default_visual": "circle",
      "default_audio": "calm-anxiety-02"
    }
  ],
  "meta": { "total": 12, "has_next": false }
}
```

### 10.2 GET /protocols/{id}

Detalhe completo do protocolo.

```json
{
  "data": {
    "id": "uuid",
    "name": "Respiração 4-7-8",
    "long_description": "...",
    "parameters": {
      "inspire": 4,
      "hold_full": 7,
      "expire": 8,
      "hold_empty": 0
    },
    "contraindications": ["glaucoma", "dpoc"],
    "evidence_level": "B",
    "references": [
      { "citation": "Weil (2011)", "url": "..." }
    ],
    "physiological_basis": "...",
    "clinical_objectives": ["insônia", "ansiedade aguda"],
    "version": 1
  }
}
```

### 10.3 GET /protocols/recommendations (Fase 2)

Recomendações personalizadas.

**Query params:**
- `time` (manhã, tarde, noite)
- `objective` (opcional, sobrescreve perfil)

---

## 11. Endpoints — Prescrições

### 11.1 POST /prescriptions (profissional)

Cria prescrição.

**Body:**
```json
{
  "patient_id": "uuid",
  "protocol_id": "uuid",
  "dose_per_day": 2,
  "schedule": ["08:00", "22:30"],
  "duration_days": 30,
  "notes": "Associar à psicoterapia"
}
```

**Resposta 201:**
```json
{
  "data": {
    "id": "uuid",
    "status": "active",
    "starts_at": "2026-06-24T00:00:00Z",
    "ends_at": "2026-07-24T00:00:00Z"
  }
}
```

### 11.2 GET /prescriptions

- Paciente: lista próprias.
- Profissional: lista que criou.

**Query params:** `status`, `patient_id` (profissional), `from`, `to`.

### 11.3 GET /prescriptions/{id}

Detalhe + adesão.

### 11.4 PATCH /prescriptions/{id}

Atualiza dose, schedule, notas, status.

### 11.5 POST /prescriptions/{id}/end

Encerra prescrição.

---

## 12. Endpoints — Sessões

### 12.1 POST /sessions

Registra nova sessão (escrita ao final).

**Body:**
```json
{
  "prescription_id": "uuid" /* opcional */,
  "protocol_id": "uuid",
  "source": "prescribed",
  "started_at": "2026-06-24T13:00:00Z",
  "ended_at": "2026-06-24T13:05:00Z",
  "duration_target_ms": 300000,
  "duration_actual_ms": 295000,
  "completion_pct": 98.3,
  "subjective_pre": 4,
  "subjective_post": 2,
  "visual_type": "circle",
  "audio_track_id": "calm-anxiety-02",
  "audio_volume": 65,
  "phases": [
    { "phase": "inspire", "duration_ms": 4000, "cycle_index": 1 },
    ...
  ],
  "adverse_event": false,
  "client_metadata": {
    "app_version": "1.0.0",
    "device": "iPhone",
    "os": "iOS 17"
  }
}
```

**Resposta 201:** Session criada com `id`.

### 12.2 GET /sessions

Lista sessões do paciente.

**Query params:** `from`, `to`, `protocol_id`, `source`, `sort`.

### 12.3 GET /sessions/{id}

Detalhe.

### 12.4 POST /sessions/{id}/adverse-event

Registra evento adverso fora do fluxo padrão.

**Body:**
```json
{
  "type": "dizziness",
  "severity": "mild",
  "description": "..."
}
```

### 12.5 GET /sessions/aggregate

Retorna agregados para dashboards.

**Query params:** `from`, `to`, `granularity` (day, week, month).

---

## 13. Endpoints — Escalas

### 13.1 GET /scales/templates

Lista escalas disponíveis + questões.

### 13.2 POST /scales/responses

Registra resposta de escala.

**Body:**
```json
{
  "scale_code": "GAD7",
  "responses": [2, 3, 2, 1, 2, 3, 2],
  "context": "routine"
}
```

**Resposta:**
```json
{
  "data": {
    "id": "uuid",
    "total_score": 15,
    "interpretation": "ansiedade moderada",
    "administered_at": "2026-06-24T13:30:00Z"
  }
}
```

### 13.3 GET /scales/responses

Lista respostas do paciente.

---

## 14. Endpoints — IA

### 14.1 GET /ai/recommendations

Recomendações personalizadas (Fase 2+).

### 14.2 POST /ai/feedback

Paciente/profissional marca recomendação como útil ou não.

### 14.3 GET /ai/insights

Insights clínicos para o paciente ou profissional.

---

## 15. Endpoints — LGPD

### 15.1 POST /me/data-export

Solicita exportação de dados.

**Body:**
```json
{
  "format": "json",
  "include": ["sessions", "scales", "notes"]
}
```

**Resposta 202:**
```json
{
  "data": {
    "request_id": "uuid",
    "status": "pending",
    "ready_at": null
  }
}
```

### 15.2 GET /me/data-export/{request_id}

Status da exportação. Quando `ready`, retorna `download_url`.

### 15.3 POST /me/delete

Solicita exclusão de conta.

**Body:**
```json
{
  "confirmation": "EXCLUIR MINHA CONTA",
  "reason": "Não uso mais"
}
```

**Resposta 202:**
```json
{
  "data": {
    "scheduled_for": "2026-08-23T13:30:00Z"
  }
}
```

### 15.4 POST /me/delete/cancel

Cancela exclusão agendada (até a data efetiva).

---

## 16. Endpoints — Admin

### 16.1 GET /admin/stats

Métricas globais.

### 16.2 GET /admin/users

Lista usuários (filtros).

### 16.3 GET /admin/protocols

Lista protocolos (incluindo rascunhos).

### 16.4 POST /admin/protocols

Cria protocolo (admin com permissão clínica).

### 16.5 PATCH /admin/protocols/{id}

Edita protocolo.

### 16.6 GET /admin/audit-log

Logs de auditoria (filtros por ator, ação, recurso).

---

## 17. Webhooks (Fase 3)

AraFlow envia webhooks para eventos importantes.

### 17.1 Eventos

| Evento | Descrição |
|--------|-----------|
| `session.completed` | Sessão concluída |
| `session.adverse_event` | Evento adverso |
| `prescription.created` | Nova prescrição |
| `prescription.ended` | Prescrição encerrada |
| `scale.critical` | Escala com escore crítico |
| `adherence.dropped` | Queda de adesão |
| `consent.updated` | Consentimento alterado |
| `account.deletion_scheduled` | Exclusão agendada |

### 17.2 Formato

```json
{
  "event": "session.completed",
  "data": { ... },
  "occurred_at": "2026-06-24T13:05:00Z",
  "idempotency_key": "uuid"
}
```

### 17.3 Segurança

- Assinatura HMAC-SHA256 no header `X-AraFlow-Signature`.
- Retry exponencial.
- Verificação de origem via secret.

---

## 18. OpenAPI

A especificação completa está em `openapi.yaml` (gerada automaticamente).

- Versionada por release.
- Documentação interativa em `https://docs.araos.com/araflow`.
- Geração de SDKs (TypeScript, Python, Swift, Kotlin).

---

*API é contrato. Mantenha estável, documente mudanças.*