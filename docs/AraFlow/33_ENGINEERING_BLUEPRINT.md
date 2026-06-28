# AraFlow — Engineering Blueprint

> **Versão:** 1.0.0
> **Data:** 2026-06-25
> **Status:** Fase 0.9 — Constituição Técnica
> **Natureza:** Documento de referência definitiva para qualquer equipe de engenharia.
> **Autoridade:** Chief Technology Officer (CTO), respondendo ao Conselho Técnico do AraOS.

> **Princípio:** *A arquitetura é o esqueleto. Se o esqueleto for bom, o corpo aguenta 10 anos. Se for ruim, a primeira doença derruba.*

---

## Sumário

1. Preâmbulo do CTO
2. Decisão arquitetural central
3. Estrutura do Projeto
4. Separação de Camadas
5. AraFlow Core (8 Engines)
6. Motor Respiratório
7. Sistema de Protocolos
8. Sistema de Áudio
9. Sistema de Animação
10. Sincronização Áudio-Animação-Timer
11. Persistência
12. Sincronização Cliente-Servidor
13. Segurança & LGPD
14. Observabilidade
15. Estratégia de Testes
16. Performance — Metas
17. Escalabilidade — Roadmap
18. Deploy & Ambientes
19. CI/CD
20. Gestão de Configuração
21. Arquitetura para IA (preparação)
22. Arquitetura para Wearables (preparação)
23. Arquitetura para HRV (preparação)
24. Arquitetura para Apple Health / Health Connect (preparação)
25. Dívida Técnica — Aceitável vs Inaceitável
26. Top 50 Riscos Técnicos
27. ADRs (Architecture Decision Records)
28. Parecer Final do CTO

---

## 1. Preâmbulo do CTO

A Fase 0.8 congelou o produto. 3 protocolos. Wellness. Mobile-first. B2B-Pro primário.

Agora cabe ao CTO responder a uma única pergunta:

**"Como construir este produto para que ele dure 10 anos sem reescritas significativas?"**

Esta Constituição Técnica responde a essa pergunta. Onde houver ambiguidade, este documento define. Onde houver decisões pendentes, este documento decide. Após a publicação, **não há mais discussão arquitetural**. Há implementação.

Toda decisão aqui segue três critérios:

1. **Durabilidade.** A decisão sobrevive a 10 anos de evolução tecnológica?
2. **Clareza.** Um engenheiro novo entende em 30 minutos?
3. **Testabilidade.** Cada peça pode ser testada isoladamente?

Se qualquer critério falhar, a decisão é revisada antes da publicação.

---

## 2. Decisão Arquitetural Central

### Comparação de padrões

| Padrão | Quando aplicar | Durabilidade | Testabilidade | Complexidade | Adequação ao AraFlow |
|--------|----------------|--------------|---------------|--------------|----------------------|
| **Mobile First** | Estratégia de plataforma | Alta | N/A | Baixa | ✅ Complementar (mas não é arquitetura) |
| **Offline First** | Quando há trabalho desconectado | Alta | Média | Média | ✅ Complementar (estratégia de dados) |
| **Event Driven** | Sistemas distribuídos | Alta | Alta | Alta | ⚠️ Overhead para mobile local |
| **Feature Based** | Organização de pastas | Média | Média | Baixa | ✅ Complementar (organização) |
| **Clean Architecture** | Apps com domínio rico | Muito alta | Muito alta | Média | ✅ **Excelente encaixe** |
| **Hexagonal** | Apps com múltiplos adaptadores | Muito alta | Muito alta | Média | ⚠️ Similar ao Clean, redundante |
| **Vertical Slice** | Times grandes paralelos | Média | Média | Baixa | ⚠️ Time pequeno não precisa |
| **Modular Monolith** | Backend em evolução | Alta | Alta | Média | ✅ Para qualquer backend próprio |
| **Microservices** | Escala > 100 serviços | Média | Alta | Muito alta | ❌ Overhead proibitivo no MVP |
| **Serverless** | Workload variável | Média | Média | Alta | ⚠️ Cold start problemático |

### Decisão Final

# **Clean Architecture + Feature-Based Modules + Offline-First.**

**Justificativa:**

- **Clean Architecture** resolve o problema central: como isolar o domínio clínico (regulação autonômica, sessões, protocolos) de frameworks, UI, banco, e APIs externas. Em 10 anos, trocaremos React Native por outra coisa, trocaremos SQLite por outro banco, trocaremos Sentry por outra ferramenta. Mas o **núcleo clínico não muda**. Clean Architecture garante isso.

- **Feature-Based Modules** organizam o código por funcionalidade de usuário (Onboarding, Session, History, Profile). Cada feature tem sua pasta com sua própria Clean Architecture interna. Time pequeno navega fácil; time grande consegue paralelizar.

- **Offline-First** é estratégia de dados, não arquitetura: a sessão precisa funcionar sem rede (consultório, avião, área rural). Backend é fonte de verdade para dados compartilhados; local é fonte de verdade para sessão em andamento.

### Por que NÃO as outras?

- **Microservices:** Time de 8 FTEs não mantém 10 serviços. Custo operacional proibitivo.
- **Serverless:** Cold start ruim para UX clínica; vendor lock-in forte.
- **Hexagonal:** Equivalente ao Clean Architecture. Escolher um evita confusão semântica.
- **Vertical Slice:** Útil com 20+ devs. Time pequeno não precisa.
- **Event Driven puro:** Complexidade desnecessária em mobile local.

---

## 3. Estrutura do Projeto

```
araflow/
├── mobile/                              # Aplicativo iOS + Android
│   ├── src/
│   │   ├── core/                        # AraFlow Core (8 engines)
│   │   │   ├── breath-engine/
│   │   │   │   ├── domain/              # Modelos puros (BreathPhase, BreathCycle)
│   │   │   │   ├── application/         # Casos de uso (startSession, pauseSession)
│   │   │   │   ├── infrastructure/      # Adaptadores (TimerAdapter, AudioAdapter)
│   │   │   │   └── index.ts
│   │   │   ├── protocol-engine/
│   │   │   ├── session-engine/
│   │   │   ├── timer-engine/
│   │   │   ├── audio-engine/
│   │   │   ├── animation-engine/
│   │   │   ├── analytics-engine/
│   │   │   └── safety-engine/
│   │   │
│   │   ├── features/                    # Funcionalidades verticais
│   │   │   ├── onboarding/
│   │   │   │   ├── presentation/        # Screens, components
│   │   │   │   ├── application/         # ViewModels, hooks
│   │   │   │   ├── domain/              # Modelos locais
│   │   │   │   ├── infrastructure/      # Local storage, services
│   │   │   │   └── index.ts
│   │   │   ├── session/
│   │   │   ├── history/
│   │   │   ├── profile/
│   │   │   ├── dashboard/
│   │   │   └── ...
│   │   │
│   │   ├── shared/                      # Compartilhado entre features
│   │   │   ├── ui/                      # Design System (botões, inputs)
│   │   │   ├── theme/                   # Tokens, paleta
│   │   │   ├── i18n/                    # Internacionalização
│   │   │   ├── errors/                  # Error types compartilhados
│   │   │   ├── utils/                   # Funções puras
│   │   │   └── types/                   # Tipos compartilhados
│   │   │
│   │   ├── infrastructure/              # Adaptadores externos
│   │   │   ├── api/                     # HTTP client, interceptors
│   │   │   ├── persistence/             # SQLite, key-value
│   │   │   ├── audio/                   # Adaptador de áudio
│   │   │   ├── haptics/                 # Vibração
│   │   │   ├── biometrics/              # Face ID, fingerprint
│   │   │   ├── crash/                   # Sentry wrapper
│   │   │   ├── analytics/               # Eventos
│   │   │   └── config/                  # Remote Config
│   │   │
│   │   ├── App.tsx
│   │   └── main.tsx
│   │
│   ├── __tests__/                       # Testes cross-feature
│   ├── e2e/                             # Testes end-to-end
│   ├── assets/                          # Imagens, áudios, fontes
│   └── package.json
│
├── backend/                             # Backend AraFlow (se houver partes próprias)
│   ├── src/
│   │   ├── modules/
│   │   │   ├── sessions/
│   │   │   ├── protocols/
│   │   │   ├── analytics/
│   │   │   └── ...
│   │   ├── shared/
│   │   └── infrastructure/
│   └── package.json
│
├── shared-contracts/                    # Tipos compartilhados mobile/backend
│   ├── protocol.schema.json
│   ├── api.types.ts
│   └── ...
│
└── docs/                                # Documentação técnica
    ├── adr/
    ├── runbooks/
    └── architecture/
```

### Princípios de organização

1. **Cada engine do Core é uma pasta isolada com sua própria Clean Architecture interna.**
2. **Cada feature tem a mesma estrutura interna (presentation/application/domain/infrastructure).**
3. **`shared/` nunca importa de `features/` ou `core/`.** Direção das dependências é para dentro.
4. **`core/` nunca importa de `features/`, `shared/`, ou `infrastructure/`.** Core é puro.
5. **`features/` pode importar de `core/`, `shared/`, e `infrastructure/`.**
6. **`infrastructure/` pode importar de `core/` (para tipos), mas não de `features/`.**

---

## 4. Separação de Camadas

### Domain (Camada de Domínio)

**Responsabilidade:** Regras de negócio puras. Sem dependências externas.

**Conteúdo:**
- Entidades (Session, Protocol, BreathPhase, Patient).
- Value Objects (Duration, ProtocolId).
- Enums (SessionState, ProtocolPhase).
- Domain Services (cálculos puros, validações).
- Domain Events (SessionStarted, SessionCompleted).

**Regras:**
- Nenhuma dependência de framework, biblioteca externa, banco, ou UI.
- Apenas TypeScript puro.
- 100% testável sem mock.

### Application (Camada de Aplicação)

**Responsabilidade:** Orquestração de casos de uso. Coordena Domain e Infrastructure.

**Conteúdo:**
- Use Cases (StartSessionUseCase, CompleteProtocolUseCase).
- Ports (interfaces que Infrastructure implementa).
- DTOs (Data Transfer Objects entre camadas).

**Regras:**
- Pode depender de Domain.
- Não pode depender de Infrastructure concreta — apenas Ports.
- Não pode depender de UI/Presentation.

### Infrastructure (Camada de Infraestrutura)

**Responsabilidade:** Adaptação a tecnologias externas.

**Conteúdo:**
- Implementações de Ports (SQLite repository, HTTP API client).
- Adaptadores de framework (React Hook Form wrappers, etc.).
- Mappers (Domain ↔ DTO ↔ DB row).

**Regras:**
- Pode depender de Domain e Application.
- Toda dependência externa (banco, API, áudio) vive aqui.
- Substituível sem alterar Domain.

### Presentation (Camada de Apresentação)

**Responsabilidade:** UI, telas, componentes.

**Conteúdo:**
- Screens, Components.
- ViewModels / Hooks (lógica de apresentação).
- Navegação.
- Estado local de UI.

**Regras:**
- Pode depender de Application (Use Cases).
- Não pode acessar Infrastructure diretamente.
- Não pode ter regras de negócio.

### Shared

**Responsabilidade:** Código genérico sem regra de negócio.

**Conteúdo:**
- Componentes de Design System reutilizáveis.
- Funções utilitárias puras.
- Tipos compartilhados.

**Regras:**
- Não pode depender de Domain, Application, Infrastructure, ou Features.
- Universalmente importável.

---

## 5. AraFlow Core (8 Engines)

O **AraFlow Core** é o coração clínico do produto. É um conjunto de 8 engines isolados, cada um com sua responsabilidade única. Eles se comunicam via eventos, não via chamadas diretas.

### 5.1 Breath Engine (Motor Respiratório)

**Responsabilidade:** Controlar o ciclo respiratório em tempo real.

**Responsabilidades específicas:**
- Definir fase atual (inhale, hold-in, exhale, hold-out).
- Calcular progresso da fase (0-100%).
- Transicionar entre fases baseado em protocolo.
- Emitir eventos de respiração (onPhaseChange, onCycleComplete).
- Suportar cancelamento, pausa, retomada.

**Dependências:**
- Timer Engine (precisão de tempo).
- Protocol Engine (qual protocolo executar).

**Isolamento:**
- Não conhece UI, áudio, ou animação.
- Não conhece banco de dados.
- Não conhece autenticação.

### 5.2 Protocol Engine (Motor de Protocolos)

**Responsabilidade:** Carregar, validar, e fornecer protocolos.

**Responsabilidades específicas:**
- Carregar protocolo de fonte (local bundled ou servidor).
- Validar estrutura do protocolo.
- Fornecer metadata (título, descrição, evidências).
- Versionar protocolo.
- Hot-reload de protocolo sem nova versão do app.

**Dependências:** Nenhuma (puramente domínio).

**Isolamento:**
- Não executa sessão.
- Não conhece UI.

### 5.3 Session Engine (Motor de Sessão)

**Responsabilidade:** Gerenciar o ciclo de vida da sessão.

**Responsabilidades específicas:**
- Criar sessão (state: created).
- Iniciar sessão (state: running).
- Pausar sessão (state: paused).
- Retomar sessão (state: running).
- Cancelar sessão (state: cancelled).
- Completar sessão (state: completed).
- Persistir estado da sessão.
- Sincronizar com servidor quando online.

**Dependências:**
- Breath Engine.
- Protocol Engine.
- Timer Engine.

### 5.4 Timer Engine (Motor de Tempo)

**Responsabilidade:** Fornecer referência temporal precisa.

**Responsabilidades específicas:**
- Fornecer relógio monotonic (não affected by wall-clock changes).
- Drift correction em background.
- Wake-up scheduling para lembretes.
- Sincronização com wall clock.

**Dependências:** Nenhuma.

### 5.5 Audio Engine (Motor de Áudio)

**Responsabilidade:** Reproduzir áudio com sincronização.

**Responsabilidades específicas:**
- Carregar áudio (cached ou streaming).
- Reproduzir/Pausar/Parar.
- Sincronizar com Breath Engine.
- Fade in/out.
- Ducking (reduzir volume durante voz guiada).
- Audio focus handling (iOS interruptions, Android audio focus).

**Dependências:**
- Timer Engine (sync).
- Breath Engine (fases).

### 5.6 Animation Engine (Motor de Animação)

**Responsabilidade:** Coordenar animações visuais.

**Responsabilidades específicas:**
- Animar círculo respiratório baseado em Breath Engine.
- Sincronizar com áudio.
- Suportar background (animação pausa em background).
- 60fps target.

**Dependências:**
- Breath Engine (estado).
- Timer Engine (sync).

### 5.7 Analytics Engine (Motor de Analytics)

**Responsabilidade:** Coletar e enviar eventos.

**Responsabilidades específicas:**
- Receber eventos de qualquer engine.
- Enriquecer com contexto (user_id, session_id, app_version).
- Filar localmente se offline.
- Enviar para backend (opt-in).
- Opt-out por categoria.

**Dependências:**
- Infrastructure (HTTP client).

### 5.8 Safety Engine (Motor de Segurança)

**Responsabilidade:** Garantir limites clínicos.

**Responsabilidades específicas:**
- Validar duração máxima de sessão.
- Validar número máximo de ciclos.
- Detectar padrões arriscados (ex.: hipoxemia simulada).
- Alertar em fadiga de uso (uso excessivo em 24h).
- Forçar interrupção se limite excedido.
- Log de eventos de segurança.

**Dependências:**
- Session Engine.

### 5.9 Comunicação entre Engines

```
[Protocol Engine] ──► [Session Engine] ──► [Breath Engine]
                                              │
                                              ├──► [Timer Engine] (sync source)
                                              │
                                              ├──► [Audio Engine] (play cues)
                                              ├──► [Animation Engine] (visual)
                                              │
                                              └──► [Safety Engine] (validate)
                                              
[Tudo] ──► [Analytics Engine] (observe)
```

**Princípio:** Engines se comunicam via **eventos**, não chamadas diretas. Isso permite:
- Testar engines isoladamente.
- Trocar implementação sem quebrar contrato.
- Adicionar engines novos sem refatorar existentes.

---

## 6. Motor Respiratório (Breath Engine) — Detalhamento

### 6.1 Modelo de domínio

```typescript
// Pure domain types — no dependencies
type BreathPhaseType = 'inhale' | 'hold-in' | 'exhale' | 'hold-out';

interface BreathPhase {
  type: BreathPhaseType;
  durationMs: number;
  curve: 'linear' | 'ease-in' | 'ease-out' | 'ease-in-out';
}

interface BreathCycle {
  id: string;
  index: number;
  phases: BreathPhase[];
}

interface BreathSession {
  protocolId: string;
  cycles: BreathCycle[];
  totalDurationMs: number;
}

interface BreathEngineState {
  status: 'idle' | 'running' | 'paused' | 'completed' | 'cancelled';
  currentCycleIndex: number;
  currentPhaseIndex: number;
  phaseElapsedMs: number;
  totalElapsedMs: number;
  sessionStartedAt: number; // monotonic clock
}
```

### 6.2 Máquina de estados

```
                    ┌─────────────┐
                    │    IDLE     │
                    └──────┬──────┘
                           │ start()
                           ▼
                    ┌─────────────┐
        ┌──────────│   RUNNING   │──────────┐
        │ pause()  └──────┬──────┘  complete() │
        ▼                 │                ▼
   ┌─────────┐            │           ┌──────────┐
   │ PAUSED  │            │           │COMPLETED │
   └────┬────┘            │           └──────────┘
        │ resume()        │
        └─────────────────┘
                           │ cancel()
                           ▼
                    ┌─────────────┐
                    │ CANCELLED   │
                    └─────────────┘
```

### 6.3 Eventos emitidos

```typescript
type BreathEngineEvent =
  | { type: 'phase.start'; phase: BreathPhase; cycleIndex: number; phaseIndex: number }
  | { type: 'phase.tick'; phase: BreathPhase; cycleIndex: number; phaseIndex: number; progress: number; elapsedMs: number }
  | { type: 'phase.end'; phase: BreathPhase; cycleIndex: number; phaseIndex: number }
  | { type: 'cycle.complete'; cycleIndex: number }
  | { type: 'session.pause'; elapsedMs: number }
  | { type: 'session.resume'; elapsedMs: number }
  | { type: 'session.cancel'; elapsedMs: number }
  | { type: 'session.complete'; totalDurationMs: number }
  | { type: 'session.error'; error: BreathEngineError };
```

### 6.4 Drift correction

Em background (app fechado), o sistema operacional pode suspender timers. Solução:

```
1. Ao iniciar: registrar sessionStartedAt (monotonic + wall clock)
2. Ao retomar: calcular elapsed = wallClock.now() - wallStartedAt
3. Se elapsed > phaseRemaining: pular para próxima fase
4. Se elapsed > totalDuration: completar sessão
5. Persistir estado a cada 5 segundos em foreground
```

### 6.5 Background handling

| Plataforma | Comportamento | Mitigação |
|------------|---------------|-----------|
| iOS (locked) | Timer suspenso | Background audio session mantém app ativo |
| iOS (killed) | Estado perdido | Persistir antes de cada phase transition |
| Android (background) | Doze mode | Foreground service para sessões longas |
| Android (killed) | Estado perdido | Persistir + restaurar on next launch |

**Estratégia:** Sessão sempre persiste estado ao final de cada fase. Em caso de kill, na próxima abertura do app, oferecemos "retomar sessão interrompida".

---

## 7. Sistema de Protocolos

### 7.1 Formato escolhido: JSON

**Comparação:**

| Formato | Vantagens | Desvantagens | Decisão |
|---------|-----------|--------------|---------|
| **JSON** | Nativo em JS/TS, schema validation, hot-reload, versionamento simples | Verbose | ✅ **Escolhido** |
| **YAML** | Mais legível, comentários | Parsing extra, ambiguidade | ❌ |
| **Banco** | Versionamento automático, queries | Acopla protocolo a schema DB | ❌ |
| **Classe TS** | Tipagem forte | Não versiona, não atualiza sem release | ❌ |

### 7.2 Schema de Protocolo

```json
{
  "id": "box_4_4_4_4",
  "version": "1.0.0",
  "title": "Box 4-4-4-4",
  "subtitle": "Respiração quadrada",
  "description": "Técnica de 4 tempos iguais. Inspire, segure, expire, segure.",
  "evidence_level": "B",
  "evidence_refs": [
    "doi:10.1000/example.2023"
  ],
  "duration_ms": 320000,
  "cycles": 10,
  "rest_between_cycles_ms": 0,
  "phases": [
    {
      "type": "inhale",
      "duration_ms": 4000,
      "curve": "ease-in-out"
    },
    {
      "type": "hold-in",
      "duration_ms": 4000,
      "curve": "linear"
    },
    {
      "type": "exhale",
      "duration_ms": 4000,
      "curve": "ease-in-out"
    },
    {
      "type": "hold-out",
      "duration_ms": 4000,
      "curve": "linear"
    }
  ],
  "audio": {
    "intro_voice_id": "voice_intro_box",
    "cue_voice_id": "voice_cue_box",
    "ambient_track_id": "ambient_calm_01",
    "volume_curve": "fade-in-end"
  },
  "contraindications": [],
  "preconditions": {
    "min_age": 18,
    "max_age": 99,
    "excludes_conditions": ["pregnancy_high_risk"]
  },
  "metadata": {
    "author": "AraFlow Clinical Team",
    "approved_at": "2026-06-25T00:00:00Z",
    "tags": ["anxiety", "stress", "beginner"]
  }
}
```

### 7.3 Versionamento

Protocolos seguem **Semantic Versioning**:
- **Major (X.0.0):** Mudança de fases ou estrutura. Requer migração de sessões históricas.
- **Minor (1.X.0):** Adição de metadata, áudio, ou tags. Compatível com sessões históricas.
- **Patch (1.0.X):** Correção de texto, audio metadata. Compatível.

### 7.4 Carregamento

```
1. App inicia.
2. Carrega versões bundled (offline-first).
3. Async: busca versões atualizadas do servidor.
4. Se servidor tem versão mais nova: valida schema, atualiza local, persiste.
5. Se servidor offline: usa bundled.
6. Cache local com TTL 24h.
```

### 7.5 Validação

Schema validado com **Zod** em runtime. Schema compartilhado entre mobile e backend (via `shared-contracts/`).

---

## 8. Sistema de Áudio

### 8.1 Responsabilidades

- Carregar áudio (local bundled, cache local, ou streaming).
- Reproduzir/Pausar/Continuar/Parar.
- Sincronizar com Breath Engine.
- Ducking (volume baixo durante voz, normal em silêncio).
- Fade in/out suave.
- Audio focus handling (interrupções).

### 8.2 Estratégia de áudio

```
[A] Voz guiada INTRO (uma vez no início)
    ↓
[B] Loop de áudio ambiente (durante toda sessão)
    ↓
[C] Cue de voz por fase (no início de cada fase)
    "Inspire" / "Segure" / "Expire"
    ↓
[D] Beep opcional na transição de fase (opt-in)
    ↓
[E] Voz OUTRO no final
```

### 8.3 Tratamento de interrupções

| Evento | Comportamento |
|--------|---------------|
| Phone call (iOS/Android) | Pausar sessão, salvar estado, retomar ao fim da chamada |
| Siri / Google Assistant | Pausar áudio ambiente; retomar |
| AirPods disconnected | Continuar via speaker com volume normal |
| Bluetooth connect delay | Buffer extra de 200ms |

### 8.4 Performance

- Áudio pré-carregado antes do início da sessão.
- Audio decoder em thread separada (não bloqueia UI).
- Latência máxima tolerada: 50ms entre cue e fase visual.

---

## 9. Sistema de Animação

### 9.1 Princípio

**Animação é derivada do estado do Breath Engine, não do tempo real.**

Isso significa:
- A animação sempre reflete o estado correto, mesmo após drift.
- Animação não precisa conhecer protocolo (apenas recebe progress 0-1).
- Trocar de animação não afeta lógica clínica.

### 9.2 Fluxo

```
Breath Engine emite "phase.tick" com progress 0.0 → 1.0
         │
         ▼
Animation Engine recebe progress
         │
         ▼
Aplica curva de easing (linear/ease-in/ease-out/ease-in-out)
         │
         ▼
Renderiza frame a 60fps via requestAnimationFrame
```

### 9.3 Apenas uma animação no MVP: **Círculo respiratório.**

```
       ⬤        ← inhale (raio cresce)
      ⬤⬤       ← hold-in (raio estável)
       ⬤        ← exhale (raio diminui)
        •        ← hold-out (raio mínimo)
```

### 9.4 Background

Em background (app minimizado), animação pausa. Áudio continua. Quando volta ao foreground, animação retoma do estado atual.

---

## 10. Sincronização Áudio-Animação-Timer

### 10.1 Princípio: Single Source of Truth

**Timer Engine é a única fonte de verdade temporal.**

- Breath Engine consulta Timer Engine.
- Audio Engine consulta Breath Engine.
- Animation Engine consulta Breath Engine.
- Tudo converge no mesmo `elapsedMs`.

### 10.2 Master Clock Pattern

```typescript
class MasterClock {
  private monotonicStart: number;
  private wallStart: number;
  
  start(): void {
    this.monotonicStart = performance.now();
    this.wallStart = Date.now();
  }
  
  getElapsedMs(): number {
    // Use monotonic to avoid jumps when wall clock changes
    return performance.now() - this.monotonicStart;
  }
  
  getWallElapsedMs(): number {
    return Date.now() - this.wallStart;
  }
}
```

### 10.3 Eventos

```
Timer Engine tick (60Hz)
   │
   ▼
Breath Engine calcula fase atual
   │
   ├──► emite phase.tick {progress, elapsedMs}
   │       │
   │       ├──► Animation Engine renderiza frame
   │       └──► Audio Engine ajusta volume (ducking)
   │
   └──► Session Engine atualiza estado
```

### 10.4 Drift Prevention

- Audio buffer scheduling (não tempo real): áudio agendado para tocar em momento exato do wall clock.
- Animação usa rAF (60fps tipicamente, mas pode variar).
- Se áudio atrasa: avançar fase visual para追上 áudio.
- Se animação atrasa: continuar áudio sem render (visual recupera no próximo frame).

---

## 11. Persistência

### 11.1 Camadas de armazenamento

| Camada | Tecnologia | Uso | Latência |
|--------|------------|-----|----------|
| **In-memory** | Variáveis JS | Estado de UI, sessão em andamento | N/A |
| **Local SQLite** | WatermelonDB ou expo-sqlite | Sessões, protocolos cached, preferências | <10ms |
| **AsyncStorage** | Key-Value | Tokens, flags simples, settings | <5ms |
| **Secure Storage** | Keychain (iOS) / Keystore (Android) | Tokens sensíveis, biometria | <50ms |
| **Backend** | Postgres (via AraOS) | Source of truth, agregações | 50-500ms |
| **Cache servidor** | Redis | Sessões ativas, rate limiting | <5ms |

### 11.2 O que fica onde

**Local (offline-first):**
- Sessão em andamento (estado + resultados).
- Protocolos cached.
- Configurações de usuário.
- Histórico de sessões (últimas 100).
- Áudios cached (top 3 protocolos).

**Servidor:**
- Histórico completo de sessões (sincronizado).
- Dados de paciente (já existe no AraOS).
- Analytics agregados.
- Configurações globais (protocolos atualizados).

### 11.3 Schema SQLite local

```sql
CREATE TABLE sessions (
  id TEXT PRIMARY KEY,
  patient_id TEXT,
  protocol_id TEXT NOT NULL,
  protocol_version TEXT NOT NULL,
  started_at INTEGER NOT NULL,  -- monotonic ms
  ended_at INTEGER,
  duration_ms INTEGER,
  status TEXT NOT NULL,  -- running|paused|completed|cancelled
  completed_cycles INTEGER,
  pre_mood INTEGER,  -- 1-5
  post_mood INTEGER,  -- 1-5
  pre_energy INTEGER,
  post_energy INTEGER,
  device_info TEXT,  -- JSON
  app_version TEXT,
  sync_status TEXT DEFAULT 'pending',  -- pending|synced|failed
  created_at INTEGER NOT NULL
);

CREATE INDEX idx_sessions_patient ON sessions(patient_id);
CREATE INDEX idx_sessions_started ON sessions(started_at);
CREATE INDEX idx_sessions_sync ON sessions(sync_status);

CREATE TABLE protocols_cached (
  id TEXT NOT NULL,
  version TEXT NOT NULL,
  payload TEXT NOT NULL,  -- JSON
  fetched_at INTEGER NOT NULL,
  PRIMARY KEY (id, version)
);

CREATE TABLE user_preferences (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);
```

---

## 12. Sincronização Cliente-Servidor

### 12.1 Quando sincronizar

| Evento | Sincronização |
|--------|---------------|
| Sessão completada | Imediato (best-effort) |
| App em foreground | Pull de protocolos atualizados |
| App em background | Push de sessões pendentes (best-effort) |
| App aberto + WiFi | Pull + Push completo |
| Manual | Botão "Sincronizar agora" |

### 12.2 Estratégia de conflito

**Last-Write-Wins para sessões** (sessões são eventos imutáveis).

**Server-Authoritative para preferências e configurações** (servidor é fonte de verdade).

### 12.3 Fila offline

```typescript
interface SyncQueue {
  enqueue(event: SyncEvent): void;
  process(): Promise<SyncResult>;
  retry(event: SyncEvent, attempt: number): void;
}

// Backoff exponencial: 1s, 5s, 30s, 5min, 30min, 1h, desistir
```

### 12.4 Resolução de conflitos de sessão

Sessões não conflitam: cada sessão tem ID único. Conflito só ocorre se dispositivo A e dispositivo B iniciaram sessão simultânea (raro). Solução: sessões simultâneas são permitidas; sincronização adiciona ambas; backend reconcilia se necessário.

---

## 13. Segurança & LGPD

### 13.1 Princípios LGPD

1. **Privacy by Design.** Toda feature nova passa por revisão de privacidade antes de ser mergeada.
2. **Minimize data.** Coletar apenas o necessário.
3. **Opt-in granular.** Cada categoria de dado requer consentimento explícito.
4. **Right to be forgotten.** Usuário pode deletar conta e todos os dados.
5. **Portability.** Usuário pode exportar todos os dados em formato legível.

### 13.2 Categorias de consentimento (LGPD)

| Categoria | Descrição | Default |
|-----------|-----------|---------|
| **Essencial** | Autenticação, dados de sessão | ✅ Opt-in implícito (necessário) |
| **Analítico** | Eventos de uso para melhorar produto | ⚠️ Opt-out |
| **Pesquisa** | Dados anonimizados para pesquisa clínica | ❌ Opt-in |
| **Personalização** | Recomendações baseadas em uso | ❌ Opt-in |
| **Marketing** | Comunicações promocionais | ❌ Opt-in |

### 13.3 Criptografia

| Camada | Algoritmo |
|--------|-----------|
| **Em trânsito** | TLS 1.3 |
| **Em repouso (servidor)** | AES-256 |
| **Em repouso (local)** | iOS: NSFileProtectionComplete; Android: EncryptedSharedPreferences + SQLCipher |
| **Tokens** | JWT com refresh tokens curtos (15min access, 7d refresh) |
| **Biometria** | Native (LocalAuthentication iOS, BiometricPrompt Android) |

### 13.4 Armazenamento seguro

- **iOS:** Keychain para tokens; NSFileProtectionComplete para SQLite database.
- **Android:** EncryptedSharedPreferences para tokens; SQLCipher para SQLite database.

### 13.5 Autenticação

- **JWT** com assinatura HS256 (suficiente para MVP; migrar para RS256 se federarmos).
- **Biometria** opcional mas recomendada.
- **2FA:** Fora do MVP (apenas biometria local).
- **Sessão:** 15min access token, 7d refresh token.

---

## 14. Observabilidade

### 14.1 Pilares

| Pilar | Ferramenta | Propósito |
|-------|------------|-----------|
| **Crash Reporting** | Sentry | Detectar crashes nativos e JS |
| **Logs estruturados** | Console + Sentry | Debug em produção |
| **Tracing** | OpenTelemetry (preparado, sem backend ainda) | Latência de requests |
| **Métricas** | Sentry + custom | KPIs técnicos |
| **Analytics** | Eventos custom → backend (opt-in) | Uso de feature |
| **Feature Flags** | Self-hosted (Unleash) ou Firebase Remote Config | Rollouts graduais |

### 14.2 Eventos de analytics

```typescript
type AnalyticsEvent =
  | { type: 'app.open' }
  | { type: 'onboarding.complete' }
  | { type: 'session.start' | { protocolId: string; sessionId: string }}
  | { type: 'session.pause' | { sessionId: string; reason: 'user' | 'interruption' }}
  | { type: 'session.complete' | { sessionId: string; durationMs: number; cyclesCompleted: number }}
  | { type: 'session.cancel' | { sessionId: string; atCycle: number }}
  | { type: 'protocol.view' | { protocolId: string }}
  | { type: 'crash' | { error: string }}
  | { type: 'safety.trigger' | { rule: string; severity: 'info' | 'warn' | 'block' }};
```

### 14.3 Sentry setup

- DSN separado por ambiente (dev, staging, prod).
- Source maps uploaded em build.
- Sampling rate: 100% de crashes, 10% de transações.
- PII scrubbing ativado.

---

## 15. Estratégia de Testes

### 15.1 Pirâmide de testes

```
                    ┌─────────────┐
                    │     E2E     │  ← Poucos, smoke tests
                    ├─────────────┤
                    │ Integração  │  ← Serviços + Repositórios
                    ├─────────────┤
                    │    Unit     │  ← Engines, Use Cases, Utils
                    └─────────────┘
```

### 15.2 Cobertura alvo

| Camada | Cobertura |
|--------|-----------|
| **Domain** | 100% (regra de negócio crítica) |
| **Application** | 95% (use cases) |
| **Infrastructure** | 80% (adaptadores, integrações) |
| **Presentation** | 70% (componentes críticos; coverage baixa em UI trivial) |

### 15.3 Tipos de teste

| Tipo | Ferramenta | Escopo |
|------|------------|--------|
| **Unitário** | Jest | Engines, use cases, utils, validações |
| **Integração** | Jest + mocks | Repositórios com SQLite in-memory, API client com MSW |
| **Widget** | React Native Testing Library | Componentes visuais |
| **Snapshot** | Jest snapshot | Componentes estáveis (design system) |
| **E2E** | Maestro ou Detox | Fluxos críticos (onboarding, sessão completa) |
| **Performance** | Flashlight, custom timing | FPS, battery, memory |
| **Carga** | k6 (backend) | Requests por segundo sob carga |

### 15.4 Testes obrigatórios

**Engines do Core devem ter:**
- Testes de estado (transições válidas e inválidas).
- Testes de eventos (cada evento emitido no momento certo).
- Testes de edge cases (cancel, pause, resume, drift).
- Testes de determinismo (mesma entrada = mesma saída).

**Use Cases devem ter:**
- Testes de happy path.
- Testes de erro (validação, network failure).
- Testes de side effects (eventos emitidos, persistência).

### 15.5 Continuous Testing

- Cada PR roda unit + integration + lint + type check.
- Cada merge em main roda E2E + performance baseline.
- Cada release roda smoke completo + accessibility audit.

---

## 16. Performance — Metas

### 16.1 Mobile (Android e iOS)

| Métrica | Meta MVP | Meta v1.1 | Como medir |
|---------|----------|-----------|------------|
| **FPS durante sessão** | ≥ 55fps | ≥ 60fps | Flashlight |
| **RAM durante sessão** | ≤ 150MB | ≤ 120MB | Xcode Instruments / Android Profiler |
| **CPU médio** | ≤ 30% | ≤ 25% | Profiler |
| **Bateria (sessão 20min)** | ≤ 5% | ≤ 3% | Battery historian |
| **Cold start (login → home)** | ≤ 3s | ≤ 2s | Custom timing |
| **Time to first session** | ≤ 5s após onboarding | ≤ 3s | Custom timing |
| **Time to interactive (sessão)** | ≤ 1s após tap | ≤ 0.5s | Custom timing |
| **Bundle size (iOS)** | ≤ 30MB | ≤ 25MB | Build artifact |
| **Bundle size (Android)** | ≤ 25MB | ≤ 20MB | Build artifact (APK split) |

### 16.2 Backend (se houver partes próprias)

| Métrica | Meta |
|---------|------|
| **Latência P95** | < 300ms |
| **Latência P99** | < 1s |
| **Uptime** | ≥ 99.5% |
| **Error rate** | < 0.5% |

### 16.3 Performance Budget

A cada release, comparamos com baseline. Regressões > 10% bloqueiam merge.

---

## 17. Escalabilidade — Roadmap

### 17.1 Mobile

Mobile é stateless por design. Não há gargalo de escala horizontal no app.

### 17.2 Backend (se houver partes próprias)

| Cenário | Usuários ativos | Arquitetura |
|---------|-----------------|-------------|
| **MVP (0-6 meses)** | 10K | Postgres único + Redis + Sentry |
| **v1.1 (6-12 meses)** | 100K | Postgres + 1 read replica + Redis cluster |
| **v2 (12-24 meses)** | 1M | Postgres sharded by tenant + Redis + CDN |
| **v3 (24-36 meses)** | 10M | Multi-region + dedicated DB per region + advanced caching |

### 17.3 Estratégia de sharding

Sharding por **tenant** (clínica ou associação) quando > 1M usuários. Cada tenant tem dados isolados por design (LGPD facilita).

### 17.4 Cache strategy

- **L1:** SQLite local (offline-first).
- **L2:** Redis (sessão atual, rate limiting).
- **L3:** CDN (assets estáticos, áudio).
- **L4:** Postgres (cold storage).

### 17.5 Load balancer

- AWS ALB ou equivalente.
- Health checks a cada 10s.
- Auto-scaling baseado em CPU.

---

## 18. Deploy & Ambientes

### 18.1 Ambientes

| Ambiente | URL | Uso | Acesso |
|----------|-----|-----|--------|
| **dev** | localhost | Desenvolvimento local | Devs |
| **staging** | staging.araflow.app | Integração + QA | Devs + QA |
| **prod** | app.araflow.app | Produção | Usuários finais |
| **feature** | feature-X.araflow.app | Feature branches em preview | Devs + Stakeholders |
| **preview** | pr-123.araflow.app | Por PR | Devs |

### 18.2 Mobile release

| Stage | Plataforma | Ferramenta |
|-------|------------|------------|
| **Internal testing** | TestFlight (iOS), Internal track (Android) | Equipe |
| **Closed beta** | TestFlight (iOS), Closed alpha (Android) | 100-1000 usuários |
| **Open beta** | TestFlight (iOS), Open beta (Android) | Opt-in |
| **Production** | App Store + Play Store | Todos |

### 18.3 Release strategy

- **Mobile:** 2-week release cycle com feature flags para rollout gradual.
- **Backend:** Continuous deployment para staging; manual approval para prod.
- **Protocolos:** Hot-reload via Remote Config (sem nova versão do app).

---

## 19. CI/CD

### 19.1 Pipeline (GitHub Actions exemplo)

```yaml
# PR aberto
on: pull_request
jobs:
  validate:
    steps:
      - checkout
      - install
      - lint (eslint, prettier)
      - type-check (tsc)
      - unit-tests (jest)
      - integration-tests (jest)
      - build (verify it compiles)
      - security-scan (snyk)

# Merge em main
on: push to main
jobs:
  deploy-staging:
    steps:
      - checkout
      - install
      - all-tests (incluindo E2E)
      - build-staging
      - deploy-staging
      - smoke-tests
      - notify (Slack)

# Tag de release
on: tag
jobs:
  deploy-prod:
    steps:
      - checkout
      - install
      - all-tests
      - build-prod
      - deploy-canary (10% traffic)
      - monitor (15min)
      - deploy-full
      - notify
```

### 19.2 Quality Gates

PR não mergeia se:
- Lint falha.
- Type check falha.
- Cobertura < meta da camada.
- Algum teste falha.
- Build falha.
- Security scan tem high severity issue.

### 19.3 Rollback

- **Backend:** Deploy anterior reativado em < 5min.
- **Mobile:** Feature flags desativadas; bad release revertida em até 24h via emergency release.

---

## 20. Gestão de Configuração

### 20.1 Camadas de configuração

| Camada | Onde mora | Atualização | Quem controla |
|--------|-----------|-------------|--------------|
| **Build-time** | Bundle do app | Nova versão do app | Engenharia |
| **Remote Config** | Servidor | Tempo real (com cache local) | Engenharia + Produto |
| **Server-side** | Backend | Deploy | Engenharia |
| **User preference** | Local + sync | Imediato | Usuário |

### 20.2 Remote Config (Firebase ou self-hosted)

**O que vai no Remote Config:**
- Versão atual de cada protocolo.
- Lista de protocolos habilitados.
- Textos de onboarding (i18n).
- Limites do Safety Engine (max sessão, max sessões/dia).
- Feature flags.
- Preços e planos.
- A/B test variants.

**Schema:**
```typescript
interface RemoteConfig {
  protocols: {
    [protocolId: string]: {
      enabled: boolean;
      version: string;
      minAppVersion: string;
    };
  };
  safety: {
    maxSessionDurationMs: number;
    maxSessionsPerDay: number;
    maxSessionsPerHour: number;
  };
  features: {
    [featureName: string]: {
      enabled: boolean;
      rolloutPercentage: number;
    };
  };
  onboardingCopy: { [locale: string]: OnboardingCopy };
  abTests: { [testId: string]: ABTestVariant };
}
```

### 20.3 Versionamento

Remote Config é versionado. Cada mudança é commit com autor, motivo, e reversão fácil.

### 20.4 Cache local

Remote Config cached por 24h. Se servidor indisponível, usa cache. Cache invalidado por push notification crítica (apenas emergências).

---

## 21. Arquitetura para IA (Preparação)

**IA não entra no MVP. Mas a arquitetura prepara.**

### 21.1 Interfaces abertas

```typescript
// Engine pode ser plugado sem alterar Core
interface IProtocolRecommender {
  recommend(context: RecommendationContext): Promise<ProtocolRecommendation[]>;
}

interface IInsightGenerator {
  generate(sessions: Session[]): Promise<Insight[]>;
}

interface IRiskDetector {
  detect(sessions: Session[]): Promise<RiskSignal[]>;
}
```

### 21.2 Telemetria rica

Analytics Engine emite eventos ricos o suficiente para IA futura:
- Sessões com contexto completo.
- Padrões de uso.
- Abandono por etapa.
- Correlações humor/energia/tempo.

### 21.3 Privacy-safe data layer

Quando IA entrar, dados serão processados localmente (on-device) ou com anonymização diferencial. Arquitetura não depende de cloud AI.

### 21.4 Plugin pattern

IA implementa interfaces acima. Core não conhece implementação. IA pode ser trocada sem refatorar.

---

## 22. Arquitetura para Wearables (Preparação)

### 22.1 Abstração de sensores

```typescript
interface ISensorProvider {
  getHeartRate(): AsyncIterable<number>;
  getHRV(): AsyncIterable<number>;
  getRespirationRate(): AsyncIterable<number>;
  getMotion(): AsyncIterable<MotionSample>;
}

interface SensorProviderRegistry {
  register(name: string, provider: ISensorProvider): void;
  getActive(): ISensorProvider[];
}
```

### 22.2 Async boundary

Sensores rodam em thread separada. UI nunca bloqueia esperando sensor.

### 22.3 Watch app separado (futuro)

Quando tivermos watchOS / Wear OS app, ele se comunica via WatchConnectivity / Wearable Data Layer com o app principal. Core do mobile já está pronto.

### 22.4 Battery-aware

Sensors desligam quando app em background ou sessão não está rodando. Não desperdiça bateria.

---

## 23. Arquitetura para HRV (Preparação)

### 23.1 Time-series data structure

```typescript
interface HRVSample {
  timestamp: number; // monotonic
  rmssd: number; // ms
  sdnn: number; // ms
  source: 'apple-watch' | 'whoop' | 'manual' | 'polar' | 'garmin';
  confidence: number; // 0-1
}

interface HRVSession {
  userId: string;
  sessionId: string;
  startedAt: number;
  endedAt: number;
  samples: HRVSample[];
  aggregates: {
    meanRmssd: number;
    meanSdnn: number;
    trend: 'improving' | 'stable' | 'declining';
  };
}
```

### 23.2 Schema SQLite (preparado, não usado em MVP)

```sql
CREATE TABLE hrv_samples (
  session_id TEXT,
  timestamp INTEGER,
  rmssd REAL,
  sdnn REAL,
  source TEXT,
  confidence REAL,
  PRIMARY KEY (session_id, timestamp)
);
```

### 23.3 Cálculo de RMSSD/SDNN

Funções utilitárias puras (testáveis, sem side effects).

### 23.4 Visualização

Quando HRV entrar, Animation Engine pode adicionar visualização HRV. Core já suporta múltiplos "vizualizadores" sobre o mesmo estado.

---

## 24. Arquitetura para Apple Health / Health Connect (Preparação)

### 24.1 HealthKit (iOS)

```typescript
interface IHealthKitAdapter {
  requestAuthorization(): Promise<boolean>;
  writeBreathingSession(session: Session): Promise<void>;
  readHRV(date: Date): Promise<HRVSample[]>;
  readHeartRate(date: Date): Promise<HeartRateSample[]>;
}
```

Implementação via `react-native-health` ou wrapper nativo.

### 24.2 Health Connect (Android)

Mesma interface, implementação via `react-native-health-connect`.

### 24.3 Abstração

UI não conhece se dado vem de HealthKit ou Health Connect. Apenas consome `ISensorProvider`.

### 24.4 Permissões

Pedir apenas o necessário:
- HRV (opt-in).
- Frequência cardíaca (opt-in).
- Mindful minutes (write automático).

---

## 25. Dívida Técnica — Aceitável vs Inaceitável

### 25.1 Aceitável no MVP

✅ **Não ter offline-first para preferências de usuário.** Sincronização eventual.

✅ **Não ter framework de A/B testing.** Feature flags simples bastam.

✅ **Não ter MFA.** Biometria local é suficiente.

✅ **Não ter analytics preditivo.** Eventos básicos bastam.

✅ **Não ter CDN para áudio.** Bundle local é suficiente para 3 protocolos.

✅ **Não ter rate limiting sofisticado.** Rate limiting básico por IP.

✅ **Não ter disaster recovery automatizado.** Backup diário manual aceitável.

✅ **Não ter sharding.** Postgres único aguenta 100K.

### 25.2 Inaceitável (jamais, mesmo no MVP)

❌ **Hardcoded secrets em código.** Use variáveis de ambiente e vault.

❌ **Lógica de sync em componentes UI.** Sempre em camada de infraestrutura.

❌ **Acesso direto ao banco de dados de componentes UI.** Sempre via Repository pattern.

❌ **Números mágicos em protocolos.** Protocolos vêm de JSON validado, não de constantes.

❌ **Skip de testes em engines do Core.** 100% coverage obrigatório.

❌ **Telemetria sem opt-in.** LGPD art. 11.

❌ **Bloqueio de thread UI.** Async obrigatório.

❌ **Uso de `any` em TypeScript.** Tipagem estrita.

❌ **Mistura de camadas.** Domain nunca importa de Infrastructure.

❌ **Bypass de feature flags em produção.** Rollout gradual é proteção.

❌ **Persistência de PII em plain text.** Sempre criptografado.

❌ **Comentários "TODO" sem issue link.** Toda dívida técnica rastreada.

❌ **Deploy sem smoke test em staging.**

---

## 26. Top 50 Riscos Técnicos

> *Ordenados por criticidade.*

| # | Risco | Probabilidade | Impacto | Mitigação |
|---|-------|---------------|---------|-----------|
| 1 | **Drift entre timer e wall clock após background longo** | Alta | Alto | Wall-clock reconciliation na retomada |
| 2 | **Sessão interrompida por phone call (iOS)** | Alta | Médio | Audio session config + persist state |
| 3 | **Android Doze mode mata o app durante sessão** | Alta | Alto | Foreground service + notification persistente |
| 4 | **Audio lag maior que fase visual** | Média | Alto | Buffer extra de 200ms + drift correction |
| 5 | **Battery drain excessivo** | Média | Alto | Profile battery + otimizar render |
| 6 | **Memory leak em loop de animação** | Média | Alto | Unit tests + leak detection no CI |
| 7 | **SQLite corruption em crash** | Baixa | Alto | WAL mode + backup automático |
| 8 | **Sync conflict entre dispositivos** | Baixa | Médio | Last-write-wins + server reconciliation |
| 9 | **JWT expirado mid-session** | Média | Médio | Refresh token automático + buffer |
| 10 | **Sentry PII leak** | Baixa | Altíssimo | PII scrubbing ativado |
| 11 | **LGPD compliance audit falha** | Baixa | Altíssimo | DPO + auditoria externa pré-launch |
| 12 | **App Store rejection por claim de saúde** | Média | Alto | Compliance editorial + disclaimers |
| 13 | **Background audio interrompido por outro app** | Média | Médio | Audio focus handling + retry |
| 14 | **Bluetooth headphones latency** | Média | Médio | A/V offset calibration por dispositivo |
| 15 | **Different screen sizes quebram layout** | Alta | Médio | Responsive design + test on 10+ devices |
| 16 | **iOS permission prompt timing errado** | Média | Médio | Pedir permissão no momento de uso |
| 17 | **Android biometric não disponível** | Alta | Baixo | Fallback para PIN |
| 18 | **Protocol JSON inválido em runtime** | Baixa | Alto | Zod validation + fallback para bundled |
| 19 | **Remote Config server down** | Baixa | Médio | Cache local de 24h + bundled fallback |
| 20 | **CDN down para assets** | Baixa | Médio | Bundle local crítico + retry |
| 21 | **Crash on cold start em update** | Baixa | Alto | Versioned migrations + smoke test |
| 22 | **State loss on app kill durante sessão** | Média | Alto | Persist state a cada phase transition |
| 23 | **Animation jank em devices antigos** | Alta | Médio | Adaptive quality + minimum SDK target |
| 24 | **React Native bridge bottleneck** | Média | Médio | New Architecture quando estável |
| 25 | **Native module incompatível com nova OS** | Média | Alto | Suportar 2 últimas versões + deprecation |
| 26 | **Test coverage drift** | Alta | Médio | CI fails abaixo de threshold |
| 27 | **Flaky E2E tests bloqueando CI** | Alta | Médio | Retry + selective E2E |
| 28 | **Database migration falha em update** | Baixa | Alto | Tested migrations + rollback path |
| 29 | **Token storage em localStorage (XSS)** | Baixa | Alto | Secure storage only |
| 30 | **Open redirect em deep link** | Baixa | Alto | Whitelist de schemes |
| 31 | **Dependency vulnerability CVE** | Alta | Médio | Dependabot + audit |
| 32 | **Bundle size bloat** | Alta | Médio | Size limit no CI + lazy load |
| 33 | **Cold start > 5s em devices antigos** | Média | Médio | Lazy init + profile |
| 34 | **Memory leak em listeners não removidos** | Média | Alto | Lint rules + tests |
| 35 | **Race condition em state machine** | Média | Alto | State machine lib testada |
| 36 | **Type unsafety em JSON parsing** | Média | Alto | Zod em runtime |
| 37 | **Locale formatting errado** | Baixa | Baixo | i18n testing |
| 38 | **Accessibility broken em screen reader** | Média | Médio | A11y testing no CI |
| 39 | **Color contrast falha WCAG** | Baixa | Médio | Contrast checker no design system |
| 40 | **Form validation server-side mismatch** | Média | Médio | Shared schemas |
| 41 | **Push notification delay crítica** | Média | Alto | FCM/APNS com fallback |
| 42 | **App killed during sync upload** | Média | Médio | Persistent queue + retry |
| 43 | **Backend DB connection pool exhaustion** | Baixa | Alto | Connection pool sizing + monitoring |
| 44 | **Hot reload quebra sessão em dev** | Alta | Baixo | Disable HMR durante sessão em dev |
| 45 | **Code signing error bloqueia release** | Baixa | Alto | Automate signing + testing |
| 46 | **App size limit Android (16MB?** | Baixa | Médio | App Bundle + split |
| 47 | **Background fetch iOS limited** | Alta | Médio | BGTaskScheduler |
| 48 | **Memory pressure kills app** | Média | Alto | Memory warning handler |
| 49 | **Time zone change durante sessão** | Baixa | Baixo | Monotonic clock |
| 50 | **Hardware-specific bugs (Samsung, Xiaomi)** | Alta | Médio | Test em top 5 OEMs |

---

## 27. ADRs (Architecture Decision Records)

### ADR-001: Clean Architecture + Feature-Based Modules

**Problema:** Como organizar o código de mobile para que dure 10 anos?

**Alternativas:**
- MVC clássico
- MVVM
- Redux puro
- Clean Architecture
- Hexagonal

**Escolha:** Clean Architecture com Feature-Based modules.

**Consequências:**
- ✅ Isolamento de camadas permite trocar frameworks.
- ✅ Testabilidade alta.
- ✅ Time novo navega fácil.
- ⚠️ Mais código boilerplate.
- ⚠️ Requer disciplina para manter separação.

---

### ADR-002: Modular Monolith para Backend Próprio

**Problema:** Como estruturar backend AraFlow se houver partes próprias?

**Alternativas:**
- Microservices
- Serverless
- Modular Monolith
- Big Ball of Mud

**Escolha:** Modular Monolith.

**Consequências:**
- ✅ Time pequeno consegue manter.
- ✅ Refatoração interna é fácil.
- ✅ Deploy é simples.
- ⚠️ Escala vertical até certo ponto.
- ⚠️ Migração para microservices é custosa depois.

---

### ADR-003: JSON para Representação de Protocolos

**Problema:** Como representar protocolos clínicos?

**Alternativas:**
- JSON
- YAML
- Banco de dados
- Classes TypeScript

**Escolha:** JSON com schema Zod.

**Consequências:**
- ✅ Versionável.
- ✅ Hot-reload via Remote Config.
- ✅ Compartilhável entre mobile e backend.
- ⚠️ Validação runtime necessária.
- ⚠️ Sem tipos estáticos sem geração de código.

---

### ADR-004: WatermelonDB para Persistência Local

**Problema:** Como persistir dados offline-first em mobile?

**Alternativas:**
- AsyncStorage puro
- SQLite puro
- WatermelonDB
- Realm
- MMKV

**Escolha:** WatermelonDB (com fallback para SQLite puro se performance insuficiente).

**Consequências:**
- ✅ Reactive queries.
- ✅ Sync nativo (preparado para backend).
- ⚠️ Curva de aprendizado.
- ⚠️ Bundle size levemente maior.

---

### ADR-005: Redux Toolkit para Estado Global

**Problema:** Como gerenciar estado global complexo?

**Alternativas:**
- Context API puro
- Redux Toolkit
- Zustand
- Jotai
- MobX

**Escolha:** Redux Toolkit.

**Consequências:**
- ✅ Padrão conhecido.
- ✅ DevTools excelente.
- ✅ Time series de estado para debug.
- ⚠️ Boilerplate maior que Zustand.

---

### ADR-006: React Native para Mobile

**Problema:** iOS e Android em time pequeno?

**Alternativas:**
- Nativo iOS + Nativo Android
- React Native
- Flutter
- Kotlin Multiplatform

**Escolha:** React Native.

**Consequências:**
- ✅ Uma codebase.
- ✅ Time JavaScript/TypeScript.
- ✅ Hot reload rápido.
- ⚠️ Bridge performance (mitigado com New Architecture).
- ⚠️ Algumas APIs nativas exigem módulos customizados.

**Nota:** Se time tiver experiência nativa forte, reconsiderar.

---

### ADR-007: Master Clock Pattern para Sincronização

**Problema:** Como garantir que áudio, animação e timer estão sincronizados?

**Alternativas:**
- Cada componente tem seu próprio timer
- Event bus único
- Master clock centralizado

**Escolha:** Master Clock centralizado.

**Consequências:**
- ✅ Single source of truth.
- ✅ Drift corrigível.
- ⚠️ Ponto único de falha (mitigado com testes).

---

### ADR-008: Offline-First para Sessões

**Problema:** Sessão precisa funcionar sem rede?

**Alternativas:**
- Online-only
- Cache-then-network
- Offline-first

**Escolha:** Offline-first para sessões.

**Consequências:**
- ✅ UX confiável.
- ✅ Funciona em qualquer contexto.
- ⚠️ Sync mais complexo.
- ⚠️ Conflitos possíveis.

---

### ADR-009: Sentry para Crash Reporting

**Problema:** Como monitorar crashes em produção?

**Alternativas:**
- Crashlytics
- Sentry
- Bugsnag
- Self-hosted (GlitchTip)

**Escolha:** Sentry.

**Consequências:**
- ✅ Source maps upload automático.
- ✅ PII scrubbing.
- ✅ Performance monitoring incluso.
- ⚠️ Custo escala com uso.

---

### ADR-010: GitHub Actions para CI/CD

**Problema:** Pipeline de CI/CD?

**Alternativas:**
- GitHub Actions
- GitLab CI
- CircleCI
- Bitrise (mobile)

**Escolha:** GitHub Actions.

**Consequências:**
- ✅ Integração com GitHub.
- ✅ Marketplace grande.
- ⚠️ Custo por minuto (atenção em builds longos).

---

### ADR-011: OpenTelemetry para Tracing (Preparação)

**Problema:** Como rastrear requests cross-service?

**Alternativas:**
- OpenTelemetry
- Datadog APM
- New Relic

**Escolha:** OpenTelemetry (instrumentação preparada, backend depois).

**Consequências:**
- ✅ Padrão aberto.
- ✅ Vendor-neutral.
- ⚠️ Backend de tracing ainda não definido.

---

### ADR-012: Pluggable Engine Pattern

**Problema:** Como permitir adicionar engines sem refatorar?

**Alternativas:**
- Hard-coded dependencies
- Plugin registry
- Dependency injection container

**Escolha:** Plugin registry.

**Consequências:**
- ✅ Extensibilidade.
- ✅ Testabilidade.
- ⚠️ Descoberta de plugins em runtime.

---

### ADR-013: Remote Config para Conteúdo Dinâmico

**Problema:** Como atualizar textos, protocolos, preços sem release?

**Alternativas:**
- Bundle only
- Remote Config (Firebase ou self-hosted)
- CMS próprio

**Escolha:** Remote Config (Firebase RC ou self-hosted se LGPD exigir).

**Consequências:**
- ✅ Updates sem release.
- ✅ Rollout gradual.
- ✅ A/B testing possível.
- ⚠️ Schema management necessário.

---

### ADR-014: LGPD Compliance via Opt-In Layers

**Problema:** Como garantir LGPD?

**Alternativas:**
- Opt-out
- Opt-in granular
- Opt-in bloqueante

**Escolha:** Opt-in granular por categoria.

**Consequências:**
- ✅ Compliance robusto.
- ✅ Transparência ao usuário.
- ⚠️ Reduz dados coletados inicialmente.

---

### ADR-015: State Machine para Sessão

**Problema:** Como modelar ciclo de vida da sessão?

**Alternativas:**
- If/else em variáveis
- State machine lib (XState)
- Redux puro

**Escolha:** State machine (XState se complexidade justificar, senão FSM caseiro).

**Consequências:**
- ✅ Transições explícitas.
- ✅ Testável.
- ✅ Visível em DevTools.

---

## 28. Parecer Final do CTO

### Pergunta do Conselho Técnico:

> *"Estou confortável para iniciar a implementação?"*

### Resposta do CTO:

# SIM, COM RESSALVAS.

---

### Por que SIM

1. **Produto está congelado.** Decisões de produto estão tomadas. Implementação pode começar sem ambiguidade.
2. **Arquitetura é defensável.** Clean Architecture + Feature Modules + Offline-First sobrevive a 10 anos.
3. **Core é isolado.** Os 8 engines são testáveis, substituíveis, e independentes de framework.
4. **Performance tem metas claras.** 60fps, <150MB, <5% bateria são alcançáveis com arquitetura proposta.
5. **LGPD está no design.** Não é afterthought.
6. **Escalabilidade tem caminho.** 10K → 10M com estratégia clara.
7. **Riscos estão mapeados.** Top 50 com mitigações.
8. **Dívida técnica está classificada.** MVP aceita; jamais nunca.
9. **ADRs estão documentados.** Time novo consegue navegar.
10. **Preparação para futuro.** IA, wearables, HRV, Apple Health têm ganchos arquiteturais.

### As 5 Ressalvas (que devem ser resolvidas em até 30 dias)

#### Ressalva 1: Decisão React Native vs Nativo

**Status:** Pendente.
**Justificativa:** A escolha de React Native está tomada, mas exige validação com time. Se time tem forte experiência nativa (Swift/Kotlin), reconsiderar para iOS+Android nativos separados. **Decisão final em 2 semanas com protótipo.**

#### Ressalva 2: Backend ownership

**Status:** Pendente.
**Justificativa:** A documentação assume que backend principal está em AraOS. Confirmar com time AraOS quais endpoints AraFlow consome e quais AraFlow precisa criar. **Reunião de alinhamento em 1 semana.**

#### Ressalva 3: Time para implementar

**Status:** Pendente.
**Justificativa:** Time de 8 FTEs está dimensionado para MVP em 6 meses. Validar composição real:
- 1 CTO
- 1 designer UX
- 1 médico clínico part-time
- 2 devs mobile
- 1 dev backend (se houver)
- 1 devops part-time
- 1 QA

Se algum desses papéis faltar, cronograma pode deslizar. **Validação em 2 semanas.**

#### Ressalva 4: Dependências externas

**Status:** Pendente.
**Justificativa:** Sentry, Firebase Remote Config, WatermelonDB são dependências externas. Confirmar contratos com fornecedores. LGPD pode exigir self-hosted para alguns (Sentry self-hosted ou equivalente brasileiro). **Decisão em 3 semanas.**

#### Ressalva 5: Ambientes de homologação

**Status:** Pendente.
**Justificativa:** Ambientes dev/staging/prod precisam estar prontos antes de começar desenvolvimento pesado. **Setup em paralelo durante sprint 0.**

### O que NÃO está pendente

- ✅ Decisão arquitetural central (Clean Architecture).
- ✅ Estrutura de pastas.
- ✅ Definição dos 8 engines.
- ✅ Estratégia de sincronização.
- ✅ Persistência e schema.
- ✅ LGPD compliance.
- ✅ Estratégia de testes.
- ✅ Metas de performance.
- ✅ Roadmap de escalabilidade.
- ✅ Pipeline de CI/CD.
- ✅ Top 50 riscos com mitigações.
- ✅ ADRs principais.

### Cronograma recomendado

| Sprint | Duração | Entregável |
|--------|---------|------------|
| **Sprint 0** | 2 semanas | Setup (ambientes, CI, dependências, ADRs) |
| **Sprint 1** | 2 semanas | Core: Timer Engine + Breath Engine com testes |
| **Sprint 2** | 2 semanas | Core: Protocol Engine + Session Engine |
| **Sprint 3** | 2 semanas | Core: Audio + Animation + Safety Engines |
| **Sprint 4-5** | 4 semanas | Mobile: Onboarding + Session screens |
| **Sprint 6-7** | 4 semanas | Mobile: LGPD, biometria, persistência |
| **Sprint 8** | 2 semanas | Integração com AraOS |
| **Sprint 9** | 2 semanas | Testes E2E + performance baseline |
| **Sprint 10** | 2 semanas | Beta interno |
| **Sprint 11** | 2 semanas | Lançamento beta externo |

**Total:** 26 semanas (6 meses) para MVP.

### Recomendação ao Conselho Técnico

**Autorizar início do desenvolvimento.**

**Condições:**
1. Resolver as 5 ressalvas em até 30 dias.
2. Sprint 0 (setup) deve começar imediatamente.
3. Apresentação de progresso semanal ao Conselho.
4. Este documento (33) é revisado apenas em 12 meses.

**Próximo marco de decisão:** Final do Sprint 0 (após setup) + início do Sprint 1.

---

### Frase final do CTO

> *A arquitetura é uma promessa. Prometemos que o AraFlow será simples de manter, simples de testar, e simples de evoluir pelos próximos 10 anos. Para cumprir essa promessa, precisamos de três coisas: disciplina para manter separação de camadas, coragem para recusar atalhos que virem dívida, e paciência para não cair em modismos. Este documento é o contrato. Honraremos.*

---

**Assinado:**

Chief Technology Officer (CTO)
AraFlow — Conselho Técnico

Data: 2026-06-25
Versão: 1.0.0 — Constituição Técnica
Próxima revisão: 2027-06-25 (apenas em 12 meses)

**Status: CONGELADO. Implementação autorizada condicionalmente.**

---

**Apêndice: Este documento é parte da Constituição do AraFlow v1.0 junto com o documento 32 (Decisões de Produto). Toda decisão arquitetural subsequente deve:**

1. **Ser proposta formalmente** com problema + alternativas + escolha + consequências.
2. **Ter ADR correspondente** salvo em `docs/araflow/adr/`.
3. **Não contradizer** este documento.
4. **Ter aprovação do CTO** antes de ser mergeada.