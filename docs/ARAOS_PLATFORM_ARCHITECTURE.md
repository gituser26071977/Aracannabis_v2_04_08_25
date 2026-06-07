# ARAOS Platform Architecture
## Medical Intelligence Operating System — Platform Layer

> **Versão:** 2.0 — Platform Unification  
> **Data:** 2026-06-07  
> **Status:** Especificação Arquitetural  
> **Princípio:** *"Stop building modules. Start building a platform."*

---

## Sumário Executivo

ARAOS evoluiu de uma aplicação monolítica de nicho (Aracannabis) para um ecossistema de três pilares:

| Pilar | Stack | Paradigma |
|-------|-------|-----------|
| **AraOS Core** (SIAP) | Flask + React + PostgreSQL | Monolito modular, CRUD |
| **AraOS Voice** | FastAPI + WebSocket + Whisper | Streaming, Async |
| **Visual Smart Flow** | FastAPI + Vanilla JS + Event Sourcing | Event-Driven, Edge |

**O problema:** Três stacks, três frontends, três formas de fazer tenant, auth, logging, IA.

**A solução:** Uma **Platform Layer** — serviços centrais compartilhados sobre os quais todos os módulos são construídos.

> **Metáfora:** O iOS não é um conjunto de apps. É uma plataforma com kernel, serviços de sistema, frameworks e apps. ARAOS deve ser o mesmo.

---

## 1. Visão da Plataforma

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              APLICAÇÕES / MÓDULOS                                │
│                                                                                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│  │ Cannabis │ │ Cardio   │ │ Nefro    │ │ Psych    │ │ Endo     │ │  [...]   │ │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘ │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐             │
│  │  Voice   │ │Smart Flow│ │ Concierge│ │  Portal  │ │Telemed   │             │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘             │
│                                                                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│                           PLATFORM LAYER (Serviços Centrais)                     │
│                                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │   TENANT    │  │  IDENTITY   │  │  EVENT BUS  │  │   AUDIT     │            │
│  │   LAYER     │  │  SERVICE    │  │             │  │  SERVICE    │            │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │   LGPD      │  │  AI AGENT   │  │  KNOWLEDGE  │  │    CONNECT  │            │
│  │  SERVICE    │  │   LAYER     │  │   LAYER     │  │  (WhatsApp  │            │
│  │             │  │             │  │             │  │  Email SMS) │            │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘            │
│  ┌─────────────────────────────────────────────────────────────────┐            │
│  │                    MODULE FRAMEWORK                              │            │
│  │  Ciclo de vida, dependências, permissões, eventos, APIs         │            │
│  └─────────────────────────────────────────────────────────────────┘            │
│                                                                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│                           INFRASTRUCTURE LAYER                                   │
│                                                                                  │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐   │
│  │ PostgreSQL │ │   Redis    │ │  Qdrant    │ │Elasticsearch│ │  MinIO/S3  │   │
│  │ (dados)    │ │  (cache/   │ │ (vectors)  │ │  (search)   │ │  (files)   │   │
│  │            │ │  pub-sub)  │ │            │ │             │ │            │   │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘ └────────────┘   │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐                                  │
│  │  Kafka/    │ │ TimescaleDB│ │   Neo4j    │                                  │
│  │ RabbitMQ   │ │ (metrics)  │ │  (graph)   │                                  │
│  │ (events)   │ │            │ │            │                                  │
│  └────────────┘ └────────────┘ └────────────┘                                  │
│                                                                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│                           RUNTIME / ORCHESTRATION                                │
│                                                                                  │
│  Kubernetes (K3s) / Docker Swarm  ──►  Traefik  ──►  CloudFlare               │
│  Observability: OpenTelemetry + Grafana + Loki + Jaeger                         │
│  CI/CD: GitHub Actions + ArgoCD                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

**Regra de Ouro:** Nenhum módulo acessa infraestrutura diretamente. Todos acessam serviços da Platform Layer.

---

## 2. Serviços Centrais da Platform Layer

### 2.1 TENANT LAYER

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ARAOS TENANT LAYER                                   │
│                                                                              │
│  Um tenant = uma organização de saúde (clínica, hospital, consultório)      │
│                                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │ Organization │  │   Clinic     │  │ Professional │  │    User      │    │
│  │              │  │   (Unit)     │  │   (Doctor)   │  │   (Login)    │    │
│  │ • name       │  │ • address    │  │ • specialty  │  │ • email      │    │
│  │ • slug       │  │ • timezone   │  │ • CRM        │  │ • password   │    │
│  │ • plan       │  │ • settings   │  │ • schedule   │  │ • roles      │    │
│  │ • features   │  │ • rooms      │  │ • services   │  │ • orgs[]     │    │
│  │ • branding   │  │ • equipment  │  │ • patients   │  │ • mfa        │    │
│  │ • limits     │  │              │  │              │  │ • biometrics │    │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘    │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                    TENANT SETTINGS & FEATURE FLAGS                    │   │
│  │                                                                       │   │
│  │  settings: {                                                          │   │
│  │    modules: ['cannabis', 'cardio', 'voice', 'smart_flow'],           │   │
│  │    features: { voice: true, telemedicine: false, biometrics: true }, │   │
│  │    branding: { logo, colors, name },                                 │   │
│  │    scheduling: { slots, specialties, rooms },                        │   │
│  │    ai: { model, temperature, max_tokens, rag_enabled },              │   │
│  │    communication: { whatsapp_number, email_from },                   │   │
│  │    lgpd: { retention_days, consent_required },                       │   │
│  │  }                                                                    │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ESTRATÉGIA DE ISOLAMENTO:                                                  │
│  ┌────────────┬────────────┬────────────────────────────────────────────┐  │
│  │  Plano     │  Isolamento│  Implementação                             │  │
│  ├────────────┼────────────┼────────────────────────────────────────────┤  │
│  │  Starter   │  Row-level │  PostgreSQL RLS (tenant_id em cada row)   │  │
│  │  Pro       │  Schema    │  PostgreSQL schemas separados             │  │
│  │  Enterprise│  Database  │  Banco dedicado por tenant                │  │
│  └────────────┴────────────┴────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

**API do Tenant Layer:**
```
GET  /platform/tenants/me              → Tenant atual do usuário
GET  /platform/tenants/{id}/settings   → Settings do tenant
PUT  /platform/tenants/{id}/settings   → Atualizar settings
GET  /platform/tenants/{id}/users      → Usuários do tenant
GET  /platform/tenants/{id}/features   → Feature flags ativas
POST /platform/tenants/{id}/switch     → Trocar de unidade/clínica
```

---

### 2.2 ARAOS IDENTITY

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ARAOS IDENTITY                                       │
│                                                                              │
│  Serviço unificado de identidade para TODOS os pontos de entrada.           │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                    MÉTODOS DE AUTENTICAÇÃO                            │   │
│  │                                                                       │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│  │  │   Password   │  │     SSO      │  │   Biometric  │              │   │
│  │  │  (bcrypt)    │  │  (OAuth2)    │  │  (Face/Voice)│              │   │
│  │  │              │  │              │  │              │              │   │
│  │  │ • Local      │  │ • Google     │  │ • DeepFace   │              │   │
│  │  │ • Magic Link │  │ • Microsoft  │  │ • Liveness   │              │   │
│  │  │ • OTP SMS    │  │ • Gov.br     │  │ • Anti-spoof │              │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                    CHECK-IN BIOMÉTRICO                                │   │
│  │                                                                       │   │
│  │  1. Paciente chega na recepção                                        │   │
│  │  2. Câmera detecta rosto (YOLO)                                       │   │
│  │  3. Liveness check (anti-spoofing)                                    │   │
│  │  4. DeepFace extrai embedding                                         │   │
│  │  5. Compara com embeddings do tenant                                  │   │
│  │  6. Se match > threshold → identificado                               │   │
│  │  7. Emite evento: CHECKIN_COMPLETED                                   │   │
│  │  8. Agenda atualizada automaticamente                                 │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                    ESTRUTURA DO TOKEN JWT                             │   │
│  │                                                                       │   │
│  │  {                                                                    │   │
│  │    "sub": "user_id",                                                  │   │
│  │    "org": "tenant_id",                                                │   │
│  │    "roles": ["doctor", "admin"],                                      │   │
│  │    "perms": ["prescribe", "view_all_patients"],                       │   │
│  │    "modules": ["cannabis", "voice"],                                  │   │
│  │    "biometric": { "enrolled": true, "liveness_passed": true },       │   │
│  │    "iat": 1717770000,                                                 │   │
│  │    "exp": 1717773600                                                  │   │
│  │  }                                                                    │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Fluxo de Identidade Unificado:**
```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Portal     │     │   SIAP Web   │     │  Smart Flow  │     │  Telemed     │
│  (Paciente)  │     │   (Médico)   │     │  (Kiosk)     │     │  (Video)     │
└──────┬───────┘     └──────┬───────┘     └──────┬───────┘     └──────┬───────┘
       │                    │                    │                    │
       └────────────────────┴────────────────────┴────────────────────┘
                                   │
                         ┌─────────▼─────────┐
                         │   ARAOS IDENTITY  │
                         │   (OAuth2 Server) │
                         └─────────┬─────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              │                    │                    │
       ┌──────▼──────┐    ┌───────▼───────┐   ┌───────▼───────┐
       │  Password   │    │   Biometric   │   │     SSO       │
       │   Store     │    │   Service     │   │   (Google)    │
       └─────────────┘    └───────────────┘   └───────────────┘
```

---

### 2.3 ARAOS EVENT BUS

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ARAOS EVENT BUS                                      │
│                                                                              │
│  Todo evento relevante na plataforma é publicado no Event Bus.              │
│  Qualquer módulo pode consumir eventos relevantes.                          │
│                                                                              │
│  FORMATO DO EVENTO:                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ {                                                                    │    │
│  │   "event_id": "uuid",                                                │    │
│  │   "event_type": "PATIENT_CREATED",                                   │    │
│  │   "event_version": "1.0",                                            │    │
│  │   "timestamp": "2026-06-07T10:00:00Z",                               │    │
│  │   "tenant_id": "org_123",                                            │    │
│  │   "aggregate_type": "patient",                                       │    │
│  │   "aggregate_id": "pat_456",                                         │    │
│  │   "actor": { "id": "user_789", "type": "doctor" },                   │    │
│  │   "payload": { "name": "João", "cpf": "..." },                       │    │
│  │   "metadata": { "source": "siap", "ip": "...", "trace_id": "..." }   │    │
│  │ }                                                                    │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  CATÁLOGO DE EVENTOS:                                                       │
│                                                                              │
│  PACIENTE:                                                                  │
│    PATIENT_CREATED, PATIENT_UPDATED, PATIENT_DELETED,                       │
│    PATIENT_MERGED, PATIENT_ANONYMIZED                                       │
│                                                                              │
│  CONSULTA:                                                                  │
│    CONSULTATION_SCHEDULED, CONSULTATION_STARTED,                            │
│    CONSULTATION_FINISHED, CONSULTATION_CANCELLED,                           │
│    CONSULTATION_NO_SHOW                                                     │
│                                                                              │
│  PRONTUÁRIO:                                                                │
│    EVOLUTION_CREATED, PRESCRIPTION_CREATED,                                 │
│    EXAM_REQUESTED, DIAGNOSIS_ADDED,                                         │
│    ALLERGY_ADDED, MEDICATION_PRESCRIBED                                     │
│                                                                              │
│  VOZ:                                                                       │
│    VOICE_SESSION_STARTED, VOICE_SESSION_ENDED,                              │
│    WAKE_WORD_DETECTED, VOICE_COMMAND_EXECUTED,                              │
│    VOICE_TRANSCRIPTION_COMPLETED, VOICE_ENTITY_EXTRACTED                    │
│                                                                              │
│  SMART FLOW:                                                                │
│    CHECKIN_DETECTED, CHECKIN_COMPLETED,                                     │
│    PATIENT_ENTERED_ROOM, PATIENT_LEFT_ROOM,                                 │
│    WAIT_TIME_EXCEEDED, FLOW_COMPLETED                                       │
│                                                                              │
│  COMUNICAÇÃO:                                                               │
│    WHATSAPP_RECEIVED, WHATSAPP_SENT,                                        │
│    EMAIL_SENT, SMS_SENT,                                                    │
│    NOTIFICATION_DELIVERED, NOTIFICATION_FAILED                              │
│                                                                              │
│  DOCUMENTOS:                                                                │
│    DOCUMENT_UPLOADED, DOCUMENT_PROCESSED,                                   │
│    OCR_COMPLETED, DOCUMENT_CLASSIFIED                                       │
│                                                                              │
│  PAGAMENTO:                                                                 │
│    INVOICE_CREATED, PAYMENT_RECEIVED,                                       │
│    PAYMENT_FAILED, SUBSCRIPTION_RENEWED                                     │
│                                                                              │
│  SEGURANÇA / LGPD:                                                          │
│    LOGIN_SUCCEEDED, LOGIN_FAILED,                                           │
│    DATA_EXPORT_REQUESTED, DATA_PURGED,                                      │
│    CONSENT_GIVEN, CONSENT_REVOKED                                           │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Padrão Publish/Subscribe:**
```
┌──────────────┐    ┌──────────────────────────────────────────────┐    ┌──────────────┐
│   Módulo A   │───►│           ARAOS EVENT BUS                    │◄───│   Módulo B   │
│  (publica)   │    │                                              │    │  (consome)   │
└──────────────┘    │  ┌────────────┐  ┌────────────┐  ┌────────┐ │    └──────────────┘
                    │  │  Topic:    │  │  Topic:    │  │ Topic: │ │
┌──────────────┐    │  │  patient   │  │  consult   │  │ voice  │ │    ┌──────────────┐
│   Módulo C   │───►│  │  events    │  │  events    │  │ events │ │◄───│   Módulo D   │
│  (publica)   │    │  └────────────┘  └────────────┘  └────────┘ │    │  (consome)   │
└──────────────┘    │                                              │    └──────────────┘
                    │  Kafka / RabbitMQ / Redis Streams            │
                    └──────────────────────────────────────────────┘
```

---

### 2.4 AUDIT SERVICE

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ARAOS AUDIT SERVICE                                  │
│                                                                              │
│  Toda ação na plataforma é auditável e imutável.                            │
│                                                                              │
│  PRINCÍPIOS:                                                                │
│  1. Append-only — nunca deleta, nunca altera                                │
│  2. Criptografado — hash chain para integridade                             │
│  3. Indexado — por tenant, usuário, data, tipo de ação                      │
│  4. Retenção — conforme LGPD (mínimo 5 anos para saúde)                     │
│                                                                              │
│  SCHEMA:                                                                    │
│  ┌──────────────┬─────────────┬──────────────────────────────────────────┐  │
│  │ Campo        │ Tipo        │ Descrição                                │  │
│  ├──────────────┼─────────────┼──────────────────────────────────────────┤  │
│  │ id           │ UUID        │ Identificador único do evento de audit   │  │
│  │ timestamp    │ TIMESTAMPTZ │ Quando ocorreu                           │  │
│  │ tenant_id    │ UUID        │ Organização                              │  │
│  │ user_id      │ UUID        │ Quem executou                            │  │
│  │ user_role    │ STRING      │ Papel do usuário                         │  │
│  │ action       │ STRING      │ Tipo da ação (CREATE, READ, UPDATE...)   │  │
│  │ resource     │ STRING      │ O que foi afetado (patient, exam...)     │  │
│  │ resource_id  │ UUID        │ ID do recurso afetado                    │  │
│  │ changes      │ JSONB       │ Delta (before / after)                   │  │
│  │ context      │ JSONB       │ IP, User-Agent, Geo, Session ID          │  │
│  │ compliance   │ JSONB       │ LGPD: base legal, consentimento          │  │
│  │ hash         │ STRING      │ Hash SHA-256 da linha + hash anterior    │  │
│  └──────────────┴─────────────┴──────────────────────────────────────────┘  │
│                                                                              │
│  CASOS DE USO:                                                              │
│  • "Quem acessou o prontuário do paciente X em Y?"                          │
│  • "Quantas prescrições o Dr. Z criou no mês passado?"                      │
│  • "Mostre todas as alterações no diagnóstico do paciente X"                │
│  • "Detecte acessos fora do horário comercial"                              │
│  • "Gere relatório de auditoria para fiscalização"                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### 2.5 LGPD SERVICE

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ARAOS LGPD SERVICE                                   │
│                                                                              │
│  Herda e expande o excelente módulo LGPD do Visual Smart Flow.              │
│  Centraliza conformidade para TODOS os módulos.                             │
│                                                                              │
│  FUNCIONALIDADES:                                                           │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 1. CONSENTIMENTO                                                    │   │
│  │    • Consentimento granular por finalidade                          │   │
│  │    • Versionamento de termos                                        │   │
│  │    • Opt-in / opt-out de IA, biométria, marketing                   │   │
│  │    • Registro de quando, como e onde consentiu                      │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │ 2. RETENÇÃO                                                         │   │
│  │    • Políticas por tipo de dado (prontuário: 20a, chat: 2a...)      │   │
│  │    • Purge automático após prazo                                    │   │
│  │    • Retenção legal vs retenção operacional                         │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │ 3. ANONIMIZAÇÃO                                                     │   │
│  │    • Pseudonimização para pesquisa                                  │   │
│  │    • Anonimização diferencial para ML                               │   │
│  │    • K-anonimity checks                                             │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │ 4. DIREITOS DO TITULAR                                              │   │
│  │    • Exportação em formato aberto (JSON, PDF)                       │   │
│  │    • Portabilidade para outro sistema                               │   │
│  │    • Retificação com trilha de mudanças                             │   │
│  │    • Exclusão (direito ao esquecimento) com proof of deletion       │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │ 5. TRILHA DE AUDITORIA                                              │   │
│  │    • Quem acessou o quê, quando, por que                            │   │
│  │    • Alertas de acessos anômalos                                    │   │
│  │    • Relatórios para DPO                                            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### 2.6 AI AGENT LAYER — ARAOS AGENT PLATFORM

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ARAOS AGENT PLATFORM                                      │
│                                                                              │
│  Framework unificado para criação, execução e gerenciamento de agentes IA.  │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                    AGENT DEFINITION                                   │   │
│  │                                                                       │   │
│  │  {                                                                    │   │
│  │    "agent_id": "concierge_001",                                       │   │
│  │    "tenant_id": "org_123",                                            │   │
│  │    "name": "Concierge AraOS",                                         │   │
│  │    "type": "concierge",  // concierge | sdr | clinical | intake      │   │
│  │    "llm_config": {                                                    │   │
│  │      "provider": "google",                                            │   │
│  │      "model": "gemini-2.5-pro",                                       │   │
│  │      "temperature": 0.3,                                              │   │
│  │      "max_tokens": 4096                                               │   │
│  │    },                                                                 │   │
│  │    "personality": {                                                   │   │
│  │      "tone": "professional",                                          │   │
│  │      "language": "pt-BR",                                             │   │
│  │      "greeting": "Olá! Sou o assistente AraOS..."                     │   │
│  │    },                                                                 │   │
│  │    "knowledge_sources": [                                             │   │
│  │      "tenant_protocols", "specialty_guidelines", "patient_history"   │   │
│  │    ],                                                                 │   │
│  │    "tools": [                                                         │   │
│  │      "search_patient", "schedule_appointment", "send_whatsapp",      │   │
│  │      "query_exams", "generate_prescription", "check_guideline"       │   │
│  │    ],                                                                 │   │
│  │    "permissions": ["read_patient", "write_appointment"],             │   │
│  │    "channels": ["whatsapp", "portal", "voice"],                      │   │
│  │    "status": "active"                                                 │   │
│  │  }                                                                    │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  TIPOS DE AGENTES NATIVOS:                                                  │
│                                                                              │
│  ┌──────────────┬───────────────────────────────────────────────────────┐   │
│  │  CONCIERGE   │ Atendimento geral: agendamento, dúvidas, direcionamento│   │
│  ├──────────────┼───────────────────────────────────────────────────────┤   │
│  │  SDR         │ Qualificação de leads, demos, campanhas               │   │
│  ├──────────────┼───────────────────────────────────────────────────────┤   │
│  │  INTAKE      │ Coleta pré-consulta: sintomas, histórico, documentos  │   │
│  ├──────────────┼───────────────────────────────────────────────────────┤   │
│  │  CLINICAL    │ Copiloto do médico: voz, RAG, evolução, prescrição   │   │
│  ├──────────────┼───────────────────────────────────────────────────────┤   │
│  │  FOLLOW-UP   │ Pós-consulta: lembretes, escalas, reagendamento      │   │
│  ├──────────────┼───────────────────────────────────────────────────────┤   │
│  │  SPECIALTY   │ Agentes especializados por área médica               │   │
│  └──────────────┴───────────────────────────────────────────────────────┘   │
│                                                                              │
│  ARQUITETURA DE EXECUÇÃO:                                                   │
│                                                                              │
│  ┌──────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────┐   │
│  │  Input   │────►│   Intent     │────►│   Context    │────►│  LLM     │   │
│  │ (texto/  │     │  Classifier  │     │  Assembler   │     │  Call    │   │
│  │  voz)    │     │              │     │ (RAG + mem)  │     │          │   │
│  └──────────┘     └──────────────┘     └──────────────┘     └────┬─────┘   │
│                                                                  │         │
│                              ┌─────────────────────────────────────┘         │
│                              ▼                                               │
│  ┌──────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────┐   │
│  │  Output  │◄────│  Response    │◄────│  Tool        │◄────│  Action  │   │
│  │ (texto/  │     │  Formatter   │     │  Executor    │     │  Parser  │   │
│  │  voz)    │     │              │     │              │     │          │   │
│  └──────────┘     └──────────────┘     └──────────────┘     └──────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### 2.7 KNOWLEDGE LAYER

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ARAOS KNOWLEDGE LAYER                                │
│                                                                              │
│  Repositório único de conhecimento para todos os agentes.                   │
│                                                                              │
│  FONTES DE CONHECIMENTO:                                                    │
│                                                                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │   STRUCTURED    │  │   UNSTRUCTURED  │  │   EXTERNAL      │             │
│  │                 │  │                 │  │                 │             │
│  │ • Patient EHR   │  │ • PDFs          │  │ • Medical       │             │
│  │ • Exams (LOINC) │  │ • Images        │  │   Guidelines    │             │
│  │ • Medications   │  │ • Transcripts   │  │ • Drug DBs      │             │
│  │   (ATC)         │  │ • Emails        │  │ • ICD-10/11     │             │
│  │ • Diagnoses     │  │ • WhatsApp      │  │ • PubMed        │             │
│  │   (ICD)         │  │   messages      │  │ • SNOMED-CT     │             │
│  │ • Vital Signs   │  │ • Voice         │  │ • UMLS          │             │
│  │ • Appointments  │  │   recordings    │  │                 │             │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘             │
│           │                    │                    │                       │
│           └────────────────────┼────────────────────┘                       │
│                                ▼                                            │
│                   ┌─────────────────────────────┐                           │
│                   │     INGESTION PIPELINE      │                           │
│                   │  • OCR (Tesseract)          │                           │
│                   │  • Entity Extraction (NER)  │                           │
│                   │  • Embedding (E5/multilingual)│                         │
│                   │  • Chunking + Metadata      │                           │
│                   │  • Indexing                 │                           │
│                   └─────────────┬───────────────┘                           │
│                                 ▼                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      KNOWLEDGE GRAPH + VECTOR STORE                  │   │
│  │                                                                      │   │
│  │  Neo4j (Relações)                    Qdrant (Embeddings)            │   │
│  │  ┌─────────────────┐                 ┌─────────────────┐            │   │
│  │  │ Paciente ──[TEM]─► Diagnóstico   │ "paciente tem    │            │   │
│  │  │ Paciente ──[USA]─► Medicamento   │  diabetes tipo 2"│            │   │
│  │  │ Medicamento ─[INTERAGE]─► Med    │  → [0.12, -0.34, │            │   │
│  │  │ Exame ──[MOSTRA]─► Resultado     │   0.56, ...]      │            │   │
│  │  └─────────────────┘                 └─────────────────┘            │   │
│  │                                                                      │   │
│  │  TimescaleDB (Séries Temporais)                                      │   │
│  │  ┌─────────────────────────────────────────────────────────────┐    │   │
│  │  │ glucose: [90, 95, 110, 105, 120, ...] @ timestamps         │    │   │
│  │  │ creatinine: [1.1, 1.2, 1.3, 1.5, 1.8, ...] @ timestamps   │    │   │
│  │  └─────────────────────────────────────────────────────────────┘    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### 2.8 ARAOS CONNECT (Communication Layer)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ARAOS CONNECT                                        │
│                                                                              │
│  Hub unificado de comunicação. Um canal de entrada, múltiplos de saída.    │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                     CANAIS DE ENTRADA                                 │   │
│  │                                                                       │   │
│  │  WhatsApp ◄── Evolution API                                          │   │
│  │  Email    ◄── SMTP / SendGrid                                        │   │
│  │  SMS      ◄── Twilio / Zenvia                                        │   │
│  │  Portal   ◄── REST API                                               │   │
│  │  Voice    ◄── WebSocket                                              │   │
│  │  Sensor   ◄── HTTP Webhook                                           │   │
│  └──────────────────────┬───────────────────────────────────────────────┘   │
│                         │                                                  │
│                         ▼                                                  │
│              ┌────────────────────┐                                        │
│              │  MESSAGE ROUTER    │                                        │
│              │                    │                                        │
│              │  • Classifica      │  → Atendimento, Urgência, Agendamento │
│              │  • Enriquece       │  → Adiciona contexto do paciente      │
│              │  • Roteia          │  → Para agente ou fila humana         │
│              │  • Prioriza        │  → SLA por canal e urgência           │
│              └─────────┬──────────┘                                        │
│                        │                                                   │
│           ┌────────────┼────────────┐                                     │
│           │            │            │                                     │
│           ▼            ▼            ▼                                     │
│    ┌──────────┐ ┌──────────┐ ┌──────────┐                               │
│    │  AGENTE  │ │  HUMANO  │ │ AUTOMATED│                               │
│    │   (IA)   │ │  (Fila)  │ │  ACTION  │                               │
│    └────┬─────┘ └────┬─────┘ └────┬─────┘                               │
│         │            │            │                                      │
│         └────────────┼────────────┘                                      │
│                      ▼                                                   │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │                     CANAIS DE SAÍDA                                   │ │
│  │                                                                       │ │
│  │  WhatsApp  ──► Evolution API                                         │ │
│  │  Email     ──► SMTP / SendGrid                                       │ │
│  │  SMS       ──► Twilio / Zenvia                                       │ │
│  │  Push      ──► Firebase / OneSignal                                  │ │
│  │  Voice     ──► TTS / Gemini Live                                     │ │
│  │  Dashboard ──► WebSocket / SSE                                       │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### 2.9 MODULE FRAMEWORK

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ARAOS MODULE FRAMEWORK                               │
│                                                                              │
│  Padrão oficial para construção de módulos sobre a Platform Layer.          │
│                                                                              │
│  ESTRUTURA DE UM MÓDULO:                                                    │
│                                                                              │
│  cannabis_module/                                                            │
│  ├── __init__.py           ← Registro do módulo na plataforma               │
│  ├── manifest.json         ← Metadados, dependências, permissões            │
│  ├── models.py             ← Models SQLAlchemy (herdam de db.Model)         │
│  ├── api.py                ← Endpoints REST (Blueprint Flask)               │
│  ├── events.py             ← Eventos que publica/consome                    │
│  ├── agents/               ← Agentes especializados do módulo               │
│  │   ├── clinical_agent.py                                                               │
│  │   └── intake_agent.py                                                              │
│  ├── frontend/             ← Componentes React                              │
│  │   ├── pages/                                                              │
│  │   └── components/                                                              │
│  ├── protocols/            ← Protocolos clínicos em JSON Schema              │
│  │   ├── dosing_protocol.json                                                              │
│  │   └── screening_protocol.json                                                              │
│  ├── scales/               │ Escalas de avaliação                            │
│  │   └── snap_iv.json                                                              │
│  └── tests/                ← Testes unitários e de integração               │
│                                                                              │
│  MANIFESTO (manifest.json):                                                 │
│  {                                                                           │
│    "module_id": "cannabis",                                                  │
│    "version": "1.0.0",                                                       │
│    "name": "AraOS Cannabis",                                                 │
│    "description": "Módulo especializado em Cannabis Medicinal",              │
│    "author": "AraOS Team",                                                   │
│    "license": "proprietary",                                                 │
│    "dependencies": [                                                         │
│      "core", "voice", "smart_flow"                                           │
│    ],                                                                        │
│    "permissions": [                                                          │
│      "read_patient", "write_prescription", "view_exams"                      │
│    ],                                                                        │
│    "events": {                                                               │
│      "publishes": ["PRESCRIPTION_CREATED", "DOSAGE_ADJUSTED"],               │
│      "consumes": ["PATIENT_CREATED", "CONSULTATION_STARTED"]                 │
│    },                                                                        │
│    "features": {                                                             │
│      "requires_ai": true,                                                    │
│      "requires_biometric": false,                                            │
│      "requires_payment": true                                                │
│    },                                                                        │
│    "ui": {                                                                   │
│      "pages": [                                                              │
│        { "route": "/cannabis/dosage", "component": "DosageManager" },        │
│        { "route": "/cannabis/protocols", "component": "ProtocolPage" }       │
│      ],                                                                      │
│      "menu_items": [                                                         │
│        { "label": "Dosagem", "icon": "medication", "route": "/cannabis/dosage" }│
│      ],                                                                      │
│      "dashboard_widgets": ["THC_CBD_Ratio", "Monthly_Prescriptions"]         │
│    }                                                                         │
│  }                                                                           │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### 2.10 ARAOS CONCIERGE

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ARAOS CONCIERGE                                      │
│                                                                              │
│  Evolução do SDR "Lia". Agente universal de relacionamento.                │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                    JORNADA DO PACIENTE                                │   │
│  │                                                                       │   │
│  │  PRÉ-CONSULTA                    CONSULTA           PÓS-CONSULTA     │   │
│  │  ┌────────────┐              ┌────────────┐       ┌────────────┐    │   │
│  │  │ Coleta de  │              │ Transcrição│       │ Follow-up  │    │   │
│  │  │ sintomas   │              │ assistida  │       │ automático │    │   │
│  │  │ via        │              │ por voz    │       │            │    │   │
│  │  │ WhatsApp   │              │            │       │ Lembrete   │    │   │
│  │  ├────────────┤              ├────────────┤       │ de exame   │    │   │
│  │  │ Upload de  │              │ Sugestões  │       │            │    │   │
│  │  │ documentos │              │ contextuais│       │ Escala de  │    │   │
│  │  │ e exames   │              │ do Copilot │       │ avaliação  │    │   │
│  │  ├────────────┤              ├────────────┤       │            │    │   │
│  │  │ Agendamento│              │ Resumo     │       │ Reagenda-  │    │   │
│  │  │ inteligente│              │ automático │       │ mento      │    │   │
│  │  │ (calendar) │              │ da consulta│       │ sugerido   │    │   │
│  │  └────────────┘              └────────────┘       └────────────┘    │   │
│  │                                                                       │   │
│  │  COMERCIAL                         RELACIONAMENTO                     │   │
│  │  ┌────────────┐              ┌────────────┐                          │   │
│  │  │ Qualificação│              │ Campanhas  │                          │   │
│  │  │ de leads   │              │ sazonais   │                          │   │
│  │  ├────────────┤              ├────────────┤                          │   │
│  │  │ Agendamento│              │ Reativação │                          │   │
│  │  │ de demos   │              │ de inativos│                          │   │
│  │  ├────────────┤              ├────────────┤                          │   │
│  │  │ Follow-up  │              │ Aniversário│                          │   │
│  │  │ pós-demo   │              │ de paciente│                          │   │
│  │  └────────────┘              └────────────┘                          │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  PERSONALIZAÇÃO POR TENANT:                                                 │
│  • Tom de voz (formal / casual)                                             │
│  • Horário de atendimento                                                   │
│  • Escalas de triagem                                                        │
│  • Fluxos de conversa (decision trees)                                      │
│  • Integrações (calendar, payment, telemedicine)                            │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Fluxo de Comunicação Entre Módulos

### 3.1 Fluxo Completo: Paciente Chega na Clínica

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  TEMPO  │  PACIENTE          │  SMART FLOW    │  EVENT BUS   │  SIAP CORE   │
├─────────────────────────────────────────────────────────────────────────────┤
│  T-24h  │ Recebe lembrete    │                │ WHATSAPP_SENT│              │
│         │ WhatsApp da consult│                │              │              │
├─────────┼────────────────────┼────────────────┼──────────────┼──────────────┤
│  T-2h   │ Responde ao bot    │                │WHATSAPP_RCVD │              │
│         │ com "vou chegar"   │                │              │              │
├─────────┼────────────────────┼────────────────┼──────────────┼──────────────┤
│  T+0    │ Chega na clínica   │ Câmera detecta │CHECKIN_DETECT│              │
│         │                    │ rosto + liveness│              │              │
├─────────┼────────────────────┼────────────────┼──────────────┼──────────────┤
│  T+1s   │                    │ Match facial   │CHECKIN_COMPLT│ Atualiza     │
│         │                    │ identifica     │              │ status para  │
│         │                    │ paciente       │              │ "Presente"   │
├─────────┼────────────────────┼────────────────┼──────────────┼──────────────┤
│  T+5s   │                    │ Painel de fila │FLOW_UPDATED  │ Notifica     │
│         │                    │ atualiza       │              │ médico       │
├─────────┼────────────────────┼────────────────┼──────────────┼──────────────┤
│  T+2min │                    │ Entra na sala  │ROOM_ENTERED  │ Inicia       │
│         │                    │ de espera      │              │ temporizador │
├─────────┼────────────────────┼────────────────┼──────────────┼──────────────┤
│  T+15min│                    │ Entra no       │ROOM_ENTERED  │ Muda status  │
│         │                    │ consultório    │              │ "Em consulta"│
├─────────┼────────────────────┼────────────────┼──────────────┼──────────────┤
│  T+45min│ Médico fala com    │                │              │ VOICE_SESSION│
│         │ paciente. AraOS    │                │              │ _STARTED     │
│         │ Voice transcreve   │                │              │              │
├─────────┼────────────────────┼────────────────┼──────────────┼──────────────┤
│  T+50min│                    │                │              │ Médico: "Ara,│
│         │                    │                │              │ solicitar    │
│         │                    │                │              │ hemograma"   │
├─────────┼────────────────────┼────────────────┼──────────────┼──────────────┤
│  T+52min│                    │                │EXAM_REQUESTED│ Prescrição   │
│         │                    │                │              │ gerada       │
├─────────┼────────────────────┼────────────────┼──────────────┼──────────────┤
│  T+55min│                    │ Sai do         │ROOM_LEFT     │ CONSULTATION_│
│         │                    │ consultório    │              │ _FINISHED    │
├─────────┼────────────────────┼────────────────┼──────────────┼──────────────┤
│  T+56min│                    │ Painel chama   │FLOW_UPDATED  │              │
│         │                    │ próximo        │              │              │
├─────────┼────────────────────┼────────────────┼──────────────┼──────────────┤
│  T+1h   │ Recebe resumo por  │                │WHATSAPP_SENT │              │
│         │ WhatsApp + receita │                │              │              │
│         │ digital            │                │              │              │
├─────────┼────────────────────┼────────────────┼──────────────┼──────────────┤
│  T+7d   │ Recebe follow-up   │                │WHATSAPP_SENT │              │
│         │ "Como está a dor?" │                │              │              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Arquitetura de Eventos Detalhada

### 4.1 Topologia

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         EVENT TOPOLOGY                                       │
│                                                                              │
│                              ┌─────────────┐                                │
│                              │   KAFKA     │                                │
│                              │  (Broker)   │                                │
│                              └──────┬──────┘                                │
│                                     │                                       │
│         ┌───────────────────────────┼───────────────────────────┐           │
│         │                           │                           │           │
│    ┌────▼────┐               ┌──────▼──────┐             ┌──────▼──────┐   │
│    │ PRODUCERS│               │   TOPICS    │             │  CONSUMERS  │   │
│    │         │               │             │             │             │   │
│    │ SIAP    │──► patient.events           │──► SIAP     │             │   │
│    │ Voice   │──► voice.events             │──► Voice    │             │   │
│    │ VSF     │──► flow.events              │──► VSF      │             │   │
│    │ Connect │──► communication.events     │──► Connect  │             │   │
│    │ Concierge│──► concierge.events        │──► Concierge│             │   │
│    │ Agents  │──► agent.events             │──► Agents   │             │   │
│    │ Audit   │──► audit.events             │──► Audit    │             │   │
│    └─────────┘               │             │             └─────────────┘   │
│                              │ audit.log   │                                │
│                              │ dead.letter │                                │
│                              └─────────────┘                                │
│                                                                              │
│  Padrão: Event Sourcing + CQRS                                               │
│  • Write: Todos os eventos são persistidos no Event Store (append-only)    │
│  • Read: Projeções materializadas para consultas rápidas                     │
│  • Replay: Estado pode ser reconstruído replayando eventos                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Arquitetura Multi-Tenant

### 5.1 Estratégia Híbrida por Plano

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    MULTI-TENANT STRATEGY                                     │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  STARTER (Shared)                                                   │   │
│  │  ┌─────────────────────────────────────────────────────────────┐   │   │
│  │  │  PostgreSQL — Schema público                                 │   │   │
│  │  │  ┌──────────┐ ┌──────────┐ ┌──────────┐                    │   │   │
│  │  │  │tenant_id │ │tenant_id │ │tenant_id │  ← RLS             │   │   │
│  │  │  │ = 'a'    │ │ = 'b'    │ │ = 'c'    │                    │   │   │
│  │  │  └──────────┘ └──────────┘ └──────────┘                    │   │   │
│  │  │  • Custo mínimo                                             │   │   │
│  │  │  • Backup único                                             │   │   │
│  │  └─────────────────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  PROFESSIONAL (Schema Isolation)                                    │   │
│  │  ┌─────────────────────────────────────────────────────────────┐   │   │
│  │  │  PostgreSQL — Schemas separados                              │   │   │
│  │  │  ┌─────────┐ ┌─────────┐ ┌─────────┐                       │   │   │
│  │  │  │tenant_a │ │tenant_b │ │tenant_c │                       │   │   │
│  │  │  │ schema  │ │ schema  │ │ schema  │                       │   │   │
│  │  │  └─────────┘ └─────────┘ └─────────┘                       │   │   │
│  │  │  • Isolamento lógico                                        │   │   │
│  │  │  • Backup/restore granular                                  │   │   │
│  │  └─────────────────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ENTERPRISE (Database Isolation)                                    │   │
│  │  ┌─────────────────────────────────────────────────────────────┐   │   │
│  │  │  PostgreSQL — Bancos dedicados                               │   │   │
│  │  │  ┌──────────┐ ┌──────────┐ ┌──────────┐                    │   │   │
│  │  │  │  DB_A    │ │  DB_B    │ │  DB_C    │                    │   │   │
│  │  │  │(dedicado)│ │(dedicado)│ │(dedicado)│                    │   │   │
│  │  │  └──────────┘ └──────────┘ └──────────┘                    │   │   │
│  │  │  • Isolamento físico                                        │   │   │
│  │  │  • Compliance máximo (hospitalar)                           │   │   │
│  │  └─────────────────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Roadmap de Migração

### Fase 1: Foundation (Mês 1-2)
| Semana | Entrega |
|--------|---------|
| S1 | Tenant Layer unificado (portar VSF tenant → SIAP) |
| S2 | Identity Service v1 (unificar login SIAP + VSF) |
| S3 | Event Bus básico (Redis Streams) + catálogo de eventos |
| S4 | Audit Service + LGPD Service centralizados |
| S5-6 | Integration tests, documentação, deploy |

### Fase 2: Intelligence (Mês 3-4)
| Semana | Entrega |
|--------|---------|
| S7 | Knowledge Layer (Qdrant + ingestão de documentos) |
| S8 | AI Agent Layer (framework + agentes Concierge e SDR) |
| S9 | ARAOS Connect (unificar WhatsApp/email/SMS) |
| S10 | Module Framework (cannabis como primeiro módulo oficial) |
| S11-12 | Polish, testes, beta com 2-3 clínicas |

### Fase 3: Fusion (Mês 5-6)
| Semana | Entrega |
|--------|---------|
| S13 | VSF como microserviço integrado (Event Bus + APIs) |
| S14 | Voice Copilot com Knowledge Layer |
| S15 | Smart Flow + SIAP unificados no frontend React |
| S16 | Concierge operacional (pré/pós consulta) |
| S17-18 | Performance tuning, segurança, LGPD audit |

### Fase 4: Scale (Mês 7-12)
- Kubernetes em produção
- Auto-scaling
- Multi-região
- Marketplace de módulos (3rd party)
- API pública
- White-label completo

---

## 7. Riscos Arquiteturais

| # | Risco | Prob. | Impacto | Mitigação |
|---|-------|-------|---------|-----------|
| 1 | **Incompatibilidade Flask/FastAPI** | Alta | Alto | Gateway API unificado (Kong/Traefik) + contratos OpenAPI |
| 2 | **SQLAlchemy 1.x vs 2.0** | Alta | Alto | Isolar models em services, não compartilhar ORM entre stacks |
| 3 | **Performance do Event Bus** | Média | Alto | Kafka para produção, Redis Streams para dev/cached |
| 4 | **Complexidade do Knowledge Layer** | Média | Alto | MVP com PostgreSQL + pgvector, evoluir para Qdrant |
| 5 | **Privacidade biométrica** | Baixa | Crítico | LGPD Service desde o dia 1, edge processing, criptografia |
| 6 | **Vendor lock-in (Google AI)** | Média | Médio | AI Gateway com LiteLLM + múltiplos providers |
| 7 | **Migração de dados** | Alta | Alto | Scripts de sync + dual-write durante transição |
| 8 | **Adoção por médicos** | Média | Alto | UX prioritária, feature flags, onboarding gradual |

---

## 8. Stack Tecnológica Recomendada

| Camada | Atual | Recomendado | Justificativa |
|--------|-------|-------------|---------------|
| **API Gateway** | Traefik (básico) | **Kong + OPA** | Rate limit, auth, routing, policies |
| **Backend Core** | Flask | **Mantener Flask** + FastAPI para serviços | Custo de migração muito alto |
| **Backend Voice** | FastAPI | **Mantener FastAPI** | Já está bem feito |
| **Backend VSF** | FastAPI | **Mantener FastAPI** como microserviço | Fusão gradual |
| **Frontend** | React CRA | **React + Vite + Module Federation** | Micro-frontends por módulo |
| **Banco Relacional** | PostgreSQL | **PostgreSQL 16 + schemas** | Mantém, adiciona RLS |
| **Vector DB** | Não existe | **Qdrant** | RAG, busca semântica |
| **Event Bus** | Não existe | **Redis Streams (dev) → Kafka (prod)** | Escalabilidade gradual |
| **Cache** | Redis (novo) | **Redis Cluster** | Sessions, cache, pub-sub |
| **Object Storage** | Local FS | **MinIO** | S3-compatível, backup |
| **Observability** | Não existe | **OpenTelemetry + Grafana** | Traces, logs, métricas |
| **CI/CD** | Manual | **GitHub Actions + ArgoCD** | Deploy automático |
| **Infra** | VPS Docker | **K3s (produção)** | Kubernetes leve |

---

## 9. Princípios de Design

1. **Platform First** — Nenhum módulo acessa infraestrutura diretamente
2. **Event-Driven** — Comunicação assíncrona por padrão, síncrona por exceção
3. **API-First** — Todo serviço expõe API REST + WebSocket + Eventos
4. **Tenant-Everywhere** — Cada linha de dados pertence a um tenant
5. **Privacy by Design** — LGPD em cada decisão arquitetural
6. **Human-in-the-Loop** — IA sugere, humano decide
7. **Graceful Degradation** — Se um serviço falha, os outros continuam
8. **Observability** — Tudo é medido, logado, rastreado

---

*Documento elaborado como especificação arquitetural mestre do ARAOS. Não implementar código antes da revisão e aprovação desta arquitetura.*
