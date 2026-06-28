# Protocol Engine

> **Status:** Sprint 0 — Foundation stub
> **Próxima implementação:** Sprint 3

## Responsabilidade

Carrega, valida, e fornece **protocolos de respiração**. Protocolos são JSON validado por schema Zod (ver `shared-contracts/src/protocol/index.ts`).

## O que ele faz

- Carrega protocolo de fonte (local bundled, cache, ou servidor).
- Valida estrutura via Zod.
- Fornece metadata (título, descrição, evidências).
- Versiona protocolo.
- Suporta hot-reload via Remote Config.

## Estrutura

```
protocol-engine/
├── domain/            # Protocol, ProtocolValidator
├── application/       # LoadProtocol, ListProtocols, GetActiveProtocol
└── infrastructure/    # BundledProtocolSource, RemoteProtocolSource
```

## Dependências

- Nenhuma (puramente domínio).

## Consumidores

- Breath Engine.
- UI (lista de protocolos disponíveis).

## Documentação adicional

Ver `docs/AraFlow/33_ENGINEERING_BLUEPRINT.md` §7 (Sistema de Protocolos).
