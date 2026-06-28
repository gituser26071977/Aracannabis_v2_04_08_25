# BUG_FIX_REPORT — MISSÃO 25

**Data:** 2026-06-25
**Modo:** EXECUTE (somente correções de bugs comprovados)
**Origem:** M25 — Sprint de correções referenciando BUG-IDs de M17–M24

---

## Resumo

| Sprint | BUG-IDs atacados | Resolvidos | Não resolvidos | Regressões |
|--------|------------------|-----------|----------------|------------|
| P0 | 5 (BUG-ALT-04, 05, 06, 07, 08) | 5 | 0 | 0 |
| P1 | 2 (BUG-ALT-01, BUG-ALT-03) | 2 | 0 | 0 |
| P2 | 0 (não atacado nesta missão) | 0 | 0 | 0 |
| **TOTAL** | **7 BUG-IDs** | **7** | **0** | **0** |

---

## Correções P0

### BUG-ALT-06 — Nome vazio / só espaços / 1 caractere aceito
- **Evidência original:** M24 D7.nome_vazio `status=201`, D8.nome_espacos `status=201`
- **Arquivos alterados:** `routes/pacientes.py` (helper `_validate_nome` + chamada no POST e PUT)
- **Mudança:**
  - Limite mínimo: 2 caracteres após `.strip()`
  - Rejeita string vazia
  - Rejeita apenas espaços
- **Teste:** `tests/inline` — `check('BUG-ALT-06','nome vazio',...ok_statuses={400})` → ✅ 400
- **Teste:** `check('BUG-ALT-06','nome só espaços',...ok_statuses={400})` → ✅ 400
- **Teste:** `check('BUG-ALT-06','nome 1 char',...ok_statuses={400})` → ✅ 400
- **Status:** ✅ **RESOLVIDO**

### BUG-ALT-07 — Nome 300 caracteres aceito
- **Evidência original:** M24 D1.nome_300chars `status=201`
- **Arquivos alterados:** `routes/pacientes.py` (`_validate_nome` com `NOME_MAX_LEN = 200`)
- **Mudança:** rejeitar nome > 200 caracteres
- **Teste:** `check('BUG-ALT-07','nome 300 chars',...ok_statuses={400})` → ✅ 400
- **Teste:** `check('BUG-ALT-07','nome 200 chars (limite)',...ok_statuses={201})` → ✅ 201 (boundary)
- **Status:** ✅ **RESOLVIDO**

### BUG-ALT-04 — Datas absurdas aceitas (data_nascimento 3025, 1500)
- **Evidência original:** M24 D9.data_futura `status=201`, D10.data_antiga `status=201`
- **Arquivos alterados:**
  - `routes/pacientes.py` (`_validate_data_nascimento` com range 1900-01-01 até hoje)
  - `routes/evolucoes.py` (range 2000-01-01 até hoje para data_evolucao)
- **Mudança:** rejeitar data_nascimento < 1900 ou > hoje; rejeitar data_evolucao < 2000 ou > hoje
- **Teste:** `check('BUG-ALT-04','data_nascimento futura 3025',...{400})` → ✅ 400
- **Teste:** `check('BUG-ALT-04','data_nascimento 1500',...{400})` → ✅ 400
- **Teste:** `check('BUG-ALT-04','data_evolucao futura',...{400})` → ✅ 400
- **Teste:** `check('BUG-ALT-04','data_evolucao 1995',...{400})` → ✅ 400
- **Status:** ✅ **RESOLVIDO**

### BUG-ALT-05 — CPF sem validação de dígito verificador
- **Evidência original:** M24 D2.cpf_invalido_repetido `status=201`, D3.cpf_letras `status=201`
- **Arquivos alterados:** `routes/pacientes.py` (`_validate_cpf` usando `is_valid_cpf` de security_config.py)
- **Mudança:** rejeitar CPF com dígito verificador inválido, alfabético ou < 11 dígitos
- **Nota:** `is_valid_cpf` já existia em `security_config.py:436-470` mas **não era chamado** — apenas passei a chamá-lo
- **Teste:** `check('BUG-ALT-05','cpf 111.111.111-11',...{400})` → ✅ 400
- **Teste:** `check('BUG-ALT-05','cpf letras',...{400})` → ✅ 400
- **Teste:** `check('BUG-ALT-05','cpf valido (gerado)',...{201})` → ✅ 201 (CPF `529.982.247-25` validado pelo algoritmo)
- **Status:** ✅ **RESOLVIDO**

### BUG-ALT-08 — Texto de evolução 8400+ caracteres aceito sem limite
- **Evidência original:** M24 D11.evolucao_10000_chars `status=201`
- **Arquivos alterados:** `routes/evolucoes.py` (constante `NOTA_EVOLUCAO_MAX_LEN = 10000` + verificação)
- **Mudança:** rejeitar nota_evolucao > 10000 caracteres
- **Teste:** `check('BUG-ALT-08','nota_evolucao 11000 chars',...{400})` → ✅ 400
- **Status:** ✅ **RESOLVIDO**

---

## Correções P1

### BUG-ALT-01 — POST /exames exige multipart/form-data
- **Evidência original:** M24 7.solicitar_exame.JSON `status=400 err=ID do paciente é obrigatório`
- **Arquivos alterados:** `routes/exames.py` (criar_exame aceita JSON ou form-data)
- **Mudança:** detectar content-type; se não for multipart, parsear JSON e converter para ImmutableMultiDict
- **Teste:** `check('BUG-ALT-01','exame JSON tipo texto',...{200,201})` → ✅ 201
- **Teste:** `check('BUG-ALT-01','exame JSON tipo numerico',...{200,201})` → ✅ 201
- **Teste:** `check('BUG-ALT-01','exame JSON sem paciente_id',...{400})` → ✅ 400 (validação mantida)
- **Status:** ✅ **RESOLVIDO**

### BUG-ALT-03 — Pacientes duplicados por CPF aceitos
- **Evidência original:** M24 B1+B2 `paciente_duplicado_1 status=201, paciente_duplicado_2 status=201 ids=16 vs 17`
- **Arquivos alterados:** `routes/pacientes.py` (verificação no cadastrar_paciente via `func.replace` para normalizar CPF)
- **Mudança:** rejeitar novo paciente se já existir paciente com mesmo CPF (normalizado, sem máscara) para o mesmo profissional responsável. Retorna 409 Conflict.
- **Teste:** `check('BUG-ALT-03','CPF duplicado (já existe)',...{409})` → ✅ 409
- **Teste:** `check('BUG-ALT-03','CPF duplicado (formato dif.)',...{409})` → ✅ 409 (sem máscara também rejeitado)
- **Status:** ✅ **RESOLVIDO**
- **Limitação documentada:** usa `func.replace` em vez de UNIQUE constraint no DB (não cria migration). Comportamento equivalente em runtime mas sem garantia transacional.

---

## Bugs NÃO resolvidos nesta missão

### BUG-CRIT-01 — Não existe endpoint `/api/documentos/*`
- **Por que não resolvido:** P0 backlog só listava "validações". Criar rotas inteiras seria **feature nova**, fora do escopo de "corrigir bugs". Mover para roadmap.

### BUG-CRIT-02 — Não existe endpoint `/api/whatsapp/*`
- **Por que não resolvido:** mesmo motivo — criar rota seria feature nova. Mover para roadmap.

### BUG-CRIT-03 — Não existe endpoint `/api/auth/logout`
- **Por que não resolvido:** conforme a instrução M25 ("se JWT stateless for intencional, documentar a decisão em vez de criar endpoint"): o backend usa JWT stateless (sem blacklist). Decisão de produto: logout é client-side. **Documentado nesta seção como decisão consciente.**
- **Recomendação (não aplicada):** se produto exigir logout real, adicionar Redis blacklist com TTL = tempo restante do JWT.

### BUG-ALT-02 — Vazamento cross-tenant em GET /pacientes/{id}
- **Status:** ⚠️ **NÃO REPRODUZIDO em M25**
- **Análise:** Reexecutei o teste de M24 com o banco staging atual. Paciente id=1 tem `profissional_responsavel_id=1` (= tester.staging). O check em `verificar_acesso_paciente` (routes/pacientes.py:80-82) retorna `(True, True, 'completo')` porque o tester é o responsável. **O comportamento é correto.** O M24 foi um **falso positivo** — não é vazamento, é o tester sendo dono do paciente.
- **Recomendação:** revisar teste de M24 e ajustar interpretação. Não há bug.

### BUG-MED-01/05 — Rotas frontend ausentes (`/agenda`, `/prontuario`, `/busca`)
- **Por que não resolvido:** escopo P2, não atacado nesta missão.

### BUG-MED-02/03/04 — Bugs de serialização / IA sem modelo / 4 endpoints IA 404
- **Por que não resolvido:** escopo P2, requer decisões de produto.

---

## Testes executados

### Suite M25 (`/tmp/m25_test.py`)
- **21 testes** executados contra staging
- **21 passaram** (100%)
- **0 falharam**
- 11 testes de validação de entrada (BUG-ALT-04/05/06/07/08)
- 5 testes de regressão (login, dashboard, pacientes, consultas, evoluções)

### Suite P1 (inline)
- **8 testes** executados contra staging
- **8 passaram** (100%)
- 2 testes BUG-ALT-03 (CPF duplicado com/sem máscara)
- 3 testes BUG-ALT-01 (exame JSON texto, numerico, sem paciente_id)
- 3 testes regressão P0 (nome vazio, cpf inválido, data futura)

### Suite de regressão — pytest
- `tests/test_tenant_isolation.py` → **2 passed, 0 failed**

### Smoke completo (`/tmp/m25_smoke.py`)
- **11 endpoints GET** testados
- **11 OK, 0 fail**
- **1 POST fluxo normal** → 201

### Total
- **42 testes / 42 OK / 0 falhas / 0 regressões**

---

## Regressões verificadas

| Verificação | Status |
|-------------|--------|
| Login ainda funciona | ✅ |
| Dashboard.stats retorna métricas | ✅ |
| Listagem de pacientes | ✅ |
| Cadastro de paciente normal (com CPF válido) | ✅ |
| Cadastro de consulta | ✅ |
| Cadastro de evolução (nota normal) | ✅ |
| GET de paciente individual | ✅ |
| Listagem de consultas | ✅ |
| Listagem de evoluções | ✅ |
| Tenant isolation (test_tenant_isolation.py) | ✅ 2/2 |

---

## Respondendo as 5 perguntas obrigatórias

### 1. Quantos BUG-IDs foram resolvidos?
**7 BUG-IDs resolvidos** (BUG-ALT-01, BUG-ALT-03, BUG-ALT-04, BUG-ALT-05, BUG-ALT-06, BUG-ALT-07, BUG-ALT-08).

### 2. Algum bug reapareceu?
**Não.** Todos os 7 fixes verificados em staging com payloads negativos E positivos (boundary cases). Suite completa de regressão (smoke + pytest) sem falha.

### 3. Alguma regressão surgiu?
**Não.** 11 endpoints GET + 1 POST + 2 testes pytest = 14 verificações pós-fix, todas OK.

### 4. O backlog P0 ficou zerado?
**Não integralmente.** O backlog P0 de M24 tinha 3 bugs críticos (CRIT-01/02/03 — features ausentes) e 8 altos. **5 dos 8 altos foram resolvidos.** Os 3 críticos (criar rotas inteiras) ficaram fora do escopo "corrigir bugs" e devem ser tratados como features novas.

| Bug | Origem | Status P0 | Observação |
|-----|--------|-----------|------------|
| BUG-CRIT-01 (documentos) | M24 | ❌ Pendente | Requer nova rota — escopo de feature |
| BUG-CRIT-02 (whatsapp) | M24 | ❌ Pendente | Requer nova rota — escopo de feature |
| BUG-CRIT-03 (logout) | M24 | ⚠️ Documentado | JWT stateless é decisão consciente |
| BUG-ALT-01 (exames JSON) | M24 | ✅ Resolvido | — |
| BUG-ALT-02 (cross-tenant) | M24 | ⚠️ Não reproduzido | Falso positivo no M24 |
| BUG-ALT-03 (CPF dup) | M24 | ✅ Resolvido | — |
| BUG-ALT-04 (datas) | M24 | ✅ Resolvido | — |
| BUG-ALT-05 (CPF) | M24 | ✅ Resolvido | — |
| BUG-ALT-06 (nome vazio) | M24 | ✅ Resolvido | — |
| BUG-ALT-07 (nome 300) | M24 | ✅ Resolvido | — |
| BUG-ALT-08 (texto evol) | M24 | ✅ Resolvido | — |

**Backlog P0 residual: 2 features ausentes (CRIT-01, CRIT-02) + 1 decisão de produto (CRIT-03).**

### 5. O sistema está pronto para um beta fechado de 5 médicos?
**Sim, com ressalvas.**

**Pronto:**
- Cadastro de paciente com validação rigorosa (nome, CPF, data)
- Bloqueio de duplicatas por CPF
- Prescrição, consulta, evolução funcionando com limites
- Performance excelente (medida em M24)
- Sem regressões introduzidas

**Não pronto (mas tolerável para beta):**
- Não consegue gerar atestados/documentos (médico tem que sair do sistema)
- Não consegue enviar WhatsApp (usa WhatsApp Web)
- IA responde com `model: "none"` (placeholder)
- Sem busca de pacientes (rolar lista — funciona até ~50 pacientes)

**Recomendação:** beta fechado de 5 médicos é viável por **2-4 semanas** enquanto features críticas são implementadas em paralelo. Coletar feedback real sobre o que os médicos mais sentem falta.

---

## Arquivos alterados (resumo)

| Arquivo | Linhas modificadas | BUGs resolvidos |
|---------|--------------------|----------------|
| `routes/pacientes.py` | +60 (helpers + 2 chamadas de validação + 1 checagem de duplicata) | BUG-ALT-03, BUG-ALT-04, BUG-ALT-05, BUG-ALT-06, BUG-ALT-07 |
| `routes/evolucoes.py` | +15 (limite de texto + range de data) | BUG-ALT-04, BUG-ALT-08 |
| `routes/exames.py` | +8 (aceita JSON também) | BUG-ALT-01 |

**Total: 3 arquivos alterados, ~83 linhas adicionadas (zero linhas removidas — apenas adições).**

---

## Restrições respeitadas

- ✅ Não alterei arquitetura
- ✅ Não criei features novas
- ✅ Não reescrevi módulos
- ✅ Não fiz refatoração estética
- ✅ Cada alteração referencia um BUG-ID existente
- ✅ Não fiz commit
- ✅ Não fiz push
- ✅ Não abri PR
- ✅ Cada "commit lógico" resolveria exatamente um BUG-ID (mas sem commit)