# AraFlow — Modelo de Dados

> **Versão:** 0.1.0
> **Data:** 2026-06-24
> **Owner:** Software Architect + Data Engineer
>
> Este documento descreve as **entidades principais**, seus **atributos**, **relacionamentos** e **regras de retenção**. É a fonte de verdade para o desenho do banco de dados do AraFlow.

---

## Sumário

1. Princípios
2. Visão geral
3. Entidades principais
4. Entidades de domínio clínico
5. Entidades de uso e engajamento
6. Entidades de personalização e IA
7. Entidades de biofeedback (Fase 3)
8. Entidades de auditoria e LGPD
9. Relacionamentos
10. Índices
11. Regras de retenção
12. Migrações
13. Considerações de performance
14. Modelo multi-tenant

---

## 1. Princípios

1. **Privacy by design.** Dados sensíveis sempre criptografados.
2. **Mínimo necessário.** Não coletar o que não gera valor.
3. **Auditabilidade.** Logs imutáveis para qualquer mudança clínica.
4. **Soft delete com prazo.** LGPD; 60 dias para exclusão definitiva.
5. **Versionamento.** Protocolos e prescrições têm versão.
6. **Consistência eventual** quando não houver risco clínico.
7. **PostgreSQL** como banco primário (alinhado ao AraOS).

---

## 2. Visão geral

```
┌─────────────────────────┐
│      USERS (AraOS)      │
└─────────────┬───────────┘
              │
      ┌───────┴────────┐
      ▼                ▼
┌──────────┐    ┌──────────────┐
│ Patient  │    │ Professional │
└────┬─────┘    └──────┬───────┘
     │                 │
     │   ┌─────────────┘
     │   │
     ▼   ▼
┌──────────────────────────┐
│   Prescription           │
└──────────┬───────────────┘
           ▼
     ┌─────────────┐
     │   Session   │ ← evento central
     └─────────────┘
           │
   ┌───────┼───────┐
   ▼       ▼       ▼
Adherence Event  Adverse
   (agg)   (raw)  Event
```

---

## 3. Entidades principais

### 3.1 User (AraOS)

> Reaproveitada do AraOS. Apenas referência por `user_id`.

### 3.2 PatientProfile (AraFlow)

```sql
patient_profile (
  id                UUID PK
  user_id           UUID FK (AraOS)
  birth_date        DATE NULL
  biological_sex    ENUM('F','M','other','prefer_not')
  primary_objective ENUM('anxiety','sleep','pain','focus','relax','burnout','cannabis','apnea','asd','adhd','general')
  consent_flags     JSONB  -- { clinical: bool, analytics: bool, research: bool, professional_share: bool }
  onboarding_state  JSONB
  preferences       JSONB  -- visual, audio, notifications, accessibility
  timezone          TEXT
  locale            TEXT DEFAULT 'pt-BR'
  created_at        TIMESTAMPTZ
  updated_at        TIMESTAMPTZ
  deleted_at        TIMESTAMPTZ NULL
)
```

### 3.3 ProfessionalProfile (AraFlow)

```sql
professional_profile (
  id                UUID PK
  user_id           UUID FK (AraOS)
  specialty         TEXT[]   -- ['psychiatry','psychology',...]
  registration      TEXT     -- CRM, CRP, CREFITO
  bio               TEXT NULL
  verified_at       TIMESTAMPTZ NULL
  created_at        TIMESTAMPTZ
  updated_at        TIMESTAMPTZ
  deleted_at        TIMESTAMPTZ NULL
)
```

### 3.4 PatientProfessionalLink

```sql
patient_professional_link (
  id           UUID PK
  patient_id   UUID FK
  professional_id UUID FK
  role         ENUM('primary','secondary','therapist','observer')
  status       ENUM('pending','active','ended')
  started_at   TIMESTAMPTZ
  ended_at     TIMESTAMPTZ NULL
  created_at   TIMESTAMPTZ
)
```

---

## 4. Entidades de domínio clínico

### 4.1 Protocol (catálogo)

```sql
protocol (
  id                UUID PK
  slug              TEXT UNIQUE
  name              TEXT
  short_description TEXT
  long_description  TEXT
  domain            TEXT     -- ansiedade, sono, etc
  intensity         ENUM('soft','moderate','intense')
  duration_min      INT      -- duração alvo
  parameters        JSONB    -- {inspire, hold_full, expire, hold_empty}
  contraindications TEXT[]
  evidence_level    ENUM('A','B','C','D')
  references        JSONB    -- lista de citações
  physiological_basis TEXT
  clinical_objectives TEXT[]
  default_visual    TEXT
  default_audio     TEXT
  status            ENUM('draft','review','published','retired')
  version           INT
  published_at      TIMESTAMPTZ
  reviewer_id       UUID FK  -- profissional revisor
  created_at        TIMESTAMPTZ
  updated_at        TIMESTAMPTZ
)
```

### 4.2 ProtocolVersion

```sql
protocol_version (
  id           UUID PK
  protocol_id  UUID FK
  version      INT
  snapshot     JSONB    -- cópia completa do protocolo
  reviewer_id  UUID FK
  published_at TIMESTAMPTZ
  notes        TEXT
)
```

### 4.3 Prescription

```sql
prescription (
  id              UUID PK
  patient_id      UUID FK
  professional_id UUID FK
  protocol_id     UUID FK
  protocol_version INT
  dose_per_day    INT
  schedule        JSONB    -- ['08:00','22:30']
  duration_days   INT NULL -- NULL = contínuo
  starts_at       TIMESTAMPTZ
  ends_at         TIMESTAMPTZ NULL
  notes           TEXT
  status          ENUM('active','paused','ended','expired')
  ended_reason    TEXT NULL
  created_at      TIMESTAMPTZ
  updated_at      TIMESTAMPTZ
)
```

---

## 5. Entidades de uso e engajamento

### 5.1 Session (evento central)

```sql
session (
  id                UUID PK
  patient_id        UUID FK
  prescription_id   UUID FK NULL  -- pode ser livre
  protocol_id       UUID FK
  protocol_version  INT
  source            ENUM('prescribed','explore','sos','quick','deep_link')
  started_at        TIMESTAMPTZ
  ended_at          TIMESTAMPTZ NULL
  duration_target_ms INT
  duration_actual_ms INT
  completion_pct    NUMERIC(5,2)
  subjective_pre    SMALLINT NULL  -- 1-5
  subjective_post   SMALLINT NULL
  visual_type       TEXT
  audio_track_id    TEXT NULL
  audio_volume      SMALLINT
  adverse_event     BOOLEAN DEFAULT FALSE
  pause_count       INT DEFAULT 0
  client_metadata   JSONB  -- device, app_version, etc
  created_at        TIMESTAMPTZ
)
```

### 5.2 SessionPhase (granular)

> Útil para analytics e IA; opcional no MVP.

```sql
session_phase (
  id            UUID PK
  session_id    UUID FK
  phase         ENUM('inspire','hold_full','expire','hold_empty')
  started_at    TIMESTAMPTZ
  duration_ms   INT
  cycle_index   INT
)
```

### 5.3 AdherenceDaily (agregado)

```sql
adherence_daily (
  patient_id        UUID
  date              DATE
  sessions_target   INT
  sessions_done     INT
  minutes_total     INT
  streak_extended   BOOLEAN
  PRIMARY KEY (patient_id, date)
)
```

### 5.4 Achievement

```sql
achievement (
  id           UUID PK
  patient_id   UUID FK
  code         TEXT      -- 'streak_7', 'first_session', ...
  unlocked_at  TIMESTAMPTZ
  seen_at      TIMESTAMPTZ NULL
)
```

### 5.5 Streak

```sql
streak (
  patient_id        UUID PK
  current_length    INT
  longest_length    INT
  last_session_date DATE
  updated_at        TIMESTAMPTZ
)
```

---

## 6. Entidades de personalização e IA

### 6.1 PatientRecommendation

> Saída da IA; sempre logada.

```sql
patient_recommendation (
  id            UUID PK
  patient_id    UUID FK
  context       JSONB
  model_version TEXT
  candidates    JSONB    -- [{protocol_id, score, explanation}]
  chosen_id     UUID FK NULL  -- o que o usuário aceitou
  shown_at      TIMESTAMPTZ
  acted_at      TIMESTAMPTZ NULL
)
```

### 6.2 ClinicalScale

```sql
clinical_scale (
  id            UUID PK
  patient_id    UUID FK
  scale_code    ENUM('GAD7','PHQ9','ISI','PSS10','EVA','WHO5','MFI20')
  responses     JSONB    -- respostas brutas
  total_score   NUMERIC(5,2)
  administered_at TIMESTAMPTZ
  context       TEXT NULL  -- 'routine', 'prescribed', 'crisis'
)
```

### 6.3 ConsentLog

```sql
consent_log (
  id           UUID PK
  patient_id   UUID FK
  consents     JSONB  -- { clinical, analytics, research, professional_share }
  source       TEXT   -- 'onboarding', 'settings', 'research_invite'
  recorded_at  TIMESTAMPTZ
)
```

---

## 7. Entidades de biofeedback (Fase 3)

### 7.1 BiometricSource

```sql
biometric_source (
  id            UUID PK
  patient_id    UUID FK
  source_type   ENUM('ppg','ecg','gsr','temperature')
  device_model  TEXT
  connected_at  TIMESTAMPTZ
  disconnected_at TIMESTAMPTZ NULL
)
```

### 7.2 BiometricSample (séries temporais)

> Armazenado em TimescaleDB hypertable ou similar.

```sql
biometric_sample (
  source_id   UUID
  ts          TIMESTAMPTZ
  metric      ENUM('hr','rmssd','coherence','gsr','temp')
  value       NUMERIC(8,2)
  quality     SMALLINT  -- 0-100
  PRIMARY KEY (source_id, ts)
)
```

### 7.3 BiometricSessionSummary

```sql
biometric_session_summary (
  id                  UUID PK
  session_id          UUID FK
  mean_hr             NUMERIC(6,2)
  mean_rmssd          NUMERIC(6,2)
  coherence_pct       NUMERIC(5,2)
  coherence_quality   ENUM('low','medium','high')
  notes               TEXT
)
```

---

## 8. Entidades de auditoria e LGPD

### 8.1 AuditLog (imutável)

```sql
audit_log (
  id          UUID PK
  actor_id    UUID     -- user_id ou system
  actor_type  ENUM('user','professional','admin','system')
  action      TEXT
  resource    TEXT
  resource_id UUID NULL
  before      JSONB NULL
  after       JSONB NULL
  ip          INET NULL
  user_agent  TEXT NULL
  created_at  TIMESTAMPTZ DEFAULT now()
)
```

> Append-only. Sem update/delete.

### 8.2 DataExportRequest

```sql
data_export_request (
  id           UUID PK
  patient_id   UUID FK
  format       ENUM('json','pdf')
  status       ENUM('pending','processing','ready','expired','failed')
  requested_at TIMESTAMPTZ
  ready_at     TIMESTAMPTZ NULL
  expires_at   TIMESTAMPTZ
  download_url TEXT NULL
  ip           INET NULL
)
```

### 8.3 AccountDeletionRequest

```sql
account_deletion_request (
  id           UUID PK
  patient_id   UUID FK
  requested_at TIMESTAMPTZ
  scheduled_for TIMESTAMPTZ  -- 60 dias depois
  executed_at  TIMESTAMPTZ NULL
  reason       TEXT NULL
  status       ENUM('pending','executed','cancelled')
)
```

---

## 9. Relacionamentos (resumo)

```
User (AraOS)
├── 1:1 → PatientProfile
├── 1:1 → ProfessionalProfile
└── 1:N → PatientProfessionalLink

Protocol
├── 1:N → ProtocolVersion
└── 1:N → Prescription

Patient
├── 1:N → Prescription (via prescription.patient_id)
├── 1:N → Session
├── 1:N → Achievement
├── 1:1 → Streak
├── 1:N → ClinicalScale
├── 1:N → ConsentLog
└── 1:N → PatientRecommendation

Session
├── N:1 → Protocol
├── N:1 → Prescription (opcional)
├── 1:N → SessionPhase
└── 1:1 → BiometricSessionSummary (Fase 3)

Professional
└── 1:N → Prescription
```

---

## 10. Índices

| Tabela | Índice |
|--------|--------|
| `patient_profile` | `user_id` (UNIQUE) |
| `protocol` | `slug` (UNIQUE), `domain`, `status` |
| `prescription` | `patient_id`, `professional_id`, `status`, `(patient_id, status)` |
| `session` | `patient_id`, `started_at`, `(patient_id, started_at DESC)`, `prescription_id` |
| `session_phase` | `(session_id, cycle_index)` |
| `adherence_daily` | `(patient_id, date DESC)` |
| `achievement` | `patient_id` |
| `clinical_scale` | `(patient_id, scale_code, administered_at DESC)` |
| `consent_log` | `patient_id`, `recorded_at` |
| `audit_log` | `(actor_id, created_at)`, `(resource, resource_id)` |
| `biometric_sample` | `(source_id, ts DESC)` (Timescale) |

---

## 11. Regras de retenção

| Dado | Retenção | Origem |
|------|----------|--------|
| Sessões (agregado) | 24 meses | produto |
| Sessões (raw) | 6 meses, depois agregado | LGPD minimização |
| Escalas clínicas | Enquanto conta ativa + 60 meses anonimizado | regulatório |
| Logs de auditoria | 60 meses | regulatório |
| Telemetria técnica | 6 meses | SRE |
| Biofeedback raw | 3 meses; agregado indefinido | LGPD |
| Exportações | 24 meses (link expira em 24h) | LGPD |
| Exclusão conta | Após 60 dias, exclusão definitiva | LGPD |

---

## 12. Migrações

- Versionamento de schema com **Alembic** (PostgreSQL) ou similar.
- Toda mudança precisa de **PR com migration + rollback**.
- **Backfill** documentado quando afetar dados existentes.
- **Testes de migração** em CI.

---

## 13. Considerações de performance

### 13.1 Volume estimado (12 meses pós-MVP)

| Tabela | Linhas estimadas |
|--------|------------------|
| `patient_profile` | 10k |
| `professional_profile` | 1k |
| `protocol` | 50 (catálogo) |
| `prescription` | 50k |
| `session` | 2M |
| `session_phase` | 30M |
| `clinical_scale` | 50k |
| `audit_log` | 5M |

### 13.2 Otimizações

- **Particionamento** de `session` por mês.
- **TimescaleDB** para séries temporais (biofeedback).
- **Materialização** de `adherence_daily` (cron noturno).
- **Cache** (Redis) para catálogos e perfis.
- **Read replicas** para dashboards.

---

## 14. Modelo multi-tenant

- **Multi-tenant por tenant (clínica/instituição)** quando aplicável.
- Coluna `tenant_id` em tabelas compartilhadas.
- Row-level security para isolamento.
- AraOS como provider de identidade; tenant vem do AraOS.

---

## 15. Considerações futuras (Fase 3+)

- **Sharding** se volume passar de 100M sessões/mês.
- **Cold storage** (S3) para sessões com mais de 24 meses.
- **Data lake** para pesquisa (desnormalizado, anonimizado).
- **Streaming** para IA em tempo real.

---

*O banco é o alicerce do cuidado. Trate-o com respeito.*