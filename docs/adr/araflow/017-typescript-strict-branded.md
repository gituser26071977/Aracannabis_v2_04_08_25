# ADR-0017 — TypeScript strict + branded types

> **Status:** Accepted
> **Data:** 2026-06-25

## Contexto

AraFlow lida com tipos semanticamente distintos que compartilham o mesmo primitivo em runtime (ex.: `SessionId` e `PatientId` são ambos `string`). Sem proteção em tempo de compilação, é fácil misturar acidentalmente.

## Decisão

**TypeScript strict em sua configuração máxima, complementado por branded types para IDs e timestamps.**

Configuração no `tsconfig.base.json`:

- `strict: true`
- `noImplicitAny: true`
- `strictNullChecks: true`
- `noUnusedLocals: true`
- `noUnusedParameters: true`
- `exactOptionalPropertyTypes: true`
- `noUncheckedIndexedAccess: true`
- `noImplicitOverride: true`
- `noPropertyAccessFromIndexSignature: true`
- `useUnknownInCatchVariables: true`

Branded types definidos em `shared-contracts/src/common.ts`:

- `PatientId`, `SessionId`, `ProtocolId`, `ProtocolVersion`, `UserId`, `TenantId`
- `Iso8601`, `MonotonicMs`, `WallClockMs`

## Alternativas consideradas

| Alternativa | Prós | Contras |
|-------------|------|---------|
| **TS sem strict** | Setup trivial | Permite `any`, `null` implícito, mistura de tipos |
| **TS strict sem branded types** | Strict suficiente | Mistura `SessionId` e `PatientId` continua possível |
| **Zod para tudo** | Validação runtime | Não substitui tipagem estática |
| **TS strict + branded (escolhido)** | Type safety máxima, runtime zero cost | Curva de aprendizado para branded types |

## Consequências

### Positivas
- Erros de tipo capturados em compile time.
- Refatoração segura.
- Onboarding mais rápido (tipos são autodocumentados).

### Negativas
- Branded types exigem `as` casts ou construtores (intencional).
- `exactOptionalPropertyTypes` quebra alguns padrões comuns (intencional).

## Conformidade com a Constituição

- ✅ Não contradiz 33 (Engenharia).
- ✅ Alinha com §25 (Dívida técnica inaceitável): "Uso de `any` em TypeScript. Tipagem estrita."
