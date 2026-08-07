# AraFlow

> **Status:** Fase 1.0 — Sprint 0 (Foundation) **Constituição:**
> `docs/AraFlow/32_FINAL_PRODUCT_DECISIONS.md` +
> `docs/AraFlow/33_ENGINEERING_BLUEPRINT.md` **Próximo marco:** Sprint 1 (Timer
> Engine)

AraFlow é o **módulo de neuroregulação digital** da plataforma AraOS. Aplicativo
mobile (iOS + Android) que oferece sessões de respiração guiadas para regulação
autonômica (ansiedade, estresse, foco, sono).

Este repositório é um **monorepo** com três workspaces:

| Workspace           | Função                                                     |
| ------------------- | REDACTED |
| `mobile/`           | App React Native (iOS + Android). O produto.               |
| `backend/`          | Fastify. Apenas para endpoints não cobertos pelo AraOS.    |
| `shared-contracts/` | Tipos e schemas Zod compartilhados entre mobile e backend. |

## Quick start

```bash
nvm use                    # Node 20.18.0
npm install                # Instala deps do monorepo
npm run prepare            # Configura Husky
npm test                   # Roda testes
npm run lint               # Lint
npm run typecheck          # Type check
```

Para rodar o mobile:

```bash
cd mobile
npm run start              # Metro
npm run ios                # iOS simulator
npm run android            # Android emulator
```

## Documentação

| Doc                  | Conteúdo                                               |
| -------------------- | REDACTED |
| `docs/AraFlow/00-20` | Visão, PRD, design system, protocolos (Fase 0.0)       |
| `docs/AraFlow/21-30` | Validação clínica (Fase 0.5)                           |
| `docs/AraFlow/31`    | Red Team Audit                                         |
| `docs/AraFlow/32`    | Decisões de Produto (CPO)                              |
| `docs/AraFlow/33`    | Engineering Blueprint (CTO) — **Constituição Técnica** |
| `docs/AraFlow/34`    | Relatório de implementação da Sprint 0                 |
| `docs/adr/araflow/`  | Architecture Decision Records                          |

## Arquitetura

**Clean Architecture + Feature-Based Modules + Offline-First.**

- `mobile/src/core/` — AraFlow Core (8 engines)
- `mobile/src/features/` — Features verticais
- `mobile/src/shared/` — Design system, i18n, types, utils
- `mobile/src/infrastructure/` — Adapters (HTTP, persistence, audio, etc.)
- `shared-contracts/` — Tipos compartilhados

## Status

| Sprint | Status   | Descrição                             |
| ------ | -------- | REDACTED |
| 0      | ✅       | Foundation (este sprint)              |
| 1      | Pendente | Timer Engine                          |
| 2      | Pendente | Breath Engine                         |
| 3      | Pendente | Protocol Engine                       |
| 4      | Pendente | Session Engine                        |
| 5      | Pendente | Audio Engine                          |
| 6      | Pendente | Animation Engine                      |
| 7      | Pendente | Analytics + Safety Engines            |
| 8–11   | Pendente | Onboarding, Session, History, Profile |
| 12+    | Pendente | Dashboard, integrações AraOS          |

## Princípios

1. **Strict TypeScript** — Sem `any`. Sem `@ts-ignore` sem justificativa.
2. **Testes obrigatórios** — Domain 100% coverage.
3. **Sem TODO em produção** — Use `NotImplementedError` se stubar.
4. **LGPD by design** — Opt-in explícito por categoria.
5. **i18n sempre** — Nunca hard-code strings visíveis ao usuário.

## Licença

Proprietary. AraCannabis SO LTDA.

## Certificação Digital — Bird ID (CESS)

Assinatura digital de prescrições, laudos e relatórios via **Bird ID / Soluti**
(Cloud Electronic Signature Service — CESS).

### Configuração

1. **Credenciais corporativas** (contrato Soluti/Bird ID) no `.env.production`
   do VPS:

   ```
   BIRD_ID_CLIENT_ID=<client_id corporativo>
   BIRD_ID_CLIENT_SECRET=<client_secret corporativo>
   BIRD_ID_BASE_URL=https://cess.lab.vaultid.com.br   # produção: https://cess.vaultid.com.br
   ```

2. **Por profissional** (tela `/certificacao-digital` → Gestão → Certificação
   Digital):
   - preencha o `certificate_alias` do certificado Bird ID do profissional
   - (opcional) credenciais próprias se não usar as corporativas globais

### Fluxo

`assinar` → cria transação (TCN) + upload → o profissional **valida no app Bird
ID** (push/QR) → o frontend faz polling em `assinatura/<tcn>` → baixa o PDF
assinado em `assinatura/<tcn>/download`.
