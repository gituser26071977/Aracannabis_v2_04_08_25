# DEPLOY_GUARD_MAINTENANCE.md

**Versão:** 1.0 (D05j F5) **Propósito:** Procedimento operacional para manter
`CRITICAL_TABLES` sincronizado com `models.py` e o schema real do banco.

---

## Por que este documento existe

Em **D05i** foi descoberto que `services/deploy_guard.py:CRITICAL_TABLES` estava
exigindo colunas que **nunca existiram** no schema real:

- `prescricoes.medicamentos` / `orientacoes` / `validade_dias` / `created_at`
- `evolucoes.created_at`
- `profissionais.senha_hash` / `is_active`

Resultado: gunicorn workers crashavam em loop → CPU 366% no VPS (crash loop do
master). Investigação custou ~6h entre D05e/F/G/H/I.

**Causa raiz:** drift entre 3 fontes de verdade:

```
models.py ←── fonte "logica" (SQLAlchemy declara o codigo)
  │
  ├── database_schema.sql ←── fonte "fisica" do banco original
  │
  └── CRITICAL_TABLES (services/deploy_guard.py) ←── fonte "contrato minimo"
                                                      que o boot assume
```

Se as 3 fontes divergem, o guard ou aborta indevidamente (D05i) ou permite subir
codigo que vai quebrar queries em runtime (cenario oposto).

---

## A regra de ouro

> **Toda coluna em `CRITICAL_TABLES` TEM que existir em `models.py`.** **Toda
> coluna "critica para startup" em `models.py` TEM que estar em
> `CRITICAL_TABLES`.**

Isso é validado **automaticamente** por:

```
tests/test_deploy_guard_sync.py
├── TestDeployGuardSync — CRITICAL_TABLES ⊆ models.py (positivos)
└── TestNoLegacyColumns — colunas legacy NAO voltam (negativos)
```

O CI (workflow `ci-validate.yml`) roda `pytest tests/test_deploy_guard_sync.py`.
**Se o teste falhar, o PR tem drift — corrigir antes de mesclar.**

---

## Quando adicionar/remover coluna crítica

### Caso 1 — coluna NOVA em `models.py` que deve abortar boot se faltar

Exemplo: você adiciona `pacientes.consentimento_revocado_em` em `models.py` e
quer garantir que o boot quebra se ela não existir no banco em produção.

**Passos:**

1. Adicionar a coluna em `models.py` (classe correspondente).
2. Criar migration Alembic:
   ```bash
   cd /root/projetos/araos
   docker exec siap-backend flask db migrate -m "add pacientes.consentimento_revocado_em"
   docker exec siap-backend flask db upgrade
   ```
3. Adicionar a coluna em `CRITICAL_TABLES` (em `services/deploy_guard.py`):
   ```python
   "pacientes": [
       ...
       "consentimento_revocado_em",  # NOVA coluna critica
   ],
   ```
4. Rodar os testes localmente:
   ```bash
   pytest tests/test_deploy_guard_sync.py -v
   ```
5. CI valida → merge → deploy.

### Caso 2 — coluna REFATORADA em `models.py` (renomeação ou split)

Exemplo: `pacientes.observacoes` (TEXT) foi dividido em
`pacientes.observacoes_clinicas` + `pacientes.observacoes_admin`.

**Passos:**

1. Criar migration que adiciona colunas novas + (se quiser) renomeia/marca a
   antiga.
2. Atualizar `models.py` refletindo o novo estado.
3. Atualizar `CRITICAL_TABLES` — removendo o nome antigo, adicionando os novos.
4. Atualizar toda rota que faz `Paciente.observacoes` (grep!):
   ```bash
   grep -rn "observacoes" routes/ services/
   ```
5. Atualizar testes existentes em `tests/test_deploy_guard.py` (a fixture
   `SCHEMA_REAL` precisa bater com o novo schema).
6. Rodar `pytest tests/test_deploy_guard.py tests/test_deploy_guard_sync.py`.

### Caso 3 — coluna REMOVIDA em `models.py` (não é mais necessária)

Exemplo: limpamos o legado e `profissionais.conselho_tipo` foi removido (porque
ninguém usa).

**Passos:**

1. Criar migration que dropa a coluna (`op.drop_column`).
2. Remover da classe em `models.py`.
3. Remover de `CRITICAL_TABLES` (se estava lá).
4. Rodar testes.

---

## Quando NÃO tocar em `CRITICAL_TABLES`

`CRITICAL_TABLES` é **minimo necessario** para o startup. Não é uma descrição
completa do schema. Não é um substituto de `models.py`.

**Não adicione coluna em `CRITICAL_TABLES` "por garantia"**. Cada entrada ali
multiplica o trabalho de manutenção. Use este criterio:

| A coluna eh usada por codigo que roda no startup?                                         | Adicionar em CRITICAL_TABLES? |
| REDACTED | ----------------------------- |
| **SIM** (rotas executadas em todo boot, decorators, before_request, hook de tenant, etc.) | SIM                           |
| NAO (rotas chamadas sob demanda, sem semantica de "boot")                                 | NAO                           |

Se tiver duvida, comece **sem** adicionar em `CRITICAL_TABLES`. O teste de smoke
em produção vai pegar se algo estiver errado (muito mais rapido do que aprender
na madrugada).

---

## Como o CI protege contra drift

```yaml
# .github/workflows/ci-validate.yml (trecho relevante)
- name: Validar sincronizacao deploy_guard vs models
  run: pytest tests/test_deploy_guard_sync.py -v --tb=short
```

Resultado tipico de um PR com drift:

```
FAILED tests/test_deploy_guard_sync.py::TestDeployGuardSync::REDACTED
AssertionError: CRITICAL_TABLES['pacientes'] exige colunas que nao existem
em models.Paciente: ['nova_coluna_inexistente'].
```

→ O PR NAO pode ser mergeado. **Não use `--no-verify`.** Corrija a divergência
antes (geralmente é typo).

---

## Como auditar o estado atual

### Audit rapido (1 comando)

```bash
cd /home/holzwarth/Projetos/Aracannabis_SO/Aracannabis_SIAP
pytest tests/test_deploy_guard_sync.py tests/test_deploy_guard.py -v
```

Esperado: `23 passed`.

### Audit profundo (diagnostico)

```bash
# 1. Diff entre CRITICAL_TABLES e models.py
pytest tests/test_deploy_guard_sync.py -v --tb=long

# 2. Estado real do banco via /api/schema-version
curl -s https://api.visualsmartflow.com.br/api/schema-version | jq .

# 3. Estado das migrations
docker exec siap-backend flask db current
docker exec siap-backend flask db heads
```

Se `2.` e `3.` batem com `1.` (testes passam), tudo está em sync.

---

## Procedimento pós-incidente (D05i como referencia)

Caso o `deploy_guard` aborte boot indevidamente no futuro:

### Passo 1 — Fotografar o erro

```bash
docker logs --tail=200 siap-backend 2>&1 | grep -A 20 "ABORT STARTUP"
```

### Passo 2 — Listar as colunas REAIS do banco

```bash
docker exec siap-db psql -U siap_user -d aracannabis -c "\d pacientes"
docker exec siap-db psql -U siap_user -d aracannabis -c "\d prescricoes"
docker exec siap-db psql -U siap_user -d aracannabis -c "\d evolucoes"
docker exec siap-db psql -U siap_user -d aracannabis -c "\d profissionais"
```

### Passo 3 — Comparar com `models.py`

```bash
grep -n "^class \(Paciente\|Consulta\|Prescricao\|Evolucao\|Profissional\)" models.py
```

Para cada coluna pedida por `CRITICAL_TABLES` que nao aparece em (2) nem em (3),
atualizar o `CRITICAL_TABLES` no codigo.

### Passo 4 — Atualizar este documento (CHANGELOG)

Adicione uma entrada na secao [Historico de divergencias corrigidas] abaixo.

---

## Historico de divergencias corrigidas

| Data       | ID        | Divergencia                                                                                                                                                                     | Acao                                                                                                               |
| ---------- | --------- | REDACTED | REDACTED |
| 2026-07-03 | D05i/D05j | `CRITICAL_TABLES` exigia `medicamentos`, `orientacoes`, `validade_dias`, `created_at`, `senha_hash`, `is_active` que NAO existiam em models.py nem no schema. Sync test criado. | `services/deploy_guard.py:CRITICAL_TABLES` reduzido ao schema real + `tests/test_deploy_guard_sync.py` (23 testes) |

---

## Checklist do operador (deploy)

Antes de fazer merge de mudanca em `models.py` que afete tabelas criticas:

- [ ] Atualizei `CRITICAL_TABLES` em `services/deploy_guard.py`?
- [ ] Criei migration Alembic correspondente?
- [ ] Apliquei a migration no banco dev/staging?
- [ ] Rodei `pytest tests/test_deploy_guard_sync.py` localmente → 0 falhas?
- [ ] Rodei `pytest tests/test_deploy_guard.py` localmente → 0 falhas?
- [ ] Verifiquei `grep` em `routes/` para garantir que codigo novo nao assume
      coluna que nao declarei em `models.py`?
- [ ] Documentei mudanca no CHANGELOG deste arquivo?

Se todos os 7 items = YES, PR pode ser mergeado.

---

## Referencias

- `services/deploy_guard.py:47-121` — CRITICAL_TABLES
- `services/deploy_guard.py:173-198` — `_table_has_columns` (SQL
  information_schema)
- `services/deploy_guard.py:340-384` — `assert_schema_columns_exist` (abortador)
- `tests/test_deploy_guard.py` — testes do comportamento do guard
- `tests/test_deploy_guard_sync.py` — testes de sync com models.py (D05j F3)
- `docs/D05I_DEPLOY_GUARD_DESYNC.md` — D05i (causa raiz do problema)
- `app_cors_livre.py:436` — onde `run_all_checks()` é chamado no boot

---

**Responsavel:** engenharia **Proxima revisao:** quando uma nova tabela critica
for adicionada ao schema
