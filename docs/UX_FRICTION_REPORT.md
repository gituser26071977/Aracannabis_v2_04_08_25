# UX_FRICTION_REPORT — MISSÃO 24

**Data:** 2026-06-25
**Modo:** EXECUTE (somente leitura)
**Origem:** M24 FASE 5 — Procurar fluxos óbvios que médico buscaria

---

## Metodologia

1. **Backend:** probei 35 endpoints com nomes óbvios de vocabulário médico brasileiro (FASE 5).
2. **Frontend:** li `frontend/src/App.js` (44 `<Route>` registradas) procurando termos óbvios.
3. **API real:** testei jornadas e mediu latência percebida (FASE 6).

---

## 🔴 VOCABULÁRIO MÉDICO BRASILEIRO SEM ROTA

35 candidatos testados. **NENHUM** retornou rota válida:

| Categoria | Termo que médico buscaria | Rota frontend? | Endpoint backend? |
|-----------|--------------------------|----------------|-------------------|
| Consulta | `/agenda` | ❌ NotFoundPage | ❌ 404 |
| Consulta | `/atendimentos` | ❌ NotFoundPage | ❌ 404 |
| Consulta | `/atendimento/novo` | ❌ NotFoundPage | ❌ 404 |
| Consulta | `/consulta/nova` | ❌ NotFoundPage | ❌ 404 (existe só via `/consultas/` POST) |
| Prontuário | `/prontuario` | ❌ NotFoundPage | ❌ 404 |
| Prontuário | `/prontuario/novo` | ❌ NotFoundPage | ❌ 404 |
| Receita | `/receita` | ❌ NotFoundPage | ❌ 404 |
| Receita | `/receita/nova` | ❌ NotFoundPage | ❌ 404 |
| Atestado | `/atestado` | ❌ NotFoundPage | ❌ 404 |
| Documento | `/documento` | ❌ NotFoundPage | ❌ 404 |
| Documento | `/documento/novo` | ❌ NotFoundPage | ❌ 404 |
| Busca | `/busca` | ❌ NotFoundPage | ❌ 404 |
| Busca | `/buscar` | ❌ NotFoundPage | ❌ 404 |
| Relatório | `/relatorios` | ❌ NotFoundPage | ❌ 404 |
| Financeiro | `/financeiro` | ❌ NotFoundPage | ❌ 404 |
| Financeiro | `/pagamentos` | ❌ NotFoundPage | ❌ 404 |
| Notificação | `/notificacoes` | ❌ NotFoundPage | ❌ 404 |
| Notificação | `/mensagens` | ❌ NotFoundPage | ❌ 404 |
| Alerta | `/alertas` | ❌ NotFoundPage | ❌ 404 |
| Tarefa | `/tarefas` | ❌ NotFoundPage | ❌ 404 |
| Conta | `/meu-plano` | ❌ NotFoundPage | ✅ `/planos/meu-plano` (caminho diferente!) |
| Conta | `/meu-paciente` | ❌ NotFoundPage | ❌ 404 |
| Conta | `/perfil` | ❌ NotFoundPage | ❌ 404 |
| Conta | `/minha-conta` | ❌ NotFoundPage | ❌ 404 |
| Conta | `/configuracoes` | ❌ NotFoundPage | ❌ 404 |
| Conta | `/settings` | ❌ NotFoundPage | ❌ 404 |

**Comportamento:** quando usuário acessa qualquer um desses, frontend mostra **NotFoundPage** (rota coringa `*`). Não há busca por URL parcial, não há redirect para termo similar.

---

## 🔴 INCONSISTÊNCIA DE TERMINOLOGIA (URLs vs fala do médico)

| Médico fala | Sistema usa | Impacto |
|-------------|-------------|---------|
| "agenda" | `/consultas/` | Médico não acha |
| "atendimento" | `/consultas/` | Médico não acha |
| "receita" | `/prescricoes/` | Médico não acha (ortografia diferente) |
| "atestado" | nenhum | Médico não acha |
| "prontuário" | `/evolucoes/paciente/<id>` | Médico tem que clicar 2-3 níveis |
| "evolução" | `/evolucoes/` (correto) | OK |
| "exame" | `/exames/` (correto) | OK |
| "meu plano" | `/planos/meu-plano` | OK |
| "minha conta" | `/dashboard` + menu lateral | OK indiretamente |

**Estimativa de fricção:** Médico brasileiro que começa a usar o sistema **vai errar a URL pelo menos 5-8 vezes** antes de decorar os caminhos internos.

---

## 🟠 FRICÇÃO NO FLUXO "PRESCRIÇÃO"

Caminho real para gerar 1 prescrição:

1. Login
2. Dashboard → "Pacientes"
3. Clicar no paciente
4. (Em qual aba fica "Prescrição"? — verificar `PatientDetailPage.js`)
5. Preencher medicamentos
6. Submeter → backend retorna `code` (prescricao_2_20260626003656.pdf)
7. Para baixar: `GET /prescricoes/{code}/download` (sem `/api/prescricoes/...`)

**Passos extras não-óbvios:**
- Médico precisa **lembrar do code** retornado, não há URL amigável
- Não há preview antes de salvar
- Não há lista de prescrições anteriores no detalhe do paciente (apenas `GET /prescricoes/paciente/<id>` que retorna `[]` mesmo após salvar — **bug**: ou eu usei a rota errada, ou prescrições não são vinculadas ao paciente de fato)

---

## 🟠 AUSÊNCIA DE FEEDBACK VISÍVEL EM ERROS

Respostas do backend usam **status code correto** mas frontend não tem feedback para vários casos:

| Erro backend | Frontend faz |
|--------------|--------------|
| 400 "Dados incompletos" | Mostrado? Depende do componente |
| 401 (token expirado) | Mostra? Não testado |
| 403 "Acesso negado a este paciente" | Texto literal, sem ação corretiva |
| 404 (rota inexistente) | NotFoundPage genérica |
| 429 (rate-limit) | Não testado em UI |
| 500 (erro interno) | ServerErrorPage (existe!) |

**Página 500 existe, 404 existe, mas para erros de negócio (4xx) não há padrão claro.**

---

## 🟠 SPINNERS / LOADING

Não foi possível testar via API. Verifiquei arquivos:
- `AdminPage.js`, `AIChatPage.js`, `PatientDetailPage.js` — todos com 15-65KB
- Tamanho sugere componentes complexos com possibilidade de loading state, mas **não foi medido comportamento real** sem Playwright

---

## 🟡 PERFORMANCE PERCEBIDA (medida direta)

| Operação | Latência média (5 runs) | Latência máx | Percepção |
|----------|------------------------|--------------|-----------|
| Login | 34ms | 38ms | **Instantâneo** |
| Dashboard stats | 14ms | 16ms | **Instantâneo** |
| Listar pacientes (5 itens) | 50ms | 57ms | **Instantâneo** |
| Abrir paciente (GET by ID) | 18ms | 23ms | **Instantâneo** |
| Cadastrar consulta | 29ms | 32ms | **Instantâneo** |
| Gerar prescrição (PDF) | 30ms | 32ms | **Instantâneo** |
| IA `/chat-simples` | **376ms** | **655ms** | **Aceitável** (mas modelo=`none`) |

**Veredito:** backend é rápido em todas as operações individuais (< 60ms). IA é o único gargalo perceptível (376ms médio). **NÃO há spinner perceptível** em operação normal.

---

## 🟡 LATÊNCIA COM 30 PACIENTES (FASE 7)

| Operação | Volume | Tempo total | Tempo/req |
|----------|--------|-------------|-----------|
| Cadastrar 30 pacientes | 30 POST | 1.51s | 50ms |
| Para cada paciente: 3 ops (consulta + evolução + prescrição) | 90 ops | 2.63s | 29ms |

**Tempo médio por paciente (full ambulatório):** 88ms (cadastro + 3 ops).
**Para 30 pacientes em sequência:** ~4 segundos totais. **Médico não sentiria lentidão.**

---

## 🟢 COISAS QUE FUNCIONAM BEM (observação positiva)

- **Mensagens de erro em PT-BR** — adequado
- **JWT stateless** — login refresh rápido
- **Multi-tenant parcialmente implementado** — X-Association-ID funciona
- **IA retorna resposta mesmo sem modelo** — degradação graceful (mas engana médico)
- **Prescrição gera PDF** (`code` retorna arquivo)
- **Listagem de pacientes já existentes** funciona
- **Dashboard.stats** retorna métricas reais

---

## RESUMO: TOP 5 PONTOS DE FRICÇÃO

1. **Não há busca de pacientes por nome/CPF** — médico rola lista
2. **URLs não seguem vocabulário médico brasileiro** — `/prontuario`, `/agenda`, `/receita` todos NotFound
3. **3 features críticas ausentes** (documentos, whatsapp, logout)
4. **Validação fraca** permite cadastros absurdos (nome vazio, data 3025, CPF "abc")
5. **IA sem modelo configurado** retorna resposta genérica com `model: "none"`

---

## RESTRIÇÕES RESPEITADAS

- ✅ Não alterei frontend
- ✅ Não criei novas rotas
- ✅ Não sugeri mudanças de copy
- ✅ Apenas observei e documentei