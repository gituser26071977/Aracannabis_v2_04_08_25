# BUG_CATALOG — MISSÃO 24

**Data:** 2026-06-25
**Origem:** M24 FASE 1+2+3+4 — Bugs reproduzidos em ambiente staging real
**Total:** 19 bugs (3 🔴 críticos, 8 🟠 altos, 5 🟡 médios, 3 🟢 baixos)

---

## 🔴 CRÍTICOS (quebra jornada do médico pagante)

### BUG-CRIT-01 — Não existe endpoint de Documentos
- **Onde:** backend (nenhum `routes/documentos.py`)
- **Como reproduzir:** `POST /api/documentos/gerar` → 404 Not Found
- **Impacto:** Médico **não consegue** gerar atestados, declarações, relatórios de consulta. Feature visível na home, não implementada.
- **Evidência:** 404 limpo, sem rota alternativa
- **Workaround atual:** Nenhum

### BUG-CRIT-02 — Não existe endpoint de WhatsApp
- **Onde:** backend (`services/whatsapp_service.py` existe, mas não há rota exposta)
- **Como reproduzir:** `POST /api/whatsapp/send` → 404
- **Impacto:** Médico não consegue enviar confirmações de consulta por WhatsApp.
- **Evidência:** 404 limpo
- **Workaround:** Usar Evolution direto (não acessível ao médico)

### BUG-CRIT-03 — Não existe endpoint de Logout
- **Onde:** `routes/auth.py` (apenas `/login`, `/register`, `/profile`)
- **Como reproduzir:** `POST /api/auth/logout` → 404
- **Impacto:** Logout é **client-side apenas**. Token JWT continua válido até expirar (24h). Em máquina compartilhada (consultório), outro usuário pega o token e impersona.
- **Evidência:** 404 limpo
- **Workaround:** Limpar localStorage manualmente

---

## 🟠 ALTOS (fricção séria, médico precisa workaround)

### BUG-ALT-01 — Endpoint /exames exige multipart/form-data
- **Arquivo:** `routes/exames.py:17-141`
- **Como reproduzir:** `POST /api/exames` com JSON `{"paciente_id":1,...}` → 400 "ID do paciente é obrigatório" (mesmo enviando o campo)
- **Causa:** código usa `request.form.get(...)`, ignora JSON
- **Impacto:** Cliente REST simples quebra. Frontend precisa usar FormData. SDKs externos (Zapier, n8n) não conseguem cadastrar exames.
- **Fix sugerido:** aceitar ambos `request.form` e `request.get_json()`

### BUG-ALT-02 — GET /pacientes/{id} não checa tenant
- **Arquivo:** `routes/pacientes.py` GET handler
- **Como reproduzir:** `GET /pacientes/1` com `X-Association-ID=99` → **200 OK** com dados do paciente
- **Impacto:** Vazamento cross-tenant em leitura (delete exige "profissional responsável", mas GET não)
- **Severidade real:** Alta (LGPD art. 6º — separação de bases)

### BUG-ALT-03 — Pacientes duplicados sem aviso
- **Como reproduzir:** 2× `POST /pacientes/` com mesmo CPF `111.111.111-11` → 2× 201 Created
- **Causa:** Sem UNIQUE constraint em `cpf`
- **Impacto:** Médico tem 2 fichas idênticas; ao consultar histórico, vê confusão

### BUG-ALT-04 — Datas absurdas aceitas
- `data_nascimento='3025-01-01'` → 201 OK
- `data_evolucao='3025-12-31'` → 201 OK
- `data_evolucao='ontem'` → 400 (apenas formato)
- **Impacto:** Médico digita errado e cria paciente "do futuro" sem feedback

### BUG-ALT-05 — CPF sem validação de dígito verificador
- `111.111.111-11` (todos iguais, inválido) → 201
- `abc.def.ghi-jk` (alfabético) → 201
- CPF vazio → 201

### BUG-ALT-06 — Nome vazio / só espaços aceito
- `nome=''` → 201
- `nome='     '` → 201
- **Impacto:** Médico tem paciente "fantasma" na lista. Clicando nele, vê só ID e timestamps.

### BUG-ALT-07 — Nome 300 caracteres aceito
- **Impacto:** UI quebra (truncamento), busca por substring fica lenta

### BUG-ALT-08 — Texto clínico 8400 chars aceito sem aviso
- `nota_evolucao` com 8400 chars → 201 OK
- **Impacto:** Suspeita de lentidão na render. Sem max_length documentado.

---

## 🟡 MÉDIOS (UX ruim ou comportamento inesperado)

### BUG-MED-01 — Frontend sem rotas para termos óbvios de médico
- **Arquivo:** `frontend/src/App.js`
- **Rotas inexistentes:** `/atendimentos`, `/agenda`, `/prontuario`, `/receita`, `/atestado`, `/busca`
- **Impacto:** Médico digita `/agenda` na URL → NotFoundPage. Não há menu óbvio.
- **44 rotas existem**, mas nenhuma para vocabulário clínico brasileiro padrão.

### BUG-MED-02 — GET /pacientes/{id} retorna 200 com `nome: null`
- **Como reproduzir:** Após DELETE de paciente, próximo GET retorna 200 com `nome: None` (não 404)
- **Impacto:** Cliente mostra "Paciente null" ou erro silencioso

### BUG-MED-03 — IA retorna `model: "none"`
- **Resposta:** `{"mensagem": "...", "model": "none", ...}`
- **Impacto:** Médico recebe resposta genérica sem saber se foi OpenAI, Anthropic ou template

### BUG-MED-04 — 5 endpoints IA alternativos 404
- `/ai/chat`, `/ia/perguntar`, `/crew-ai/perguntar`, `/crew-ai/ask` → todos 404
- **Impacto:** Se frontend chama qualquer um, usuário vê 404 sem ação

### BUG-MED-05 — Sem rota `/busca`
- Médico que procura paciente pelo nome precisa rolar lista inteira
- **Impacto:** Fadiga operacional em listas > 50 pacientes

---

## 🟢 BAIXOS (polimento)

### BUG-BAIXO-01 — Pacientes de teste pré-existentes
- `Joao Silva` (id=1) estava no banco antes da missão
- **Impacto:** Ambiente não isolado

### BUG-BAIXO-02 — Mensagem 403 genérica
- "Acesso negado a este paciente" — não diz se é por tenant ou por vínculo
- **Impacto:** Médico fica sem saber se mudou de clínica ou se é bug

### BUG-BAIXO-03 — GET /pacientes/3 retorna nome null após edição
- Após `PUT /pacientes/3` com payload mínimo, GET subsequente retorna `nome: None`
- **Impacto:** Bug de serialização

---

## Bugs JÁ CONHECIDOS (de missões anteriores, ainda presentes)

| Bug | Origem | Status |
|-----|--------|--------|
| BUG-001 REDIS_URL ausente em .env.staging | M21.5 / M23 | Aberto |
| /api/health retorna 500 sob Redis outage | M23 FASE 6 | Aberto |
| Login rate-limit 10/min satura com 10 usuários | M23 FASE 5 | Aberto |
| `/api/prescricoes/` (sem /gerar) 404 | M22.1 / M23 | Aberto (esperado, rota correta é `/gerar`) |
| `/api/chat-simples` payload documentado diverge do real | M22.2 | Aberto |

---

## Bugs COMPORTAMENTAIS (não técnicos, mas urgentes)

| # | Comportamento | Risco |
|---|---------------|-------|
| COMP-01 | `POST /pacientes/` aceita payload quase vazio sem erro | Médico cria paciente "rascunho" e esquece |
| COMP-02 | IA responde mesmo sem modelo configurado | Médico pode confiar em alucinação |
| COMP-03 | Token JWT sem mecanismo de revogação | Após "logout" (client-side), token continua válido |
| COMP-04 | Sem endpoint de busca de pacientes por nome/CPF | Médico não acha paciente antigo |

---

## Priorização sugerida para time

1. **CRIT-01, CRIT-02, CRIT-03** → P0 (1 sprint) — sem essas 3 features, jornada está incompleta
2. **ALT-02** → P0 — vazamento cross-tenant viola LGPD
3. **ALT-01** → P1 — quebra integração REST simples
4. **ALT-03, ALT-04, ALT-05, ALT-06** → P1 — validação de entrada
5. **MED-01, MED-05** → P2 — UX
6. Demais → Backlog

---

## Restrições respeitadas

- ✅ Apenas leitura
- ✅ Nenhum bug corrigido
- ✅ Nenhum commit/push/PR