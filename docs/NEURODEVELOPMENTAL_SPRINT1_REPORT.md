# Sprint 1 — Módulo NEURODESENVOLVIMENTO — Relatório de Entrega

> Plataforma multi-propósito de assistência, pesquisa, gestão e ensino em
> neurodesenvolvimento. **Substitui e amplia o "módulo TEA"**.
> Multi-tenant, audit-friendly, LGPD-compliant, IA clínica NÃO diagnóstica.

**Tag:** `v1.0.0-neuro-s1` (a tagger após aprovação humana)
**Branch:** `feature/neurodevelopmental-sprint-1`
**Período:** 2026-07-14 → 2026-07-15
**Status:** 🟢 **Pronto para aprovação humana antes de Sprint 2**

---

## TL;DR

Sprint 1 entrega o **esqueleto institucional** + o **primeiro subsistema plugin-based (escalas)**:

- Camada de plataforma: permissões, roles, eventos, migrations, mixins audit
- 2 escalas builtin (GAD-7 + PHQ-9) rodando via registry plugin-aware
- 5 endpoints REST + persistência polimórfica
- 2 páginas React + 1 service client
- **178/178 testes passando, cobertura 98%**

Tudo pronto para que o **Sprint 2** adicione mais 6 escalas sem tocar no código central
(plugin-based architecture).

---

## Definição de Pronto (DoD) — checklist

| Critério | Status | Evidência |
|---|---|---|
| Pacote `araos.specialties.neurodevelopmental` criado | ✅ | `araos/specialties/neurodevelopmental/{__init__.py,db_models.py,scales/}/` |
| `AuditFieldsMixin` em `araos.platform.tenant.models` | ✅ | `created_by/updated_by/deleted_by` columns |
| Permissões `neuro.*` em `Permission` | ✅ | 20 constantes + registradas em `PermissionRegistry._VALID_PERMISSIONS` |
| 3 roles novas (`neuro_physician`, `health_secretary`, `scientific_producer`) | ✅ | `RoleRegistry._ROLES` |
| 15 eventos `NEURODEVELOPMENTAL_*` em `_EVENT_CATALOG` | ✅ | Todos `sensitive=True` (LGPD) |
| Migração Alembic cria `neuro_scale_responses` | ✅ | `migrations/versions/REDACTED.py` |
| Plugin registry: `ScaleSpec`, `ScaleRegistry`, `ScaleRunner`, `ScaleResponseStore` | ✅ | `araos/specialties/neurodevelopmental/scales/` |
| 2 escalas builtin (GAD-7 + PHQ-9) com JSON Schema, score e interpretação | ✅ | `scales/builtins/{gad7,phq9}.py` |
| 5 rotas Flask `/api/neuro/scales/*` | ✅ | `routes/neuro_scales.py` |
| 2 páginas React + 1 service | ✅ | `frontend/src/pages/neuro/`, `services/neuroService.js` |
| Suíte de testes ≥95% cobertura | ✅ | **98% statements, 178/178 passing** |
| Smoke test manual | 🟡 pendente aprovação humana | gravado após aprovação |

---

## Arquivos criados / modificados

### Plataforma (compartilhado)

| Arquivo | Mudança |
|---|---|
| `araos/platform/tenant/models.py` | +`AuditFieldsMixin` (10 linhas) |
| `araos/platform/identity/permissions.py` | +20 `NEURODEVELOPMENTAL_*` constants + 3 roles |
| `araos/platform/events/catalog.py` | +15 entries `domain="neurodevelopmental"`, `sensitive=True` |

### Pacote `neurodevelopmental` (greenfield)

```
araos/specialties/neurodevelopmental/
├── __init__.py                     # API pública (re-exports)
├── db_models.py                    # NeuroScaleResponseModel
├── scales/
│   ├── __init__.py                 # public re-exports
│   ├── base.py                     # ScaleSpec, ScaleSubscale, ScaleInterpretation, ScaleResult
│   ├── registry.py                 # ScaleRegistry (versioned + semantic sort)
│   ├── runner.py                   # ScaleRunner (validate→compute→interpret)
│   ├── store.py                    # ScaleResponseStore (SQLAlchemy persistence)
│   └── builtins/
│       ├── __init__.py             # _register_all() auto-registra
│       ├── gad7.py                 # GAD-7 (Spitzer et al. 2006)
│       └── phq9.py                 # PHQ-9 (Kroenke et al. 2001)
└── (Sprint 2 vai adicionar escalas sem tocar aqui)
```

### Migrações

| Arquivo | Conteúdo |
|---|---|
| `migrations/versions/REDACTED.py` | cria `neuro_scale_responses` com 9 índices (simples + compostos) |

### Rotas Flask

| Arquivo | Endpoints |
|---|---|
| `routes/neuro_scales.py` | `GET /catalog` · `GET /<code>` · `POST /<code>/apply` · `GET /responses/<id>` · `GET /responses` |

### Frontend (JS + JSDoc)

| Arquivo | Função |
|---|---|
| `frontend/src/services/neuroService.js` | cliente HTTP para `/api/neuro/scales/*` |
| `frontend/src/pages/neuro/NeuroScalesListPage.js` | catálogo de escalas (filtro idade + busca) |
| `frontend/src/pages/neuro/NeuroScaleApplyPage.js` | formulário genérico dinâmico via JSON Schema |

### Testes

| Arquivo | Cobertura |
|---|---|
| `tests/neuro_sprint1/__init__.py` | (vazio) |
| `tests/neuro_sprint1/test_base.py` | dataclasses (ScaleSpec, ScaleInterpretation, ScaleResult) |
| `tests/neuro_sprint1/test_registry.py` | registro, lookup, semantic versioning |
| `tests/neuro_sprint1/test_runner.py` | pipeline validate→compute→interpret, helpers estáticos |
| `tests/neuro_sprint1/test_builtins.py` | GAD-7 + PHQ-9 end-to-end (32 casos incluindo bandas, item crítico 9) |
| `tests/neuro_sprint1/test_store.py` | persistência, listagem, tenant-isolation |
| `tests/neuro_sprint1/test_routes_neuro_scales.py` | 5 endpoints Flask + JWT + X-Association-ID |
| `tests/neuro_sprint1/test_platform_extensions.py` | regressão de AuditFieldsMixin / permissions / roles / catalog |

**Total:** 178 testes · 393 statements · **98% cobertura** (target ≥95%)

---

## Cobertura de testes — sumário

```
Name                                                               Stmts   Miss  Cover
───────────────────────────────────────────────────────────────────────────────
araos/specialties/neurodevelopmental/__init__.py                       4      0   100%
araos/specialties/neurodevelopmental/db_models.py                     33      2    94%
araos/specialties/neurodevelopmental/scales/__init__.py                6      0   100%
araos/specialties/neurodevelopmental/scales/base.py                   69      0   100%
araos/specialties/neurodevelopmental/scales/builtins/__init__.py      13      0   100%
araos/specialties/neurodevelopmental/scales/builtins/gad7.py          30      1    97%
araos/specialties/neurodevelopmental/scales/builtins/phq9.py          39      2    95%
araos/specialties/neurodevelopmental/scales/registry.py               76      3    96%
araos/specialties/neurodevelopmental/scales/runner.py                 57      0   100%
araos/specialties/neurodevelopmental/scales/store.py                  66      1    98%
───────────────────────────────────────────────────────────────────────────────
TOTAL                                                                393      9    98%
```

**Como rodar:**

```bash
.venv/bin/python3 -m pytest tests/neuro_sprint1/ \
    --cov=araos/specialties/neurodevelopmental \
    --cov-report=term-missing
```

---

## Decisões arquiteturais relevantes

### 1. Plugin-based scales (núcleo crítico)

Adicionar nova escala = criar 1 arquivo em `scales/builtins/` + 1 linha em `_register_all()`.
Zero alteração no runner, store, rotas ou frontend. Validado com GAD-7 (≥14a) e
PHQ-9 (≥12a) que demonstram o caminho completo:

- 1 arquivo `gad7.py` declara `*_SPEC = ScaleSpec(...)`
- builtins `__init__.py` faz `ScaleRegistry.register(GAD7_SPEC)` no import
- Frontend descobre dinamicamente via `GET /api/neuro/scales/catalog`
- Formulário é gerado a partir do `json_schema` da escala (renderiza Likert
  automaticamente quando range 0-3)

### 2. Persistência polimórfica

`neuro_scale_responses.raw_responses` e `interpretation` são JSON. A coluna `interpretation`
foi ajustada para receber `dict` puro (não `ScaleInterpretation` dataclass) via helper
`_interpretation_to_dict()` no store. Risco eliminado de incompatibilidade com column JSON
do SQLAlchemy.

### 3. Multi-tenancy + LGPD

- Toda tabela nova herda de `Base` (declarativa) + `AuditFieldsMixin`
- 9 índices (single + composite) otimizam queries por tenant + paciente + escala
- Todos os 15 eventos têm `sensitive=True` → fluem para `EventAuditPipeline` →
  `araos_audit_ledger`
- Helper `_resolve_tenant_id()` exige `X-Association-ID` header (ou fallback do JWT)

### 4. IA clínica preparada (mas não-ativada nesta sprint)

`NeurodevelopmentalAgent` ainda não foi criado (Sprint 6). Mas a infra está pronta:
- Trust levels `STRUCTURED_DATA`/`GENERATED_SUMMARY` mapeados na spec
- Permission `NEURODEVELOPMENTAL_AI_USE` reservada
- Eventos de domínio modelados para suportar `AI_SUMMARY_GENERATED`

### 5. Cannabis não-reimplementado

NEURODESENVOLVIMENTO consome `araos.specialties.cannabis` (dataclasses) via import
deferido. Não há acoplamento no Sprint 1; será ativado no Sprint 4.

---

## Definition of Ready para Sprint 2

| Pré-requisito | Status |
|---|---|
| Plugin registry comprovadamente extensível | ✅ (2 escalas funcionam) |
| Schema e migrations Alic完备 | ✅ |
| Camada HTTP testada com JWT + tenant | ✅ |
| Cobertura ≥95% | ✅ (98% no domínio) |
| Plugin UI dinâmico funcionando | ✅ (NeuroScaleApplyPage renderiza qualquer escala do registry) |

## Próximos passos (Sprint 2 — 6 escalas)

| Escala | Categoria | Idade | Complexidade |
|---|---|---|---|
| **M-CHAT-R/F** | TEA screening | 16-30 meses | Alta (follow-up estructurado) |
| **CARS2** | TEA avaliação | ≥2 anos | Alta (15 itens + T scores) |
| **ATEC** | TEA longitudinal | 2-12 anos | Média (4 subescalas) |
| **Vineland-3** | Comportamento adaptativo | nascimento-90a | Alta (5 domínios, parent form) |
| **SNAP-IV** | TDAH screening | 6-17 anos | Baixa (similar a PHQ-9) |
| **SRS-2** | TEA social | 2,5+ anos | Média (65 itens, T scores) |

Sprint 2 alvo: implementar essas 6 + auto-registro, com ≥95% cobertura mantida.

---

## Comando de validação

```bash
# 1. Suite completa
.venv/bin/python3 -m pytest tests/neuro_sprint1/ \
    --cov=araos/specialties/neurodevelopmental \
    --cov-fail-under=95

# 2. Aplicar migration
alembic upgrade head

# 3. Sanity check Flask
python -c "from routes.neuro_scales import neuro_scales_bp; print('OK', neuro_scales_bp.url_prefix)"

# 4. Catálogo (via Python)
python -c "
from araos.specialties.neurodevelopmental.scales.builtins import _register_all
from araos.specialties.neurodevelopmental.scales.registry import ScaleRegistry
_register_all()
print([s.code for s in ScaleRegistry.list()])
"
# Esperado: ['GAD7', 'PHQ9']
```

---

## Riesgos conocidos (carry-over)

| Risco | Mitigação nesta sprint |
|---|---|
| Poucas escalas no catálogo (2) | Sprint 2 entrega 6 adicionais |
| Sem perfil neurodev ainda | Sprint 3 entrega `NeurodevelopmentalProfile` |
| Sem timeline unificada | Sprint 4 entrega |
| Sem dashboards | Sprint 5 |
| Sem IA clínica | Sprint 6 |

---

## Aguardando aprovação humana para:

1. ✅ Revisar este relatório
2. 🟡 Aprovar merge de `feature/neurodevelopmental-sprint-1` → `main`
3. 🟡 Aprovar início de **Sprint 2** (M-CHAT, CARS, ATEC, Vineland, SNAP-IV, SRS-2)
4. 🟡 Considerar demo gravada de 5min (apenas após aprovação)

---

**Gerado por:** Claude (M3 / Sonnet 4.6) · 2026-07-15
**Plano de referência:** `/home/holzwarth/.claude/plans/vivid-snuggling-moth.md` (aprovado)
