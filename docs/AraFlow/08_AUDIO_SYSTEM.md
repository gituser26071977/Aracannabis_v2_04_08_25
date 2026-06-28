# AraFlow — Sistema de Áudio

> **Versão:** 0.1.0
> **Data:** 2026-06-24
> **Owner:** Product Owner + UX Designer
>
> Este documento define como o AraFlow usa **áudio** para amplificar a experiência terapêutica: música, narração, ruído ambiente, feedback sonoro e acessibilidade.

---

## Sumário

1. Princípios
2. Camadas de áudio
3. Biblioteca musical
4. Narração guiada
5. Ruído ambiente e paisagens sonoras
6. Feedback sonoro (UI)
7. Áudio como guia respiratório (metronômo)
8. Áudio como dado clínico (biofeedback — Fase 3)
9. Modos por objetivo clínico
10. Mixagem e masterização
11. Acessibilidade auditiva
12. Direitos autorais e licenciamento
13. Especificações técnicas
14. Roadmap de conteúdo

---

## 1. Princípios

1. **Nunca competir com a respiração.** O áudio deve facilitar, nunca distrair.
2. **Caminho de saída sempre presente.** Em qualquer camada, sempre é possível silenciar.
3. **Calmo, mas não monótono.** Variação sutil é mais terapêutica.
4. **Padrão harmônico coerente** (432 Hz ou 528 Hz como base opcional, sem afirmar efeito terapêutico direto).
5. **Latência mínima** entre ação do usuário e resposta sonora.

---

## 2. Camadas de áudio

O áudio do AraFlow é organizado em **5 camadas independentes**:

```
┌──────────────────────────────────┐
│ 1. Metronômo respiratório (TTS)  │ ← guia da respiração
├──────────────────────────────────┤
│ 2. Música de fundo               │ ← trilha
├──────────────────────────────────┤
│ 3. Paisagem sonora ambiente      │ ← textura
├──────────────────────────────────┤
│ 4. Narração guiada (opcional)    │ ← voz
├──────────────────────────────────┤
│ 5. Feedback de UI                │ ← cliques, alertas
└──────────────────────────────────┘
```

Cada camada tem volume independente e pode ser ativada/desativada.

---

## 3. Biblioteca musical

### 3.1 Categorias

| Categoria | BPM aprox. | Tonalidade | Uso |
|-----------|-----------|-----------|-----|
| **Calma profunda** | 40–60 | Lá menor / Ré maior | Ansiedade, sono |
| **Calma média** | 50–70 | Dó maior / Fá maior | Meditação, dor |
| **Foco suave** | 60–80 | Sol maior | Trabalho, estudo |
| **Energia suave** | 70–90 | Lá maior | Manhã, motivação |
| **Infantil** | 80–100 | Dó maior / Sol maior | TEA, TDAH |
| **Sono (drone)** | 30–50 | Drone contínuo | Indução ao sono |

### 3.2 Estilos

- **Ambient** (principal)
- **Piano solo minimalista**
- **Pads sintetizados** (caldos, quentes)
- **Natureza + textura** (chuva, vento, floresta)
- **Binaural beats** (opcional, com aviso)
- **Classical adaptativo** (Bach, Satie, Pärt)

### 3.3 Duração

- Faixas de **5, 10, 20 e 30 minutos**.
- Loopagem suave (crossfade de 8s).
- Sem breaks ou interrupções bruscas.

### 3.4 Banco inicial do MVP

| Trilha | Categoria | Duração |
|--------|-----------|---------|
| `calm-deepsleep-01` | Calma profunda | 30 min |
| `calm-deepsleep-02` | Calma profunda | 20 min |
| `calm-anxiety-01` | Calma média | 10 min |
| `calm-anxiety-02` | Calma média | 5 min |
| `focus-deep-01` | Foco suave | 20 min |
| `focus-deep-02` | Foco suave | 10 min |
| `morning-rise-01` | Energia suave | 5 min |
| `sleep-drone-01` | Drone contínuo | 30 min |
| `rain-light` | Paisagem | 60 min (loop) |
| `forest-soft` | Paisagem | 60 min (loop) |
| `ocean-far` | Paisagem | 60 min (loop) |
| `white-noise-soft` | Ruído | 60 min (loop) |

> Total MVP: **12 trilhas**. Biblioteca Fase 2: **40+ trilhas**.

---

## 4. Narração guiada

### 4.1 Função
- Guiar sessões longas (body scan).
- Acolhimento inicial.
- Encerramento.

### 4.2 Vozes

| Voz | Característica | Uso |
|-----|----------------|-----|
| **Feminina 1 (PT-BR)** | Calma, pausada, levemente grave | Padrão |
| **Feminina 2 (PT-BR)** | Mais suave, maternal | Modo sono |
| **Masculina (PT-BR)** | Firme, neutra | Modo foco |
| **Infantil** | Divertida, ritmada | Modo TEA/TDAH |
| **EN (Fase 2)** | Internacional | — |
| **ES (Fase 3)** | Internacional | — |

### 4.3 Diretrizes de gravação

- Frequência fundamental: **110–180 Hz**.
- Velocidade: **0.85x** (mais lento).
- Pausas: ≥ 700ms entre frases.
- Sem "ahs", "uhms", respirações invasivas.
- Tom acolhedor, nunca diretivo ("Vamos respirar juntos" > "Respire agora").

### 4.4 Conteúdo de narração

| Sessão | Fala |
|--------|------|
| Início | "Encontre uma posição confortável. Vamos começar." |
| Inspiração | "Inspire... suavemente." |
| Expiração | "Expire... soltando." |
| Pausa (cheio) | "Segure... sem forçar." |
| Pausa (vazio) | "Solte... devagar." |
| Encerramento | "Muito bem. Quando estiver pronto, abra os olhos." |

---

## 5. Ruído ambiente e paisagens sonoras

### 5.1 Categorias

| Tipo | Uso | Volume sugerido |
|------|-----|------------------|
| Chuva leve | Calma, sono | -18 dB |
| Floresta com pássaros | Meditação, ansiedade | -18 dB |
| Oceano distante | Sono | -20 dB |
| Vento suave | Foco | -22 dB |
| Ruído branco | TDAH (mask de distractores) | -16 dB |
| Ruído rosa | Recuperação | -16 dB |

### 5.2 Paisagens vs música
- Usuário pode escolher **somente paisagem**, **somente música**, ou **ambos mixados**.
- Paisagens mixadas com música têm volume reduzido automaticamente.

---

## 6. Feedback sonoro (UI)

| Evento | Som | Duração |
|--------|-----|---------|
| Toque em botão | "tap" suave | 60ms |
| Sucesso | "ding" acolhedor | 200ms |
| Erro | "thud" abafado | 150ms |
| Início de sessão | "bloom" (3 notas) | 600ms |
| Fim de sessão | "bell" suave | 800ms |
| Conquista | "chime" ascendente | 500ms |

**Princípios:**
- Sons curtos (<1s).
- Em região 200–800 Hz (calor).
- Volume -22 dB (não compete com música).
- Totalmente substituíveis pelo usuário.

---

## 7. Áudio como guia respiratório (metronômo)

### 7.1 Função
Sinalizar **quando** inspirar, segurar, expirar, segurar.

### 7.2 Modalidades

| Modalidade | Descrição | Quando usar |
|------------|-----------|-------------|
| **Tom suave** | Sine wave 220 Hz | Padrão |
| **Tom grave** | 110 Hz | Segurar (cheio) |
| **Tom médio** | 165 Hz | Expirar |
| **Tom agudo** | 330 Hz | Inspirar |
| **Voz TTS curta** | "inspire", "solte" | Para iniciantes |
| **Ping + fade** | Decai em 4s | Para meditadores experientes |
| **Vibração** | Tátil (em mobile) | Acessibilidade |

### 7.3 Volume relativo
- **Mais alto** que música (3 dB acima).
- **Mais suave** que voz.
- Ajustável em -20 dB a 0 dB.

### 7.4 Mapeamento temporal

```
Inspirar 4s:
  T=0s ─────── T=4s
  volume: 0.4 ──────> 0.0 (fade decrescente)

Segurar 4s:
  T=0s ─────── T=4s
  tom único, sem variação

Expirar 4s:
  T=0s ─────── T=4s
  volume: 0.0 ──────> 0.4 (fade crescente)
```

---

## 8. Áudio como dado clínico (biofeedback — Fase 3)

Na Fase 3, o áudio também será **dado de feedback**:

- HRV modulando timbre de fundo.
- Tom "mais brilhante" = mais coerência.
- Permite "ouvir" seu estado autonômico.

### 8.1 Implementação (planejada)
- Entrada: HRV (PPG ou ECG).
- Processamento: em tempo real no cliente.
- Saída: filtro modulante no áudio ambiente.

---

## 9. Modos por objetivo clínico

| Objetivo | Camadas típicas |
|----------|-----------------|
| Ansiedade | Drone + narração feminina + tom respiratório + paisagem chuva |
| Sono | Drone + narração feminina + tom respiratório + paisagem chuva/ocean |
| Foco | Música pad + tom respiratório curto (sem narração) + silêncio |
| TDAH | Música ritmada + tom respiratório ping + ruído branco |
| TEA | Música infantil + tom suave + narração infantil |
| Dor | Drone grave + narração feminina + body scan |
| Cannabis medicinal | Drone + tom respiratório + narração breve |
| Burnout | Drone + paisagem + tom respiratório + acolhimento |

---

## 10. Mixagem e masterização

### 10.1 Padrões técnicos

| Parâmetro | Valor |
|-----------|-------|
| Sample rate | 48 kHz |
| Bit depth | 24-bit |
| Loudness | -18 LUFS |
| True peak | -1 dBTP |
| Formato | FLAC (biblioteca), AAC 128 kbps (streaming) |

### 10.2 Masterização
- Todas as trilhas passam por master **mesmo nível**.
- Sem compressão agressiva.
- Faixa dinâmica preservada.

### 10.3 Crossfade entre sessões
- 4s entre faixas (suave).

---

## 11. Acessibilidade auditiva

### 11.1 Para pessoas com deficiência auditiva
- **Vibração** sincronizada com fases (mobile).
- **Visual respiratório** sempre presente.
- **Subtítulos** para narração (futuro).

### 11.2 Para pessoas com hipersensibilidade
- Modo "sem áudio": apenas visual + vibração.
- Modo "baixa frequência": retira graves.

### 11.3 Para TDAH / TEA
- Modo "ruído mascarante": ruído branco/rosa mais intenso.

---

## 12. Direitos autorais e licenciamento

### 12.1 Princípios
- **100% royalty-free** ou **licenciado para AraFlow** em definitivo.
- Atribuição visível em página de créditos (rodapé do app).
- Sem conteúdo gerado por IA sem revisão humana na MVP.

### 12.2 Fontes preferenciais
- Compositores independentes (assinatura direta).
- Bancos royalty-free com licença perpétua (Epidemic Sound, Artlist).
- Músicos parceiros (criação original sob demanda).

### 12.3 Créditos obrigatórios
```
AraFlow · Trilha "Calma Profunda 01"
Composição: [Nome]
Licença: AraFlow
© 2026
```

---

## 13. Especificações técnicas

### 13.1 Formatos suportados

| Plataforma | Formato | Codec |
|------------|---------|-------|
| Web | MP3 / AAC | streaming adaptativo |
| iOS | AAC | nativo |
| Android | AAC / Opus | nativo |
| Offline | FLAC (pacote) + AAC (cache) | — |

### 13.2 Streaming e cache

- Streaming adaptativo: **128 kbps mínimo**.
- Cache local: últimas 5 trilhas usadas.
- Offline-first: pacote de 3 trilhas embarcadas.

### 13.3 Latência
- Início da sessão ao primeiro som: **< 800ms**.
- Sincronia visual-auditiva: **±50ms**.

---

## 14. Roadmap de conteúdo

| Fase | Quantidade de trilhas |
|------|------------------------|
| MVP | 12 (3 por categoria) |
| Fase 2 | 40 (8 por categoria) |
| Fase 3 | 100+ (incluindo biofeedback) |

### 14.1 Calendário de lançamentos
- Lançamento MVP: pacote essencial.
- A cada 2 meses: novas trilhas sazonais (inverno, primavera, etc.).
- Anualmente: pacote de "foco cultural" (meditação tibetana, indígena, etc.).

---

*O silêncio também é parte da biblioteca. Nem toda sessão precisa de áudio.*