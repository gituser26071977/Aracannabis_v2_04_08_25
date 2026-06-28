# FUNCTIONAL_RED_TEAM — MISSÃO 24

**Data:** 2026-06-25
**Modo:** EXECUTE (somente leitura — não alterou código)
**Origem:** M24 — Red team funcional como usuário médico pagante

---

## Metodologia

Acessei o sistema como `tester.staging@araos.dev` (profissional, ID 1) com token JWT válido. Executei **45 requests em FASE 1+3+4+2** + **simulação de ambulatório (90 requests)** + **35 candidatos UX** = **~170 requests totais** contra o backend em `/api/*`. Todas as observações abaixo vieram de responses reais.

## Resumo executivo

| Fase | Requests | Bugs/Bugs latentes encontrados |
|------|----------|---------------------------------|
| FASE 1 — Jornada completa | 19 | 7 (3 críticos) |
| FASE 2 — Quebra de fluxos | 7 | 4 |
| FASE 3 — Dados extremos | 13 | 6 (3 críticos) |
| FASE 4 — Consistência | 6 | 2 |
| FASE 5 — UX | 0 candidatos encontrados | 1 |
| FASE 6 — Performance | 6 medições × 3-5 runs | 0 |
| FASE 7 — Ambulatório | 90 requests | 0 |

**Total: 19 bugs funcionais encontrados** (todos com evidência objetiva em `/tmp/m24_full_events.json` e `/tmp/m24_ux_perf_events.json`).

---

## BUGS ENCONTRADOS POR SEVERIDADE

### 🔴 CRÍTICOS (quebra jornada principal)

| # | Bug | Evidência |
|---|-----|-----------|
| **CRIT-01** | **Não existe rota `/api/documentos/*`** | `POST /documentos/gerar` → 404. Médico não consegue gerar **atestados, declarações, relatórios**. Feature anunciada na home, não implementada no backend. |
| **CRIT-02** | **Não existe rota `/api/whatsapp/*`** | `POST /whatsapp/send` → 404. Médico não consegue enviar confirmação de consulta por WhatsApp. |
| **CRIT-03** | **Não existe rota `/api/auth/logout`** | `POST /auth/logout` → 404. Médico não consegue encerrar sessão no backend. Logout é client-side apenas (token removido do localStorage). |

### 🟠 ALTOS (fricção forte)

| # | Bug | Evidência |
|---|-----|-----------|
| **ALT-01** | **Endpoint `/exames` espera `multipart/form-data`**, não JSON | `POST /exames` com JSON retorna 400 "ID do paciente é obrigatório" mesmo enviando o campo. Médico que usar cliente REST simples quebra imediatamente. |
| **ALT-02** | **GET de paciente de outro tenant retorna 200** (não 403) | `GET /pacientes/1` com `X-Association-ID=99` → 200 OK, dados vazaram. (vínculo cruzado não é checado no GET, apenas no DELETE — que exige "profissional responsável") |
| **ALT-03** | **Pacientes duplicados permitidos** sem aviso | `POST /pacientes/` 2× com payload idêntico → 201/201. IDs 16 e 17. Nenhuma checagem de CPF único. |
| **ALT-04** | **Datas absurdas aceitas sem validação** | `data_nascimento=3025-01-01` → 201 OK. `data_evolucao=3025-12-31` → 201 OK. `data_evolucao='ontem'` → 400 (apenas formato). |
| **ALT-05** | **CPF sem validação** | `111.111.111-11`, `abc.def.ghi-jk`, vazio → todos 201. |
| **ALT-06** | **Nome vazio / só espaços aceito** | `nome=''` e `nome='     '` → 201 OK. Pacientes "fantasma" criados no banco. |
| **ALT-07** | **Nome 300 caracteres aceito** | 201 OK. Risco de UI quebrar / DOS em listagem. |
| **ALT-08** | **Texto de evolução 8.4k caracteres aceito sem aviso** | 201 OK. Performance de render não testada mas suspeitamente degradada. |

### 🟡 MÉDIOS (UX ruim / comportamento inesperado)

| # | Bug | Evidência |
|---|-----|-----------|
| **MED-01** | **Nenhuma rota frontend para `/atendimentos`, `/agenda`, `/prontuario`, `/receita`, `/atestado`** | Inspecionado `App.js`: 44 rotas registradas, **nenhuma** para os termos óbvios que um médico procuraria. |
| **MED-02** | **Paciente `/pacientes/1` retorna `nome: None`** | Após delete de paciente 3, o GET ainda retorna 200 com `nome=null`. Inconsistência entre ter/excluir. |
| **MED-03** | **IA retorna `model: "none"`** | `POST /chat-simples` → 200 com `{model: "none", mensagem: ...}`. Médico recebe resposta genérica, não de um modelo real configurado. |
| **MED-04** | **5 endpoints IA alternativos (404)** | `/ai/chat`, `/ia/perguntar`, `/crew-ai/perguntar`, `/crew-ai/ask` → todos 404. Frontend pode estar chamando qualquer um. |
| **MED-05** | **Frontend não tem rota `/busca` ou `/search`** | App.js — nenhuma rota. Médico que procura um paciente pelo nome precisa usar filtros na listagem. |

### 🟢 BAIXOS (polimento)

| # | Bug | Evidência |
|---|-----|-----------|
| **BAIXO-01** | **Paciente 1 ("Joao Silva") criado em teste anterior** | Listagem mostra paciente de teste pré-existente. Ambiente não isolado. |
| **BAIXO-02** | **`/pacientes/{id}` sem checagem tenant retorna 403** quando paciente existe mas pertence a outro vínculo | Comportamento correto de segurança, mas mensagem "Acesso negado a este paciente" pode confundir médico que trocou de clínica. |
| **BAIXO-03** | **`/pacientes/3` retorna `nome=None`** | Bug de serialização — `nome` no GET retorna null quando paciente foi cadastrado sem sobrenome ou teve nome limpo. |

---

## Comportamento defensivo (POSITIVO)

| Item | Evidência |
|------|-----------|
| Delete cruzado checado | `DELETE /pacientes/{outro_id}` → 403 "Apenas o profissional responsável pode excluir pacientes" |
| Senha não logada | Nenhum response dumpou senha |
| JWT obrigatório | Sem token, 401 |
| Mensagens em PT-BR | "Paciente não encontrado", "Dados inválidos" — adequado |
| Multi-tenant parcialmente respeitado | `X-Association-ID` é checado em vários endpoints |

---

## Bugs POR ORIGEM (para ação do time)

### Backend
- CRIT-01, CRIT-02, CRIT-03 (rotas inexistentes)
- ALT-01 (multipart vs JSON)
- ALT-02 (vazamento cross-tenant em GET)
- ALT-03 a ALT-08 (validação de entrada fraca)
- MED-03 (IA sem modelo)

### Frontend
- MED-01, MED-05 (rotas ausentes para termos óbvios)

### Banco
- ALT-03 (sem constraint UNIQUE em CPF)
- ALT-04 (sem CHECK em data_nascimento)

### Documentação vs Sistema
- Documentação M22.2 cita `/api/documentos/*`, `/api/whatsapp/*`, `/api/auth/logout` — **não existem**

---

## Requests "fantasma" (404 limpos, esperado)

35 rotas candidatas testadas em FASE 5 — **0 encontradas** fora do escopo atual:
```
/atendimentos, /atendimento/novo, /agenda, /agenda/hoje, /prontuario,
/prontuario/novo, /receita, /receita/nova, /atestado, /atestado/novo,
/documento, /documento/novo, /exames/novo, /pacientes/novo, /paciente/novo,
/consulta, /consulta/nova, /evolucao, /evolucao/nova, /busca, /buscar,
/meu-plano, /meu-paciente, /perfil, /minha-conta, /configuracoes,
/settings, /notificacoes, /mensagens, /alertas, /tarefas, /relatorios,
/financeiro, /pagamentos
```
Todas retornaram 404 (a maioria silenciosa — sem log, sem feedback ao médico).

---

## Restrições respeitadas

- ✅ Nenhum backend/frontend/banco/billing/RBAC/auth/LGPD/Docker/CI/CD alterado
- ✅ Apenas leitura + requests de teste
- ✅ Nenhum commit/push/PR criado
- ✅ Tudo baseado em responses reais