# AraFlow — Wireframes

> **Versão:** 0.1.0
> **Data:** 2026-06-24
> **Owner:** UX Designer
>
> Wireframes em **ASCII**. Servem como guia de layout, não como design final. Todos os wireframes são **mobile-first** (360×800). Variações desktop são indicadas quando relevantes.

---

## Legenda de símbolos

```
[ ]   Botão / ação clicável
[...]  Campo de entrada de texto
(...)  Indicador de estado / label
===    Divisor / separador
~~~    Imagem / ícone / mídia
▼     Dropdown / expansível
★     Estrela / favorito / marcador
●     Ponto de estado
⏱     Tempo / cronômetro
▶ ⏸ ⏹ Controles de mídia
+ -   Mais / menos
→     Fluxo / próxima tela
[OK]  Confirmação
```

---

## Índice de telas

1. Splash / Loading
2. Onboarding — Boas-vindas
3. Onboarding — Escolher objetivo
4. Onboarding — Permissões
5. Login
6. Home do paciente
7. Player de sessão
8. Player — controles expandidos
9. Tela de conclusão de sessão
10. Avaliação subjetiva pós-sessão
11. Explorar (biblioteca)
12. Filtros de exploração
13. Detalhe do protocolo
14. Categoria de protocolos
15. Progresso
16. Relatório semanal
17. Escalas clínicas (Fase 2)
18. Conta
19. Perfil
20. Consentimentos (LGPD)
21. Notificações
22. Acessibilidade
23. Ajuda
24. Exportar dados (LGPD)
25. Excluir conta (LGPD)
26. Modo SOS (ansiedade aguda)
27. Modo idoso (acessibilidade)
28. Modo infantil (TEA/TDAH)
29. Tela inicial do profissional
30. Selecionar paciente (prescrição)
31. Escolher protocolo (prescrição)
32. Definir dose e confirmar prescrição
33. Meus pacientes (profissional)
34. Detalhe do paciente (profissional)
35. Biblioteca de protocolos (profissional)
36. Admin AraFlow (AraOS)

---

## 1. Splash / Loading

```
┌──────────────────────────┐
│                          │
│                          │
│                          │
│                          │
│       ~~~ AraFlow ~~~    │
│                          │
│      "Respire com       │
│        cuidado"          │
│                          │
│         ( • )            │
│                          │
│                          │
│                          │
└──────────────────────────┘
```

---

## 2. Onboarding — Boas-vindas (1/4)

```
┌──────────────────────────┐
│  (1)  (2)  (3)  (4)      │
│                          │
│     ~~~ flor ~~~         │
│                          │
│   Bem-vindo ao AraFlow   │
│                          │
│  Respiração, foco e      │
│  calma com base          │
│  científica.             │
│                          │
│                          │
│                          │
│  [      Pular      ]     │
│  [    Continuar  → ]     │
└──────────────────────────┘
```

---

## 3. Onboarding — Escolher objetivo (2/4)

```
┌──────────────────────────┐
│  (✓)  (•)  ( )  ( )      │
│                          │
│   O que você busca?      │
│                          │
│  [ ] Reduzir ansiedade   │
│  [ ] Dormir melhor       │
│  [ ] Aliviar dor         │
│  [ ] Mais foco           │
│  [ ] Relaxar             │
│                          │
│  (Você poderá mudar      │
│   depois)                │
│                          │
│                          │
│  [    Continuar  → ]     │
└──────────────────────────┘
```

---

## 4. Onboarding — Permissões (3/4)

```
┌──────────────────────────┐
│  (✓)  (✓)  (•)  ( )      │
│                          │
│   Para uma boa           │
│   experiência,           │
│   podemos:               │
│                          │
│  [ ✓ ] Notificações      │
│       Lembrar suas       │
│       sessões            │
│                          │
│  [ ] Áudio em segundo    │
│      plano              │
│                          │
│                          │
│  [    Continuar  → ]     │
└──────────────────────────┘
```

---

## 5. Login

```
┌──────────────────────────┐
│  ←                       │
│                          │
│       ~~~ AraOS ~~~      │
│       "Entrar"           │
│                          │
│  Você está entrando no   │
│  AraFlow com sua conta   │
│  AraOS.                  │
│                          │
│  Email:                  │
│  [....................]  │
│                          │
│  Senha:                  │
│  [....................]  │
│                          │
│  [    Entrar      ]      │
│                          │
│  Esqueci a senha         │
└──────────────────────────┘
```

---

## 6. Home do paciente

```
┌──────────────────────────┐
│  Olá, Carlos ☀           │
│  Hoje, terça, 24 jun     │
│                          │
│ ╭──────────────────────╮ │
│ │   Prescrito hoje     │ │
│ │   2 sessões          │ │
│ │                      │ │
│ │  [ Começar agora ]   │ │
│ ╰──────────────────────╯ │
│                          │
│  Para você               │
│  ─────────────           │
│  ╭──────╮ ╭──────╮       │
│  │ ~~~  │ │ ~~~  │       │
│  │Calma │ │Sono  │       │
│  │ 5min │ │ 10m  │       │
│  ╰──────╯ ╰──────╯       │
│                          │
│  Streak: 7 dias 🔥        │
│                          │
├──────────────────────────┤
│ 🏠    🧭    📈    👤      │
│ Home Explorar Progresso  │
└──────────────────────────┘
```

---

## 7. Player de sessão

```
┌──────────────────────────┐
│        ✕                 │
│                          │
│                          │
│       ╭───────╮          │
│       │       │          │
│       │   ◯   │ ← círculo respiratório
│       │       │          │
│       ╰───────╯          │
│                          │
│      Inspire...          │
│                          │
│      ⏱ 02:34 / 05:00    │
│                          │
│                          │
│      [  ⏸ Pausar  ]      │
│                          │
│                          │
│      [ Encerrar ]        │
│                          │
│      🔊 ▁▂▃▄▅▆▇          │
│                          │
├──────────────────────────┤
│   ●●●●○                 │
│   sessão em andamento    │
└──────────────────────────┘
```

Estados do círculo:

```
Inspire (cresce)   Segure (cheio)   Expire (diminui)   Segure (vazio)
    ╭───╮             ╭───╮            ╭───╮              ╭───╮
    │ ◯ │             │ ◉ │            │ ○ │              │ · │
    ╰───╯             ╰───╯            ╰───╯              ╰───╯
```

---

## 8. Player — controles expandidos

```
┌──────────────────────────┐
│        ✕                 │
│                          │
│      [ Visualização ]    │
│                          │
│   ╭──────────────────╮   │
│   │   círculo grande │   │
│   │   respirando     │   │
│   ╰──────────────────╯   │
│                          │
│  Cronômetro: 02:34       │
│  ████████░░░░░░ 50%      │
│                          │
│  Visual:                 │
│  (•) Círculo             │
│  ( ) Pulmão              │
│  ( ) Onda                │
│  ( ) Flor                │
│                          │
│  Áudio:                  │
│  (•) Música              │
│  ( ) Guiado por voz      │
│  ( ) Silencioso          │
│                          │
│  Volume: 🔊 ▁▂▃▄▅▆▇      │
│                          │
│  [  ⏸ Pausar  ]          │
└──────────────────────────┘
```

---

## 9. Tela de conclusão de sessão

```
┌──────────────────────────┐
│                          │
│        ✨                │
│                          │
│      Muito bem,          │
│      Carlos!             │
│                          │
│   Você completou 5:00    │
│   minutos de calma.      │
│                          │
│   Streak: 7 dias 🔥      │
│                          │
│   Como você se sente?    │
│   [ 😞 ] [ 😐 ] [ 😊 ]   │
│                          │
│                          │
│  [ Ver progresso ]       │
│  [ Voltar à home ]       │
└──────────────────────────┘
```

---

## 10. Avaliação subjetiva pós-sessão

```
┌──────────────────────────┐
│                          │
│   Como você está agora?  │
│   (opcional)             │
│                          │
│   1 ──────── 5           │
│   muito       muito      │
│   ansioso     calmo      │
│                          │
│   [ 1 ] [ 2 ] [ 3 ]      │
│   [ 4 ] [ 5 ]            │
│                          │
│   Algo a registrar?      │
│   [.....................]│
│                          │
│   [ Salvar ]             │
│   [ Pular ]              │
└──────────────────────────┘
```

---

## 11. Explorar (biblioteca)

```
┌──────────────────────────┐
│  Explorar          🔍    │
│                          │
│  Categorias              │
│  ╭──────╮ ╭──────╮       │
│  │Ansie-│ │ Sono │       │
│  │ dade │ │      │       │
│  ╰──────╯ ╰──────╯       │
│  ╭──────╮ ╭──────╮       │
│  │ Foco │ │ Dor  │       │
│  ╰──────╯ ╰──────╯       │
│                          │
│  Em destaque             │
│  ─────────────           │
│  ╭──────╮ ╭──────╮       │
│  │ 4-7-8 │ │ Box  │       │
│  │ 5 min │ │ 5min │       │
│  ╰──────╯ ╰──────╯       │
│                          │
│  Mais populares          │
│  ─────────────           │
│  ╭──────╮ ╭──────╮       │
│  │ ~~~  │ │ ~~~  │       │
│  ╰──────╯ ╰──────╯       │
│                          │
├──────────────────────────┤
│ 🏠    🧭    📈    👤      │
└──────────────────────────┘
```

---

## 12. Filtros de exploração

```
┌──────────────────────────┐
│  ←  Filtros        [×]  │
│                          │
│  Duração                 │
│  [3 min][5 min][10 min]  │
│                          │
│  Intensidade             │
│  [Suave][Moderada]       │
│  [Intensa]               │
│                          │
│  Com áudio?              │
│  [Sim][Não]              │
│                          │
│  Nível                   │
│  [Iniciante]             │
│  [Intermediário]         │
│  [Avançado]              │
│                          │
│  Evidência               │
│  [Estudos randomizados]  │
│                          │
│  [ Aplicar 8 ]           │
└──────────────────────────┘
```

---

## 13. Detalhe do protocolo

```
┌──────────────────────────┐
│  ←    ★ Compartilhar     │
│                          │
│  ╭──────────────────╮    │
│  │     ~~~ capa ~~~  │   │
│  ╰──────────────────╯    │
│                          │
│  Respiração 4-7-8        │
│  para dormir             │
│                          │
│  ⏱ 5 min   ● Avançado    │
│                          │
│  "Inspiração curta,      │
│   expiração longa para   │
│   acalmar o sistema      │
│   nervoso."              │
│                          │
│  ⚠ Contraindicado em:    │
│  glaucoma, hérnia de     │
│  hiato, gravidez de      │
│  risco.                  │
│                          │
│  Base fisiológica        │
│  ────────────────        │
│  Ativação parassimpática │
│  via nervo vago...       │
│                          │
│  Evidência: nível B      │
│  (2 estudos RCT)         │
│                          │
│                          │
│  ╭─────────────────╮     │
│  │  Iniciar agora  │     │
│  ╰─────────────────╯     │
└──────────────────────────┘
```

---

## 14. Categoria de protocolos

```
┌──────────────────────────┐
│  ←  Ansiedade            │
│                          │
│  Para momentos agudos    │
│  ╭──────╮ ╭──────╮       │
│  │ 4-7-8 │ │ SOS  │       │
│  ╰──────╯ ╰──────╯       │
│                          │
│  Para o dia a dia        │
│  ╭──────╮ ╭──────╮       │
│  │ Box  │ │ Coer.│       │
│  ╰──────╯ ╰──────╯       │
│                          │
│  Manutenção (programa)   │
│  ╭──────╮ ╭──────╮       │
│  │ 7 dia│ │ 21dia│       │
│  ╰──────╯ ╰──────╯       │
└──────────────────────────┘
```

---

## 15. Progresso

```
┌──────────────────────────┐
│  Seu progresso           │
│                          │
│  ╭──────╮  ╭──────╮      │
│  │  12  │  │  60  │      │
│  │sessões│ │min tot│     │
│  ╰──────╯  ╰──────╯      │
│                          │
│  Streak: 7 dias 🔥       │
│                          │
│  Últimos 7 dias          │
│  ▁▂▃▅▇▆▇                  │
│                          │
│  Como você tem           │
│  se sentido?             │
│  (média últimas 4 sem.)  │
│                          │
│  ▁▃▄▆                    │
│                          │
│  [ Relatório completo ]  │
│  [ Compartilhar ]        │
│                          │
├──────────────────────────┤
│ 🏠    🧭    📈    👤      │
└──────────────────────────┘
```

---

## 16. Relatório semanal

```
┌──────────────────────────┐
│  ←  Relatório — Jun 17..23│
│                          │
│  Resumo                  │
│  Sessões: 5              │
│  Tempo total: 28 min     │
│  Categorias:             │
│   • Ansiedade 3          │
│   • Sono 2               │
│                          │
│  Padrão de uso           │
│  Manhã  ▇▇▇              │
│  Tarde  ▇                │
│  Noite  ▇▇▇▇             │
│                          │
│  Como você se sentiu     │
│  antes vs depois:        │
│  Antes: 4.1              │
│  Depois: 2.8             │
│                          │
│  [ Exportar PDF ]        │
│  [ Compartilhar          │
│    com profissional ]    │
└──────────────────────────┘
```

---

## 17. Escalas clínicas (Fase 2)

```
┌──────────────────────────┐
│  ←  GAD-7                │
│  (Questionário de        │
│  ansiedade)              │
│                          │
│  Nas últimas 2 semanas,  │
│  com que frequência      │
│  você foi incomodado     │
│  por:                    │
│                          │
│  1. Sentir-se nervoso,   │
│     ansioso ou no limite │
│                          │
│  (0) Nenhuma vez         │
│  (1) Vários dias         │
│  (2) Mais da metade      │
│  (3) Quase todos os dias │
│                          │
│  [ Próxima (2/7) → ]     │
│                          │
│  ███░░░░░ 30%            │
└──────────────────────────┘
```

---

## 18. Conta

```
┌──────────────────────────┐
│  Conta                   │
│                          │
│  Carlos Henrique         │
│  carlos@exemplo.com      │
│                          │
│ ────────────────────────  │
│                          │
│  👤 Perfil               │
│  🔔 Notificações         │
│  ♿ Acessibilidade       │
│                          │
│  🔒 Privacidade          │
│  ─ Consentimentos        │
│  ─ Exportar dados        │
│  ─ Excluir conta         │
│                          │
│  ❓ Ajuda                │
│  📜 Termos e privacidade │
│  🚪 Sair                 │
│                          │
├──────────────────────────┤
│ 🏠    🧭    📈    👤      │
└──────────────────────────┘
```

---

## 19. Perfil

```
┌──────────────────────────┐
│  ←  Perfil               │
│                          │
│  ╭────╮                 │
│  │ 👤 │   Carlos H.     │
│  ╰────╯                 │
│                          │
│  Nome                    │
│  [Carlos Henrique]       │
│                          │
│  Email (AraOS)           │
│  carlos@exemplo.com      │
│                          │
│  Data de nascimento      │
│  [12 / 04 / 1990]        │
│                          │
│  Objetivo principal      │
│  ▼ Dormir melhor         │
│                          │
│  [ Salvar ]              │
└──────────────────────────┘
```

---

## 20. Consentimentos (LGPD)

```
┌──────────────────────────┐
│  ←  Seus consentimentos  │
│                          │
│  Para usar o AraFlow,    │
│  você precisa aceitar:   │
│                          │
│  ☑ Termos de Uso         │
│  ☑ Política de           │
│    Privacidade           │
│  ☑ Consentimento para    │
│    uso clínico           │
│                          │
│  Opcionais (recomendados)│
│                          │
│  ☐ Compartilhar dados    │
│    com meu profissional  │
│  ☐ Analytics de uso      │
│    anônimo                │
│  ☐ Pesquisa clínica      │
│                          │
│  [ Atualizar ]           │
└──────────────────────────┘
```

---

## 21. Notificações

```
┌──────────────────────────┐
│  ←  Notificações         │
│                          │
│  Lembretes de sessão      │
│  [●─────────] 08:00      │
│  [●─────────] 22:30      │
│                          │
│  Som gentil              │
│  [●─────────]             │
│                          │
│  Resumo semanal           │
│  [●─────────] domingo    │
│                          │
│  Avisos críticos          │
│  (sempre ligado)         │
│                          │
│  [ Salvar ]              │
└──────────────────────────┘
```

---

## 22. Acessibilidade

```
┌──────────────────────────┐
│  ←  Acessibilidade       │
│                          │
│  Modo simplificado       │
│  (texto grande,          │
│  botões grandes)         │
│  [    ]                  │
│                          │
│  Tamanho do texto        │
│  A A A                   │
│  [P] [M] [G]             │
│                          │
│  Alto contraste           │
│  [    ]                  │
│                          │
│  Sem animação            │
│  (apenas áudio)          │
│  [    ]                  │
│                          │
│  Leitor de tela           │
│  (otimizado)             │
│                          │
│  [ Salvar ]              │
└──────────────────────────┘
```

---

## 23. Ajuda

```
┌──────────────────────────┐
│  ←  Ajuda                │
│                          │
│  Como usar               │
│  ────────────            │
│  • Começando             │
│  • Fazendo uma sessão    │
│  • Entendendo os dados   │
│                          │
│  Perguntas frequentes    │
│  ────────────            │
│  • Funciona offline?     │
│  • Posso usar durante    │
│    gravidez?             │
│  • O app substitui       │
│    remédio?              │
│                          │
│  Falar com suporte       │
│  ────────────            │
│  [ Chat ]                │
│  [ Email ]               │
│                          │
│  Em caso de urgência      │
│  ────────────            │
│  ⚠ Procure um serviço    │
│  de saúde. O AraFlow não │
│  é atendimento de        │
│  emergência.             │
│  SAMU: 192               │
│  CVV: 188                │
└──────────────────────────┘
```

---

## 24. Exportar dados (LGPD)

```
┌──────────────────────────┐
│  ←  Exportar dados       │
│                          │
│  Você pode baixar todos  │
│  os dados que o AraFlow  │
│  tem sobre você.         │
│                          │
│  Formato:                │
│  (•) JSON                │
│  ( ) PDF (legível)       │
│                          │
│  Incluir:                │
│  ☑ Sessões               │
│  ☑ Escalas               │
│  ☑ Notas                 │
│                          │
│  [ Gerar link de         │
│    download ]            │
│                          │
│  ⚠ O link expira em      │
│  24 horas e é único.     │
└──────────────────────────┘
```

---

## 25. Excluir conta (LGPD)

```
┌──────────────────────────┐
│  ⚠  Excluir conta        │
│                          │
│  Esta ação é definitiva. │
│  Todos os seus dados,    │
│  sessões e prescrições   │
│  serão apagados.         │
│                          │
│  Antes de excluir,       │
│  recomendamos exportar   │
│  seus dados.             │
│                          │
│  [ Exportar dados ]      │
│                          │
│  Para confirmar,         │
│  digite:                 │
│  "EXCLUIR MINHA CONTA"   │
│  [......................]│
│                          │
│  [ Cancelar ]            │
│  [ Excluir agora ]       │
│  (botão destrutivo)      │
└──────────────────────────┘
```

---

## 26. Modo SOS (ansiedade aguda)

```
┌──────────────────────────┐
│                          │
│   Você está bem?         │
│                          │
│   Vamos respirar         │
│   juntos por 3 minutos.  │
│                          │
│   ╭───────────╮          │
│   │     ◯     │          │
│   ╰───────────╯          │
│                          │
│      Inspire 4s          │
│                          │
│      ⏱ 00:12 / 03:00    │
│                          │
│   [ Encerrar ]           │
│                          │
│                          │
│   ⚠ Se sentir dor no     │
│   peito, fraqueza ou     │
│   pensamentos de         │
│   autoagressão, pare e   │
│   ligue 192 (SAMU).      │
└──────────────────────────┘
```

---

## 27. Modo idoso (acessibilidade)

```
┌──────────────────────────┐
│                          │
│       Olá, Antônio       │
│                          │
│  ╭──────────────────╮    │
│  │                  │    │
│  │  DORMIR MELHOR   │    │
│  │                  │    │
│  ╰──────────────────╯    │
│                          │
│  ╭──────────────────╮    │
│  │                  │    │
│  │  RESPIRAR CALMO  │    │
│  │                  │    │
│  ╰──────────────────╯    │
│                          │
│  ╭──────────────────╮    │
│  │   AJUDA          │    │
│  ╰──────────────────╯    │
│                          │
│  (Sem ícones.            │
│   Letras grandes.        │
│   Botões grandes.)       │
└──────────────────────────┘
```

---

## 28. Modo infantil (TEA / TDAH)

```
┌──────────────────────────┐
│   ✨ Olá, Lucas! ✨       │
│                          │
│   ╭────────────────╮     │
│   │   ❀            │     │
│   │   Flor que     │     │
│   │   respira      │     │
│   ╰────────────────╯     │
│                          │
│   [ Tocar! ]             │
│                          │
│   ⭐⭐⭐ (3 estrelas)     │
│                          │
│   (Visual lúdico,        │
│    cores saturadas,      │
│    música divertida.)    │
└──────────────────────────┘
```

Durante a sessão:
```
┌──────────────────────────┐
│                          │
│       ❀ ─── ❀            │
│      (flor abrindo)      │
│                          │
│      Respire com a flor  │
│                          │
│       ⏱ 02:30            │
│                          │
│      [ Sair ]            │
└──────────────────────────┘
```

---

## 29. Tela inicial do profissional

```
┌──────────────────────────┐
│  Olá, Dra. Marina        │
│  Pacientes com AraFlow: 14│
│                          │
│  ╭──────────────────╮    │
│  │  + Prescrever    │    │
│  ╰──────────────────╯    │
│                          │
│  Hoje                    │
│  ─────────               │
│  • Carlos H. — 3/5 sessão│
│  • Bia S. — não fez hje  │
│  • Helena M. — completou │
│                          │
│  Alertas                 │
│  ─────────               │
│  ⚠ Carlos — queda        │
│    de adesão (7 dias)    │
│                          │
├──────────────────────────┤
│ 👥    📚    📊    👤      │
│ Pacotes Biblioteca Dash  │
└──────────────────────────┘
```

---

## 30. Selecionar paciente (prescrição)

```
┌──────────────────────────┐
│  ←  Prescrever — Passo 1 │
│                          │
│  Selecione o paciente    │
│  ─────────               │
│  🔍 [.................]  │
│                          │
│  Recentes                │
│  • Carlos H.             │
│  • Bia S.                │
│  • Helena M.             │
│                          │
│  Todos os pacientes       │
│  • Antônio F.            │
│  • Mariana C.            │
│  • João P.               │
│  ...                     │
└──────────────────────────┘
```

---

## 31. Escolher protocolo (prescrição)

```
┌──────────────────────────┐
│  ←  Passo 2 / 4          │
│  Carlos Henrique         │
│                          │
│  Escolha o protocolo     │
│                          │
│  Categoria               │
│  ▼ Ansiedade             │
│                          │
│  Sugeridos               │
│  ╭──────╮ ╭──────╮       │
│  │ 4-7-8 │ │ Box  │       │
│  ╰──────╯ ╰──────╯       │
│                          │
│  Buscar                  │
│  [....................]  │
│                          │
│  Biblioteca completa     │
│  ─────────               │
│  • Coerência 5.5         │
│  • Body scan 10 min      │
│  • 4-7-8 (Andrew Weil)   │
│  • Box 4-4-4-4           │
│  ...                     │
│                          │
│  [  Continuar →  ]       │
└──────────────────────────┘
```

---

## 32. Definir dose e confirmar prescrição

```
┌──────────────────────────┐
│  ←  Passo 4 / 4          │
│  Carlos Henrique         │
│  Respiração 4-7-8        │
│                          │
│  Dose                    │
│  ─────────               │
│  Frequência:             │
│  (•) 1x/dia             │
│  ( ) 2x/dia             │
│  ( ) Personalizado       │
│                          │
│  Horário sugerido:       │
│  [08:00] [22:30]         │
│                          │
│  Duração do plano:       │
│  (•) 14 dias             │
│  ( ) 30 dias             │
│  ( ) 60 dias             │
│  ( ) Contínuo            │
│                          │
│  Observações:            │
│  [....................]  │
│  [....................]  │
│                          │
│  ╭─────────────────╮     │
│  │   Prescrever     │    │
│  ╰─────────────────╯     │
└──────────────────────────┘
```

---

## 33. Meus pacientes (profissional)

```
┌──────────────────────────┐
│  Meus pacientes    🔍    │
│                          │
│  Filtros                 │
│  ▼ Todos                 │
│  Ordenar: última atividade│
│                          │
│  ─────────               │
│  Carlos H.               │
│  Adesão 86% • Streak 7   │
│  Última: hoje            │
│                          │
│  Bia S.                  │
│  Adesão 60% • Streak 0   │
│  Última: ontem           │
│                          │
│  Helena M.               │
│  Adesão 92% • Streak 21  │
│  Última: hoje            │
│                          │
│  Antônio F.              │
│  Adesão 50% • Streak 3   │
│  Última: 3 dias atrás ⚠  │
└──────────────────────────┘
```

---

## 34. Detalhe do paciente (profissional)

```
┌──────────────────────────┐
│  ←  Carlos Henrique      │
│                          │
│  Prescrição ativa:       │
│  4-7-8 • 5 min • 2x/dia  │
│                          │
│  Adesão (últ. 30d)       │
│  ████████░░ 86%          │
│                          │
│  Padrão                  │
│  Manhã  ▇▇▇              │
│  Noite  ▇▇▇▇             │
│                          │
│  Escalas                 │
│  GAD-7 inicial: 16       │
│  GAD-7 atual:   11       │
│  Δ -5 ✓                  │
│                          │
│  Notas clínicas          │
│  [....................]  │
│  [ Salvar ]              │
│                          │
│  [ Ajustar prescrição ]  │
│  [ Encerrar prescrição ] │
└──────────────────────────┘
```

---

## 35. Biblioteca de protocolos (profissional)

```
┌──────────────────────────┐
│  Biblioteca      🔍      │
│                          │
│  Por objetivo clínico    │
│  ─────────               │
│  • Ansiedade             │
│  • Insônia               │
│  • Dor                   │
│  • Foco                  │
│  • Burnout               │
│  • TEA / TDAH            │
│  • Cannabis medicinal    │
│                          │
│  Por evidência            │
│  ─────────               │
│  • Nível A (forte)        │
│  • Nível B (moderado)    │
│  • Nível C (fraco)       │
│                          │
│  Adicionados             │
│  ─────────               │
│  • 4-7-8                 │
│  • Coerência 5.5         │
│  • Body scan             │
└──────────────────────────┘
```

---

## 36. Admin AraFlow (AraOS)

```
┌──────────────────────────┐
│  AraOS · Admin           │
│  Módulos → AraFlow       │
│                          │
│  Resumo                  │
│  • Usuários ativos: 1.234│
│  • Profissionais: 87     │
│  • Sessões/dia: 320      │
│  • Uptime: 99,8%         │
│                          │
│  ─────────               │
│  Configurações           │
│  [ ] Manutenção          │
│  [ ] Liberação Fase 2    │
│  [ ] Liberação Fase 3    │
│                          │
│  ─────────               │
│  Logs de auditoria       │
│  [ Ver ]                 │
│  [ Exportar ]            │
└──────────────────────────┘
```

---

## 37. Anotações gerais dos wireframes

- **Sem ícones de redes sociais** no MVP.
- **Botão "voltar" sempre presente** exceto no player fullscreen.
- **"Cancelar"** sempre à esquerda, **"Confirmar"** à direita.
- **Botões destrutivos** sempre vermelhos + dupla confirmação.
- **Estado vazio** sempre oferece uma ação.
- **Estados de erro** sempre oferecem caminho de saída.

---

*Wireframes são documentos vivos. Iterar com base em testes de usabilidade.*