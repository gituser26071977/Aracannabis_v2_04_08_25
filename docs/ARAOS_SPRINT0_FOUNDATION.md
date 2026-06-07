# ARAOS Sprint 0 — Foundation Layer
## Plano Técnico Detalhado

> **Versão:** 1.0  
> **Data:** 2026-06-07  
> **Status:** Especificação para Implementação  
> **Princípio:** *"Build the foundation. Not the features."*

---

## Sumário Executivo

Esta sprint estabelece os **quatro pilares inquebrantáveis** sobre os quais toda a plataforma ARAOS será construída:

| Pilar | Responsabilidade | Stack |
|-------|-----------------|-------|
| **Tenant Layer** | Isolamento multi-organização | PostgreSQL RLS + SQLAlchemy |
| **Identity Service** | Autenticação unificada | JWT (PyJWT) + bcrypt |
| **Event Bus** | Comunicação assíncrona | Redis Streams |
| **Audit Service** | Auditoria imutável | PostgreSQL append-only |

**Regra de Ouro:** Nenhum módulo futuro (Voice, Smart Flow, Clinical) acessa infraestrutura diretamente. Todos consomem serviços da Foundation Layer.

---

## 1. Estrutura de Diretórios

```
/home/holzwarth/Projetos/Aracannabis_SO/Aracannabis_SIAP/
│
├── araos/                          # NOVO — Platform Layer
│   ├── __init__.py
│   │
│   ├── platform/                   # Serviços centrais
│   │   ├── __init__.py
│   │   │
│   │   ├── tenant/                 # Entrega 1: Tenant Layer
│   │   │   ├── __init__.py
│   │   │   ├── models.py           # Organization, Clinic, Professional, User
│   │   │   ├── service.py          # TenantService, TenantContext
│   │   │   ├── resolver.py         # TenantResolver (subdomain/header/JWT)
│   │   │   ├── middleware.py       # TenantMiddleware (Flask)
│   │   │   ├── api.py              # Blueprint: /platform/tenant/*
│   │   │   └── schemas.py          # Pydantic schemas
│   │   │
│   │   ├── identity/               # Entrega 2: Identity Service
│   │   │   ├── __init__.py
│   │   │   ├── models.py           # IdentityUser, Credential, Session
│   │   │   ├── service.py          # IdentityService
│   │   │   ├── token.py            # JWT issue/validate/refresh
│   │   │   ├── password.py         # Hashing (bcrypt)
│   │   │   ├── biometric_stub.py   # Interface para biometria futura
│   │   │   ├── middleware.py       # AuthRequiredMiddleware
│   │   │   ├── api.py              # Blueprint: /platform/auth/*
│   │   │   └── schemas.py          # Pydantic schemas
│   │   │
│   │   ├── event_bus/              # Entrega 3: Event Bus
│   │   │   ├── __init__.py
│   │   │   ├── bus.py              # EventBus (publish/subscribe)
│   │   │   ├── publisher.py        # EventPublisher
│   │   │   ├── consumer.py         # EventConsumer (background worker)
│   │   │   ├── registry.py         # EventRegistry (catálogo tipado)
│   │   │   ├── store.py            # EventStore (Redis Streams)
│   │   │   ├── schemas.py          # EventEnvelope, DomainEvent
│   │   │   └── catalog.py          # Registro de todos os eventos
│   │   │
│   │   └── audit/                  # Entrega 4: Audit Service
│   │       ├── __init__.py
│   │       ├── models.py           # AuditEntry (append-only)
│   │       ├── service.py          # AuditService (log, query, hash)
│   │       ├── middleware.py       # AuditMiddleware (auto-log)
│   │       ├── hash_chain.py       # SHA-256 chain
│   │       ├── api.py              # Blueprint: /platform/audit/*
│   │       └── schemas.py          # Pydantic schemas
│   │
│   └── shared/                     # Utilitários compartilhados
│       ├── __init__.py
│       ├── db.py                   # SQLAlchemy db instance
│       ├── config.py               # Config centralizada
│       ├── errors.py               # Exceções customizadas
│       ├── decorators.py           # @require_tenant, @require_auth
│       └── utils.py                # Funções auxiliares
│
├── services/                       # EXISTENTE — módulos do SIAP
├── routes/                         # EXISTENTE — blueprints Flask
├── models.py                       # EXISTENTE — models legados
├── app_cors_livre.py               # EXISTENTE — entrypoint Flask
├── docker-compose.prod.yml         # EXISTENTE — infra
│
└── docs/
    ├── ARAOS_PLATFORM_ARCHITECTURE.md
    └── ARAOS_SPRINT0_FOUNDATION.md  # Este documento
```

---

## 2. Entrega 1: ARAOS Tenant Layer

### 2.1 Models

```python
# araos/platform/tenant/models.py

class Organization(db.Model):
    """Organização de saúde (clínica, hospital, consultório)."""
    __tablename__ = "araos_organizations"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    slug = db.Column(db.String(63), unique=True, nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    legal_name = db.Column(db.String(255), nullable=True)
    cnpj = db.Column(db.String(18), nullable=True, unique=True)
    plan = db.Column(db.String(20), nullable=False, default="starter")  # starter, pro, enterprise
    status = db.Column(db.String(20), nullable=False, default="active")  # active, suspended, cancelled

    # Configurações
    timezone = db.Column(db.String(50), default="America/Sao_Paulo")
    locale = db.Column(db.String(10), default="pt-BR")
    currency = db.Column(db.String(3), default="BRL")

    # Limites por plano
    max_users = db.Column(db.Integer, default=5)
    max_patients = db.Column(db.Integer, default=500)
    max_clinics = db.Column(db.Integer, default=1)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)

    # Relacionamentos
    clinics = db.relationship("Clinic", back_populates="organization", cascade="all, delete-orphan")
    users = db.relationship("PlatformUser", back_populates="organization")
    settings = db.relationship("TenantSettings", uselist=False, back_populates="organization")


class Clinic(db.Model):
    """Unidade física da organização."""
    __tablename__ = "araos_clinics"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = db.Column(db.String(36), db.ForeignKey("araos_organizations.id"), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    code = db.Column(db.String(20), nullable=False)  # Código interno

    # Endereço
    address = db.Column(db.JSON, default=dict)
    timezone = db.Column(db.String(50), nullable=True)

    # Configurações operacionais
    settings = db.Column(db.JSON, default=dict)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    organization = db.relationship("Organization", back_populates="clinics")

    __table_args__ = (
        db.UniqueConstraint("organization_id", "code"),
    )


class PlatformUser(db.Model):
    """Usuário da plataforma (médico, secretária, admin, paciente)."""
    __tablename__ = "araos_users"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = db.Column(db.String(36), db.ForeignKey("araos_organizations.id"), nullable=False)

    # Identidade
    email = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    full_name = db.Column(db.String(255), nullable=False)

    # Papel
    role = db.Column(db.String(30), nullable=False, default="viewer")
    # SUPER_ADMIN, ORG_ADMIN, CLINIC_ADMIN, DOCTOR, NURSE, RECEPTIONIST, PATIENT, SENSOR

    # Estado
    status = db.Column(db.String(20), nullable=False, default="active")
    email_verified = db.Column(db.Boolean, default=False)
    phone_verified = db.Column(db.Boolean, default=False)

    # MFA
    mfa_enabled = db.Column(db.Boolean, default=False)
    mfa_secret = db.Column(db.String(255), nullable=True)

    # Biometria (stub para futuro)
    biometric_enrolled = db.Column(db.Boolean, default=False)
    biometric_embedding = db.Column(db.LargeBinary, nullable=True)  # Criptografado

    # Metadados
    preferences = db.Column(db.JSON, default=dict)
    last_login_at = db.Column(db.DateTime, nullable=True)
    last_login_ip = db.Column(db.String(45), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    organization = db.relationship("Organization", back_populates="users")

    __table_args__ = (
        db.UniqueConstraint("organization_id", "email"),
        db.Index("idx_araos_users_org", "organization_id", "status"),
    )


class TenantSettings(db.Model):
    """Configurações customizáveis por organização."""
    __tablename__ = "araos_tenant_settings"

    organization_id = db.Column(db.String(36), db.ForeignKey("araos_organizations.id"), primary_key=True)

    # Módulos ativos
    enabled_modules = db.Column(db.JSON, default=list)  # ["cannabis", "voice", "smart_flow"]

    # Feature flags
    feature_flags = db.Column(db.JSON, default=dict)
    # {"voice": true, "telemedicine": false, "biometrics": true}

    # Branding
    branding = db.Column(db.JSON, default=dict)
    # {"logo_url": "...", "primary_color": "#4CAF50", "favicon": "..."}

    # Comunicação
    communication = db.Column(db.JSON, default=dict)
    # {"whatsapp_number": "...", "email_from": "..."}

    # LGPD
    lgpd = db.Column(db.JSON, default=dict)
    # {"retention_days": 7305, "consent_required": true}

    # AI
    ai_config = db.Column(db.JSON, default=dict)
    # {"model": "gemini-2.5-pro", "temperature": 0.3}

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    organization = db.relationship("Organization", back_populates="settings")
```

### 2.2 APIs

```
GET    /platform/tenant/organizations/me          → Organization atual
GET    /platform/tenant/organizations/{id}         → Detalhes da org
PUT    /platform/tenant/organizations/{id}         → Atualizar org

GET    /platform/tenant/clinics                    → Listar unidades
POST   /platform/tenant/clinics                    → Criar unidade
GET    /platform/tenant/clinics/{id}               → Detalhes da unidade
PUT    /platform/tenant/clinics/{id}               → Atualizar unidade

GET    /platform/tenant/users                      → Listar usuários
POST   /platform/tenant/users                      → Criar usuário
GET    /platform/tenant/users/{id}                 → Detalhes do usuário
PUT    /platform/tenant/users/{id}                 → Atualizar usuário
DELETE /platform/tenant/users/{id}                 → Desativar usuário

GET    /platform/tenant/settings                   → Configurações
PUT    /platform/tenant/settings                   → Atualizar configurações
GET    /platform/tenant/features                   → Feature flags ativas
```

### 2.3 Middleware — Tenant Resolution

```python
# araos/platform/tenant/middleware.py

class TenantMiddleware:
    """
    Resolve o tenant a partir de múltiplas fontes, em ordem de prioridade:
    1. Header X-Tenant-ID
    2. Subdomain (clinica.araos.com.br)
    3. JWT claim (org_id)
    4. Query param ?tenant_id=
    5. Path param /api/{tenant}/...
    """

    STRATEGIES = [
        "header",
        "subdomain",
        "jwt_claim",
        "query_param",
        "path_param",
    ]

    def resolve(self, request) -> TenantContext:
        # Implementação
        ...

class TenantContext:
    """Contexto do tenant para a requisição atual."""
    organization_id: str
    clinic_id: Optional[str]
    user_id: Optional[str]
    user_role: Optional[str]
    plan: str
    feature_flags: dict
```

### 2.4 Migration

```sql
-- migration: create tenant layer tables
CREATE TABLE araos_organizations (...);
CREATE TABLE araos_clinics (...);
CREATE TABLE araos_users (...);
CREATE TABLE araos_tenant_settings (...);

-- Índices
CREATE INDEX idx_org_slug ON araos_organizations(slug);
CREATE INDEX idx_org_status ON araos_organizations(status);
CREATE INDEX idx_clinic_org ON araos_clinics(organization_id);
CREATE INDEX idx_user_org_email ON araos_users(organization_id, email);
```

---

## 3. Entrega 2: ARAOS Identity

### 3.1 Models

```python
# araos/platform/identity/models.py

class Credential(db.Model):
    """Credencial de autenticação (password, OAuth, etc.)."""
    __tablename__ = "araos_credentials"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey("araos_users.id"), nullable=False)
    credential_type = db.Column(db.String(20), nullable=False)  # password, oauth, biometric_stub

    # Password
    password_hash = db.Column(db.String(255), nullable=True)

    # OAuth
    oauth_provider = db.Column(db.String(50), nullable=True)  # google, microsoft, govbr
    oauth_subject = db.Column(db.String(255), nullable=True)
    oauth_data = db.Column(db.JSON, nullable=True)

    # Estado
    is_active = db.Column(db.Boolean, default=True)
    failed_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SessionToken(db.Model):
    """Sessão ativa (refresh token tracking)."""
    __tablename__ = "araos_sessions"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey("araos_users.id"), nullable=False)
    refresh_token_jti = db.Column(db.String(255), unique=True, nullable=False)

    # Contexto
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)
    device_fingerprint = db.Column(db.String(255), nullable=True)

    # Estado
    is_valid = db.Column(db.Boolean, default=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    revoked_at = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

### 3.2 Identity Service Interface

```python
# araos/platform/identity/service.py

class IdentityService:
    """
    Serviço unificado de identidade.
    Futuro: absorverá biometria, OAuth, MFA.
    """

    async def authenticate(self, email: str, password: str,
                           tenant_id: str) -> AuthResult:
        """Autentica usuário por email/senha."""
        ...

    async def authenticate_oauth(self, provider: str, code: str,
                                  tenant_id: str) -> AuthResult:
        """Autentica via OAuth (Google, Microsoft, Gov.br)."""
        ...

    async def authorize(self, token: str, required_permissions: list) -> bool:
        """Verifica se token possui permissões necessárias."""
        ...

    def issue_token(self, user_id: str, tenant_id: str,
                    role: str, permissions: list) -> TokenPair:
        """Emite access + refresh tokens."""
        ...

    def validate_token(self, token: str) -> TokenPayload:
        """Valida access token."""
        ...

    def refresh_token(self, refresh_token: str) -> TokenPair:
        """Gera novo par de tokens."""
        ...

    async def revoke_session(self, session_id: str) -> None:
        """Revoga sessão (logout)."""
        ...

    async def register(self, email: str, password: str,
                       full_name: str, tenant_id: str) -> PlatformUser:
        """Registra novo usuário."""
        ...

    async def change_password(self, user_id: str,
                               old_password: str, new_password: str) -> None:
        """Altera senha."""
        ...

    # Stub para biometria futura
    async def biometric_stub_enroll(self, user_id: str,
                                     face_embedding: bytes) -> None:
        """Placeholder para enrollment facial."""
        ...

    async def biometric_stub_verify(self, user_id: str,
                                     face_embedding: bytes) -> bool:
        """Placeholder para verificação facial."""
        ...
```

### 3.3 JWT Structure

```python
# Access Token Payload
{
    "sub": "user_uuid",
    "org": "org_uuid",
    "role": "doctor",
    "perms": ["read_patient", "write_prescription"],
    "modules": ["cannabis", "voice"],
    "iat": 1717770000,
    "exp": 1717773600,       # 1 hora
    "jti": "unique_token_id" # Para revogação
}

# Refresh Token Payload
{
    "sub": "user_uuid",
    "org": "org_uuid",
    "type": "refresh",
    "iat": 1717770000,
    "exp": 1718374800,       # 7 dias
    "jti": "unique_refresh_id"
}
```

### 3.4 APIs

```
POST   /platform/auth/register               → Criar conta
POST   /platform/auth/login                  → Login (email/senha)
POST   /platform/auth/login-oauth            → Login OAuth (Google)
POST   /platform/auth/refresh                → Renovar token
POST   /platform/auth/logout                 → Revogar sessão
GET    /platform/auth/me                     → Perfil do usuário
PUT    /platform/auth/me                     → Atualizar perfil
PUT    /platform/auth/me/password            → Alterar senha
POST   /platform/auth/forgot-password        → Solicitar reset
POST   /platform/auth/reset-password         → Resetar senha
GET    /platform/auth/sessions               → Listar sessões ativas
DELETE /platform/auth/sessions/{id}          → Revogar sessão
```

### 3.5 Migration

```sql
CREATE TABLE araos_credentials (...);
CREATE TABLE araos_sessions (...);
CREATE INDEX idx_credentials_user ON araos_credentials(user_id, credential_type);
CREATE INDEX idx_sessions_refresh ON araos_sessions(refresh_token_jti);
CREATE INDEX idx_sessions_user ON araos_sessions(user_id, is_valid);
```

---

## 4. Entrega 3: ARAOS Event Bus

### 4.1 Event Schema

```python
# araos/platform/event_bus/schemas.py

class EventEnvelope(BaseModel):
    """Envelope padrão de todo evento na plataforma."""
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str  # PATIENT_CREATED, VOICE_SESSION_STARTED, etc.
    event_version: str = "1.0"
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Contexto
    tenant_id: str
    actor_id: Optional[str] = None
    actor_type: Optional[str] = None  # doctor, patient, system, agent
    session_id: Optional[str] = None

    # Dados
    aggregate_type: str  # patient, consultation, document, voice_session
    aggregate_id: str
    payload: dict

    # Metadados
    metadata: dict = Field(default_factory=dict)
    # {"source": "siap", "ip": "...", "trace_id": "...", "correlation_id": "..."}

    # Prioridade e retry
    priority: int = 0  # 0=normal, 1=high, 2=critical
    retry_count: int = 0
    max_retries: int = 3
```

### 4.2 Event Catalog (Catálogo Inicial)

```python
# araos/platform/event_bus/catalog.py

EVENTS = {
    # PACIENTE
    "PATIENT_CREATED": {
        "aggregate": "patient",
        "schema": PatientCreatedPayload,
        "consumers": ["audit", "knowledge", "concierge"],
    },
    "PATIENT_UPDATED": {
        "aggregate": "patient",
        "schema": PatientUpdatedPayload,
        "consumers": ["audit", "knowledge"],
    },

    # CONSULTA
    "CONSULTATION_SCHEDULED": {
        "aggregate": "consultation",
        "schema": ConsultationScheduledPayload,
        "consumers": ["audit", "connect", "smart_flow"],
    },
    "CONSULTATION_STARTED": {
        "aggregate": "consultation",
        "schema": ConsultationStartedPayload,
        "consumers": ["audit", "voice", "smart_flow"],
    },
    "CONSULTATION_FINISHED": {
        "aggregate": "consultation",
        "schema": ConsultationFinishedPayload,
        "consumers": ["audit", "connect", "concierge"],
    },

    # DOCUMENTOS
    "DOCUMENT_UPLOADED": {
        "aggregate": "document",
        "schema": DocumentUploadedPayload,
        "consumers": ["audit", "intake"],
    },
    "DOCUMENT_PROCESSED": {
        "aggregate": "document",
        "schema": DocumentProcessedPayload,
        "consumers": ["audit", "knowledge"],
    },

    # COMUNICAÇÃO
    "WHATSAPP_RECEIVED": {
        "aggregate": "message",
        "schema": WhatsAppReceivedPayload,
        "consumers": ["audit", "connect", "concierge"],
    },
    "WHATSAPP_SENT": {
        "aggregate": "message",
        "schema": WhatsAppSentPayload,
        "consumers": ["audit", "connect"],
    },

    # VOZ
    "VOICE_SESSION_STARTED": {
        "aggregate": "voice_session",
        "schema": VoiceSessionStartedPayload,
        "consumers": ["audit", "smart_flow"],
    },
    "VOICE_SESSION_ENDED": {
        "aggregate": "voice_session",
        "schema": VoiceSessionEndedPayload,
        "consumers": ["audit", "knowledge"],
    },

    # SMART FLOW
    "CHECKIN_COMPLETED": {
        "aggregate": "checkin",
        "schema": CheckinCompletedPayload,
        "consumers": ["audit", "connect", "siap"],
    },

    # SEGURANÇA
    "LOGIN_SUCCEEDED": {
        "aggregate": "session",
        "schema": LoginSucceededPayload,
        "consumers": ["audit"],
    },
    "LOGIN_FAILED": {
        "aggregate": "session",
        "schema": LoginFailedPayload,
        "consumers": ["audit", "identity"],
    },
}
```

### 4.3 Event Bus Interface

```python
# araos/platform/event_bus/bus.py

class EventBus:
    """
    Barramento de eventos centralizado.
    Implementação inicial: Redis Streams.
    """

    async def publish(self, event: EventEnvelope) -> str:
        """Publica evento no bus. Retorna event_id."""
        ...

    async def subscribe(self, event_types: list[str],
                         consumer_group: str,
                         handler: Callable) -> None:
        """
        Registra consumidor para tipos de evento.
        Usa Redis Consumer Groups para processamento distribuído.
        """
        ...

    async def consume(self, consumer_group: str,
                       consumer_name: str,
                       block_ms: int = 5000) -> list[EventEnvelope]:
        """Lê eventos pendentes do consumer group."""
        ...

    async def acknowledge(self, event_ids: list[str]) -> None:
        """Confirma processamento de eventos."""
        ...

    async def get_event_history(self, aggregate_type: str,
                                 aggregate_id: str) -> list[EventEnvelope]:
        """Retorna histórico de eventos para um aggregate."""
        ...
```

### 4.4 Redis Streams Structure

```
# Stream: araos:events:patient
# Stream: araos:events:consultation
# Stream: araos:events:document
# Stream: araos:events:voice
# Stream: araos:events:flow
# Stream: araos:events:communication
# Stream: araos:events:security

# Consumer Groups:
#   audit-consumers      → lê de TODOS os streams
#   connect-consumers    → lê communication
#   voice-consumers      → lê voice, consultation
#   smart-flow-consumers → lê flow, consultation
#   concierge-consumers  → lê communication, consultation
```

---

## 5. Entrega 4: ARAOS Audit Service

### 5.1 Model

```python
# araos/platform/audit/models.py

class AuditEntry(db.Model):
    """Registro de auditoria — append-only, imutável."""
    __tablename__ = "araos_audit_entries"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Timestamp com timezone
    occurred_at = db.Column(db.DateTime(timezone=True), nullable=False,
                            default=datetime.utcnow, index=True)

    # Contexto
    tenant_id = db.Column(db.String(36), nullable=False, index=True)
    user_id = db.Column(db.String(36), nullable=True, index=True)
    user_role = db.Column(db.String(30), nullable=True)

    # Ação
    action = db.Column(db.String(20), nullable=False, index=True)
    # CREATE, READ, UPDATE, DELETE, LOGIN, LOGOUT, EXPORT, PURGE, etc.

    # Recurso afetado
    resource_type = db.Column(db.String(50), nullable=False, index=True)
    resource_id = db.Column(db.String(36), nullable=True, index=True)

    # Mudanças (delta)
    before = db.Column(db.JSON, nullable=True)
    after = db.Column(db.JSON, nullable=True)
    changes_summary = db.Column(db.Text, nullable=True)

    # Contexto técnico
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)
    request_path = db.Column(db.String(255), nullable=True)
    request_method = db.Column(db.String(10), nullable=True)
    session_id = db.Column(db.String(36), nullable=True)
    trace_id = db.Column(db.String(36), nullable=True)

    # LGPD
    compliance_context = db.Column(db.JSON, nullable=True)
    # {"base_legal": "execução_de_contrato", "consent_id": "..."}

    # Hash chain (integridade)
    previous_hash = db.Column(db.String(64), nullable=True)
    entry_hash = db.Column(db.String(64), nullable=False)

    __table_args__ = (
        db.Index("idx_audit_tenant_time", "tenant_id", "occurred_at"),
        db.Index("idx_audit_user_action", "user_id", "action"),
        db.Index("idx_audit_resource", "resource_type", "resource_id"),
    )
```

### 5.2 Hash Chain

```python
# araos/platform/audit/hash_chain.py

class HashChain:
    """
    Garante integridade imutável dos registros de auditoria.
    Cada entrada contém o hash da entrada anterior.
    """

    def compute_hash(self, entry_data: dict, previous_hash: str) -> str:
        """
        SHA-256(entry_json + previous_hash)
        Se first entry: previous_hash = "0" * 64
        """
        data = json.dumps(entry_data, sort_keys=True)
        combined = f"{data}|{previous_hash}"
        return hashlib.sha256(combined.encode()).hexdigest()

    def verify_chain(self, entries: list[AuditEntry]) -> bool:
        """Verifica se a cadeia de hashes está intacta."""
        for i, entry in enumerate(entries):
            expected_prev = entries[i-1].entry_hash if i > 0 else "0" * 64
            if entry.previous_hash != expected_prev:
                return False
            # Recomputar hash e comparar
            ...
        return True
```

### 5.3 Audit Service Interface

```python
# araos/platform/audit/service.py

class AuditService:
    """
    Serviço de auditoria centralizado.
    Todo módulo pode chamar audit.log() para registrar ações.
    """

    async def log(self,
                  tenant_id: str,
                  user_id: Optional[str],
                  action: str,
                  resource_type: str,
                  resource_id: Optional[str],
                  before: Optional[dict] = None,
                  after: Optional[dict] = None,
                  context: Optional[dict] = None) -> AuditEntry:
        """Registra entrada de auditoria com hash chain."""
        ...

    async def query(self,
                    tenant_id: str,
                    filters: AuditFilters,
                    page: int = 1,
                    per_page: int = 50) -> AuditQueryResult:
        """Consulta registros de auditoria com filtros."""
        ...

    async def export(self,
                     tenant_id: str,
                     user_id: str,
                     format: str = "json") -> str:
        """Exporta auditoria para direito do titular (LGPD)."""
        ...

    async def get_user_activity(self,
                                 tenant_id: str,
                                 user_id: str,
                                 days: int = 30) -> list[AuditEntry]:
        """Retorna atividade de um usuário."""
        ...

    async def detect_anomalies(self,
                                tenant_id: str) -> list[AnomalyReport]:
        """Detecta padrões anômalos (acessos fora de horário, etc.)."""
        ...
```

### 5.4 Auto-Log Middleware

```python
# araos/platform/audit/middleware.py

class AuditMiddleware:
    """
    Middleware Flask que registra automaticamente:
    - Toda requisição que modifica dados (POST, PUT, DELETE, PATCH)
    - Login/logout
    - Acesso a dados sensíveis (pacientes, exames, prescrições)
    """

    SENSITIVE_RESOURCES = [
        "/api/pacientes",
        "/api/exames",
        "/api/prescricoes",
        "/api/evolucoes",
        "/api/consultas",
    ]

    def before_request(self, request):
        # Captura estado "before" para resources sensíveis
        ...

    def after_request(self, request, response):
        # Compara before/after e gera AuditEntry se houve mudança
        ...
```

### 5.5 APIs

```
GET    /platform/audit/entries              → Listar entradas (paginado)
GET    /platform/audit/entries/{id}         → Detalhes de entrada
GET    /platform/audit/me                   → Minha atividade
GET    /platform/audit/users/{id}           → Atividade de usuário
GET    /platform/audit/resources/{type}     → Atividade de recurso
POST   /platform/audit/export               → Exportar (LGPD)
GET    /platform/audit/anomalies            → Anomalias detectadas
GET    /platform/audit/integrity            → Verificar hash chain
```

---

## 6. Dependências Necessárias

```txt
# requirements.txt — adições para Sprint 0

# Tenant + Identity
bcrypt>=4.0.0
PyJWT>=2.8.0
cryptography>=42.0.0

# Event Bus
redis>=5.0.0
hiredis>=2.3.0

# Audit
# (usa hashlib da stdlib, não precisa de lib externa)

# Shared
pydantic>=2.0.0
python-dotenv>=1.0.0

# Dev
pytest-asyncio>=0.23.0
httpx>=0.27.0  # para testes de API
```

---

## 7. Ordem de Implementação Recomendada

```
Semana 1 ──► Tenant Layer (models, service, resolver, middleware)
       │
       ├──► Migration: araos_organizations, araos_clinics,
       │              araos_users, araos_tenant_settings
       │
       ├──► API: /platform/tenant/*
       │
       └──► Test: resolver de tenant, isolamento por org

Semana 2 ──► Identity Service (models, token, password, service)
       │
       ├──► Migration: araos_credentials, araos_sessions
       │
       ├──► API: /platform/auth/*
       │
       └──► Test: login, logout, refresh, token validation

Semana 3 ──► Event Bus (schemas, registry, bus, publisher, consumer)
       │
       ├──► Redis Streams setup
       │
       ├──► Catalog: 15+ eventos definidos
       │
       ├──► Consumer Group: audit-consumers
       │
       └──► Test: publish/consume, retry, dead letter

Semana 4 ──► Audit Service (models, hash chain, service, middleware)
       │
       ├──► Migration: araos_audit_entries
       │
       ├──► Hash chain implementation
       │
       ├──► Auto-log middleware
       │
       ├──► API: /platform/audit/*
       │
       └──► Test: hash integrity, query, export

Semana 5 ──► Integração
       │
       ├──► SIAP Core consome Tenant Layer
       │
       ├──► SIAP Core emite eventos (Event Bus)
       │
       ├──► SIAP Core gera audit entries
       │
       ├──► Voice Server consome Tenant Layer
       │
       ├──► Voice Server emite eventos
       │
       └──► Test end-to-end

Semana 6 ──► Documentação, Deploy, Polish
       │
       ├──► API documentation (OpenAPI)
       │
       ├──► Docker Compose update (Redis healthcheck)
       │
       ├──├──► Deploy no VPS
       │
       └──► Handoff para Sprint 1
```

---

## 8. Riscos Técnicos

| # | Risco | Prob. | Impacto | Mitigação |
|---|-------|-------|---------|-----------|
| 1 | **Conflito de models.py existente** | Alta | Alto | Isolar em `araos/platform/*`, não tocar `models.py` legado |
| 2 | **JWT legado do SIAP vs novo** | Alta | Alto | Dual-validation durante transição, gradualmente migrar |
| 3 | **Redis não disponível em dev** | Média | Alto | Fallback para SQLite/PostgreSQL para Event Bus em dev |
| 4 | **Performance do hash chain** | Baixa | Médio | Pré-computar hash, índice em previous_hash |
| 5 | **Migração de usuários existentes** | Alta | Alto | Script de migração: `Profissional` → `PlatformUser` |
| 6 | **Tenant resolution lenta** | Média | Médio | Cache de tenant em Redis, TTL 5min |
| 7 | **Dead letters no Event Bus** | Média | Alto | DLQ (dead letter queue) com alerta + retry manual |
| 8 | **Duplo-write durante migração** | Alta | Alto | Feature flag: usar novo sistema vs legado |

---

## 9. Cronograma

| Semana | Foco | Entregáveis |
|--------|------|-------------|
| **S1** | Tenant Layer | Models, resolver, middleware, APIs, tests |
| **S2** | Identity Service | JWT, login, logout, refresh, tests |
| **S3** | Event Bus | Redis Streams, catalog, consumer groups, tests |
| **S4** | Audit Service | Hash chain, auto-log, APIs, tests |
| **S5** | Integração | SIAP + Voice conectados à Platform Layer |
| **S6** | Deploy + Docs | VPS deploy, OpenAPI docs, handoff |

**Duração total estimada:** 6 semanas (1.5 meses)

**Equipe recomendada:** 2 devs backend sêniors + 1 devops (meio período)

---

## 10. Critérios de Aceitação

Ao final da Sprint 0, os seguintes testes devem passar:

```
✅ Tenant Layer
   [ ] Criar organization via API
   [ ] Criar clinic dentro da organization
   [ ] Criar user vinculado à organization
   [ ] Resolver tenant por header X-Tenant-ID
   [ ] Resolver tenant por JWT claim
   [ ] Feature flags retornam corretamente por tenant
   [ ] Dados de um tenant não são visíveis para outro

✅ Identity Service
   [ ] Registrar usuário com senha hasheada (bcrypt)
   [ ] Login retorna access + refresh tokens
   [ ] Token JWT contém org_id, role, permissions
   [ ] Refresh token gera novo par de tokens
   [ ] Logout revoga refresh token
   [ ] Middleware rejeita requests sem token válido

✅ Event Bus
   [ ] Publicar evento PATIENT_CREATED
   [ ] Consumir evento via consumer group
   [ ] Evento persistido no Redis Stream
   [ ] Retry automático em falha
   [ ] Dead letter para eventos que falham 3x

✅ Audit Service
   [ ] Criar entrada de auditoria via service
   [ ] Hash chain computado corretamente
   [ ] Auto-log middleware registra POST/PUT/DELETE
   [ ] Query de auditoria por tenant filtra corretamente
   [ ] Export JSON para LGPD
   [ ] Verificação de integridade da cadeia passa

✅ Integração
   [ ] SIAP Core usa Tenant Middleware
   [ ] SIAP Core emite eventos via Event Bus
   [ ] Voice Server usa Tenant Middleware
   [ ] Voice Server emite eventos via Event Bus
   [ ] Todas as operações críticas geram audit entry
```

---

*Documento elaborado como plano técnico mestre da Sprint 0 — Foundation Layer do ARAOS.*
*Aprovar antes do início da implementação.*
