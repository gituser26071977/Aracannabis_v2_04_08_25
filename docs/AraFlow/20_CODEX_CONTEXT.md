# AraFlow — Contexto para Implementação (Codex)

> **Versão:** 0.1.0
> **Data:** 2026-06-24
> **Owner:** Tech Lead
>
> Este documento é a **porta de entrada** para qualquer agente de IA que for implementar o AraFlow no futuro. Ele consolida a essência do produto e aponta para os documentos detalhados.

---

## Sumário

1. Propósito deste documento
2. Resumo executivo do AraFlow
3. Stack tecnológica esperada
4. Princípios inegociáveis
5. Arquitetura lógica
6. Mapa dos documentos
7. Glossário de termos
8. Restrições regulatórias
9. Critérios de qualidade
10. Como começar a implementação
11. Armadilhas comuns
12. Decisões já tomadas
13. Pontos abertos (precisam de decisão)
14. Definição de pronto (DoD)
15. Como contribuir

---

## 1. Propósito deste documento

Este é o documento que um **Codex** (ou outro agente de IA) deve ler **antes** de qualquer tarefa de implementação. Ele contém:

- Contexto de negócio suficiente para tomar decisões técnicas coerentes.
- Princípios inegociáveis.
- Mapa de documentos para detalhes.
- Avisos sobre armadilhas comuns.

> **Se você (Codex) tiver dúvida, volte a este documento primeiro.**

---

## 2. Resumo executivo do AraFlow

**O que é:** Plataforma digital de **neuroregulação baseada em evidências**, módulo do AraOS.

**Para quem:**
- Pacientes (com prescrição ou uso livre).
- Profissionais de saúde (médicos, psicólogos, fisioterapeutas).
- Clínicas e instituições.

**O que entrega:**
- 12+ protocolos clínicos de respiração.
- Sessões com visual animado + áudio terapêutico.
- Modos especiais (SOS, Idoso, Infantil).
- Prescrição e acompanhamento.
- LGPD completo.
- Acessibilidade WCAG AA.

**O que NÃO é:**
- Não é um app genérico de bem-estar.
- Não substitui psicoterapia.
- Não é um dispositivo médico no MVP.
- Não é uma ferramenta de diagnóstico.

**Fase atual:** F0 — Discovery + Arquitetura. **Não implementar antes da Fase 1.**

---

## 3. Stack tecnológica esperada

> Alinhamento com AraOS. Valores entre parênteses são preferenciais; ajustes permitidos com justificativa.

### 3.1 Backend
- **Linguagem:** Python (FastAPI) ou Node.js (NestJS) ou Go.
- **Banco:** PostgreSQL 15+.
- **Cache:** Redis.
- **Fila:** RabbitMQ ou Kafka (eventos clínicos).
- **Séries temporais (Fase 3):** TimescaleDB.
- **Storage:** S3 / GCS.

### 3.2 Frontend
- **Framework:** React (preferencial) ou Next.js.
- **Mobile:** PWA (MVP); React Native ou nativo (Fase 2+).
- **Estado:** Redux Toolkit ou Zustand.
- **Estilo:** Tailwind ou Emotion (alinhado ao AraOS).
- **Animações:** Framer Motion + Lottie.

### 3.3 Infraestrutura
- **Cloud:** AWS, GCP ou similar (multi-cloud possível).
- **Container:** Docker + Kubernetes (EKS/GKE).
- **CI/CD:** GitHub Actions ou GitLab CI.
- **Monitoramento:** Datadog, Grafana, Sentry.
- **Logs:** CloudWatch ou Stackdriver.

### 3.4 Áudio
- Streaming: HLS / DASH.
- Formatos: AAC (streaming), FLAC (download), MP3 fallback.
- Processamento: ffmpeg (transcoding).

### 3.5 IA (Fase 2+)
- Treino: scikit-learn, XGBoost, LightGBM.
- Deep learning (Fase 3): PyTorch.
- LLM (Fase 3): Claude / GPT via API com guardrails.
- Serving: BentoML ou Seldon.

---

## 4. Princípios inegociáveis

1. **Privacidade por padrão (LGPD).**
2. **Acessibilidade WCAG 2.1 AA como piso.**
3. **Segurança clínica antes de feature.**
4. **Sem dark patterns.**
5. **Não substituir o profissional de saúde.**
6. **Sem gamificação monetária.**
7. **Não viciar; ajudar.**
8. **Funciona offline (sessão completa).**
9. **Logs clínicos imutáveis.**
10. **Documentação sempre atualizada.**

---

## 5. Arquitetura lógica

```
┌─────────────────────────────────────────────┐
│              AraOS (plataforma)              │
│                                              │
│  ┌──────────────────────────────────────┐    │
│  │         Módulo AraFlow               │    │
│  │                                      │    │
│  │  ┌────────────┐  ┌────────────┐     │    │
│  │  │  Paciente  │  │ Profissional│    │    │
│  │  └─────┬──────┘  └─────┬──────┘     │    │
│  │        │                │           │    │
│  │        └─────┬──────────┘           │    │
│  │              │                      │    │
│  │       ┌──────┴────────┐             │    │
│  │       │  Core (Sessão,│             │    │
│  │       │  Protocolo,   │             │    │
│  │       │  Prescrição)  │             │    │
│  │       └──────┬────────┘             │    │
│  │              │                      │    │
│  │  ┌───────────┼───────────┐          │    │
│  │  │           │           │          │    │
│  │  │           │           │          │    │
│  │  ▼           ▼           ▼          │    │
│  │ Áudio      Visual      IA           │    │
│  │ Service    Engine      Service      │    │
│  │                                      │    │
│  └──────────────────────────────────────┘    │
│                                              │
└─────────────────────────────────────────────┘
```

### 5.1 Componentes principais

| Componente | Responsabilidade |
|------------|-------------------|
| **Auth Service** | SSO AraOS, sessões, MFA |
| **Patient Service** | Perfil, consentimentos |
| **Protocol Service** | Catálogo, versionamento |
| **Prescription Service** | Prescrições, doses, vínculos |
| **Session Service** | Player state, registro de sessões |
| **Adherence Service** | Streak, adesão, agregados |
| **Scale Service** | Escalas clínicas (Fase 2) |
| **Audio Service** | Streaming, cache, narração |
| **Visual Engine** | Renderização do visual respiratório |
| **AI Service** | Recomendações, insights (Fase 2+) |
| **Biofeedback Service** | HRV, coerência (Fase 3) |
| **Notification Service** | Push, e-mail, lembretes |
| **Consent Service** | LGPD, export, delete |
| **Audit Service** | Logs imutáveis |
| **Analytics Service** | Eventos, dashboards |
| **Admin Service** | Gestão interna |

---

## 6. Mapa dos documentos

| # | Documento | Para que serve |
|---|-----------|-----------------|
| 00 | `00_VISION.md` | Entender o "porquê" do AraFlow |
| 01 | `01_PRD.md` | Requisitos funcionais e não-funcionais |
| 02 | `02_USER_PERSONAS.md` | Conhecer os usuários |
| 03 | `03_USER_JOURNEY.md` | Fluxos de uso |
| 04 | `04_INFORMATION_ARCHITECTURE.md` | Mapa do site, navegação |
| 05 | `05_WIREFRAMES.md` | Wireframes ASCII das telas |
| 06 | `06_DESIGN_SYSTEM.md` | Cores, tipografia, componentes |
| 07 | `07_BREATH_PROTOCOLS.md` | Protocolos clínicos (ficha completa) |
| 08 | `08_AUDIO_SYSTEM.md` | Áudio terapêutico |
| 09 | `09_ANIMATION_SYSTEM.md` | Animações respiratórias |
| 10 | `10_GAMIFICATION.md` | Gamificação leve |
| 11 | `11_ANALYTICS.md` | Métricas e eventos |
| 12 | `12_AI.md` | IA (futuro) |
| 13 | `13_DATABASE_MODEL.md` | Modelo de dados |
| 14 | `14_API_SPECIFICATION.md` | API REST |
| 15 | `15_SECURITY.md` | Segurança e LGPD |
| 16 | `16_ROADMAP.md` | Roadmap por fase |
| 17 | `17_BACKLOG.md` | Backlog priorizado |
| 18 | `18_MVP.md` | Definição exata do MVP |
| 19 | `19_FUTURE_FEATURES.md` | Features pós-MVP |
| 20 | `20_CODEX_CONTEXT.md` | Este documento |

### 6.1 Ordem de leitura sugerida

1. `00_VISION.md`
2. `01_PRD.md`
3. `02_USER_PERSONAS.md`
4. `03_USER_JOURNEY.md`
5. `05_WIREFRAMES.md`
6. `06_DESIGN_SYSTEM.md`
7. `07_BREATH_PROTOCOLS.md`
8. `18_MVP.md` ← foco principal
9. `13_DATABASE_MODEL.md`
10. `14_API_SPECIFICATION.md`
11. `15_SECURITY.md`

---

## 7. Glossário de termos

| Termo | Significado |
|-------|-------------|
| **AraFlow** | Este produto |
| **AraOS** | Plataforma-mãe |
| **Protocolo** | Técnica de respiração parametrizada |
| **Sessão** | Execução de um protocolo por um paciente |
| **Prescrição** | Indicação clínica de uso |
| **Adesão** | Cumprimento da prescrição |
| **Streak** | Dias consecutivos com sessão |
| **Coerência cardíaca** | Estado de sincronia autonômica (5,5 resp/min) |
| **HRV** | Variabilidade da frequência cardíaca |
| **GAD-7** | Escala de ansiedade (Fase 2) |
| **ISI** | Índice de gravidade de insônia (Fase 2) |
| **PSS-10** | Escala de estresse percebido (Fase 2) |
| **EVA** | Escala visual analógica de dor |
| **Visual respiratório** | Animação que guia a respiração |
| **SOS** | Modo de crise aguda |
| **Módulo** | Sub-aplicação do AraOS |

---

## 8. Restrições regulatórias

### 8.1 MVP
- **Classificar como software de bem-estar** (wellness device).
- **Não fazer diagnóstico.**
- **Não sugerir medicação.**
- **Sempre exibir disclaimer de "não substitui profissional".**
- **LGPD 100% desde o dia 1.**

### 8.2 Futuras
- Avaliar SaMD (Fase 3).
- ANVISA (Fase 3).
- GDPR (se expandir para UE).

### 8.3 O que nunca fazer

- ❌ Diagnosticar.
- ❌ Recomendar dose de medicação.
- ❌ Comentar sobre outros profissionais.
- ❌ Avaliar gravidade clínica sem contexto.
- ❌ Compartilhar dados sem consentimento.
- ❌ Treinar modelos com dados identificáveis sem revisão do DPO.

---

## 9. Critérios de qualidade

### 9.1 Código
- Cobertura de testes ≥ 80% em lógica de negócio.
- Lint obrigatório (lint-staged em pre-commit).
- TypeScript quando possível.
- Revisão por 1+ engenheiro.
- Commits semânticos.

### 9.2 UX
- Acessibilidade WCAG AA validada em todas as telas principais.
- Testes com usuários reais (≥ 5 por persona).
- Latência percebida < 100ms em interações.

### 9.3 Segurança
- SAST em CI.
- DAST semanal.
- Pentest anual.
- 0 vulnerabilidades P0/P1.

### 9.4 Performance
- Lighthouse Performance ≥ 85.
- LCP < 2.5s.
- INP < 200ms.
- CLS < 0.1.

### 9.5 Privacidade
- 0 incidentes de vazamento.
- 100% de cobertura de consent log.
- DPO aprova qualquer mudança de schema.

---

## 10. Como começar a implementação

> **Não implementar antes da aprovação do discovery (Fase 0) e do kick-off (Fase 1).**

### 10.1 Antes de começar

1. Leia `00_VISION.md` para entender o porquê.
2. Leia `18_MVP.md` para saber o escopo exato.
3. Leia `13_DATABASE_MODEL.md` para o modelo de dados.
4. Leia `14_API_SPECIFICATION.md` para o contrato de API.
5. Leia `15_SECURITY.md` para os controles obrigatórios.
6. Leia `06_DESIGN_SYSTEM.md` para o visual.
7. Leia `05_WIREFRAMES.md` para a UI.

### 10.2 Primeiros passos sugeridos

1. **Setup do repositório** (alinhado ao AraOS).
2. **Configurar CI/CD** com testes + lint + SAST.
3. **Modelar banco de dados** (vide `13_DATABASE_MODEL.md`).
4. **Implementar autenticação** via SSO AraOS.
5. **Seed da biblioteca de protocolos** (12 protocolos).
6. **Implementar player de sessão** (state machine).
7. **Implementar visual respiratório** (círculo).
8. **Implementar áudio** (12 trilhas + narração).
9. **Implementar modos especiais** (SOS, Idoso, Infantil).
10. **Implementar prescrição** (profissional).
11. **Implementar LGPD** completo.
12. **Implementar analytics essenciais**.
13. **Implementar acessibilidade**.
14. **QA + beta fechado**.
15. **Lançamento**.

### 10.3 Dependências externas (verificar antes)

| Dependência | Owner | Status |
|-------------|-------|--------|
| SSO AraOS | Time AraOS | Contato direto |
| Modelo de módulos AraOS | Time AraOS | Em definição |
| Pacote de áudio royalty-free | Produto | Licenciado |
| Locutor PT-BR | Produto | Contratado |
| Revisor clínico dos protocolos | Diretor clínico | Confirmado |

---

## 11. Armadilhas comuns

| Armadilha | Como evitar |
|----------|-------------|
| Criar dependência da estrutura do AraOS | Usar contratos; não acoplar internals. |
| Implementar IA antes de ter dados | F1 sem IA; F2 com regras; F3 com ML. |
| Misturar lógica clínica com UI | Service layer dedicado. |
| Quebrar LGPD por esquecimento | DPO revisa PRs com dados sensíveis. |
| Streak que pune | Testar com pacientes reais. |
| Visual que distrai | Testar com idosos e TDAH. |
| Áudio que compete com respiração | Volume relativo; mute fácil. |
| Acessibilidade como afterthought | Implementar desde o início. |
| Ignorar offline | Sessão deve funcionar 100% offline. |
| Tradução automática de escalas clínicas | Usar traduções validadas. |
| Notificações intrusivas | Limites éticos. |
| Monetização antiética | Não fazer. |

---

## 12. Decisões já tomadas

> Estas decisões **não devem ser mudadas** sem aprovação do comitê.

1. **Stack alinhada ao AraOS** (vide § 3).
2. **Classificação regulatória no MVP:** software de bem-estar.
3. **12 protocolos** específicos (vide `07_BREATH_PROTOCOLS.md`).
4. **LGPD 4 categorias** de consentimento.
5. **Janela de exclusão: 60 dias** de carência.
6. **WCAG AA** como piso.
7. **Funciona offline** (sessão completa).
8. **Sem gamificação monetária.**
9. **Sem ranking competitivo.**
10. **Não viciar; ajudar.**

---

## 13. Pontos abertos (precisam de decisão)

| Ponto | Quem decide | Quando |
|-------|-------------|--------|
| Stack final do backend | Tech Lead | Antes da F1 |
| Stack final do frontend | Tech Lead + UX | Antes da F1 |
| Fornecedor de música royalty-free | Produto | Antes da F1 |
| Revisor clínico dos protocolos | Diretor clínico | Antes do seed |
| Modelo de módulos AraOS | Time AraOS | Antes da F1 |
| Classificação regulatória formal | DPO + jurídico | Antes do beta |
| Nuvem (AWS vs GCP vs outro) | Tech Lead + SRE | Antes da F1 |
| Política de DPO interno | Diretor | Antes do beta |

> **Codex NÃO deve tomar essas decisões sozinho.** Deve perguntar ao Tech Lead.

---

## 14. Definição de pronto (DoD)

Para qualquer feature ser considerada "pronta":

- [ ] Código revisado por 1+ engenheiro.
- [ ] Testes unitários (≥ 80% cobertura em lógica de negócio).
- [ ] Testes de integração (fluxo principal).
- [ ] Testes de segurança (autorização).
- [ ] Acessibilidade verificada (quando aplicável).
- [ ] Documentação atualizada.
- [ ] Eventos de analytics implementados.
- [ ] Logs clínicos gerados (quando aplicável).
- [ ] QA aprovado.
- [ ] PM aceitou.
- [ ] Sem warnings de lint.
- [ ] Sem dependências vulneráveis.

---

## 15. Como contribuir

### 15.1 Repositório

- Seguir padrão do AraOS (alinhamento).
- Branch por feature.
- PR com descrição + screenshots.
- CI verde obrigatório.

### 15.2 Commits

Formato convencional:

```
tipo(escopo): descrição curta

Descrição longa opcional.

Refs: #issue
```

Tipos: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`, `security`.

### 15.3 Pull Requests

- 1 reviewer mínimo.
- DPO revisa mudanças com dados clínicos.
- Tech Lead revisa mudanças de arquitetura.

### 15.4 Documentação

- Toda nova feature atualiza docs relevantes.
- Toda decisão é registrada em ADR (Architecture Decision Record).

---

## 16. Comandos úteis (sugestão)

> Estes comandos pressupõem alinhamento com AraOS. Adaptar conforme necessário.

```bash
# Setup
make setup

# Dev
make dev

# Testes
make test
make test:e2e
make test:security

# Lint + format
make lint
make format

# Build
make build

# Deploy
make deploy:staging
make deploy:production
```

---

## 17. Checklist rápido do Codex

Antes de implementar qualquer feature, confirme:

- [ ] Li `00_VISION.md` e `18_MVP.md`.
- [ ] Estou dentro do escopo do MVP (ou fase apropriada).
- [ ] Tenho o modelo de dados correto.
- [ ] Tenho o contrato de API correto.
- [ ] Respeitei LGPD.
- [ ] Implementei acessibilidade.
- [ ] Adicionei testes.
- [ ] Documentei mudanças.
- [ ] Não inventei features fora do escopo.

> Se qualquer item estiver **não**, **pare e pergunte**.

---

## 18. Quando NÃO começar a implementação

- ❌ Antes da aprovação formal do discovery (F0).
- ❌ Sem o kick-off da Fase 1.
- ❌ Sem o conjunto de 12 protocolos revisado por profissional.
- ❌ Sem a biblioteca de áudio licenciada.
- ❌ Sem o ambiente de homologação configurado.
- ❌ Sem o DPO designado.

---

## 19. Filosofia de implementação

> **Cuide primeiro. Features depois.**

A primeira implementação do AraFlow deve:

1. Ser pequena o suficiente para validar com cuidado.
2. Ser segura o suficiente para colocar em produção.
3. Ser acessível o suficiente para servir qualquer pessoa.
4. Ser clínica o suficiente para merecer confiança.
5. Ser privada o suficiente para merecer respeito.

> **O AraFlow é uma ferramenta de cuidado. Implemente com cuidado.**

---

*Fim do documento. Boa implementação.*