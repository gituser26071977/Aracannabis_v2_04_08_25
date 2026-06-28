# PRODUCTION_CONFIDENCE — MISSÃO 24

**Data:** 2026-06-25
**Modo:** EXECUTE (somente leitura)
**Origem:** M24 — Consolidação das 7 fases

---

## Respondendo as 6 perguntas obrigatórias

### 1. Quais bugs um médico encontrará na primeira hora?

**Ordenados por probabilidade de encontro:**

| Probabilidade | Bug | Momento do encontro |
|---------------|-----|---------------------|
| **100%** | **Não há rota para gerar documentos/atestados** | Após primeira consulta, quando tenta "imprimir atestado" |
| **100%** | **Não há rota para enviar WhatsApp** | Quando tenta avisar paciente sobre retorno |
| **100%** | **Não há rota de logout** | Ao tentar fechar expediente (token continua válido) |
| **90%** | **Não há busca de pacientes** | Quando tem > 10 pacientes e procura "João" |
| **90%** | **URLs não seguem vocabulário médico** (`/agenda`, `/prontuario` → NotFound) | Logo após login, ao explorar menus |
| **80%** | **IA retorna `model: "none"`** | Ao usar chat IA (resposta genérica, sem provenance) |
| **70%** | **Endpoint de exames exige form-data** | Ao integrar com sistema externo |
| **50%** | **Pacientes duplicados permitidos** | Quando digita CPF errado duas vezes |

**Conclusão:** **5-7 bugs inevitáveis na primeira hora** de uso real.

---

### 2. Quais fluxos causam retrabalho?

| Fluxo | Retrabalho |
|-------|-----------|
| **Buscar paciente antigo** | Médico rola lista inteira; sem filtro por nome/CPF/data |
| **Cadastrar consulta em paciente errado** | Sem preview do histórico antes de salvar |
| **Editar evolução** | PUT `/evolucoes/{id}` não documentado; médico acaba criando nova |
| **Gerar prescrição duplicada** | Cada submit gera novo `code`; sem proteção contra duplo-clique |
| **Anexar exame** | Endpoint requer form-data; frontend precisa FormData; reinvente para cada cliente |
| **Tentar logar depois de 10 tentativas erradas** | 429 por IP/sessão (já documentado em M23) |
| **Trocar de tenant (clínica)** | X-Association-ID não persiste; médico tem que lembrar de trocar |

**Conclusão:** **5-7 fluxos com retrabalho claro**.

---

### 3. Quais funcionalidades parecem "inacabadas"?

| Feature | Estado |
|---------|--------|
| **Gerar documentos** (atestado, relatório) | Anunciada, rota 404 — **inacabada** |
| **Enviar WhatsApp** | Serviço existe (`services/whatsapp_service.py`), mas sem rota HTTP — **inacabada** |
| **Logout** | Blueprint auth só tem login/register/profile — **inacabada** |
| **Busca de pacientes** | Sem rota — **inacabada** |
| **IA de verdade** | Retorna `model: "none"` — **placeholder** |
| **Relatórios** | Rota 404 — **inacabada** |
| **Notificações/alertas** | Rota 404 — **inacabada** |
| **Onboarding profissional** | `onboarding_step: 0`, `onboarding_completed: false` no perfil → médico entra no sistema sem onboarding |
| **Multi-tenant rigoroso** | GET não checa, DELETE sim — **inconsistente** |
| **Validação de dados** | Sem CHECK em datas, sem UNIQUE em CPF — **inacabada** |

**Total de features inacabadas: 10** (de 35+ candidatas pesquisadas)

---

### 4. Quais problemas fariam um médico desistir de pagar?

**Ordem de impacto na decisão de cancelamento:**

| # | Problema | Por que desiste |
|---|----------|------------------|
| 1 | **Não consegue gerar atestado** | Funcionalidade básica de consultório; quebra o dia-a-dia |
| 2 | **Não consegue avisar paciente por WhatsApp** | Confirmação de consulta vira telefone/WhatsApp pessoal |
| 3 | **Vazamento de pacientes entre clínicas** (cross-tenant) | Violação ética grave; médico cancela por medo de processo |
| 4 | **Pacientes duplicados** sem aviso | Histórico fica confuso; médico perde confiança no sistema |
| 5 | **IA dá resposta sem modelo configurado** | Médico pode confiar em alucinação; prejuízo clínico |
| 6 | **Não consegue deslogar** | Em consultório compartilhado, outro profissional vê dados |
| 7 | **Busca por paciente é só "rolar lista"** | Com > 30 pacientes, fica inviável |
| 8 | **Sistema não lembra do tenant** | Se médico trabalha em 2 clínicas, confunde dados |

**Conclusão:** **3 problemas seriam motivo de cancelamento imediato** (1, 2, 3). Outros 5 são motivo de cancelamento em 1-3 meses.

---

### 5. O sistema aguenta um ambulatório inteiro sem intervenção manual?

**SIM.** Evidência de FASE 7:

```
30 pacientes × 3 operações (consulta + evolução + prescrição) = 90 requests
Tempo total: 2.63s (29ms por request)
0 erros
100% dos cadastros bem-sucedidos
```

**Detalhes:**
- 30/30 pacientes cadastrados em 1.51s
- 30/30 consultas agendadas
- 30/30 evoluções registradas
- 30/30 prescrições geradas
- 0 timeout, 0 erro 5xx
- CPU do backend em **ocioso durante toda operação** (medido em M23)

**Cenário real extrapolado (NÃO medido, NÃO comprovado):**
- 50 pacientes/dia × 3 ops = 150 requests ≈ 5 segundos → OK
- 100 pacientes/dia × 3 ops = 300 requests ≈ 9 segundos → OK
- Backend não é gargalo; gargalo seria a **interface do médico** (digitação)

**MAS** com ressalvas:
- ⚠️ Sem feature de **geração de documento**, médico tem que sair do sistema para fazer atestado (anula o ganho)
- ⚠️ Sem feature de **WhatsApp**, médico tem que abrir WhatsApp Web separadamente
- ⚠️ Sem feature de **busca**, médico perde 5-10min/dia rolando lista

**Veredito:** tecnicamente **SIM**. Funcionalmente **NÃO** (porque faltam features que o médico usa 5-10× por dia).

---

### 6. O que precisa ser corrigido antes de cobrar a primeira mensalidade?

**Lista de bloqueadores para cobrança:**

| # | Bloqueador | Categoria | Esforço estimado |
|---|-----------|-----------|------------------|
| 1 | Criar rota `/api/documentos/gerar` (atestado, declaração, relatório) | Backend | 2-3 dias |
| 2 | Criar rota `/api/auth/logout` com revogação JWT (blacklist Redis) | Backend | 1-2 dias |
| 3 | Criar rota `/api/whatsapp/send` ou integração Evolution | Backend | 3-5 dias |
| 4 | Corrigir GET /pacientes/{id} para checar tenant | Backend | 0.5 dia |
| 5 | Validação rigorosa de CPF (dígito verificador) | Backend | 1 dia |
| 6 | CHECK constraint em data_nascimento (< hoje, > 1900) | DB migration | 0.5 dia |
| 7 | UNIQUE constraint em CPF (com cuidado para registros existentes) | DB migration | 0.5 dia |
| 8 | Aceitar JSON em POST /exames OU documentar claramente form-data | Backend | 0.5 dia |
| 9 | Configurar modelo de IA real (OpenAI/Anthropic) | Backend + env | 1 dia |
| 10 | Criar rota `/api/pacientes/buscar?q=` | Backend | 1 dia |
| 11 | Adicionar rotas frontend `/agenda`, `/prontuario`, `/receita` (aliases) | Frontend | 1 dia |
| 12 | Onboarding profissional forçado no primeiro login | Frontend | 1-2 dias |

**Total estimado:** **2-3 sprints** (4-6 semanas para 1 dev)

**NÃO bloqueadores** (podem ir depois):
- Validação de nome (vazio, tamanho)
- Nome 300 chars (limite razoável, mas não crítico)
- Performance percebida (já está OK)
- IA model: "none" (resposta existe, é genérica)
- Spinners / loading states

---

## NÍVEL DE CONFIANÇA PARA PRODUÇÃO

| Dimensão | Nota (1-5) | Comentário |
|----------|------------|-----------|
| **Funcionalidade core** (consulta + evolução + prescrição) | 4/5 | Funciona, rápido, completo |
| **Funcionalidade periférica** (documento, whatsapp, logout) | 1/5 | 3 features não existem |
| **Validação de dados** | 1/5 | Aceita lixo |
| **Segurança multi-tenant** | 2/5 | GET não checa, delete sim |
| **Performance** | 5/5 | Excelente |
| **UX frontend** | 3/5 | URLs confusas, sem busca |
| **Consistência** | 3/5 | Maioria OK, alguns bugs |
| **IA** | 2/5 | Funciona mas sem modelo |
| **Billing** | não testado | Fora do escopo M24 |
| **LGPD** | não testado | Fora do escopo M24 |

**Nota geral:** **2.6/5 — NÃO recomendado cobrar antes de 2-3 sprints de correções.**

---

## RECOMENDAÇÃO FINAL

> **NÃO COBRAR mensalidade enquanto:**
> 1. Não existir rota de documento/atestado
> 2. Não existir logout com revogação
> 3. Não existir checagem de tenant em GET
> 4. CPF não tiver validação real
> 
> **Demais correções podem entrar em roadmap** sem bloquear cobrança.
> 
> **Estimativa: 1 sprint focado (2-3 semanas) destrava 80% dos bloqueadores.**

---

## RESTRIÇÕES RESPEITADAS

- ✅ Não alterei backend/frontend/banco/Docker/CI/CD/billing/RBAC/auth/LGPD
- ✅ Não corrigi nenhum bug
- ✅ Não criei nenhuma feature
- ✅ Não fiz commits, push, PR
- ✅ Tudo baseado em responses HTTP reais
- ✅ Tudo baseado em medições objetivas de latência
- ✅ O que não pôde ser testado (UI visual) marcado como inferência baseada em código