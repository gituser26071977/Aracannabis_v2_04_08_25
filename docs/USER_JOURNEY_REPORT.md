# USER_JOURNEY_REPORT — MISSÃO 24

**Data:** 2026-06-25
**Modo:** EXECUTE (somente leitura)
**Origem:** M24 FASE 1 — Jornada completa do médico + cronômetro

---

## Cronograma observado (1 médico, 1 paciente, sem pausas)

| # | Etapa | Endpoint | Tempo (ms) | Status | Notas |
|---|-------|----------|------------|--------|-------|
| 1 | Login | `POST /api/auth/login` | 34 (média 5x) | ✅ 200 | Login com `email`/`senha` |
| 2 | Dashboard | `GET /api/dashboard/stats` | 14 | ✅ 200 | 5 pacientes, 0 em_tratamento |
| 3 | Cadastrar paciente | `POST /api/pacientes/` | 50-80 | ✅ 201 | Campos: nome, cpf, data_nascimento, telefone, email, endereco |
| 4 | Editar paciente | `PUT /api/pacientes/{id}` | 50 | ✅ 200 | Só envia campos alterados |
| 5 | Ver paciente atualizado | `GET /api/pacientes/{id}` | 20 | ✅ 200 | Retorna `nome: None` se nome foi alterado para vazio (bug) |
| 6 | Cadastrar consulta | `POST /api/consultas/` | 30 | ✅ 201 | Campo obrigatório: `data_hora` (não `data_consulta`) |
| 7 | Listar consultas | `GET /api/consultas/` | 20 | ✅ 200 | Retorna dict `{consultas:[]}` |
| 8 | Criar evolução | `POST /api/evolucoes/paciente/{id}` | 20-30 | ✅ 201 | Campo: `nota_evolucao` (não `descricao`) |
| 9 | Solicitar exame | `POST /api/exames` | 10 (400) | ⚠️ 400 | **Exige multipart/form-data, não JSON** |
| 10 | Gerar prescrição | `POST /api/prescricoes/gerar` | 30 | ✅ 200 | Retorna `code` para download |
| 11 | Gerar documento | `POST /api/documentos/gerar` | 1 | ❌ 404 | **Não existe rota** |
| 12 | Enviar WhatsApp | `POST /api/whatsapp/send` | 0 | ❌ 404 | **Não existe rota** |
| 13 | IA chat | `POST /api/chat-simples` | 240-650 | ✅ 200 | Retorna `model: "none"` |
| 14 | Logout | `POST /api/auth/logout` | 0 | ❌ 404 | **Não existe rota** |

**Tempo total para 1 paciente completo (do login à prescrição):** ~360ms de backend.
**Frontend provavelmente adiciona ~500-1000ms** de render + rede → jornada completa real: **~1.5-2 segundos**.

---

## Mapa do caminho feliz vs realidade

```
Esperado pelo médico (1 paciente):
  Login → Dashboard → Novo paciente → Cadastrar consulta → Evoluir → Exame → Prescrição → Documento → WhatsApp → Logout
                                  ⬇                    ⬇
Realidade no AraOS:
  Login ✅ → Dashboard ✅ → Novo paciente ✅ → Consulta ✅ → Evolução ✅ → Exame ⚠️(form-data) → Prescrição ✅ → Documento ❌ → WhatsApp ❌ → Logout ❌

Cobertura da jornada básica: 6/9 (67%)
```

---

## 6 jornadas tentadas, quais funcionam?

| Jornada | Funciona? | Etapas quebradas |
|---------|-----------|------------------|
| **Consulta simples** (1 paciente, 1 consulta, 1 evolução) | ✅ Sim | Nenhuma |
| **Prescrição** (1 paciente, 1 prescrição, gerar PDF) | ✅ Sim | Nenhuma |
| **Exame laboratorial** | ⚠️ Parcial | Frontend precisa usar FormData |
| **Documento/Atestado** | ❌ Não | Rota não existe |
| **Confirmação WhatsApp** | ❌ Não | Rota não existe |
| **Logout seguro** | ❌ Não | Rota não existe; token continua válido |
| **Busca de paciente por nome** | ❌ Não | Rota não existe |
| **Ambulatório completo (30 pacientes)** | ✅ Sim | Tudo OK em 2.6s |

---

## NÚMEROS CONSOLIDADOS (medidos nesta missão)

### Latência

| Endpoint | p50 | p95 | p99 |
|----------|-----|-----|-----|
| Login | 34ms | 38ms | 38ms |
| Dashboard | 14ms | 16ms | 16ms |
| Listar pacientes (5) | 50ms | 57ms | 57ms |
| GET paciente | 18ms | 23ms | 23ms |
| POST consulta | 29ms | 32ms | 32ms |
| POST prescrição | 30ms | 32ms | 32ms |
| IA | 376ms | 655ms | 655ms |

### Throughput (FASE 7 ambulatório)

- **30 pacientes cadastrados:** 1.51s (50ms/paciente)
- **30 consultas + 30 evoluções + 30 prescrições:** 2.63s (29ms/op)
- **Total:** 90 requests em 2.63s = **34 req/s sustentado** sem erro

### Disponibilidade observada
- Backend up durante toda a missão: **100%**
- 0 timeout
- 0 erro 5xx durante operação normal
- 1 erro 5xx (Redis) já conhecido de M23

---

## Confiança do usuário

| Pergunta implícita | Resposta observada |
|--------------------|--------------------|
| "Consigo cadastrar paciente?" | ✅ Sim, em 50ms |
| "Consigo marcar consulta?" | ✅ Sim, em 30ms |
| "Consigo prescrever?" | ✅ Sim, em 30ms |
| "Consigo gerar atestado?" | ❌ Não |
| "Consigo avisar paciente por WhatsApp?" | ❌ Não |
| "Consigo deslogar com segurança?" | ❌ Não (token continua válido) |
| "Pacientes duplicados vão me confundir?" | ⚠️ Sim (sem validação de CPF único) |
| "O sistema aguenta 30 pacientes de manhã?" | ✅ Sim (~4s total) |
| "A IA me ajuda?" | ⚠️ Sim, mas modelo = "none" |

---

## PRINCIPAIS ACHADOS (ordenados por impacto)

1. **3 features BACKEND INEXISTENTES** (documentos, whatsapp, logout) — médico NÃO consegue completar jornada "natural" que inclui essas funções.

2. **Endpoint /exames requer form-data** — quebra integração REST simples, exige workaround.

3. **Validação de entrada é fraca** — nome vazio, data 3025, CPF "abc" todos passam. Poluição de banco.

4. **Vazamento cross-tenant em GET** — `GET /pacientes/1` retorna 200 com `X-Association-ID=99` (não confere vínculo).

5. **Sistema aguenta ambulatório real (30 pacientes)** com folga — sem lentidão perceptível.

6. **Latência excelente em todas operações** (< 60ms exceto IA) — backend está otimizado.

7. **IA sem modelo configurado** retorna resposta genérica — médico pode confiar em alucinação.

---

## RECOMENDAÇÕES IMEDIATAS (próximo sprint)

| Prioridade | Ação |
|-----------|------|
| P0 | Criar rotas `/api/documentos/*`, `/api/whatsapp/*`, `/api/auth/logout` |
| P0 | Adicionar validação de tenant em GET /pacientes/{id} |
| P1 | Aceitar JSON em POST /exames (ou documentar que é só form-data) |
| P1 | Adicionar CHECK constraint em data_nascimento (não futuro, não > 150 anos) |
| P1 | Adicionar UNIQUE constraint em CPF |
| P1 | Configurar modelo de IA real (não retornar `model: "none"`) |
| P2 | Criar rota de busca de pacientes (`/pacientes/buscar?q=`) |
| P2 | Adicionar rotas frontend `/agenda`, `/prontuario`, `/receita` |

---

## RESTRIÇÕES RESPEITADAS

- ✅ Não alterei código
- ✅ Não corrigi bugs
- ✅ Não criei features
- ✅ Não fiz commits
- ✅ Toda conclusão baseada em requests reais e responses observadas