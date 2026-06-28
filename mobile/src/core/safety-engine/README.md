# Safety Engine

> **Status:** Sprint 0 — Foundation stub
> **Próxima implementação:** Sprint 7

## Responsabilidade

Garante **limites clínicos** do uso. Detecta padrões arriscados e força interrupção se necessário.

## O que ele faz

- Valida duração máxima de sessão.
- Valida número máximo de ciclos.
- Detecta uso excessivo (sessões/hora, sessões/dia).
- Detecta fadiga de uso (tempo total em 24h).
- Força interrupção quando limite é atingido.
- Loga eventos de segurança.

## Estrutura

```
safety-engine/
├── domain/            # SafetyRule, SafetyLimit, SafetyViolation
├── application/       # CheckLimits, EnforceLimit, GetAlerts
└── infrastructure/    # LocalLimitStore, TelemetrySink
```

## Dependências

- Session Engine (estado da sessão).
- Timer Engine (duração acumulada).

## Consumidores

- Session Engine (bloqueio).
- UI (alertas e toasts).
- Analytics Engine (eventos de segurança).

## Documentação adicional

Ver `docs/AraFlow/33_ENGINEERING_BLUEPRINT.md` (Top 50 Riscos Técnicos) e `docs/AraFlow/23_SAFETY_PROTOCOLS.md`.
