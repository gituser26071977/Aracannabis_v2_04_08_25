# D05i — DEPLOY GUARD DESYNC (CAUSA RAIZ DO CRASH LOOP)

**Data:** 2026-07-03 **Status:** **DIAGNÓSTICO COMPLETO** — correção requer
mudança de código (fora do escopo D05e) **Origem:** Investigação da CPU alta no
VPS + D05e webhook secrets recovery

---

## TL;DR

O `siap-backend` estava em **CRASH LOOP** consumindo **366% de CPU** porque:

1. ✅ Webhook secrets ausentes → resolvido (D05f)
2. ❌ `deploy_guard` abortava startup reclamando de colunas **que NÃO EXISTEM em
   `models.py` nem no schema SQL original**
3. Cada tentativa de boot importava `crewai` (~30-60s × 3 workers = ~360% CPU)
4. Master gunicorn respawnava workers em loop → CPU permanentemente alta

**Causa raiz REAL:** `CRITICAL_TABLES` em `services/deploy_guard.py:47-77` está
**desatualizado em relação a `models.py` e `database_schema.sql`**.

---

## 1. EVIDÊNCIA OBJETIVA

### 1.1 CPU alta no VPS (print do usuário)

Print do hPanel Hostinger mostrou 3 processos gunicorn em CPU "HIGH" (~80-90%
cada).

### 1.2 Estado real via SSH

```
load average: 4.61 (com 2 CPUs) → 2.3× sobrecarregado
siap-backend CPU: 366.26%
Memória: 179 MiB → baixo (NÃO é leak)
NET I/O: 1.98 kB / 252 B → ZERO tráfego
```

### 1.3 py-spy dump dos 3 workers

```
Worker PID=8 → compiling bytecode em crewai/knowledge/knowledge.py:7
Worker PID=9 → building pydantic em crewai/knowledge/knowledge_config.py:4
Worker PID=10 → idle (boot completo)
```

→ Todos os workers gastavam ~120% CPU cada importando `crewai`.

### 1.4 Log do container (após webhook secrets OK)

```
RuntimeError: [deploy_guard] ABORT STARTUP: schema incompleto.
Tabelas/colunas ausentes:
  - prescricoes: faltando ['medicamentos', 'orientacoes', 'validade_dias', 'created_at']
  - evolucoes: faltando ['created_at']
  - profissionais: faltando ['senha_hash', 'is_active']
[2026-07-03 02:57:30] [ERROR] Worker failed to boot.
[2026-07-03 02:57:31] [INFO] Booting worker with pid: 7/8/9
... 3+ ciclos em 1 minuto
```

---

## 2. CADEIA DE CAUSAS

```
CPU alta (366%) = CRASH LOOP do gunicorn master
   ↓ master respawna workers a cada falha
CRASH LOOP = deploy_guard aborta startup
   ↓ deploy_guard exige colunas inexistentes
COLUNAS INEXISTENTES = CRITICAL_TABLES desatualizado
   ↓ CRITICAL_TABLES não reflete models.py nem database_schema.sql
DESATUALIZAÇÃO = código evoluiu (refactor de senha_hash → senha,
                                  adicionado conteudo_json em prescricoes)
              mas CRITICAL_TABLES não foi atualizado
```

---

## 3. ANÁLISE DETALHADA

### 3.1 Schema real do banco (via psql)

```sql
-- profissionais
id, nome, crm, uf_crm, conselho_tipo, usuario, **senha** (não senha_hash),
email, role, data_expiracao, created_at, status_cadastro, motivo_rejeicao,
data_aprovacao, aprovado_por, validation_data, status_conta, email_verified,
onboarding_completed, onboarding_step, **conselho_tipo**
-- FALTAM no schema: is_active, senha_hash

-- prescricoes
id, associacao_id, paciente_id, profissional_id, data_emissao, arquivo_path,
**conteudo_json**, observacoes
-- FALTAM no schema: medicamentos, orientacoes, validade_dias, created_at

-- evolucoes
id, associacao_id, paciente_id, profissional_id, data_evolucao,
nota_evolucao, fonte_origem
-- FALTAM no schema: created_at
```

### 3.2 Models SQLAlchemy (models.py)

```python
class Prescricao(db.Model):
    id, associacao_id, paciente_id, profissional_id, data_emissao,
    arquivo_path, conteudo_json, observacoes  # SEM medicamentos/orientacoes

class Evolucao(db.Model):
    id, associacao_id, paciente_id, profissional_id, data_evolucao,
    nota_evolucao, fonte_origem  # SEM created_at

class Profissional(db.Model):
    id, nome, crm, uf_crm, conselho_tipo, usuario, senha, email, role,
    ...  # SEM senha_hash, SEM is_active
```

### 3.3 database_schema.sql (origem do schema)

```sql
CREATE TABLE profissionais (
    id SERIAL PRIMARY KEY, nome TEXT, crm TEXT, usuario TEXT,
    **senha TEXT**,  -- não senha_hash
    ...
    **ativo BOOLEAN NOT NULL DEFAULT TRUE**,  -- não is_active
    ...
);
```

→ O schema original usa `senha` (não `senha_hash`) e `ativo` (não `is_active`).

### 3.4 Alembic state (catastrófico)

```
$ docker exec siap-db psql -U siap_user -d aracannabis \
    -c "SELECT version_num FROM alembic_version;"
              version_num
REDACTED
 REDACTED
```

**Apenas 1 migration aplicada** num repo com 15+ migrations. A cadeia real é:

```
0331305d2b3c (init) → ec450c16ec01 → f3a8c9d2e1b4 →
bb2cbd44835d (merge) → a7b8c9d0e1f2 (merge) → d3e4f5a6b7c8 →
2026_06_17 → 2026_06_21 → 2026_06_22
```

MAS: `flask db heads` retorna **só `2026_06_22` como head** — significa que **as
outras 13+ migrations estão OBSOLETAS** (não linkam mais à cadeia ativa).

**Quem fez o `alembic stamp 2026_06_22`?** Desconhecido — provavelmente alguém
rodou `alembic stamp` direto para pular todas as migrations.

---

## 4. O QUE FOI FEITO (D05e → D05i)

### D05e/D05f — RESOLVIDO ✅

- **Webhook secrets ausentes** corrigidos
- Backup `.env.production.bak.pre_d05f_20260701_225023`
- 4 secrets gerados via `secrets.token_urlsafe(32)` (tam=43 cada)
- `MERCADOPAGO_MODULOS_WEBHOOK_SECRET` = mesmo valor de
  `MERCADOPAGO_WEBHOOK_SECRET`
- Aplicação atômica via `os.replace()`
- `chmod 600 root:root`
- `INTERNAL_SERVICE_KEY` já estava presente
- Coluna `alembic_version.version_num` alterada para `VARCHAR(255)` (tinha 32,
  nomes de migrations novas têm 41)

### D05g — RESOLVIDO ✅

- **CPU alta investigada e explicada:** crash loop, não leak
- py-spy dump identificou que workers ficam em `crewai/*` durante boot
- Cada ciclo de boot = 30-60s × 3 workers = ~360% CPU

### D05h — PARCIAL ⏸️

- Parar crash loop: ✅ (`docker compose stop siap-backend`)
- Aplicar migrations: ⚠️ Parcial (só 1 migration aplicável, outras obsoletas)
- Validar boot: ❌ Falha — deploy_guard continua abortando

### D05i — DIAGNÓSTICO COMPLETO ✅

- **Causa raiz identificada:** `CRITICAL_TABLES` desatualizado
- Validação: `models.py` NÃO declara as colunas exigidas
- Validação: `database_schema.sql` original NÃO tem essas colunas
- Validação: migrations no repo NÃO criam essas colunas
- **Conclusão:** deploy_guard está pedindo colunas que nunca existiram

---

## 5. AÇÕES RECOMENDADAS (fora do escopo D05e)

### Opção A — Atualizar `CRITICAL_TABLES` (RECOMENDADO)

Em `services/deploy_guard.py:47-77`, substituir as colunas exigidas pelas que
existem realmente:

```python
CRITICAL_TABLES: Dict[str, List[str]] = {
    "pacientes": [
        "id", "nome", "data_nascimento", "cpf", "profissional_responsavel_id",
        "associacao_id", "created_at", "updated_at", "is_active",
        "data_revogacao", "consentimento_lgpd", "data_consentimento",
        "foto_nome", "foto_caminho", "foto_tipo", "foto_tamanho",
    ],
    "consultas": [
        "id", "paciente_id", "profissional_id", "data_hora",
        "status", "tipo_consulta", "associacao_id",
    ],
    "prescricoes": [
        "id", "paciente_id", "profissional_id",
        "conteudo_json",  # era medicamentos+orientacoes+validade_dias (refactor)
        "associacao_id", "data_emissao",  # data_emissao já cobre created_at
    ],
    "evolucoes": [
        "id", "paciente_id", "profissional_id",
        "data_evolucao",  # já existe, faz papel de created_at
        "nota_evolucao", "associacao_id",
    ],
    "profissionais": [
        "id", "nome", "crm", "uf_crm", "usuario",
        "senha",  # era senha_hash (não foi refatorado no banco)
        "email", "role",
        # SEM is_active (não existe — schema original usa "ativo" em outras tabelas)
    ],
}
```

**Risco:** se o código SQLAlchemy em produção realmente depender dessas colunas
(e.g., algum `SELECT` com `is_active`), vai quebrar queries em runtime.

**Mitigação:** rodar
`grep -rn "is_active\|senha_hash\|medicamentos\|orientacoes\|validade_dias" routes/ services/`
para confirmar que o código NÃO usa essas colunas em runtime.

### Opção B — Criar migrations para adicionar colunas

Criar uma nova migration `REDACTED.py` que
adiciona:

- `prescricoes.medicamentos` (JSON), `orientacoes` (TEXT), `validade_dias`
  (INT), `created_at` (TIMESTAMP)
- `evolucoes.created_at` (TIMESTAMP)
- `profissionais.senha_hash` (VARCHAR), `is_active` (BOOLEAN)

**Risco:** se o código não usa essas colunas, é trabalho desperdiçado. **Risco
2:** se a aplicação usa essas colunas mas com nomes diferentes, vai dar
conflito.

### Opção C — Comentar deploy_guard (NÃO RECOMENDADO)

Pior opção. Perde-se toda a proteção que o deploy_guard oferece.

---

## 6. RECOMENDAÇÃO FINAL

**Recomendação: Opção A + smoke test rigoroso antes de produção.**

1. Atualizar `CRITICAL_TABLES` em `services/deploy_guard.py:47-77`
2. Adicionar testes automatizados para validar sincronização `CRITICAL_TABLES`
   vs `models.py`
3. Adicionar CI check que falha se `CRITICAL_TABLES` declarar coluna não
   presente em `models.py`
4. Documentar em `docs/DEPLOY_GUARD_MAINTENANCE.md` como manter sincronizado

---

## 7. ESTADO ATUAL DO VPS

| Item                                 | Status                                               |
| REDACTED | REDACTED |
| Webhook secrets                      | ✅ RESOLVIDO                                         |
| Migrations alembic                   | ✅ Atualizada (2026_06_22)                           |
| Coluna `alembic_version.version_num` | ✅ VARCHAR(255)                                      |
| Container `siap-backend`             | ⏸️ PARADO (decisão consciente para parar crash loop) |
| `deploy_guard`                       | ❌ BLOQUEANDO (desatualizado)                        |
| CPU VPS                              | ✅ Normalizado (após stop)                           |
| `siap-frontend`                      | ✅ UP (Up 5h+)                                       |
| Traefik                              | ✅ Funcionando (responde 502 quando backend cai)     |

---

## 8. PENDÊNCIAS EXTERNAS (webhooks)

Após fix do deploy_guard, ainda há sincronização externa:

| Sistema                | Secret                                               | Ação necessária                                                                       |
| ---------------------- | REDACTED | REDACTED |
| MercadoPago Developers | `MERCADOPAGO_WEBHOOK_SECRET`                         | Provisionar novo secret no painel MP para `/api/mercadopago/webhook`                  |
| MercadoPago Developers | `MERCADOPAGO_MODULOS_WEBHOOK_SECRET` (= mesmo valor) | Provisionar para `/api/modulos/webhook`                                               |
| Evolution API          | `EVOLUTION_WEBHOOK_SECRET`                           | Configurar via `curl POST /webhook/set/<instance>` (PHASE4_DEPLOY_CHECKLIST.md:53-63) |
| Dr.Anderson Agent      | `DR_ANDERSON_WEBHOOK_SECRET`                         | Configurar no Agent                                                                   |

---

## 9. PRÓXIMOS PASSOS

1. **Sprint dedicado** para Opção A (atualizar `CRITICAL_TABLES`)
2. Adicionar testes de sincronização `CRITICAL_TABLES` ↔ `models.py`
3. Adicionar CI check
4. Aplicar migrations pendentes após atualização do código
5. Subir `siap-backend` e validar smoke completo
6. Re-rodar D05f F7 (smoke endpoints)
7. Re-rodar D05f F8 (sincronização externa de webhooks)

---

**Referências:**

- `services/deploy_guard.py:47-77` — CRITICAL_TABLES desatualizado
- `services/deploy_guard.py:367-380` — lógica de assertion
- `services/webhook_auth.py:432-442` — assert_required_secrets_on_startup
  (correto)
- `models.py` — SQLAlchemy models (fonte da verdade)
- `database_schema.sql` — schema original
- `app_cors_livre.py:436` — chamada de `run_all_checks`
- `.env.production.bak.pre_d05f_20260701_225023` — backup com secrets OK
- `services/webhook_auth.py` — webhook secrets OK
