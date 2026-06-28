# AraFlow — Sistema de Animações (Motion Design para Respiração)

> **Versão:** 0.1.0
> **Data:** 2026-06-24
> **Owner:** UX Designer + Motion Designer
>
> Este documento define o **sistema central de animações** que acompanha a respiração do usuário. A animação é a principal interface visual durante a sessão; por isso, precisa ser cuidadosamente desenhada para facilitar a regulação autonômica, sem distrair.

---

## Sumário

1. Função terapêutica da animação
2. Princípios de motion design
3. Catálogo de animações propostas
   - 3.1 Círculo respiratório
   - 3.2 Pulmão
   - 3.3 Flor
   - 3.4 Onda
   - 3.5 Esfera
   - 3.6 Mandala
   - 3.7 Partículas
4. Comparação entre animações
5. Recomendações por objetivo clínico
6. Recomendações por público
7. Recomendações por dispositivo
8. Estados da animação
9. Parâmetros ajustáveis
10. Performance
11. Acessibilidade
12. Integração com áudio
13. Implementação técnica (alto nível)
14. Testes e validação

---

## 1. Função terapêutica da animação

A animação serve a **4 funções simultâneas**:

1. **Pacer visual.** Marca o ritmo da respiração (substituindo metrônomo para quem prefere visual).
2. **Foco atencional.** Concentra a atenção no movimento, reduzindo ruminação.
3. **Modelagem.** Demonstra a forma ideal de respirar (amplitude, ritmo).
4. **Regulação emocional.** Calma visualmente, sem sobrecarregar.

---

## 2. Princípios de motion design

| Princípio | Aplicação |
|-----------|-----------|
| **Suavidade acima de velocidade** | Easing ease-breath; sem "saltos". |
| **Sincronia visual ↔ fisiológica** | Crescimento real (não abstrato). |
| **Loop orgânico** | Sem início/fim abruptos. |
| **Nada compete com a respiração** | Cores silenciadas; sem efeitos piscantes. |
| **Acessibilidade em primeiro lugar** | Respeita `prefers-reduced-motion`. |
| **Responsivo a hardware** | 60fps em mid-range. |

### 2.1 Easing curves

| Nome | Curva | Uso |
|------|-------|-----|
| `ease-breath-inspire` | `cubic-bezier(.42, 0, .58, 1)` | Inspiração (mais linear no meio) |
| `ease-breath-hold` | `linear` | Pausas |
| `ease-breath-expire` | `cubic-bezier(.42, 0, .58, 1)` | Expiração |
| `ease-soft-in` | `cubic-bezier(.16, 1, .3, 1)` | Entradas de tela |
| `ease-soft-out` | `cubic-bezier(.7, 0, .84, 0)` | Saídas |

### 2.2 Durações

A duração das fases **vem do protocolo**. Não há animação "decorativa" sobreposta.

---

## 3. Catálogo de animações propostas

Cada animação abaixo é descrita em: **forma, movimento, comportamento por fase, vantagens, desvantagens, público-alvo**.

### 3.1 Círculo respiratório

#### Descrição
Círculo central que cresce na inspiração e diminui na expiração. Linha ou preenchimento gradual.

```
Inspirar (cresce)        Expirar (diminui)
   ╭───────╮                ╭───╮
   │       │                │   │
   │   ●   │                │ ● │
   │       │                │   │
   ╰───────╯                ╰───╯
```

#### Movimento
- Escala: 0.7 → 1.3 → 0.7.
- Centro da tela, foco principal.
- Glow interno aumenta/diminui.

#### Vantagens
- **Universal.** Familiar a qualquer cultura.
- **Simples.** Mínima carga cognitiva.
- **Equação direta** com diafragma.

#### Desvantagens
- **Pouco lúdico.** Não atrai crianças.
- **Genérico.** Pouca identidade visual.

#### Público ideal
- Adulto genérico.
- Iniciação.

#### Cor
Gradiente `primary-300` → `primary-500`.

---

### 3.2 Pulmão

#### Descrição
Visual estilizado de pulmões em vista frontal, com brônquios visíveis. Expande ao inspirar.

```
Inspirar                Expirar
   ╭─╮ ╭─╮                  ╭╮ ╭╮
   │ │ │ │                  ││ ││
   │ │ │ │                  ││ ││
   ╰─╯ ╰─╯                  ╰╯ ╰╯
   ───────                  ──────
```

#### Movimento
- Pulmões expandem lateralmente (largura).
- Brônquios brilham.
- Som de "enchimento".

#### Vantagens
- **Didático.** Ensinadiafragmática.
- **Reverente ao corpo.** Convida à auto-observação.
- **Único.** Pouco explorado por concorrentes.

#### Desvantagens
- **Anatômico demais.** Pode incomodar sensíveis.
- **Carrega simbolismo** médico forte (pode gerar ansiedade em alguns).

#### Público ideal
- Profissionais de saúde.
- Educativo (escolas, cursos).
- Modo "Aprender" do app.

#### Cor
Gradiente `calm-300` → `calm-500`.

---

### 3.3 Flor

#### Descrição
Flor estilizada que abre pétalas na inspiração e fecha na expiração.

```
Inspirar (abre)            Expirar (fecha)
       ✿                        ·
    ❀     ❀                  ✿
  ❀         ❀               ❀ ❀
   ❀       ❀                ✿
    ❀ ❀ ❀                     ·
```

#### Movimento
- Pétalas rotacionam ~30° para fora.
- Centro da flor brilha.
- Tiny partículas soltam (opcional).

#### Vantagens
- **Lúdica.** Atrai crianças e TEA.
- **Orgânica.** Sensação de "cultivo interno".
- **Universais cross-culturais.**

#### Desvantagens
- **Feminino.** Pode parecer pouco inclusivo para alguns homens.
- **Distrai** se muito colorida.

#### Público ideal
- TEA (infantil).
- TDAH (lúdico).
- Modo "Calma + Lúdico".

#### Cor
Gradiente `primary-300` → `energy-500` (para TDAH) ou `calm-500` (para TEA).

---

### 3.4 Onda

#### Descrição
Onda senoidal horizontal que sobe e desce com a respiração.

```
Inspirar                 Expirar
 ╱╲    ╱╲                  ╱─╲
╱  ╲╱╲╱  ╲                ╱    ╲
        (alta)                   (baixa)
```

#### Movimento
- Onda senoidal de comprimento fixo.
- A "altura" da onda sobe (inspiração) e desce (expiração).
- Cor varia com altura.

#### Vantagens
- **Fluida.** Boa para sono e meditação.
- **Suave.** Cansa menos visualmente.
- **Moderna.** Identidade forte.

#### Desvantagens
- **Abstrata.** Não ensina ritmo diretamente.
- **Pouco engajante** para crianças.

#### Público ideal
- Sono.
- Meditação.
- Profissionais que pedem "algo diferente".

#### Cor
Gradiente `sleep-300` → `sleep-500`.

---

### 3.5 Esfera

#### Descrição
Esfera 3D (estilo planeta) que rotaciona lentamente enquanto cresce/encolhe.

```
Inspirar (esfera cresce)
   ╭────────╮
  ╱          ╲
 │     🌍    │
  ╲          ╱
   ╰────────╯

Expirar (esfera encolhe)
   ╭────╮
  ╱      ╲
 │   🌍   │
  ╲      ╱
   ╰────╯
```

#### Movimento
- Rotação contínua (suave, anti-horário).
- Escala varia.
- Atmosfera sutil ao redor.

#### Vantagens
- **Profunda.** Sensação de "espaço interno".
- **Hipnótica.** Boa para foco profundo.
- **Distinta.** Diferencia AraFlow.

#### Desvantagens
- **Poder de processamento** maior.
- **Menos didática** que círculo.

#### Público ideal
- Foco profundo.
- Profissionais (médicos, devs).
- Performance cognitiva.

#### Cor
Gradiente `primary-500` → `info-700` com atmosfera.

---

### 3.6 Mandala

#### Descrição
Mandala geométrica que rotaciona e "respira" com o usuário.

```
Inspirar (mandala abre)
     ╱─────╲
   ╱         ╲
  │   ╱─╲   │
  │  │ • │  │
  │   ╲─╱   │
   ╲         ╱
     ╲─────╱

Expirar (mandala fecha)
     ╱───╲
   ╱       ╲
  │   •    │
   ╲       ╱
     ╲───╱
```

#### Movimento
- Rotação horária lenta.
- Escala e rotação combinadas.
- Detalhes simétricos pulsam.

#### Vantagens
- **Rica visualmente.** Funciona para sessões longas.
- **Tradição contemplativa** (várias culturas).
- **Convidativa** para meditadores experientes.

#### Desvantagens
- **Pode distrair** se muito complexa.
- **Carrega simbolismo** que pode afastar alguns.

#### Público ideal
- Mindfulness experiente.
- Profissionais de saúde mental.
- "Modo profundo".

#### Cor
Monocromática `primary-500` com detalhes `calm-300`.

---

### 3.7 Partículas

#### Descrição
Campo de partículas que se movem de forma orgânica, criando uma "nuvem respiratória".

```
Inspirar (partículas expandem)      Expirar (partículas contraem)

  ·  ·     ·                          · ·
   · ·   ·                              ·
 ·  · ·  ·                              · ·
  · · ·                                   ·
```

#### Movimento
- Partículas se afastam do centro (inspirar) ou se aproximam (expirar).
- Movimento browniano sutil.
- Brilho varia com ritmo.

#### Vantagens
- **Imersiva.** Sensação de "flutuar".
- **Moderna.** Tendência de apps atuais.
- **Dinâmica** sem ser distrativa.

#### Desvantagens
- **Menos direta** como pacer.
- **Maior custo computacional.**
- **Pode gerar enjoo** se muito acelerada.

#### Público ideal
- Jovens adultos.
- Performance cognitiva.
- Modo "Energia".

#### Cor
Partículas `primary-500` em fundo `neutral-900` (modo escuro).

---

## 4. Comparação entre animações

| Animação | Didática | Calma | Ludicidade | Inclusividade | Performance | Recomendação |
|----------|----------|-------|------------|---------------|-------------|--------------|
| **Círculo** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Padrão MVP |
| **Pulmão** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | Educativo |
| **Flor** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | TEA / infantil |
| **Onda** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Sono |
| **Esfera** | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | Foco |
| **Mandala** | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | Mindfulness |
| **Partículas** | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | Jovens / energia |

---

## 5. Recomendações por objetivo clínico

| Objetivo | Animação primária | Animação alternativa |
|----------|-------------------|-----------------------|
| Ansiedade | Círculo | Onda, Mandala |
| Insônia | Onda | Mandala, Esfera |
| Dor crônica | Pulmão | Círculo |
| Foco | Esfera | Círculo |
| Burnout | Mandala | Onda |
| TDAH | Flor | Partículas |
| TEA | Flor | Círculo |
| Cannabis | Mandala | Círculo |
| SAHOS (pré-sono) | Onda | Mandala |

---

## 6. Recomendações por público

| Público | Animação |
|---------|----------|
| Adulto generalista | Círculo |
| Idoso | Círculo, Pulmão (com cor dessaturada) |
| Adolescente | Partículas, Esfera |
| Criança (TEA) | Flor |
| Profissional de saúde | Pulmão, Círculo |

---

## 7. Recomendações por dispositivo

| Dispositivo | Animação suportada |
|-------------|---------------------|
| Mobile low-end | Círculo, Flor |
| Mobile mid/high | Todas exceto Partículas avançadas |
| Desktop | Todas |
| Tablet | Todas |

---

## 8. Estados da animação

A animação tem **5 estados** além do ciclo:

| Estado | Visual |
|--------|--------|
| **Idle (pré-sessão)** | Parado, respiração leve interna |
| **Inspirar** | Crescimento + brilho |
| **Segurar (cheio)** | Pulsação sutil |
| **Expirar** | Diminuição + brilho reduzido |
| **Segurar (vazio)** | Parado, opacidade reduzida |
| **Conclusão** | Fade + glow de "completude" |

---

## 9. Parâmetros ajustáveis

| Parâmetro | Quem ajusta | Limites |
|-----------|-------------|---------|
| Tipo de animação | Usuário | Selecionável em sessão |
| Velocidade de fase | Protocolo | 2–12s |
| Intensidade de glow | Usuário | 0–100% |
| Cor base | Modo (calma, sono, etc.) | Tokens do design system |
| Rotação (quando aplicável) | Fixo | 1 rev / 30s |
| Tamanho da forma | Usuário | 50–100% da tela |
| Opacidade geral | Usuário | 50–100% |

---

## 10. Performance

### 10.1 Frame budget

- **60fps** como meta em mid-range (iPhone 12, Galaxy A52).
- Frame time máximo: **16ms**.
- Otimização: usar `transform` e `opacity` (compositor only).

### 10.2 Técnica de implementação preferida

- **Lottie** para animações com paths complexos.
- **CSS animations** para transformações simples (círculo, onda).
- **Canvas/WebGL** para partículas e esferas 3D (Fase 2).
- **SVG** para formas geométricas (mandala, pulmão).

### 10.3 Adaptive quality

- Detectar FPS real e reduzir partículas se < 50.
- `prefers-reduced-motion` desabilita rotação e troca para fade.

---

## 11. Acessibilidade

### 11.1 `prefers-reduced-motion`

- Substituir movimento por **estados estáticos com transição de opacidade**.
- Visual ainda presente, mas sem cinética.

### 11.2 Daltonismo

- Cores de fase não devem depender só de matiz.
- Adicionar ícone ou texto ("Inspire") como auxiliar.

### 11.3 TDAH

- Versão **menos detalhada** (sem partículas extras).
- Versão **mais colorida** (engajamento).

### 11.4 TEA

- Versão **previsível e repetível** (ciclo idêntico).
- Sem surpresas visuais.

---

## 12. Integração com áudio

A animação deve estar **sincronizada ao áudio** dentro de margem de **±50ms**.

| Camada de áudio | Sincronia |
|-----------------|-----------|
| Metronômo respiratório | 100% (guiam juntos) |
| Música de fundo | Independente |
| Narração | Dentro de pausas (não interrompe fase) |

---

## 13. Implementação técnica (alto nível)

### 13.1 Stack recomendada

| Camada | Tecnologia |
|--------|-----------|
| Animações simples | CSS Animations + React Spring |
| Animações complexas | Lottie (lottie-react) |
| 3D | Three.js (Fase 2) |
| Partículas | Canvas2D + WebGL (Fase 2) |

### 13.2 Estado global

```ts
type BreathState =
  | { phase: 'inspire'; t: number }
  | { phase: 'hold_full'; t: number }
  | { phase: 'expire'; t: number }
  | { phase: 'hold_empty'; t: number }
  | { phase: 'idle' };
```

A animação subscreve a `BreathState` e atualiza visualmente.

---

## 14. Testes e validação

### 14.1 Critérios de aceite por animação

- 60fps em iPhone 12 por 10 minutos contínuos.
- Sincronia visual-auditiva ±50ms.
- Sem "saltos" perceptíveis entre ciclos.
- Conformidade com `prefers-reduced-motion`.

### 14.2 Testes com usuários

- **5 usuários por animação** com observação.
- Perguntas: didática, calma, ludicidade.
- Ajustes iterativos.

### 14.3 Biomarcadores (futuro)

- HRV durante uso de cada animação.
- Correlacionar percepção com regulação autonômica real.

---

*O movimento da respiração é o coração do AraFlow. Trate-o com cuidado.*