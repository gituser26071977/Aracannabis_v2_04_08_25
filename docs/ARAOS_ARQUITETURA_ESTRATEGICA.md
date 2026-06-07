# ARAOS — Arquitetura Estratégica e Roadmap de Evolução

> **De:** Aracannabis Prontuário (nicho Cannabis)  
> **Para:** ARAOS — Ara Operating System (Sistema Operacional Médico Inteligente)  
> **Versão:** 1.0  
> **Data:** 2026-06-07

---

## Sumário Executivo

O projeto atual possui **~45 rotas backend, ~35 páginas frontend, 40+ models** e um ecossistema de IA já funcional (CrewAI, LLM Gateway, OCR, agentes clínicos). A base é sólida mas monolítica, com acoplamento forte entre domínios que deveriam ser independentes.

Este documento propõe a **evolução arquitetural** de uma aplicação monolítica de nicho para uma **plataforma operacional médica modular**, multi-especialidade, multi-tenant e nativamente assistida por IA.

---

## 1. Diagnóstico da Arquitetura Atual

### 1.1 Inventário do Estado Atual

| Camada | Estado | Observação |
|--------|--------|------------|
| **Backend** | Flask monolítico | ~45 blueprints, lógica misturada entre domínios |
| **Frontend** | React SPA (CRA) | ~35 páginas, componentes acoplados a domínio Cannabis |
| **Banco** | PostgreSQL | 40+ tabelas, sem partições, sem CDC |
| **IA** | CrewAI + LLM Gateway | Funcional mas acoplado ao domínio médico |
| **Comunicação** | E-mail + Webhooks | WhatsApp parcial (via webhooks genéricos) |
| **Pagamento** | Mercado Pago + Stripe + Asaas | Multi-provider implementado (Fase 1) |
| **Segurança** | JWT + middleware | Subscription middleware novo (Fase 1) |
| **Deploy** | Docker Compose + Traefik | VPS único, sem orquestração |
| **OCR** | Tesseract + IA | Existe mas não integrado ao fluxo clínico |

### 1.2 Redundâncias e Problemas Identificados

```
┌─────────────────────────────────────────────────────────────┐
│ REDUNDÂNCIAS CRÍTICAS                                       │
├─────────────────────────────────────────────────────────────┤
│ 1. Múltiplos serviços de e-mail (email_service.py +         │
│    email_service_backup.py) — consolidar em um              │
│ 2. CatalogoDocumentProcessor + CatalogoExtractionService +   │
│    OCRResultado — 3 caminhos de OCR não integrados          │
│ 3. AI_Chat_Simples + AI_Clinical + Crew_AI — 3 stacks de    │
│    IA com propósitos sobrepostos                            │
│ 4. Patient_Portal + Patient_Auth + Patient_Dashboard —      │
│    3 rotas para o mesmo usuário (paciente)                  │
│ 5. Billing_Service + Billing_Service_V2 + Payment_Service + │
│    MercadoPago_Service — 4 camadas de pagamento             │
│ 6. FeatureFlagService não usado em ~80% das rotas —         │
│    implementado mas não adotado                             │
│ 7. ConfiguracaoIA + ConfigIATenant + AIConfig + LLMConfig — │
│    4 tabelas de configuração de IA                          │
└─────────────────────────────────────────────────────────────┘
```

### 1.3 Débito Técnico Prioritário

| Problema | Impacto | Custo de Correção |
|----------|---------|-------------------|
| Models.py com 40+ classes | Alto acoplamento | Refatorar em módulos |
| Frontend CRA (não Vite/Next) | Build lento, bundle grande | Migração para Vite |
| google.generativeai deprecated | Warnings, risco de breaking | Migrar para google.genai |
| Sem testes automatizados | Regressões silenciosas | Adicionar suite de testes |
| Sem eventos assíncronos | Síncrono por toda parte | Adicionar fila de eventos |
| docker-compose sem healthchecks adequados | Falhas silenciosas | Melhorar observabilidade |

---

## 2. Arquitetura de Módulos Proposta (ARAOS)

### 2.1 Princípios de Design

1. **Domain-Driven Design (DDD)** — Cada módulo é um domínio autônomo
2. **Event-Driven Architecture** — Comunicação entre módulos via eventos
3. **Plugin Architecture** — Especialidades são plugins que registram campos/protocolos
4. **API-First** — Cada módulo expõe API REST + WebSocket + GraphQL (futuro)
5. **CQRS para leituras intensivas** — Dashboards e relatórios separados

### 2.2 Reestruturação dos Módulos

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         ARAOS PLATFORM                                   │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │   CORE      │  │    AI       │  │  CONNECT    │  │   INTAKE    │    │
│  │  (kernel)   │  │  (cérebro)  │  │  (nervos)   │  │  (sentidos) │    │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘    │
│         │                │                │                │           │
│  ┌──────┴──────┐  ┌──────┴──────┐  ┌──────┴──────┐  ┌──────┴──────┐    │
│  │• Pacientes  │  │• Agentes    │  │• WhatsApp   │  │• OCR        │    │
│  │• Agenda     │  │• Resumos    │  │• Email      │  │• Exames     │    │
│  │• Prontuário │  │• Evoluções  │  │• SMS        │  │• Documentos │    │
│  │• Prescrições│  │• Busca sem. │  │• Portal     │  │• Voz        │    │
│  │• Exames     │  │• Memória    │  │• Notificações│  │• Formulários│    │
│  │• Financeiro │  │• RAG        │  │• Webhooks   │  │• Indexação  │    │
│  │• Tenant Mgmt│  │• Fine-tuning│  │• Push       │  │• Chatbot    │    │
│  │• Auth/Perm  │  │             │  │             │  │  Intake     │    │
│  │• Audit Logs │  │             │  │             │  │             │    │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │              ARAOS SPECIALTIES (Plugins)                         │    │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │    │
│  │  │ Cannabis │ │ Cardio   │ │ Nefro    │ │ Psiquia  │  [...]    │    │
│  │  │• Campos  │ │• Campos  │ │• Campos  │ │• Campos  │           │    │
│  │  │• Protocol│ │• Protocol│ │• Protocol│ │• Protocol│           │    │
│  │  │• Escalas │ │• Escalas │ │• Escalas │ │• Escalas │           │    │
│  │  │• Agentes │ │• Agentes │ │• Agentes │ │• Agentes │           │    │
│  │  │• Dash    │ │• Dash    │ │• Dash    │ │• Dash    │           │    │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │              ARAOS VISUAL SMART FLOW (Módulo Nativo)             │    │
│  │  • Agendamento com captura de documentos                        │    │
│  │  • Check-in biométrico (opcional)                               │    │
│  │  • Gestão de filas e salas                                      │    │
│  │  • Painel de chamada                                            │    │
│  │  • Integração automática com prontuário e agenda                │    │
│  └─────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.3 Comparação: Antes vs Depois

| Aspecto | Antes (Aracannabis) | Depois (ARAOS) |
|---------|---------------------|----------------|
| **Especialidades** | Cannabis hardcoded | Plugin system |
| **Campos clínicos** | Fixos no model Paciente | JSON Schema por especialidade |
| **Escalas** | Snap-IV, PHQ9, GAD7, Beck hardcoded | Registro dinâmico de escalas |
| **Agentes IA** | Cannabis-focused | Templates por especialidade |
| **Dashboards** | Único | Por especialidade + geral |
| **Prescrições** | Cannabis-focused | Template engine por especialidade |
| **Intake** | Não existe | Motor genérico de formulários |
| **Voz** | Não existe | Módulo nativo |
| **Biometria** | Não existe | Check-in facial opcional |

---

## 3. Arquitetura Técnica Moderna

### 3.1 Visão Geral

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         CLIENTES                                         │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────────────┐   │
│  │ Web App │ │  PWA    │ │  Mobile │ │  Portal │ │  Quiosque/Kiosk │   │
│  │(React)  │ │(React)  │ │(Flutter)│ │Paciente │ │  (Smart Flow)   │   │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────────┬────────┘   │
│       └───────────┴───────────┴───────────┴───────────────┘             │
│                           │                                             │
│                    ┌──────┴──────┐                                      │
│                    │   CDN/Edge  │  (CloudFlare / AWS CloudFront)      │
│                    │  + WAF      │                                      │
│                    └──────┬──────┘                                      │
└───────────────────────────┼─────────────────────────────────────────────┘
                            │
┌───────────────────────────┼─────────────────────────────────────────────┐
│                     API GATEWAY                                          │
│  ┌────────────────────────┴─────────────────────────────────────────┐   │
│  │  • Rate Limiting (Redis)  • Auth (JWT + OAuth2)                  │   │
│  │  • Tenant Resolution      • Request Routing                      │   │
│  │  • API Versioning         • Observability (traces/metrics)       │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
┌───────▼───────┐  ┌────────▼────────┐  ┌──────▼──────┐
│  ARAOS CORE   │  │   ARAOS AI      │  │  EVENT BUS  │
│  (FastAPI)    │  │   (Python)      │  │  (Redis +   │
│               │  │                 │  │   RabbitMQ) │
│ • REST API    │  │ • LLM Gateway   │  │             │
│ • WebSocket   │  │ • RAG Pipeline  │  │ • Eventos   │
│ • GraphQL     │  │ • Agent Swarm   │  │   assíncronos│
│ • gRPC (int)  │  │ • Fine-tuning   │  │ • Webhooks  │
│               │  │ • Embeddings    │  │ • Job Queue │
└───────┬───────┘  └────────┬────────┘  └──────┬──────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            │
┌───────────────────────────┼─────────────────────────────────────────────┐
│                     CAMADA DE DADOS                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐ │
│  │ PostgreSQL   │  │  Redis       │  │ Elasticsearch│  │  MinIO/S3   │ │
│  │ (principal)  │  │  (cache +    │  │ (busca full  │  │  (arquivos) │ │
│  │              │  │   sessions + │  │  text +      │  │             │ │
│  │ • Multi-tenant│  │   pub/sub)  │  │  semantic)   │  │ • Exames    │ │
│  │   por schema  │  │              │  │              │  │ • Fotos     │ │
│  │   ou row-level│  │ • Rate limit │  │ • Pacientes  │  │ • Documentos│ │
│  │ • Read replica│  │ • Sessions   │  │ • Prontuários│  │ • Áudio     │ │
│  │ • Particiona- │  │ • Pub/Sub    │  │ • Memória    │  │             │ │
│  │   mento por   │  │ • Job Queue  │  │   clínica    │  │             │ │
│  │   tenant/data │  │              │  │              │  │             │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └─────────────┘ │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │
│  │  TimescaleDB │  │  Qdrant      │  │  Neo4j       │                  │
│  │  (métricas   │  │  (vector DB  │  │  (grafo de   │                  │
│  │   temporais) │  │   para RAG)  │  │   relações   │                  │
│  │              │  │              │  │   clínicas)  │                  │
│  │ • Evoluções  │  │ • Embeddings │  │ • Medicações │                  │
│  │ • Sintomas   │  │ • Similarity │  │ • Diagnósticos│                 │
│  │ • Sinais vita│  │ • Retrieval  │  │ • Interações │                  │
│  └──────────────┘  └──────────────┘  └──────────────┘                  │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Stack Tecnológica Recomendada

| Camada | Tecnologia Atual | Tecnologia ARAOS | Justificativa |
|--------|-----------------|------------------|---------------|
| **Backend API** | Flask | **FastAPI** | Performance, async nativo, OpenAPI auto |
| **Frontend Web** | React CRA | **React + Vite** | Build 10x mais rápido, HMR |
| **Mobile** | Não existe | **Flutter** | Single codebase, performance nativa |
| **Banco Principal** | PostgreSQL | **PostgreSQL 16** + schemas por tenant | Mantém dados, adiciona isolamento |
| **Cache/Sessões** | Não existe | **Redis Cluster** | Rate limit, sessions, pub/sub |
| **Busca/Vector** | Não existe | **Qdrant** + **Elasticsearch** | RAG, busca semântica, full-text |
| **Fila de Eventos** | Não existe | **RabbitMQ** ou **Apache Kafka** | Eventos assíncronos, CQRS |
| **Object Storage** | Local filesystem | **MinIO** (S3-compatible) | Escalabilidade, backup |
| **Observabilidade** | Não existe | **OpenTelemetry + Grafana + Loki** | Traces, logs, métricas |
| **CI/CD** | Manual | **GitHub Actions + ArgoCD** | Deploy automático |
| **Infra** | VPS único | **Kubernetes (K3s)** | Orquestração, auto-scale |

### 3.3 API Gateway e Tenant Resolution

```python
# Proposta: Tenant Resolution no Gateway
class TenantResolver:
    """Resolve o tenant a partir de múltiplas fontes, em ordem de prioridade."""
    
    STRATEGIES = [
        "subdomain",      # clinica.aros.com.br
        "header",         # X-Tenant-ID: clinica-abc
        "jwt_claim",      # tenant_id no token
        "path_param",     # /api/v1/{tenant}/pacientes
        "api_key",        # X-API-Key mapeado para tenant
    ]
```

### 3.4 Event Bus — Comunicação Entre Módulos

```python
# Eventos centrais da plataforma
class DomainEvent:
    """Base para todos os eventos de domínio."""
    event_id: UUID
    tenant_id: str
    timestamp: datetime
    aggregate_type: str
    aggregate_id: str
    event_type: str
    payload: dict

# Exemplos de eventos
class PacienteCadastrado(DomainEvent):
    event_type = "paciente.cadastrado"

class ConsultaIniciada(DomainEvent):
    event_type = "consulta.iniciada"

class DocumentoProcessado(DomainEvent):
    event_type = "documento.processado"

class PrescricaoAprovada(DomainEvent):
    event_type = "prescricao.aprovada"
```

---

## 4. Arquitetura Multi-Tenant

### 4.1 Estratégia Híbrida

ARAOS usará **três níveis de isolamento**, escolhidos pelo plano do cliente:

```
┌─────────────────────────────────────────────────────────────────┐
│              ESTRATÉGIAS DE MULTI-TENANCY                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  NÍVEL 1: Schema Isolation (Planos Enterprise)                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  PostgreSQL                                              │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐                   │   │
│  │  │ tenant_a│ │ tenant_b│ │ tenant_c│                   │   │
│  │  │ schema  │ │ schema  │ │ schema  │                   │   │
│  │  │• tables │ │• tables │ │• tables │                   │   │
│  │  └─────────┘ └─────────┘ └─────────┘                   │   │
│  │                                                         │   │
│  │  ✅ Isolamento máximo                                    │   │
│  │  ✅ Backup/restore independente                          │   │
│  │  ❌ Custo maior (schemas duplicados)                     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  NÍVEL 2: Row-Level Security (Planos Profissional/Avançado)    │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  PostgreSQL                                              │   │
│  │  ┌─────────────────────────────────────────────────┐   │   │
│  │  │  Tabela: pacientes                               │   │   │
│  │  │  ┌────────┬──────────┬─────────────┬──────────┐  │   │   │
│  │  │  │ id     │ nome     │ tenant_id   │ ...      │  │   │   │
│  │  │  ├────────┼──────────┼─────────────┼──────────┤  │   │   │
│  │  │  │ 1      │ João     │ tenant_a    │ ...      │  │   │   │
│  │  │  │ 2      │ Maria    │ tenant_b    │ ...      │  │   │   │
│  │  │  └────────┴──────────┴─────────────┴──────────┘  │   │   │
│  │  │                                                   │   │   │
│  │  │  CREATE POLICY tenant_isolation ON pacientes      │   │   │
│  │  │  USING (tenant_id = current_setting('app.tenant'))│   │   │
│  │  └─────────────────────────────────────────────────┘   │   │
│  │                                                         │   │
│  │  ✅ Bom isolamento                                       │   │
│  │  ✅ Escalabilidade                                       │   │
│  │  ⚠️ RLS pode impactar performance sem índices            │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  NÍVEL 3: Shared Database (Plano Starter/Gratuito)             │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Mesma tabela, tenant_id como FK simples                 │   │
│  │  Sem RLS (aplicação filtra)                              │   │
│  │                                                         │   │
│  │  ✅ Custo mínimo                                         │   │
│  │  ✅ Simplicidade                                         │   │
│  │  ❌ Menor isolamento                                     │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Modelo de Dados Multi-Tenant

```sql
-- Tabela central de tenants
CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug VARCHAR(63) UNIQUE NOT NULL,          -- clinica-aros
    name VARCHAR(255) NOT NULL,
    plan VARCHAR(50) NOT NULL,                 -- starter, pro, enterprise
    tenant_level INT NOT NULL DEFAULT 2,        -- 1=schema, 2=RLS, 3=shared
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    status VARCHAR(20) DEFAULT 'active'        -- active, suspended, cancelled
);

-- Tabela de usuários (cross-tenant, para login)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    oauth_provider VARCHAR(50),                -- google, microsoft
    oauth_id VARCHAR(255),
    email_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Associação usuário-tenant (um usuário pode estar em múltiplos tenants)
CREATE TABLE tenant_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id),
    user_id UUID REFERENCES users(id),
    role VARCHAR(50) NOT NULL,                 -- admin, medico, secretaria
    permissions JSONB DEFAULT '{}',
    is_default BOOLEAN DEFAULT FALSE,          -- tenant padrão do usuário
    joined_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(tenant_id, user_id)
);

-- Configuração por tenant
CREATE TABLE tenant_settings (
    tenant_id UUID PRIMARY KEY REFERENCES tenants(id),
    specialty_modules JSONB DEFAULT '[]',      -- ['cannabis', 'cardio']
    branding JSONB DEFAULT '{"logo": null, "colors": {}}',
    features JSONB DEFAULT '{}',               -- feature flags por tenant
    ai_config JSONB DEFAULT '{}',
    communication_channels JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 5. Arquitetura de Agentes de IA

### 5.1 Princípios

1. **Um agente por propósito**, não por especialidade
2. **Memória clínica longitudinal** — todo paciente tem um "cérebro" vetorial
3. **RAG com fontes verificáveis** — toda resposta da IA cita fontes
4. **Human-in-the-loop** — médico sempre aprova antes de persistir
5. **Observabilidade total** — todo prompt, resposta, latência logado

### 5.2 Stack de IA

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    ARAOS AI PLATFORM                                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    LLM GATEWAY                                   │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │   │
│  │  │ OpenAI   │ │ Anthropic│ │ Google   │ │ Local    │          │   │
│  │  │ GPT-4o   │ │ Claude   │ │ Gemini   │ │ Llama    │          │   │
│  │  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘          │   │
│  │       └────────────┴────────────┴────────────┘                 │   │
│  │                    │                                           │   │
│  │              Routing Strategy                                  │   │
│  │  • Custo      • Latência    • Qualidade    • Compliance      │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                              │                                          │
│  ┌───────────────────────────┼─────────────────────────────────────┐   │
│  │              RAG PIPELINE  │                                      │   │
│  │                           ▼                                      │   │
│  │  ┌────────────┐  ┌──────────────┐  ┌──────────────────────┐   │   │
│  │  │ Document   │  │  Chunking +  │  │  Qdrant Vector DB    │   │   │
│  │  │ Ingestion  │→ │  Embedding   │→ │  (768-1536 dims)     │   │   │
│  │  │            │  │              │  │                      │   │   │
│  │  │ • PDF      │  │ • Semantic   │  │ • HNSW Index         │   │   │
│  │  │ • HTML     │  │ • Overlap    │  │ • Metadata filters   │   │   │
│  │  │ • Text     │  │ • Summarize  │  │ • Tenant isolation   │   │   │
│  │  └────────────┘  └──────────────┘  └──────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │              AGENT SWARM ( crewai + autogen )                    │   │
│  │                                                                  │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │   │
│  │  │ IntakeAgent │  │ ClinicalAgent│  │ VoiceAgent  │            │   │
│  │  │             │  │             │  │             │            │   │
│  │  │ Coleta info │  │ Diagnóstico │  │ Transcrição │            │   │
│  │  │ pré-consulta│  │ Diferencial │  │ Consulta    │            │   │
│  │  │ via WhatsApp│  │ Evidências  │  │ em tempo    │            │   │
│  │  │             │  │             │  │ real        │            │   │
│  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘            │   │
│  │         │                │                │                   │   │
│  │  ┌──────┴──────┐  ┌──────┴──────┐  ┌──────┴──────┐          │   │
│  │  │ Prescription│  │  SummaryAgent│  │  FollowUpAgent│          │   │
│  │  │    Agent    │  │             │  │             │          │   │
│  │  │             │  │ Resumo      │  │ Lembrete    │          │   │
│  │  │ Gera receitu│  │ clínico     │  │ pós-consulta│          │   │
│  │  │ário validado│  │ para humanos│  │ via WhatsApp│          │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘          │   │
│  │                                                                  │   │
│  │  ┌─────────────────────────────────────────────────────────┐   │   │
│  │  │              Orchestrator Agent                          │   │   │
│  │  │  Coordena os agentes, gerencia estado, decide fluxo     │   │   │
│  │  └─────────────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │              MEMÓRIA CLÍNICA LONGITUDINAL                        │   │
│  │                                                                  │   │
│  │  Para cada paciente, um grafo de conhecimento + vetores:        │   │
│  │                                                                  │   │
│  │  • Diagnósticos → CID-10/11                                      │   │
│  │  • Medicamentos → ATC codes                                      │   │
│  │  • Exames → LOINC codes                                          │   │
│  │  • Alergias → RxNorm                                             │   │
│  │  • Queixas → SNOMED-CT                                           │   │
│  │  • Evoluções → Embeddings temporais                              │   │
│  │                                                                  │   │
│  │  Neo4j: relações entre entidades                                 │   │
│  │  Qdrant: busca semântica em documentos                           │   │
│  │  TimescaleDB: série temporal de sinais vitais                    │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

### 5.3 Memória Clínica Longitudinal

```python
class ClinicalMemory:
    """
    Representa a memória completa de um paciente.
    Usado por todos os agentes para contexto.
    """
    
    def build_context(self, patient_id: str) -> dict:
        return {
            "demographics": self.get_demographics(patient_id),
            "timeline": self.get_chronological_events(patient_id),
            "active_conditions": self.get_active_diagnoses(patient_id),
            "medications": self.get_current_medications(patient_id),
            "allergies": self.get_allergies(patient_id),
            "recent_exams": self.get_recent_exams(patient_id, days=90),
            "risk_factors": self.get_risk_factors(patient_id),
            "specialty_data": self.get_specialty_specific_data(patient_id),
        }
    
    def semantic_search(self, patient_id: str, query: str, k: int = 5):
        """Busca informações similares no histórico do paciente."""
        embedding = self.embed(query)
        return self.vector_db.search(
            collection=f"patient_{patient_id}",
            vector=embedding,
            limit=k
        )
```

---

## 6. Arquitetura de Banco de Dados

### 6.1 Estratégia por Tipo de Dado

| Tipo de Dado | Tecnologia | Justificativa |
|-------------|-----------|---------------|
| **Dados transacionais** | PostgreSQL (RLS) | ACID, relacionamentos complexos |
| **Cache/Sessões** | Redis | Baixa latência, TTL automático |
| **Busca textual** | Elasticsearch | Full-text, fuzzy, agregações |
| **Vetores/RAG** | Qdrant | Otimizado para embeddings, filtros |
| **Séries temporais** | TimescaleDB | Compressão, consultas temporais |
| **Grafo de relações** | Neo4j (opcional) | Interações medicamentosas, redes |
| **Arquivos** | MinIO (S3) | Imutabilidade, versionamento |
| **Eventos** | Kafka/RabbitMQ | Durabilidade, replay |

### 6.2 Modelo de Dados por Domínio

#### CORE — Pacientes (Modelo Polimórfico por Especialidade)

```sql
-- Tabela base (todos os pacientes)
CREATE TABLE patients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    
    -- Dados pessoais (LGPD: dados sensíveis)
    full_name VARCHAR(255) NOT NULL,
    cpf VARCHAR(14) UNIQUE,
    birth_date DATE,
    gender VARCHAR(20),
    phone VARCHAR(20),
    email VARCHAR(255),
    address JSONB,
    
    -- Dados clínicos base
    blood_type VARCHAR(5),
    emergency_contact JSONB,
    
    -- Metadados
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Índices
    CONSTRAINT fk_tenant_patients FOREIGN KEY (tenant_id) REFERENCES tenants(id)
);

-- Índice para busca por tenant (essencial para RLS performance)
CREATE INDEX idx_patients_tenant ON patients(tenant_id);
CREATE INDEX idx_patients_name ON patients USING gin(to_tsvector('portuguese', full_name));

-- Dados específicos por especialidade (EAV ou JSONB)
CREATE TABLE patient_specialty_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    specialty VARCHAR(50) NOT NULL,              -- 'cannabis', 'cardio', 'nefro'
    schema_version INT NOT NULL DEFAULT 1,
    data JSONB NOT NULL DEFAULT '{}',            -- Campos específicos da especialidade
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(patient_id, specialty)
);

-- Exemplo de dados por especialidade:
-- Cannabis: { "indication": "dor_crônica", "previous_experience": true, "strains_tried": [...] }
-- Cardio: { "nyha_class": "II", "ef": 45, "previous_mi": true, "stents": [...] }
-- Nefro: { "ckd_stage": "3b", "dialysis_type": null, "transplant_date": null }
```

#### CORE — Prontuário Eletrônico (Timeline de Eventos)

```sql
-- Timeline clínica unificada (todos os eventos de um paciente)
CREATE TABLE clinical_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    patient_id UUID NOT NULL REFERENCES patients(id),
    
    event_type VARCHAR(50) NOT NULL,             -- consultation, exam, prescription, evolution, symptom
    event_subtype VARCHAR(50),                   -- tipo específico
    
    occurred_at TIMESTAMPTZ NOT NULL,            -- quando o evento ocorreu
    recorded_at TIMESTAMPTZ DEFAULT NOW(),       -- quando foi registrado
    recorded_by UUID,                            -- profissional
    
    -- Dados do evento
    title VARCHAR(255),
    summary TEXT,                                -- Resumo gerado por IA
    raw_data JSONB,                              -- Dados originais
    structured_data JSONB,                       -- Dados estruturados
    
    -- Fontes e evidências
    source VARCHAR(50) DEFAULT 'manual',         -- manual, ai, integration, device
    source_id UUID,                              -- ID da fonte
    confidence FLOAT,                            -- Confiança da IA (0-1)
    
    -- Tags e códigos
    icd10_codes TEXT[],                          -- Códigos CID-10
    snomed_codes TEXT[],                         -- Códigos SNOMED-CT
    atc_codes TEXT[],                            -- Códigos ATC (medicamentos)
    
    -- Audit
    verified_by UUID,                            -- Quem validou (human-in-the-loop)
    verified_at TIMESTAMPTZ,
    
    -- Índices para performance
    CONSTRAINT fk_tenant_events FOREIGN KEY (tenant_id) REFERENCES tenants(id)
);

-- Particionamento por tenant + data (TimescaleDB ou PostgreSQL nativo)
CREATE INDEX idx_clinical_events_patient_time ON clinical_events(patient_id, occurred_at DESC);
CREATE INDEX idx_clinical_events_tenant ON clinical_events(tenant_id, event_type);
```

---

## 7. Roadmap: MVP → Beta → Produção

### 7.1 Visão Geral

```
Fase 0 ──► Fase 1 ──► Fase 2 ──► Fase 3 ──► Fase 4 ──► Fase 5
(Atual)   (Completo)  (MVP)      (Beta)     (RC)       (Produção)
  │         ✅         🔄         📅         📅          📅
  │
  └─ Fase 0-1: Base Aracannabis (concluído)
     • Prontuário Cannabis completo
     • Faturamento real
     • Segurança e onboarding
     • SGA Catálogo IA
```

### 7.2 Fase 2: MVP ARAOS (3-4 meses)

**Objetivo:** Sistema operacional mínimo funcional, multi-especialidade básica.

| Sprint | Entrega | Critério de Aceite |
|--------|---------|-------------------|
| **S1** | **Rebranding Core** | Renomear para ARAOS, novo branding, landing page |
| **S2** | **Tenant Engine** | Multi-clínica funcional (RLS), cadastro de clínicas, convite de membros |
| **S3** | **Paciente Polimórfico** | Modelo de paciente com specialty_data JSONB, módulo Cannabis como plugin |
| **S4** | **Especialidade #2** | Cardiologia ou Psiquiatria com campos/protocolos próprios |
| **S5** | **ARAOS Intake v1** | Formulários dinâmicos por especialidade, pré-atendimento via WhatsApp básico |
| **S6** | **ARAOS AI v1** | Memória clínica básica, resumo automático de prontuário, 1 agente por especialidade |

**MVP = CORE + 2 especialidades + Intake básico + IA básica**

### 7.3 Fase 3: Beta (3-4 meses)

| Sprint | Entrega |
|--------|---------|
| **S7** | **ARAOS Connect** — WhatsApp empresarial integrado, notificações automáticas |
| **S8** | **ARAOS Voice v1** — Transcrição de consulta, extração de entidades, evolução sugerida |
| **S9** | **ARAOS Visual Smart Flow** — Check-in, filas, painel de chamada, integração com agenda |
| **S10** | **Especialidades #3 e #4** — Nefrologia + Endocrinologia |
| **S11** | **Portal do Paciente v2** — Acesso a prontuário, exames, agendamento |
| **S12** | **Telemedicina básica** — Videochamada integrada |

### 7.4 Fase 4: Release Candidate (2-3 meses)

- Performance e otimização
- Testes de carga multi-tenant
- Conformidade LGPD completa (DPO, DIREITOS, consentimento granular)
- Certificação de software médico (RDC 657/2022 se aplicável)
- Documentação completa
- Treinamento de IA com dados reais (anônimos)

### 7.5 Fase 5: Produção e Escala

- Kubernetes em produção
- Auto-scaling
- Multi-região
- Marketplace de especialidades (3rd party plugins)
- API pública para integrações
- White-label completo

---

## 8. Diferenciais Competitivos

### 8.1 Diferenciais Tecnológicos

| # | Diferencial | Descrição | Barreira de Entrada |
|---|------------|-----------|---------------------|
| 1 | **Prontuário pré-preenchido** | Paciente chega e o médico já vê resumo clínico completo | Integração complexa de múltiplas fontes |
| 2 | **Consulta assistida por voz** | Médico conversa, sistema estrutura | Pipeline de NLP + validação clínica |
| 3 | **Memória clínica longitudinal** | Toda interação alimenta conhecimento do paciente | Infraestrutura de vetores + grafo |
| 4 | **Plugin de especialidades** | Novas especialidades em semanas, não meses | Arquitetura de plugins bem desenhada |
| 5 | **Jornada omnichannel** | WhatsApp → Check-in → Consulta → Follow-up sem fricção | Integração de múltiplos canais |

### 8.2 Diferenciais de Negócio

| # | Diferencial | Impacto |
|---|------------|---------|
| 1 | **Setup em 24h** | Clínica operando no dia seguinte à contratação |
| 2 | **Precificação por uso** | Clínica pequena paga pouco, grande paga proporcional |
| 3 | **Marketplace de especialidades** | Comunidade de médicos contribui com protocolos |
| 4 | **Rede ARAOS** | Paciente pode migrar entre clínicas da rede com histórico |
| 5 | **Dados para pesquisa** (anônimos, consentidos) | Publicações científicas aumentam credibilidade |

---

## 9. Prioridade de Construção dos Módulos

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    MATRIZ IMPACTO × COMPLEXIDADE                         │
│                                                                         │
│  Alto Impacto │  [4] AI Memória    [5] Intake        [6] Voice        │
│               │                                                         │
│               │  [3] Tenant Engine  [2] Paciente Polimórfico           │
│               │                                                         │
│  Baixo Impacto│  [9] Biometria     [8] Smart Flow    [7] Telemedicina │
│               │                                                         │
│               └───────────────────────────────────────────────────────   │
│                    Baixa Complexidade        Alta Complexidade          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Ordem de Construção Recomendada

```
1. ████████████████████  Rebranding e Tenant Engine (base de tudo)
2. ████████████████      Paciente Polimórfico + Especialidade como Plugin
3. ████████████          ARAOS AI Core (Memória + Agentes)
4. ██████████            ARAOS Intake (formulários + pré-atendimento)
5. ████████              ARAOS Connect (WhatsApp + notificações)
6. ██████                ARAOS Visual Smart Flow (check-in + filas)
7. ████                  ARAOS Voice (transcrição)
8. ██                    Telemedicina
9. ██                    Biometria Facial
```

---

## 10. Riscos Regulatórios

### 10.1 LGPD — Lei Geral de Proteção de Dados

| Risco | Severidade | Mitigação |
|-------|-----------|-----------|
| **Dados sensíveis de saúde** | 🔴 Crítico | Criptografia em repouso + trânsito, pseudonimização, consentimento granular |
| **Direitos do titular** | 🔴 Crítico | API de exportação/deleção, DPO designado, registro de operações |
| **Compartilhamento** | 🟡 Alto | Termos claros, consentimento por finalidade, anonimização para pesquisa |
| **Retenção** | 🟡 Alto | Política de retenção por tipo de dado, deleção automática pós prazo |
| **Transferência internacional** | 🟡 Alto | Se usar cloud externa (OpenAI, etc.), garantir adequação ou SCCs |
| **Violação** | 🔴 Crítico | Notificação em 72h, plano de resposta, logs de auditoria |

### 10.2 Regulação da Área Médica

| Risco | Severidade | Mitigação |
|-------|-----------|-----------|
| **Software como dispositivo médico** | 🟡 Alto | Avaliar se se enquadra na RDC 657/2022 (Class I ou II) |
| **Assinatura digital de receituário** | 🟡 Alto | Certificado digital ICP-Brasil, não simples hash |
| **Telemedicina** | 🟡 Alto | CFM/CRM aprovado, registro da consulta, consentimento |
| **Prescrição de substâncias controladas** | 🔴 Crítico | Integração com Sistema Nacional de Gerenciamento de Produtos Controlados |
| **Responsabilidade médica** | 🔴 Crítico | Termos claros de que IA é assistiva, decisão final é do médico |
| **Publicidade médica** | 🟡 Médio | Cuidado com claims de eficácia na landing page |

### 10.3 Regulação de Cannabis Medicinal

| Risco | Severidade | Mitigação |
|-------|-----------|-----------|
| **Prescrição de Cannabis** | 🔴 Crítico | Manter módulo separado, conforme com Anvisa/MS |
| **Rastreabilidade** | 🟡 Alto | Lote, validade, farmácia de manipulação vinculada |

### 10.4 Recomendações de Compliance

1. **DPO (Data Protection Officer)** — Designar imediatamente
2. **Privacy by Design** — LGPD em toda decisão de produto
3. **Consentimento granular** — Paciente escolhe o que compartilha
4. **Anonimização diferencial** — Para pesquisa e treinamento de IA
5. **Auditoria contínua** — Logs de acesso, alertas de anomalia
6. **Localização de dados** — Preferencialmente no Brasil (LGPD + latência)
7. **Modelo de responsabilidade** — Termos claros: "IA sugere, médico decide"

---

## 11. Viabilidade Técnica: Biometria Facial e Voz

### 11.1 Identificação Biométrica Facial (Check-in)

| Aspecto | Avaliação |
|---------|-----------|
| **Tecnologia** | Face-api.js (browser) ou AWS Rekognition / Azure Face API |
| **Precisão** | 99%+ em condições controladas; 85-90% em ambientes clínicos reais |
| **Custo** | ~$0.001-0.01 por verificação (cloud); gratuito se local |
| **LGPD** | Dado biométrico é sensível — requer consentimento explícito e justificativa |
| **Viabilidade** | ✅ **Viável como opcional** — não obrigatório |
| **Implementação** | Capturar foto no cadastro → embedding facial → comparar no check-in |
| **Riscos** | Falsos negativos (paciente não reconhecido), vieses racial/gênero |

**Recomendação:** Implementar como **opt-in** com QR code como fallback. Não bloquear jornada se falhar.

### 11.2 Consulta Assistida por Voz

| Aspecto | Avaliação |
|---------|-----------|
| **STT (Speech-to-Text)** | Whisper (OpenAI) — SOTA para português; ou Whisper local (faster-whisper) |
| **Latência** | ~1-2s para transcrição em tempo real (stream) |
| **Custo** | $0.006/minuto (API) ou GPU local (custo fixo) |
| **NLP pós-transcrição** | LLM para extração de entidades clínicas |
| **Precisão médica** | ~85-90% para termos médicos comuns; 60-70% para termos raros |
| **LGPD** | Gravação de consulta = dado sensível — consentimento obrigatório |
| **CFM** | Possível exigência de guarda do áudio por N anos |

**Recomendação:** ✅ **Viável e diferencial forte**. Implementar em fases:
1. Fase 1: Gravação + transcrição post-consulta (não real-time)
2. Fase 2: Transcrição em tempo real (stream)
3. Fase 3: Extração automática de entidades + sugestão de evolução

---

## 12. Visão de Longo Prazo: ARAOS como Plataforma Operacional

### 12.1 Evolução em 5 Anos

```
ANO 1 ──► ANO 2 ──► ANO 3 ──► ANO 4 ──► ANO 5
  │         │         │         │         │
  │         │         │         │         └─ OS Médica Completa
  │         │         │         │            • Hospitalar
  │         │         │         │            • Laboratorial
  │         │         │         │            • Radiológica
  │         │         │         │            • Farmacêutica
  │         │         │         │
  │         │         │         └─ Marketplace + Rede
  │         │         │            • 3rd party plugins
  │         │         │            • Rede ARAOS (interoperabilidade)
  │         │         │            • API pública
  │         │         │
  │         │         └─ Ecossistema
  │         │            • Parceiros (laboratórios, farmácias)
  │         │            • Insurance integration
  │         │            • Research network
  │         │
  │         └─ Expansão
  │            • 10+ especialidades
  │            • Mobile nativo
  │            • Telemedicina completa
  │
  └─ Fundação (ARAOS v1)
     • 3-5 especialidades
     • Multi-tenant
     • IA nativa
     • 50-100 clínicas
```

### 12.2 Modelo de Negócio Futuro

| Linha de Receita | Descrição |
|-----------------|-----------|
| **SaaS subscription** | Mensalidade por clínica (tiered por volume) |
| **Transaction fee** | % sobre pagamentos processados |
| **Marketplace commission** | % sobre plugins e integrações de terceiros |
| **Data intelligence** (anônimo) | Insights epidemiológicos para indústria farmacêutica |
| **White-label licensing** | Licenciamento para hospitais e grandes redes |
| **Training & certification** | Cursos de uso da plataforma |

### 12.3 Posicionamento Estratégico

```
                    ESPECIALIZAÇÃO
                         ▲
                         │
              ┌──────────┼──────────┐
              │  Sistemas│de nicho   │  ← Aracannabis (hoje)
              │  (Vittau,│Prescrypt) │
              │          │          │
  INTEGRAÇÃO  │──────────┼──────────│  ← ARAOS (futuro)
  ◄───────────┤  Plataformas        │     "O iOS da Medicina"
              │  operacionais       │
              │  (não existe ainda) │
              │          │          │
              │  Sistemas│genéricos │  ← TISS, MV, Philips
              │  (legacy,           │     (hospitalar pesado)
              │  on-premise)        │
              └──────────┼──────────┘
                         │
                         ▼
                    GENERALISMO
```

ARAOS não compete com sistemas hospitalares legacy (MV, Tasy). ARAOS compete com o **Excel, o papel e a desorganização** das clínicas médicas de médio porte.

### 12.4 Manifesto ARAOS

> **ARAOS é o sistema operacional da prática médica moderna.**
>
> Assim como o iOS unificou telefone, música, fotos e internet em um único dispositivo, ARAOS unifica paciente, agenda, prontuário, IA, comunicação e financeiro em uma única plataforma.
>
> O médico não deveria precisar de 5 sistemas diferentes. O paciente não deveria contar sua história 5 vezes. A clínica não deveria perder dinheiro com ineficiência.
>
> **ARAOS resolve isso.**

---

## 13. Checklist de Próximos Passos Imediatos

### Semana 1-2: Decisões Estratégicas

- [ ] Definir nome final (ARAOS é provisório?)
- [ ] Decidir entre evolução incremental vs rewrite
- [ ] Definir especialidade #2 (Cardio ou Psiquiatria?)
- [ ] Contratar/identificar DPO
- [ ] Registrar marca e domínio

### Semana 3-4: Fundação Técnica

- [ ] Criar monorepo estruturado (ou manter repo atual)
- [ ] Implementar Tenant Engine (nível 2: RLS)
- [ ] Refatorar Paciente para modelo polimórfico
- [ ] Criar sistema de plugins para especialidades
- [ ] Setup de infraestrutura: Redis, Elasticsearch, Qdrant

### Mês 2: MVP Funcional

- [ ] Especialidade Cannabis como plugin
- [ ] Especialidade #2 como plugin
- [ ] Intake básico (formulários dinâmicos)
- [ ] IA: Memória clínica básica
- [ ] Rebranding completo

### Mês 3: Integração e Polish

- [ ] WhatsApp Business API
- [ ] Onboarding de clínicas
- [ ] Testes beta com 3-5 clínicas
- [ ] Documentação
- [ ] Preparação para LGPD

---

## 14. Apêndice: Análise de Redundâncias — Plano de Consolidação

| Redundância | Ação | Esforço |
|------------|------|---------|
| `email_service.py` + `email_service_backup.py` | Consolidar em `araos_connect/email/service.py` | 1 dia |
| `CatalogoDocumentProcessor` + `OCRResultado` | Unificar em `araos_intake/document_processor.py` | 3 dias |
| `ai_chat_simples` + `ai_clinical` + `crew_ai` | Consolidar em `araos_ai/` com roteamento por intenção | 1 semana |
| `patient_portal` + `patient_auth` + `patient_dashboard` | Unificar em `araos_core/patients/portal.py` | 3 dias |
| `billing_service` + `billing_service_v2` + `payment_service` | Consolidar em `araos_core/billing/` | 1 semana |
| `ConfiguracaoIA` + `ConfigIATenant` + `AIConfig` + `LLMConfig` | Consolidar em `araos_ai/config.py` com hierarquia global→tenant→user | 3 dias |
| `dr_anderson_agent` + `dynamic_tenant_agent` | Consolidar em `araos_ai/agents/` com registry dinâmico | 1 semana |
| 5 rotas de testes/psicometria | Extrair para `araos_specialties/psychiatry/scales/` | 3 dias |

**Esforço total estimado de consolidação:** ~3-4 semanas de refactoring focado.

---

*Documento elaborado com base na análise da base de código atual do SIAP Aracannabis e nas melhores práticas de arquitetura de software para healthtech.*
