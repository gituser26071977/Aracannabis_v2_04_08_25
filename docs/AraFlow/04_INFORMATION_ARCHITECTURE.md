# AraFlow — Arquitetura da Informação

> **Versão:** 0.1.0
> **Data:** 2026-06-24
> **Owner:** UX Designer + Software Architect

---

## Sumário

1. Visão geral
2. Princípios de IA
3. Mapa do site (sitemap)
4. Taxonomia de protocolos
5. Modelo de navegação
6. Hierarquia de telas
7. Estrutura de URLs
8. Sistema de busca
9. Componentes de página
10. Padrões de listagem
11. Modal vs página
12. Estados e mensagens
13. Internacionalização

---

## 1. Visão geral

A Arquitetura da Informação (AI) do AraFlow organiza o conteúdo de modo a:

- **Reduzir a distância até a sessão**: o paciente deve chegar ao "começar agora" em ≤ 2 cliques a partir de qualquer tela.
- **Separar o que é "meu" (pessoal) do que é "biblioteca" (geral)**: dois eixos cognitivos distintos.
- **Reforçar a hierarquia profissional-paciente**: profissionais veem primeiro a prescrição; pacientes veem primeiro a sessão.

A IA é desenhada para ser **futurível**: o MVP cabe em poucos níveis; a Fase 3 caberá com expansão modular.

---

## 2. Princípios de IA

| # | Princípio | Aplicação |
|---|-----------|-----------|
| 1 | **Começar antes de configurar** | A tela principal já tem um botão "Começar agora". |
| 2 | **Menos é mais** | Apenas 4 áreas principais para o paciente. |
| 3 | **Reconhecimento > lembrança** | Ícones e cores sinalizam o tipo de protocolo. |
| 4 | **Hierarquia clara** | Sessão > Prescrição > Biblioteca > Conta. |
| 5 | **Erros são caminhos** | Estados vazios sempre oferecem uma ação. |
| 6 | **Mobile-first** | Toda navegação é testada em 360px primeiro. |
| 7 | **Consistência cross-ARA** | Padrões visuais e de nomenclatura do AraOS. |

---

## 3. Mapa do site (sitemap)

### 3.1 Paciente

```
Home (AraFlow)
├── Começar agora (Sessão rápida)
├── Prescrito (a fazer hoje)
├── Explorar (biblioteca geral)
│   ├── Categoria (Ansiedade, Sono, Foco, ...)
│   │   └── Protocolo (detalhe + iniciar)
│   └── Busca
├── Progresso
│   ├── Estatísticas (sessões, minutos, streak)
│   ├── Relatórios (semanal, mensal)
│   └── Escalas (GAD-7, ISI, PSS-10) [Fase 2]
├── Conta
│   ├── Perfil
│   ├── Consentimentos
│   ├── Notificações
│   ├── Acessibilidade
│   ├── Exportar dados (LGPD)
│   ├── Excluir conta (LGPD)
│   └── Ajuda
└── (futuro) Profissionais
    └── Lista de profissionais que acompanham
```

### 3.2 Profissional

```
AraFlow (modo profissional)
├── Prescrever
│   ├── Selecionar paciente
│   ├── Escolher protocolo
│   ├── Definir dose
│   └── Confirmar
├── Meus pacientes (lista)
│   ├── Detalhe do paciente
│   │   ├── Adesão
│   │   ├── Histórico de sessões
│   │   ├── Escalas
│   │   └── Notas clínicas
├── Biblioteca de protocolos
│   ├── Categorias
│   └── Protocolo (detalhe + referências)
└── Conta
```

### 3.3 Admin (AraOS)

```
Admin → Módulos → AraFlow
├── Estatísticas globais
├── Lista de usuários
├── Logs clínicos
└── Configurações do módulo
```

---

## 4. Taxonomia de protocolos

### 4.1 Nível 1 — Domínio clínico

| Código | Domínio | Exemplos |
|--------|---------|---------|
| ANS | Ansiedade | "Respiração 4-7-8", "Box breathing" |
| SON | Sono | "Coerência cardíaca 5.5", "4-7-8 para dormir" |
| DOR | Dor | "Respiração diafragmática para dor" |
| FOC | Foco | "Respiração alternada", "Foco profundo 5 min" |
| REL | Relaxamento | "Body scan 10 min" |
| BUR | Burnout | "Reset 5 min" |
| CAN | Cannabis medicinal | "Respiração de ancoragem" |
| APN | AH/SD / Apneia | "Respiração lenta supervisionada" |
| TEA | TEA / regulação | "Flor que abre" (visual lúdico) |
| TDA | TDAH / atenção | "Reset 3 min", "Foco curto" |
| SAI | Saúde geral | "Respiração matinal" |

### 4.2 Nível 2 — Objetivo

- Agudo (intervenção curta)
- Manutenção (programa longo)
- Performance (pré-tarefa)

### 4.3 Nível 3 — Intensidade

- Suave (4-6 respirações/min)
- Moderada (6-10)
- Intensa (>10)

### 4.4 Nível 4 — Duração

- Micro (3 min)
- Curto (5 min)
- Médio (10 min)
- Longo (20 min)

### 4.5 Tags transversais

- "com áudio", "silencioso", "guiado por voz", "apenas visual"
- "iniciante", "intermediário", "avançado"
- "com música", "com ruído branco", "com biofeedback"

---

## 5. Modelo de navegação

| Tipo de navegação | Onde | Como |
|-------------------|------|------|
| **Bottom tab** (mobile) | Home, Explorar, Progresso, Conta | Fixo, sempre visível |
| **Top bar** | Título, voltar, ações | Contextual |
| **FAB (botão flutuante)** | "Começar agora" | Central, persistente |
| **Side menu** | Apenas profissional | Desktop |
| **Modal** | Configurações rápidas | Foco único |

---

## 6. Hierarquia de telas

```
Nível 0 (raiz)
└── Home

Nível 1
├── Sessão (player)
├── Explorar
├── Progresso
├── Conta
└── (profissional) Prescrever

Nível 2
├── Protocolo detalhe
├── Relatório detalhe
└── Perfil detalhe

Nível 3 (raros)
├── Configurações avançadas
└── Diagnóstico de erro
```

Regra: **nunca mais que 3 níveis de profundidade** sem um indicador claro de caminho.

---

## 7. Estrutura de URLs (futura)

| Recurso | URL |
|---------|-----|
| Home | `/araflow` |
| Sessão | `/araflow/session/:id` |
| Explorar | `/araflow/explore` |
| Categoria | `/araflow/explore/c/:slug` |
| Protocolo | `/araflow/protocol/:id` |
| Progresso | `/araflow/progress` |
| Conta | `/araflow/account` |
| Prescrever | `/araflow/prof/prescribe` |
| Pacientes | `/araflow/prof/patients` |
| Paciente detalhe | `/araflow/prof/patients/:id` |

---

## 8. Sistema de busca

### 8.1 Quando buscar
- Em "Explorar" (biblioteca geral).
- Em "Prescrever" (para profissional achar protocolo).

### 8.2 Critérios de busca
- Texto livre (nome, descrição).
- Filtros: domínio, duração, intensidade, nível.
- Ordenação: popularidade, evidência, novidade.

### 8.3 UX
- Sugestões automáticas após 2 caracteres.
- Resultados com thumbnail e tempo de duração visíveis.
- Estado vazio sempre com sugestão ("Tente 'ansiedade'" ou "Ver todos").

---

## 9. Componentes de página

| Componente | Função |
|------------|--------|
| **Header** | Título + ações contextuais |
| **BottomNav** | Tabs principais |
| **FAB** | Botão flutuante "Começar agora" |
| **CardProtocolo** | Capa, título, duração, intensidade |
| **PlayerSessao** | Visual respiratório + controles |
| **BarraProgresso** | Tempo decorrido / total |
| **ListaSessoes** | Histórico do dia/semana |
| **ModalConfirmacao** | Confirmações críticas |
| **Toast** | Feedback rápido |
| **EmptyState** | Estado vazio com ação |
| **ErrorState** | Erro com recuperação |
| **BannerClinico** | Alerta ou contraindicação |

---

## 10. Padrões de listagem

| Lista | Layout |
|-------|--------|
| Protocolos | Grid 2 colunas (mobile 1 coluna) |
| Sessões (histórico) | Lista vertical compacta |
| Pacientes (profissional) | Lista com avatar + último status |
| Conquistas | Grid horizontal scroll |

---

## 11. Modal vs página

| Caso | Modal | Página |
|------|-------|--------|
| Confirmação de prescrição | ✅ | |
| Detalhe de protocolo (rápido) | ✅ | |
| Player de sessão | | ✅ (fullscreen) |
| Relatório detalhado | | ✅ |
| Configurações avançadas | | ✅ |
| Escala clínica (Fase 2) | ✅ (modal longo) | |

---

## 12. Estados e mensagens

### 12.1 Estado vazio (exemplo)

> **Tela:** Histórico de sessões (paciente novo)
> **Mensagem:** "Você ainda não fez nenhuma sessão."
> **Ação:** [Começar agora]

### 12.2 Estado de erro

> **Tela:** Sessão interrompida por falha de rede
> **Mensagem:** "Não conseguimos continuar. Seu progresso foi salvo."
> **Ação:** [Tentar de novo] [Voltar à home]

### 12.3 Estado de sucesso

> **Tela:** Fim de sessão
> **Mensagem:** "Muito bem. +5 minutos para seu streak."
> **Ação:** [Ver progresso] [Voltar à home]

### 12.4 Contraindicação clínica

> **Tela:** Protocolo "Respiração intensa 6-2-6"
> **Banner:** "Contraindicado em: glaucoma, hernia de hiato grande, gravidez de risco. Confirme com seu médico."

---

## 13. Internacionalização

### 13.1 Idiomas planejados

| Idioma | Fase |
|--------|------|
| PT-BR | MVP |
| EN | Fase 2 |
| ES | Fase 3 |

### 13.2 Padrões
- Não concatenar strings em código.
- Toda string em arquivo de tradução.
- Suporte a pluralização correta.
- Datas e números em formato local.

---

## 14. Acessibilidade da informação

- **Contraste** mínimo WCAG AA.
- **Leitor de tela**: títulos hierárquicos corretos; ARIA em componentes custom.
- **Foco visível** sempre.
- **Atalhos**: tecla `Espaço` para iniciar/pausar sessão.
- **Modo simples** com vocabulário reduzido.

---

## 15. Wireframes textuais (resumo)

Wireframes detalhados em `05_WIREFRAMES.md`. Resumo aqui:

| Tela | Elementos principais |
|------|----------------------|
| Home | Saudação, FAB "Começar agora", prescrição ativa, recomendação |
| Player | Visual animado + cronômetro + controles |
| Explorar | Filtros + grid de protocolos |
| Protocolo | Capa, ficha técnica, botão "Iniciar" |
| Progresso | Cards de estatística + gráfico simples |
| Conta | Lista de seções (perfil, consentimento, ajuda) |
| Prescrever | Busca de paciente → protocolo → dose → confirmar |

---

## 16. Decisões de IA abertas (registrar quando decididas)

| Decisão | Pendência |
|---------|-----------|
| Player deve ser página ou modal? | Página fullscreen (decidido) |
| Relatórios ficam em "Progresso" ou em subseção? | Subseção "Progresso → Relatórios" (decidido) |
| Profissional tem app separado? | Não, é o mesmo app com modo. (decidido) |
| Biofeedback é app separado? | Sim, módulo dedicado na Fase 3 (decidido) |

---

*Esta IA é documento vivo. Deve ser revisitada a cada marco.*