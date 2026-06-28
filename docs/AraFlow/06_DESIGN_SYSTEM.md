# AraFlow — Design System

> **Versão:** 0.1.0
> **Data:** 2026-06-24
> **Owner:** UX Designer
>
> Este documento define tokens, componentes, padrões visuais e de interação do AraFlow. O AraFlow deve seguir a **identidade visual do AraOS**, mas com camada própria de **modo "terapêutico"** (visual mais orgânico, paleta mais suave em contextos sensíveis).

---

## Sumário

1. Princípios
2. Identidade visual
3. Tipografia
4. Paleta de cores
5. Espaçamento e grid
6. Sombras e elevação
7. Bordas e raios
8. Iconografia
9. Animações e motion design
10. Botões
11. Cards
12. Inputs e formulários
13. Toggles e checkboxes
14. Tags e chips
15. Timers e cronômetros
16. Barras de progresso
17. Visualização respiratória (componente central)
18. Listas e itens
19. Modais e sheets
20. Toasts e feedbacks
21. Estados vazios, de erro e de carregamento
22. Acessibilidade
23. Tom de voz e microcopy
24. Padrões específicos do modo terapêutico

---

## 1. Princípios

1. **Calmo, não ansioso.** Nada de cores berrantes ou animações bruscas.
2. **Clínico, mas humano.** Não parece um hospital, mas tem rigor.
3. **Inclusivo.** Funciona em tela pequena, com baixo contraste, com leitor de tela.
4. **Respirante.** Espaço vazio é tão importante quanto conteúdo.
5. **Semântica antes da estética.** A cor deve significar algo.

---

## 2. Identidade visual

| Aspecto | Decisão |
|---------|---------|
| Nome | **AraFlow** |
| Símbolo | Folha/onda (união da identidade Ara + fluxo respiratório) |
| Linguagem | Orgânica + clínica + minimalista |
| Tagline oficial | *"Respire com cuidado."* |
| Tagline alternativa | *"Terapia em movimento."* |
| Logo | Versão monocromática + versão "modo clínico" + versão "modo profundo" |

---

## 3. Tipografia

### 3.1 Famílias

| Uso | Família | Origem |
|-----|---------|--------|
| UI principal | **Inter** (sans-serif) | Open source |
| Sessão / numerais | **Inter** com tabular figures | — |
| Long-form / blog | **Source Serif** | Open source |
| Acessibilidade alta | Permite troca para **Atkinson Hyperlegible** | Open source |

### 3.2 Escala tipográfica (modular, razão 1.25)

| Token | Tamanho (px) | Uso |
|-------|--------------|-----|
| `text-xs` | 12 | Captions, labels pequenas |
| `text-sm` | 14 | Texto secundário |
| `text-base` | 16 | Corpo padrão |
| `text-lg` | 18 | Texto de destaque |
| `text-xl` | 20 | Subtítulos |
| `text-2xl` | 24 | Títulos de seção |
| `text-3xl` | 30 | Títulos de tela |
| `text-4xl` | 36 | Hero / títulos de destaque |
| `text-5xl` | 48 | Apenas landing / campanha |

### 3.3 Pesos

| Peso | Uso |
|------|-----|
| Regular (400) | Corpo |
| Medium (500) | Botões, labels |
| Semibold (600) | Títulos |
| Bold (700) | Apenas destaques raros |

### 3.4 Line-height

| Contexto | Valor |
|----------|-------|
| UI | 1.5 |
| Títulos | 1.25 |
| Sessão (texto grande) | 1.4 |

---

## 4. Paleta de cores

### 4.1 Cores primárias (identidade)

| Token | Hex | Uso |
|-------|-----|-----|
| `primary-50` | `#E6F4F1` | Fundos suaves |
| `primary-100` | `#BFE3DA` | Hover, fundo destaque |
| `primary-300` | `#6BBFAF` | Estados ativos secundários |
| `primary-500` | `#1F8F77` | **Cor primária do AraFlow** |
| `primary-700` | `#0F6E5C` | Pressionado, foco |
| `primary-900` | `#0A4A3E` | Texto sobre fundo claro |

### 4.2 Cores de suporte (acalmar / energizar / sono)

| Token | Hex | Significado |
|-------|-----|-------------|
| `calm-500` | `#7AB7B7` | Modo calma (ansiedade) |
| `calm-700` | `#3F8585` | Pressionado |
| `energy-500` | `#E8B14C` | Modo foco |
| `energy-700` | `#A87A1E` | Pressionado |
| `sleep-500` | `#5C5A8E` | Modo sono |
| `sleep-700` | `#3D3B66` | Pressionado |
| `pain-500` | `#A0B98E` | Modo dor |
| `pain-700` | `#74865F` | Pressionado |

### 4.3 Cores semânticas

| Token | Hex | Uso |
|-------|-----|-----|
| `success-500` | `#3DA46E` | Conclusão, sucesso |
| `success-100` | `#D9F1E2` | Fundo de sucesso |
| `warning-500` | `#D08D2D` | Atenção |
| `warning-100` | `#FAEAD0` | Fundo de atenção |
| `danger-500` | `#C04A4A` | Erro, destrutivo |
| `danger-100` | `#F6D9D9` | Fundo de erro |
| `info-500` | `#4A7EC0` | Informativo |
| `info-100` | `#DCE6F4` | Fundo informativo |

### 4.4 Neutros

| Token | Hex | Uso |
|-------|-----|-----|
| `neutral-0` | `#FFFFFF` | Fundo puro |
| `neutral-50` | `#F8FAF9` | Fundo padrão |
| `neutral-100` | `#EFF2F0` | Fundo elevado |
| `neutral-200` | `#DDE2DF` | Divisor |
| `neutral-400` | `#9CA39E` | Texto terciário |
| `neutral-600` | `#5E655F` | Texto secundário |
| `neutral-800` | `#2B2F2C` | Texto primário |
| `neutral-900` | `#161816` | Texto alto contraste |

### 4.5 Regras

- **Nunca usar cor pura** (red, blue) — sempre versões dessaturadas.
- **Modo escuro:** espelho do modo claro com `neutral-900` como base.
- **Modo terapêutico:** paleta mais dessaturada ainda (vide § 24).

---

## 5. Espaçamento e grid

### 5.1 Escala (múltiplos de 4)

| Token | Valor |
|-------|-------|
| `space-0` | 0 |
| `space-1` | 4px |
| `space-2` | 8px |
| `space-3` | 12px |
| `space-4` | 16px |
| `space-5` | 20px |
| `space-6` | 24px |
| `space-8` | 32px |
| `space-10` | 40px |
| `space-12` | 48px |
| `space-16` | 64px |

### 5.2 Grid

- **Mobile:** 4 colunas, gutter 16px, margem 16px.
- **Tablet:** 8 colunas, gutter 16px, margem 24px.
- **Desktop:** 12 colunas, gutter 24px, margem 32px.

---

## 6. Sombras e elevação

| Token | Valor | Uso |
|-------|-------|-----|
| `shadow-xs` | `0 1px 2px rgba(0,0,0,.06)` | Inputs |
| `shadow-sm` | `0 2px 4px rgba(0,0,0,.08)` | Cards |
| `shadow-md` | `0 4px 12px rgba(0,0,0,.10)` | Cards elevados, modais |
| `shadow-lg` | `0 8px 24px rgba(0,0,0,.12)` | Sheets |
| `shadow-focus` | `0 0 0 3px rgba(31,143,119,.35)` | Foco acessível |

---

## 7. Bordas e raios

| Token | Valor | Uso |
|-------|-------|-----|
| `radius-sm` | 4px | Tags |
| `radius-md` | 8px | Botões, inputs |
| `radius-lg` | 12px | Cards |
| `radius-xl` | 20px | Cards de destaque |
| `radius-full` | 9999px | Avatares, pílulas |

---

## 8. Iconografia

### 8.1 Biblioteca
- **Primária:** Lucide (open source, consistente, leve).
- **Específicos do AraFlow:** desenhados pela equipe, set minimal stroke 1.5px.

### 8.2 Tamanhos

| Token | Valor |
|-------|-------|
| `icon-xs` | 12px |
| `icon-sm` | 16px |
| `icon-md` | 20px |
| `icon-lg` | 24px |
| `icon-xl` | 32px |

### 8.3 Custom icons do AraFlow

| Nome | Significado |
|------|-------------|
| `ar-flow-leaf` | Folha com onda |
| `ar-flow-breath-circle` | Círculo respiratório |
| `ar-flow-sleep-moon` | Lua para sono |
| `ar-flow-focus-eye` | Olho sereno |
| `ar-flow-pain-leaf` | Folha suave |
| `ar-flow-streak` | Chama de sequência |

---

## 9. Animações e motion design

### 9.1 Princípios

- **Suavidade acima de velocidade.**
- **Sempre desacelerar no fim** (easing ease-out).
- **Sem "saltos"** entre estados.
- **Respeitar `prefers-reduced-motion`.**

### 9.2 Curvas

| Nome | Curva | Uso |
|------|-------|-----|
| `ease-soft` | `cubic-bezier(.4,0,.2,1)` | Padrão |
| `ease-breath` | `cubic-bezier(.42,0,.58,1)` | Respiração |
| `ease-out-soft` | `cubic-bezier(.16,1,.3,1)` | Entradas |
| `ease-in-soft` | `cubic-bezier(.7,0,.84,0)` | Saídas |

### 9.3 Durações

| Token | Valor | Uso |
|-------|-------|-----|
| `dur-instant` | 80ms | Feedback imediato |
| `dur-fast` | 160ms | Hover |
| `dur-base` | 240ms | Transições |
| `dur-slow` | 400ms | Entradas de tela |
| `dur-deep` | 800ms | Modais, sheets |
| `dur-breath` | variável | Respiração (1–6s) |

### 9.4 Tipos de animação

- **Fade** (entradas)
- **Scale 0.96 → 1** (entradas sutis)
- **Slide vertical** (sheets)
- **Circular grow/shrink** (visual respiratório)
- **Particle drift** (modo profundo)

### 9.5 Respeitando acessibilidade

```css
@media (prefers-reduced-motion: reduce) {
  * { animation: none !important; transition: none !important; }
}
```

---

## 10. Botões

### 10.1 Variantes

| Variante | Uso | Estilo |
|----------|-----|--------|
| `primary` | Ação principal | Preenchido, `primary-500` |
| `secondary` | Ação secundária | Outline, `primary-500` |
| `ghost` | Ação terciária | Apenas texto |
| `danger` | Destrutiva | Preenchido, `danger-500` |
| `quiet` | Contexto terapêutico | Cor dessaturada |

### 10.2 Tamanhos

| Token | Altura | Padding horizontal |
|-------|--------|-------------------|
| `sm` | 32px | 12px |
| `md` | 44px | 16px |
| `lg` | 56px | 24px |
| `xl` | 64px | 32px |

### 10.3 Estados

| Estado | Mudança |
|--------|---------|
| Default | Cor base |
| Hover | +6% luminosidade + sombra |
| Active | -8% luminosidade |
| Focus | Anel `shadow-focus` |
| Disabled | 40% opacidade, cursor not-allowed |
| Loading | Spinner + texto mantido |

### 10.4 Botão "Começar agora" (FAB)

- **Tamanho:** 64×64 (mínimo 56 para acessibilidade).
- **Cor:** `primary-500`.
- **Animação de entrada:** pulse suave a cada 30s.
- **Posição:** central inferior; 16px das bordas.

---

## 11. Cards

### 11.1 Anatomia

```
┌─────────────────────────┐
│  [Capa / ícone]         │
│                         │
│  Título (text-lg,       │
│   semibold)             │
│                         │
│  Descrição (text-sm,    │
│   neutral-600)          │
│                         │
│  ⏱ 5min • ● Médio       │
└─────────────────────────┘
```

### 11.2 Variantes

| Variante | Sombra | Uso |
|----------|--------|-----|
| `flat` | nenhuma | Listas |
| `default` | `shadow-sm` | Padrão |
| `elevated` | `shadow-md` | Destaque |
| `interactive` | `shadow-sm` + hover `shadow-md` | Clicável |

---

## 12. Inputs e formulários

### 12.1 Anatomia

```
Label (text-sm, semibold)
[.........................]  ← input
Helper (text-xs) ou erro
```

### 12.2 Estados

| Estado | Borda |
|--------|-------|
| Default | `neutral-200` |
| Focus | `primary-500` + anel |
| Error | `danger-500` |
| Disabled | `neutral-100` fundo |

### 12.3 Tipos

- Text
- Email
- Senha (com toggle de visibilidade)
- Data
- Hora
- Seleção (dropdown)
- Slider (volume, intensidade)
- Stepper (doses)

---

## 13. Toggles e checkboxes

| Componente | Tamanho | Cor ativa |
|------------|---------|-----------|
| Toggle | 52×32 | `primary-500` |
| Checkbox | 20×20 | `primary-500` |
| Radio | 20×20 | `primary-500` |

---

## 14. Tags e chips

| Tipo | Uso | Cor |
|------|-----|-----|
| `categoria` | Domínio clínico | `primary-500` texto + fundo `primary-50` |
| `duracao` | Tempo | `neutral-600` texto + fundo `neutral-100` |
| `intensidade` | Suave/Moderada/Intensa | `calm-500` / `energy-500` / `sleep-500` |
| `evidencia` | Nível A/B/C | `success-500` / `warning-500` / `neutral-500` |
| `novo` | Lançamento recente | `info-500` texto + `info-100` fundo |

---

## 15. Timers e cronômetros

### 15.1 Display numérico

- Fonte **tabular figures** (evitar pulos).
- Tamanho: 48px em player.
- Cor: `neutral-800`.
- Formato: `mm:ss` (até 60 min) ou `h:mm:ss`.

### 15.2 Animação de transição de número

- Crossfade de 200ms entre valores.

---

## 16. Barras de progresso

### 16.1 Linear

- Altura: 8px (padrão) ou 4px (sutil).
- Fundo: `neutral-100`.
- Preenchimento: gradiente `primary-300` → `primary-500`.
- Borda arredondada: `radius-full`.

### 16.2 Circular (anel respiratório)

- Anel externo: trilha `neutral-100`.
- Anel de progresso: `primary-500`.
- Animação: stroke-dashoffset com `ease-breath`.

---

## 17. Visualização respiratória (componente central)

### 17.1 Especificações

| Aspecto | Valor |
|---------|-------|
| Forma | Círculo SVG ou Canvas |
| Cor base | `primary-500` com gradiente radial |
| Crescimento | 1.0 → 1.4 (escala) |
| Tempo | Sincronizado com a fase do protocolo |
| Glow | `box-shadow` interno `primary-300` 30% |

### 17.2 Fases visuais

| Fase | Visual |
|------|--------|
| Inspirar | Cresce + brilho aumenta |
| Segurar (cheio) | Pulsação leve |
| Expirar | Diminui + brilho reduz |
| Segurar (vazio) | Parado, opacidade reduzida |

### 17.3 Alternativas (vide `09_ANIMATION_SYSTEM.md`)

- Pulmão (para fins didáticos)
- Flor (modo infantil / TEA)
- Onda (modo sono)
- Esfera (modo profundo)
- Mandala (modo mindfulness)
- Partículas (modo energia)

---

## 18. Listas e itens

### 18.1 Histórico de sessões

```
┌─────────────────────────┐
│ ⏱ 4-7-8        5 min ✓  │
│    terça, 24 jun        │
│    • Como se sentiu: 😊  │
└─────────────────────────┘
```

### 18.2 Lista de pacientes (profissional)

```
┌─────────────────────────┐
│ ╭──╮                    │
│ │CH│ Carlos Henrique    │
│ ╰──╯ Adesão 86% 🔥 7    │
│       Última: hoje       │
└─────────────────────────┘
```

---

## 19. Modais e sheets

### 19.1 Modal

- Centralizado.
- `shadow-lg`, `radius-lg`.
- Padding `space-6`.
- Backdrop com `rgba(0,0,0,.4)`.

### 19.2 Bottom sheet

- 100% largura.
- Topo arredondado `radius-xl`.
- Drag handle visível.
- Altura adaptativa ao conteúdo.

---

## 20. Toasts e feedbacks

| Tipo | Cor de fundo | Ícone |
|------|-------------|-------|
| Sucesso | `success-100` | ✓ |
| Erro | `danger-100` | ! |
| Aviso | `warning-100` | ! |
| Info | `info-100` | i |

Posição: topo (não inferior, para não atrapalhar sessão).
Duração: 3–5s. Dismissível.

---

## 21. Estados vazios, de erro e de carregamento

### 21.1 Estado vazio

- Ilustração leve.
- Título amigável.
- Ação clara.

Exemplo:
```
┌─────────────────────────┐
│                         │
│     ~~~ vazio ~~~       │
│                         │
│  Você ainda não fez      │
│  nenhuma sessão.         │
│                         │
│  [ Começar agora ]      │
└─────────────────────────┘
```

### 21.2 Erro

- Mensagem sem jargão técnico.
- Caminho de recuperação sempre presente.

### 21.3 Carregamento

- Skeleton (não spinner) em listas.
- Spinner central em ações.

---

## 22. Acessibilidade

### 22.1 Contraste
- Mínimo **4.5:1** para texto normal.
- Mínimo **3:1** para texto grande.

### 22.2 Foco
- Sempre visível.
- Cor `primary-500` + anel `shadow-focus`.

### 22.3 Leitor de tela
- Labels em todos os campos.
- ARIA em componentes custom.
- Ordem de leitura lógica.

### 22.4 Toque
- Área mínima **44×44 px**.
- Espaçamento entre alvos **8px mínimo**.

### 22.5 Movimento
- Respeitar `prefers-reduced-motion`.
- Versão "sem animação" (apenas áudio).

---

## 23. Tom de voz e microcopy

### 23.1 Princípios
- **Humano, nunca robótico.**
- **Acolhedor, nunca alarmista.**
- **Curto, nunca prolixo.**
- **Inclusivo (linguagem neutra).**

### 23.2 Exemplos

| Situação | Copy |
|----------|------|
| Iniciar sessão | "Vamos começar" |
| Conclusão | "Muito bem" |
| Sessão perdida | "Sem culpa. Retome quando quiser." |
| Erro técnico | "Algo deu errado. Tente de novo." |
| Re-engajamento (7 dias) | "Sentimos sua falta." |
| Re-engajamento (30 dias) | "Recomeçar é simples." |
| SOS | "Vamos respirar juntos" |
| Modo sono | "Boa noite" |

### 23.3 O que evitar

- "Falha catastrófica"
- "Erro 503"
- "Oops!"
- Gatilhos negativos
- Julgamento

---

## 24. Padrões específicos do modo terapêutico

### 24.1 "Modo Terapêutico" (paciente)

Ativado automaticamente quando o paciente indica objetivo clínico (ansiedade, dor, sono). Características:

- Paleta dessaturada (ex: `calm-500` em vez de `primary-500`).
- Tipografia levemente maior.
- Animações mais lentas (`+200ms`).
- Sem cores "alertas" (warning).
- Visual respiratório mais orgânico.

### 24.2 "Modo Profundo" (sessão)

Durante a sessão ativa:
- Fundo `neutral-50` ou escuro suave (`#1B1F1D`).
- Sem header / navegação.
- Apenas o visual respiratório + cronômetro.
- Áudio sempre opcional.
- Botão "encerrar" discreto mas acessível.

### 24.3 "Modo Idoso"

- Texto: `text-lg` mínimo (18px).
- Botões: altura mínima 56px.
- Sem ícones decorativos.
- Linguagem simples.

### 24.4 "Modo Infantil"

- Visual lúdico (flor, animal).
- Cores vibrantes controladas.
- Música divertida.
- Sem texto clínico.

---

## 25. Documentação viva

Este design system é a fonte de verdade. Mudanças exigem:
- PR de design.
- Revisão por UX + Tech Lead.
- Atualização dos componentes e tokens.
- Comunicação à equipe.

---

*Design é um sistema, não uma página.*