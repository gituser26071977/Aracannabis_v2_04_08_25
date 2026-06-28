# ADR-0020 — Breath Engine Implementation

> **Status:** Accepted
> **Data:** 2026-06-25

## Contexto

A Sprint 2 implementa o Breath Engine, complementar ao Timer Engine da Sprint 1. Este ADR documenta decisões de implementação do Breath Engine que não conflitam com ADRs existentes.

## Decisões

### D1. Breath Engine subscreve ao Timer Engine (event-driven)

- **Não usa polling próprio** (`setInterval` próprio seria proibido).
- Subscreve ao evento `tick` do Timer Engine.
- Cada tick: lê `getTotalElapsedMs()`, computa phase, detecta transições.
- **Razão:** garante que Timer Engine permaneça a única fonte de tempo. Polling duplicaria medição.

### D2. Sessão medida como delta da baseline

- `start()` captura `_sessionStartedAtTimerElapsedMs = timerEngine.getTotalElapsedMs()`.
- Cada tick: `sessionElapsedMs = totalElapsedMs - baseline`.
- **Razão:** desacopla Breath Engine do estado interno do Timer Engine. Não importa como o Timer Engine acumula tempo; importa apenas o delta desde o start.

### D3. Breath Engine NÃO gerencia ciclo de vida do Timer Engine

- Caller é responsável por iniciar o Timer Engine antes do Breath Engine.
- `start()` valida que Timer Engine está em `running`; caso contrário, lança AppError.
- **Razão:** mantém separação clara de responsabilidades. Permite múltiplos consumers do Timer Engine.

### D4. 9 eventos (8 do spec + 1 extensão)

- Spec original listou 8: `phaseChanged`, `cycleStarted`, `cycleCompleted`, `breathStarted`, `breathCompleted`, `interrupted`, `cancelled`, `completed`.
- Adicionado 1 extensão: `resumed-from-interrupt` (sinaliza resume após background).
- **Razão:** a spec é omissa sobre o sinal de resume. Sem evento explícito, consumers teriam que correlacionar `interrupted` com mudança de estado. Mais limpo emitir um evento dedicado.

### D5. Distinção semântica breath-completed vs cycle-completed vs completed

- `breath-completed`: emitido quando a fase `exhaling` termina (antes de `holdAfterExhale`). Per-cycle.
- `cycle-completed`: emitido quando `holdAfterExhale` termina (fim do ciclo). Per-cycle.
- `completed`: emitido uma vez quando a sessão inteira termina (= último cycle-completed).
- **Razão:** consumers podem escolher o evento que melhor sincroniza com sua lógica. Áudio quer `breath-completed` (fim de som de respiração); UI quer `cycle-completed` (fim do ciclo visual); analytics quer `completed` (fim da sessão).

### D6. Curvas injetáveis + registro centralizado

- Cada curva é uma função pura `CurveFn = (progress: number) => number`.
- Resolução por nome via `resolveCurve(name)` para descoberta dinâmica.
- **Razão:** permite que Protocol Engine defina curvas customizadas sem alterar Breath Engine. Arquitetura extensível sem modificação.

### D7. Exhale usa 1 - curve(progress)

- Não `curve(1 - progress)`.
- **Razão:** matematicamente equivalente para curvas simétricas (easeInOut, cosine), mas conceitualmente mais claro: "a curva descreve como a profundidade evolui; exalação é o inverso".

### D8. Zero-hold phases são configurações válidas

- `holdAfterInhaleMs: 0` ou `holdAfterExhaleMs: 0` são aceitos.
- Transição direta entre inhaling→exhaling ou exhaling→(next inhaling).
- **Razão:** Coherent Breathing (5-0-5-0) e variantes usam zero-hold. Forçar duração > 0 seria restritivo e exigiria workaround no Protocol Engine.

### D9. Disposal limpa listeners

- `dispose()` cancela subscription ao Timer Engine e limpa listeners próprios.
- Após `dispose()`, engine não recebe mais eventos.
- **Razão:** permite garbage collection correto em cenários onde engine é descartado (e.g., HMR, testes).

## Alternativas consideradas

| Alternativa | Por que não |
|-------------|-------------|
| Polling com `setInterval` próprio | Viola Timer Engine como única fonte de tempo |
| Timer Engine dentro do Breath Engine | Acoplamento desnecessário |
| State machine com XState | Dependência externa; ciclo não é state machine típico |
| Cálculo de profundidade via `requestAnimationFrame` | Acopla a render loop |
| Eventos em kebab-case (cycle-started) vs camelCase (cycleStarted) | Timer Engine usa kebab-case; consistência |

## Consequências

### Positivas
- Timer Engine permanece a única fonte de tempo.
- Engine 100% testável com FakeClockProvider.
- API pequena, imutável, fortemente tipada.
- Curves extensíveis sem modificar BreathEngine.

### Negativas
- `resumed-from-interrupt` é extensão (não no spec original); consumidores cross-platform podem precisar polling.
- 9 eventos é mais que o spec (8); pode confundir consumidores que esperam contagem exata.

### Neutras
- Requer ADR-007 (Master Clock) vigente — já existe.
- Não impacta outros engines diretamente até a Sprint 3.

## Conformidade com a Constituição

- ✅ Não contradiz 32 (Decisões de Produto).
- ✅ Não contradiz 33 (Engenharia, ADR-007, ADR-008, §10 Sincronização).
- ✅ Não contradiz 34 (Sprint 0 Foundation).
- ✅ Não contradiz 35 (Sprint 1 Timer Engine).
- ✅ Implementa mecânica respiratória pura, sem conhecimento clínico.

## Recomendações para Protocol Engine (Sprint 3)

1. **Reutilize `computePhaseInfo` e `computeDepth`** — funções puras, fáceis de invocar.
2. **Use `resolveCurve` para descoberta de curvas**, ou aceite `CurveFn` injetada.
3. **Reuse `BreathEngine.subscribe` para sincronização** — não implemente listeners próprios.
4. **Componha protocolos clínicos como `BreathCycleConfig`** — sem lógica adicional no Breath Engine.
5. **Considere adicionar curva customizada para protocolos específicos** (e.g., "triangle wave" para protocolos de potência).
6. **Use `BreathCycleConfig` para ratio/cadence derivados** — `computeBreathRatio`, `computeBreathCadence` são gratuitos.

## Conformidade com a Constituição do Produto

- ✅ Sem conhecimento clínico (Box, 4-7-8, ansiedade, insônia).
- ✅ Sem dependência de UI / React / RN.
- ✅ Determinístico e re-entrante.
- ✅ Totalmente desacoplado.