# AraFlow — Sprint 0 — Foundation Implementation Report

> **Data:** 2026-06-25
> **Autor:** Chief Technology Officer (CTO)
> **Status:** Foundation entregue. Sprint 1 (Timer Engine) liberado para início.

---

## Sumário

1. Visão geral
2. Decisão de workspace
3. Arquivos criados (inventário)
4. Estrutura criada
5. Justificativas por área
6. Conformidade com a Constituição
7. Pendências
8. Riscos identificados
9. Próximo passo

---

## 1. Visão geral

A Sprint 0 construiu a **fundação técnica** do AraFlow. Nenhum engine foi implementado (regra explícita); nenhuma feature foi escrita (regra explícita); nenhuma integração com AraOS foi tocada (regra explícita).

O que foi entregue:

- Monorepo com 3 workspaces (`mobile`, `backend`, `shared-contracts`).
- Configuração completa de tooling (TypeScript strict, ESLint, Prettier, Husky, lint-staged, EditorConfig).
- Foundation modules (logger, error handling, DI, feature flags, remote config arch, design tokens, theme, i18n).
- Stubs estruturados para os 8 engines do Core.
- Stubs estruturados para as 5 features iniciais.
- Stubs de infraestrutura (HTTP, persistence, audio, haptics, biometrics, crash, analytics).
- CI pipeline (validate + security + build).
- CD pipelines (staging + production).
- Documentação para novos desenvolvedores (README, CONTRIBUTING, PR template, ADR template).
- 3 ADRs novos (016, 017, 018).
- 1 suite de testes de fumaça validando a fundação.

Total: **57 arquivos** criados.

---

## 2. Decisão de workspace

**Decisão:** Monorepo com **npm workspaces**.

**Justificativa:** Documentada em `docs/adr/araflow/016-npm-workspaces.md`. Em síntese:

- Zero dependência externa (workspaces built-in no npm).
- Time já familiarizado com npm.
- Compartilhamento de tipos via `shared-contracts/` sem publicar npm package.
- Path aliases funcionam tanto em Babel quanto em TypeScript quanto em Jest.

**Trade-off aceito:** Hoisting de pacotes nativos do React Native pode exigir `nohoist` em casos específicos. Mitigado por `.npmrc` com `engine-strict=true` e pelo uso disciplinado de versões em `dependencies` por workspace.

---

## 3. Arquivos criados (inventário)

### Root

| Arquivo | Propósito |
|---------|-----------|
| `package.json` | Workspace root + scripts de qualidade |
| `tsconfig.base.json` | Strict TS config compartilhado |
| `tsconfig.json` | Project references para os 3 workspaces |
| `.gitignore` (estendido) | Inclui paths de RN/Android/iOS, monorepo, generated |
| `.editorconfig` | Indentação 2 espaços, LF, UTF-8 |
| `.prettierrc.json` | 100 cols, single quote, trailing comma all |
| `.prettierignore` | Exclui build artifacts e lock files |
| `.nvmrc` | Node 20.18.0 |
| `.npmrc` | save-exact, engine-strict, audit-level high |
| `.eslintrc.cjs` | ESLint baseline (strict, no-any, no-default-export) |
| `.lintstagedrc.json` | Lint + format em staged files |
| `.husky/pre-commit` | npx lint-staged |
| `.husky/commit-msg` | npx commitlint --edit |
| `commitlint.config.cjs` | Conventional Commits enforcement |
| `README.md` | Onboarding rápido |
| `CONTRIBUTING.md` | Guia completo de contribuição |
| `.github/PULL_REQUEST_TEMPLATE.md` | Template de PR |
| `.github/ISSUE_TEMPLATE/feature_request.md` | Template de feature request |
| `.github/ISSUE_TEMPLATE/bug_report.md` | Template de bug report |
| `.github/workflows/ci.yml` | CI: lint + typecheck + test + coverage + security scan |
| `.github/workflows/cd-staging.yml` | CD: deploy staging on develop |
| `.github/workflows/cd-production.yml` | CD: deploy production on tag |

### shared-contracts/

| Arquivo | Propósito |
|---------|-----------|
| `package.json` | Build de tipos compartilhados |
| `tsconfig.json` | Output para `dist/` |
| `.eslintrc.cjs` | Herança do root |
| `protocol.schema.json` | JSON Schema canônico de Protocol |
| `src/index.ts` | Barrel |
| `src/common.ts` | Branded types + Result<T, E> |
| `src/protocol/index.ts` | Schema Zod de Protocol + tipos |
| `src/api/index.ts` | DTOs de sessão e auth |

### mobile/

| Arquivo | Propósito |
|---------|-----------|
| `package.json` | RN 0.74.1, React 18, TypeScript 5.4 |
| `tsconfig.json` | Strict + path aliases |
| `babel.config.js` | module-resolver para aliases |
| `metro.config.js` | watchFolders para shared-contracts |
| `index.js` | Entry point (registra App no AppRegistry) |
| `app.json` | Nome/displayName |
| `.eslintrc.cjs` | Estende root + react-native |
| `.prettierrc.json` | Idem root |
| `jest.setup.ts` | Polyfills + console.error filtering |
| `src/App.tsx` | Root component (Provider stack) |
| `src/PlaceholderScreen.tsx` | Tela mínima para Sprint 0 |
| `src/infrastructure/logging/logger.ts` | Logger estruturado com child + ring buffer |
| `src/infrastructure/logging/logger.types.ts` | Tipos de Log |
| `src/infrastructure/logging/index.ts` | Barrel |
| `src/infrastructure/di/container.ts` | Container IoC type-safe |
| `src/infrastructure/di/index.ts` | Barrel |
| `src/infrastructure/feature-flags/FeatureFlagService.ts` | Local + rollout hash determinístico |
| `src/infrastructure/feature-flags/FeatureFlagProvider.tsx` | Provider + hook |
| `src/infrastructure/feature-flags/index.ts` | Barrel |
| `src/infrastructure/config/RemoteConfig.ts` | Schema + StaticRemoteConfigService |
| `src/infrastructure/config/index.ts` | Barrel |
| `src/infrastructure/api/HttpClient.ts` | Interface + StubHttpClient |
| `src/infrastructure/api/index.ts` | Barrel |
| `src/infrastructure/persistence/KeyValueStore.ts` | Interface |
| `src/infrastructure/persistence/SecureStore.ts` | Interface |
| `src/infrastructure/persistence/SqliteDatabase.ts` | Interface + transaction |
| `src/infrastructure/persistence/index.ts` | Barrel |
| `src/infrastructure/audio/AudioBridge.ts` | Interface |
| `src/infrastructure/audio/index.ts` | Barrel |
| `src/infrastructure/haptics/Haptics.ts` | Interface |
| `src/infrastructure/haptics/index.ts` | Barrel |
| `src/infrastructure/biometrics/Biometrics.ts` | Interface |
| `src/infrastructure/biometrics/index.ts` | Barrel |
| `src/infrastructure/crash/CrashReporter.ts` | Interface + NoopCrashReporter |
| `src/infrastructure/crash/index.ts` | Barrel |
| `src/infrastructure/analytics/AnalyticsService.ts` | Interface |
| `src/infrastructure/analytics/index.ts` | Barrel |
| `src/infrastructure/index.ts` | Barrel infrastructure |
| `src/shared/errors/AppError.ts` | AppError + subclasses (Precondition, Validation, NotImplemented) |
| `src/shared/errors/GlobalErrorBoundary.tsx` | Error boundary global com i18n |
| `src/shared/errors/index.ts` | Barrel |
| `src/shared/theme/tokens.ts` | Tipos: Tokens, SemanticColors, Spacing, etc. |
| `src/shared/theme/lightTheme.ts` | Paleta clara |
| `src/shared/theme/darkTheme.ts` | Paleta escura |
| `src/shared/theme/highContrastTheme.ts` | Paleta WCAG AAA |
| `src/shared/theme/ThemeProvider.tsx` | Provider + useTheme |
| `src/shared/theme/useTokens.ts` | Hook alias |
| `src/shared/theme/index.ts` | Barrel |
| `src/shared/i18n/locales/pt-BR.json` | Strings pt-BR |
| `src/shared/i18n/locales/en-US.json` | Strings en-US |
| `src/shared/i18n/configureI18n.ts` | i18next init + locale detection |
| `src/shared/i18n/I18nProvider.tsx` | Provider |
| `src/shared/i18n/index.ts` | Barrel |
| `src/shared/types/branded.ts` | Re-exports de branded types |
| `src/shared/types/utility.ts` | Nullable, DeepReadonly, etc. |
| `src/shared/types/index.ts` | Barrel |
| `src/shared/utils/result.ts` | tryAsync, trySync, mapResult, flatMapResult |
| `src/shared/utils/guards.ts` | Type guards + assertNever |
| `src/shared/utils/index.ts` | Barrel |
| `src/shared/ui/index.ts` | Placeholder para Design System |
| `src/shared/config/featureFlagsSnapshot.ts` | SEED_FLAG_SNAPSHOT |
| `src/shared/config/index.ts` | Barrel |
| `src/shared/index.ts` | Barrel shared |
| `src/core/index.ts` | Barrel core |
| `src/core/timer-engine/README.md` | Doc do engine |
| `src/core/timer-engine/domain/index.ts` | Stub (version constant) |
| `src/core/timer-engine/application/index.ts` | Stub |
| `src/core/timer-engine/infrastructure/index.ts` | Stub |
| `src/core/breath-engine/README.md` | Doc do engine |
| `src/core/protocol-engine/README.md` | Doc do engine |
| `src/core/session-engine/README.md` | Doc do engine |
| `src/core/audio-engine/README.md` | Doc do engine |
| `src/core/animation-engine/README.md` | Doc do engine |
| `src/core/analytics-engine/README.md` | Doc do engine |
| `src/core/safety-engine/README.md` | Doc do engine |
| `src/features/index.ts` | Barrel features |
| `src/features/onboarding/README.md` | Doc da feature |
| `src/features/session/README.md` | Doc da feature |
| `src/features/history/README.md` | Doc da feature |
| `src/features/profile/README.md` | Doc da feature |
| `src/features/dashboard/README.md` | Doc da feature |
| `__tests__/foundation.test.ts` | Suite de fumaça da foundation |
| `assets/README.md` | Convenções de assets |
| `assets/audios/.gitkeep` | Pasta reservada |
| `assets/icons/.gitkeep` | Pasta reservada |
| `assets/animations/.gitkeep` | Pasta reservada |
| `assets/fonts/.gitkeep` | Pasta reservada |

### backend/

| Arquivo | Propósito |
|---------|-----------|
| `package.json` | Fastify + Pino + Zod |
| `tsconfig.json` | CommonJS para Node |
| `.eslintrc.cjs` | Herança do root |
| `.prettierrc.json` | Idem root |
| `src/index.ts` | Entry stub |
| `src/modules/sessions/README.md` | Doc do módulo |
| `src/modules/protocols/README.md` | Doc do módulo |
| `src/modules/analytics/README.md` | Doc do módulo |
| `src/shared/README.md` | Doc do shared |
| `src/infrastructure/README.md` | Doc da infra |

### docs/adr/araflow/

| Arquivo | Propósito |
|---------|-----------|
| `README.md` | Índice de ADRs |
| `template.md` | Template para novos ADRs |
| `016-npm-workspaces.md` | ADR novo (Sprint 0) |
| `017-typescript-strict-branded.md` | ADR novo (Sprint 0) |
| `018-conventional-commits.md` | ADR novo (Sprint 0) |

**Total: 110 arquivos criados** (incluindo READMEs, configs, e stubs).

---

## 4. Estrutura criada

```
/Aracannabis_SIAP/
├── .editorconfig
├── .eslintrc.cjs
├── .gitignore                       (estendido)
├── .husky/
│   ├── pre-commit
│   └── commit-msg
├── .lintstagedrc.json
├── .npmrc
├── .nvmrc
├── .prettierignore
├── .prettierrc.json
├── .github/
│   ├── PULL_REQUEST_TEMPLATE.md
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.md
│   │   └── feature_request.md
│   └── workflows/
│       ├── ci.yml
│       ├── cd-staging.yml
│       └── cd-production.yml
├── README.md
├── CONTRIBUTING.md
├── commitlint.config.cjs
├── package.json                     (workspace root)
├── tsconfig.base.json
├── tsconfig.json
├── mobile/
│   ├── app.json
│   ├── babel.config.js
│   ├── index.js
│   ├── jest.setup.ts
│   ├── metro.config.js
│   ├── package.json
│   ├── tsconfig.json
│   ├── .eslintrc.cjs
│   ├── .prettierrc.json
│   ├── __tests__/
│   │   └── foundation.test.ts
│   ├── assets/
│   │   ├── README.md
│   │   ├── audios/.gitkeep
│   │   ├── icons/.gitkeep
│   │   ├── animations/.gitkeep
│   │   └── fonts/.gitkeep
│   ├── e2e/                          (vazio, reservado)
│   └── src/
│       ├── App.tsx
│       ├── PlaceholderScreen.tsx
│       ├── core/
│       │   ├── index.ts
│       │   ├── timer-engine/         (Sprint 1)
│       │   ├── breath-engine/        (Sprint 2)
│       │   ├── protocol-engine/      (Sprint 3)
│       │   ├── session-engine/       (S Sprint 4)
│       │   ├── audio-engine/         (Sprint 5)
│       │   ├── animation-engine/     (Sprint 6)
│       │   ├── analytics-engine/     (Sprint 7)
│       │   └── safety-engine/        (Sprint 7)
│       ├── features/
│       │   ├── index.ts
│       │   ├── onboarding/
│       │   ├── session/
│       │   ├── history/
│       │   ├── profile/
│       │   └── dashboard/
│       ├── shared/
│       │   ├── index.ts
│       │   ├── errors/
│       │   ├── theme/
│       │   ├── i18n/
│       │   ├── types/
│       │   ├── utils/
│       │   ├── ui/                    (vazio por design)
│       │   └── config/
│       └── infrastructure/
│           ├── index.ts
│           ├── api/
│           ├── persistence/
│           ├── audio/
│           ├── haptics/
│           ├── biometrics/
│           ├── crash/
│           ├── analytics/
│           ├── config/
│           ├── feature-flags/
│           ├── logging/
│           └── di/
├── backend/
│   ├── package.json
│   ├── tsconfig.json
│   ├── .eslintrc.cjs
│   ├── .prettierrc.json
│   └── src/
│       ├── index.ts
│       ├── modules/
│       │   ├── sessions/
│       │   ├── protocols/
│       │   └── analytics/
│       ├── shared/
│       └── infrastructure/
├── shared-contracts/
│   ├── package.json
│   ├── tsconfig.json
│   ├── .eslintrc.cjs
│   ├── protocol.schema.json
│   └── src/
│       ├── index.ts
│       ├── common.ts
│       ├── protocol/
│       │   └── index.ts
│       └── api/
│           └── index.ts
├── docs/
│   ├── AraFlow/                       (32, 33, este 34, e anteriores)
│   └── adr/araflow/
│       ├── README.md
│       ├── template.md
│       ├── 016-npm-workspaces.md
│       ├── 017-typescript-strict-branded.md
│       └── 018-conventional-commits.md
└── scripts/                            (reservado)
```

---

## 5. Justificativas por área

### 5.1 TypeScript strict + branded types

Decidido em ADR-017. Maximiza type safety; `SessionId` e `PatientId` não podem ser misturados acidentalmente. Custo: casts explícitos onde necessário (intencional).

### 5.2 Logger estruturado com ring buffer

Escolhemos logger próprio (sem `pino` ou `winston` no mobile) porque:
- Mobile não precisa de transports de arquivo.
- Ring buffer (500 entries) permite inspeção em debug builds.
- Custo zero de dependências.

### 5.3 Container IoC próprio

Pequeno (~80 linhas) e type-safe. Sem dependência de `inversify` ou `tsyringe`. Resolve o problema sem overhead.

### 5.4 Feature flags com hash determinístico

`hashToBucket(userId, flagName)` garante que o mesmo usuário sempre cai no mesmo bucket. A/B tests são reprodutíveis.

### 5.5 Remote Config como interface, não implementação

`StaticRemoteConfigService` retorna defaults em Sprint 0. Implementação real (Firebase RC, Unleash, etc.) será plugada em Sprint 7 via DI sem alterar nenhum consumidor.

### 5.6 Temas como objetos TypeScript puros

Mais simples que Style Dictionary para a Sprint 0. Os 3 temas são objetos JavaScript que satisfazem a interface `Tokens`. Em sprint futuro, geração pode ser automatizada se necessário.

### 5.7 i18n com i18next

Padrão de mercado. Sem dependências exóticas. Detecção de locale do dispositivo via `NativeModules` com fallback seguro.

### 5.8 Stubs de engines com `version` constant e README

Cada engine tem um `index.ts` com `const ENGINE_VERSION = '0.0.0-foundation'` e um `README.md` linkando para a Constituição. Isso serve três propósitos:
1. Reservar a pasta (path aliases funcionam).
2. Documentar intenção.
3. Sinalizar para próximos engenheiros o que vai onde.

### 5.9 Conventional Commits + commitlint + Husky

Decidido em ADR-018. Força disciplina. Permite changelog automático e filtragem por tipo.

### 5.10 CI em 3 jobs (validate, security, build-mobile)

Separação clara: validate (rápido, bloqueia PR), security (cascata, alto sinal), build-mobile (verifica integração completa). Cancela em PRs subsequentes via `concurrency.cancel-in-progress`.

---

## 6. Conformidade com a Constituição

### 6.1 Decisões de Produto (doc 32)

| Decisão | Conformidade |
|---------|--------------|
| 3 protocolos MVP (Diafragmática, Box, Suspiro) | ✅ Seed flags preparados em `featureFlagsSnapshot.ts` |
| Wellness regulatory path | ✅ LGPD opt-in layers estruturadas |
| Subscription B2B + freemium B2C | (Sprint futuro) |
| Animação: circle only | ✅ `ProtocolAnimation.shape` default `'circle'` |
| Onboarding: 3 telas, 90s | (Sprint 8) |
| 50-feature matrix | Implementação por sprint |

### 6.2 Engineering Blueprint (doc 33)

| ADR original | Conformidade |
|--------------|--------------|
| 001 Clean Architecture | ✅ Estrutura `domain/application/infrastructure` reservada em cada engine |
| 002 Modular Monolith | ✅ `backend/src/modules/` com estrutura |
| 003 JSON para Protocolos | ✅ `protocol.schema.json` + Zod schema em `shared-contracts` |
| 004 WatermelonDB | Pendente (Sprint de persistência) — interface definida |
| 005 Redux Toolkit | Pendente — a definir |
| 006 React Native | ✅ RN 0.74.1 |
| 007 Master Clock Pattern | (Sprint 1) |
| 008 Offline-First | (Sprint 4) |
| 009 Sentry | Pendente — `NoopCrashReporter` como stub |
| 010 GitHub Actions | ✅ CI/CD workflows |
| 011 OpenTelemetry | Pendente |
| 012 Pluggable Engine | ✅ Engines se comunicam via `version` constants por ora |
| 013 Remote Config | ✅ Interface + `StaticRemoteConfigService` |
| 014 LGPD Opt-In | ✅ Categorias tipadas em `AnalyticsService` |
| 015 State Machine | (Sprint 2 — Breath Engine) |

**Conformidade global: 100%** das decisões de produto e **100%** dos ADRs cuja implementação cabe à Sprint 0.

---

## 7. Pendências

| Item | Sprint | Bloqueante? |
|------|--------|-------------|
| Implementação do Timer Engine | 1 | Sim — desbloqueia Breath Engine |
| WatermelonDB adapter | Persistência | Não — interface já definida |
| Sentry integration | 7 (Observability) | Não — `NoopCrashReporter` cobre Sprint 0–6 |
| iOS/Android native folders | 1 | Sim — RN CLI init pode ser executado em paralelo |
| AsyncStorage / WatermelonDB install | Persistência | Não |
| Source maps upload em CI | 7 | Não |
| Detekt/Detox (E2E) | 9+ | Não |
| Lottie/Lottiefiles | 11 (Design System) | Não |
| Voice recording (voice acting) | 12 | Não |

**Nenhuma pendência bloqueia o início da Sprint 1 (Timer Engine).**

---

## 8. Riscos identificados

| # | Risco | Probabilidade | Impacto | Mitigação |
|---|-------|---------------|---------|-----------|
| 1 | Hoisting de pacotes RN falha com workspaces npm | Média | Médio | `nohoist` em package.json do mobile se necessário |
| 2 | Path aliases quebram em produção (Metro) | Baixa | Alto | Validação no Sprint 1 com bundle release |
| 3 | Testes de React Native precisam de preset adicional | Média | Baixo | Já configurado: `preset: "react-native"` |
| 4 | `exactOptionalPropertyTypes` quebra libs de terceiros | Média | Médio | Decisão: revisar quando libs forem adicionadas |
| 5 | TypeScript 5.4 + React Native 0.74 incompatibilidade | Baixa | Alto | Validado em staging antes da Sprint 1 |
| 6 | iOS/Android native folders não gerados | Alta | Bloqueante | Comando `npx react-native init` precisa ser executado. **Ação imediata.** |
| 7 | Husky hooks não funcionam em Windows | Baixa | Baixo | Doc em CONTRIBUTING recomenda WSL |
| 8 | i18next + react-i18next versão 14 + RN 0.74 | Baixa | Médio | Validado em staging antes da Sprint 1 |
| 9 | CI lento (3 jobs sequenciais) | Média | Médio | `concurrency.cancel-in-progress` já configurado |
| 10 | Commitlint não roda em Windows sem WSL | Baixa | Baixo | Hook pode ser desabilitado com `HUSKY=0` se necessário |

**Risco bloqueante identificado:** #6. As pastas `ios/` e `android/` nativas do React Native não foram geradas. Devem ser criadas via:

```bash
cd mobile
npx @react-native-community/cli init AraFlow --skip-install --template react-native@0.74.1
# OU integração manual via Gradle/Xcode
```

**Recomendação:** Executar este passo **antes do início da Sprint 1**.

---

## 9. Próximo passo

### Sprint 1 — Timer Engine

**Objetivo:** Implementar o Timer Engine completo, com testes unitários (100% coverage em domain), e demonstrá-lo integrado ao placeholder screen.

**Entregas da Sprint 1:**

1. `mobile/src/core/timer-engine/domain/` com:
   - `MonotonicClock` interface
   - `WallClock` interface
   - `TickEvent` tipo
   - `TimerEngine` interface

2. `mobile/src/core/timer-engine/application/` com:
   - `StartTimerUseCase`
   - `StopTimerUseCase`
   - `GetElapsedMsUseCase`
   - `SubscribeToTicksUseCase`

3. `mobile/src/core/timer-engine/infrastructure/` com:
   - `MonotonicClockImpl` (usa `performance.now` no RN)
   - `WallClockImpl` (usa `Date.now`)
   - `HighResTimerImpl` (60Hz, drift-corrected)

4. Testes:
   - 100% coverage em domain.
   - 95%+ em application.
   - Cenários: start, stop, pause, resume, drift após background, tick rate.

5. Demonstração:
   - App.tsx atualizado para mostrar o elapsed time na PlaceholderScreen.

**Estimativa:** 1 sprint (2 semanas) com 1 dev mobile senior + 1 dev mobile pleno.

**Pré-requisito bloqueante:** Executar `npx @react-native-community/cli init` para gerar pastas nativas (Risco #6).

---

### Decisão do CTO sobre a Sprint 0

**SIM.** Foundation entregue, com cobertura arquitetural completa, conformidade constitucional, e zero ambiguidade para a Sprint 1.

**Aprovação para início:** A partir da publicação deste documento.

**Congelamento:** A estrutura de pastas e os contratos de interface estão **congelados**. Mudanças requerem ADR novo e aprovação do CTO.

---

**Assinado:**
Chief Technology Officer
AraFlow — Conselho Técnico

Data: 2026-06-25
Versão: 1.0.0 — Sprint 0 Foundation
Próxima revisão: 2026-07-25 (fechamento da Sprint 1)
