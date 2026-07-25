# Sprint 2 — Módulo NEURODESENVOLVIMENTO — Relatório de Entrega

> Plugin registry ampliado de 2 → 8 escalas neuropsicológicas.
> **Arquitetura plugin-based comprovada:** 6 novas escalas entregues
> SEM alteração no runner, store, rotas ou frontend.

**Tag:** `v1.0.0-neuro-s2` (a tagger após aprovação humana)
**Branch:** `feature/neurodevelopmental-sprint-2`
**Período:** 2026-07-15
**Status:** 🟢 **Pronto para aprovação humana antes de Sprint 3**

---

## TL;DR

Sprint 2 entrega **6 escalas adicionais** somando **8 escalas totais** no registry.
Todas com referência bibliográfica ABNT, JSON Schema validável, score_function
pura e interpretation_function com bandas clínicas.

| # | Escala | Categoria | Idade | Função clínica |
|---|---|---|---|---|
| 1 | **GAD-7** | Ansiedade | ≥14a | Screening |
| 2 | **PHQ-9** | Depressão | ≥12a | Screening + item 9 (autolesão) |
| 3 | **M-CHAT-R/F** | TEA | 16-30m | Rastreamento populacional |
| 4 | **CARS2** | TEA | ≥2a | Avaliação clínica por profissional |
| 5 | **ATEC** | TEA longitudinal | 2-12a | Monitoramento de intervenção |
| 6 | **Vineland-3** | Comportamento adaptativo | 0-90a | Avaliação adaptativa |
| 7 | **SNAP-IV** | TDAH/TOD | 6-17a | Screening |
| 8 | **SRS-2** | TEA social | ≥2,5a | Rastreamento |

---

## Resultados de testes

```
238 passed in 2.62s
Coverage: 806 statements, 20 missing, 98%
```

**Quebra por arquivo:**

| Módulo | Stmts | Miss | Cover |
|---|---|---|---|
| `ataec.py` | 82 | 0 | **100%** |
| `mchat.py` | 53 | 0 | **100%** |
| `scales/runner.py` | 57 | 0 | **100%** |
| `scales/base.py` | 69 | 0 | **100%** |
| `scales/store.py` | 66 | 1 | 98% |
| `scales/builtins/__init__.py` | 19 | 0 | **100%** |
| `gad7.py` (Sprint 1) | 30 | 1 | 97% |
| `srs2.py` | 79 | 2 | 97% |
| `vineland.py` | 80 | 3 | 96% |
| `registry.py` | 76 | 3 | 96% |
| `cars2.py` | 39 | 2 | 95% |
| `phq9.py` | 30 | 1 | 97% |
| `snap_iv.py` | 74 | 4 | 95% |
| `db_models.py` | 33 | 2 | 94% |
| **TOTAL** | **806** | **20** | **98%** ✅ |

---

## Decisões críticas da Sprint 2

### 1. M-CHAT-R/F — Critical items rule

O protocolo M-CHAT-R/F (Robins et al. 2014) tem regra assimétrica: ≥2 itens
críticos positivos (Q2, Q5, Q7, Q9, Q13, Q14, Q15) já indicam **alto risco**
independentemente do escore total. Implementado em `_interpret_mchat`:

```python
if critical >= 2:
    band = "alto_risco"  # mesmo se total ≤ 2
elif total <= 2:
    band = "baixo_risco"
elif total <= 7:
    band = "medio_risco"
else:
    band = "alto_risco"
```

### 2. CARS2 — Likert 1-4 (não 0-3)

Diferente das outras escalas, CARS-2 usa 1-4 (1=típico, 4=severamente atípico)
porque "0" não é clinicamente significativo (comportamento SEMPRE apresenta
algum grau). Schema validation `minimum: 1, maximum: 4` enforça.

### 3. ATEC — 4 sub-escalas com ranges heterogêneos

ATEC é a única escala com **3 ranges diferentes** na mesma escala:
- Speech/Language, Sociability, Sensory: 0-2 (3 domínios × 5-10 itens)
- Health/Behavior: 0-3 (1 domínio × 13 itens)

`ScaleSpec.subscales` lista cada domínio com `min/max` próprios. Testes
parametrizados por sub-escala.

### 4. Vineland-3 — versão reduzida documentada como tal

`VINELAND_SPEC.description` declara explicitamente:

> "Esta versão reduzida opera com escores brutos e NÃO produz T-scores
> oficiais. Para uso clínico definitivo, aplicar protocolo original
> com tabelas normativas por idade."

Anti-engano: 3 alertas no JSON Schema description + 1 banner na `description`
do spec. Sub-escala Motor é opcional (`required` não inclui vn16-vn20)
porque o domínio Motor não compõe o Adaptive Behavior Composite após 6 anos.

### 5. SNAP-IV — sub-escala por média (não soma)

SNAP-IV usa **média** dos itens por sub-escala (não soma), porque pontos
de corte são normalizados (≥1.0 = sugestivo, ≥1.5 = severo). Implementado
em `_score_snap` retornando tanto `total` (soma) quanto `mean` por sub-escala.

### 6. SRS-2 — redução científica de 65 → 25 itens

SRS-2 oficial exige licenciamento Western Psychological Services.
A versão reduzida (5 itens × 5 sub-escalas) é a única forma de
disponibilizar o screening sem licença. Documentado em `description`:
T-score oficial NÃO é produzido. Para T-score real, o sistema deve
integrar tabelas normativas em sprint futura.

---

## Plugins validados (zero alteração de código central)

Sprint 1 entregou 2 escalas (GAD-7, PHQ-9). Sprint 2 entregou 6 escalas
adicionais. Para isso:

- ✅ Nenhuma alteração em `scales/base.py`
- ✅ Nenhuma alteração em `scales/registry.py`
- ✅ Nenhuma alteração em `scales/runner.py`
- ✅ Nenhuma alteração em `scales/store.py`
- ✅ Nenhuma alteração em `routes/neuro_scales.py`
- ✅ Nenhuma alteração em `frontend/src/pages/neuro/NeuroScaleApplyPage.js`
- ✅ 1 arquivo por escala em `scales/builtins/`
- ✅ 1 linha por escala em `scales/builtins/__init__.py`

**Custo de adicionar uma 9ª escala:** 1 arquivo (~200 linhas) + 2 linhas
no `__init__.py`. Zero deploy de backend ou frontend.

---

## Definition of Done (DoD)

| Critério | Status |
|---|---|
| 6 escalas adicionais implementadas | ✅ |
| Todas com JSON Schema, score e interpretação | ✅ |
| Todas com referência bibliográfica ABNT | ✅ |
| Auto-registro funcionando | ✅ |
| Catálogo lista 8 escalas via `GET /api/neuro/scales/catalog` | ✅ |
| Filter por idade funciona | ✅ |
| Formulário dinâmico renderiza qualquer escala | ✅ |
| Suíte de testes ≥95% cobertura | ✅ (98%) |
| 238 testes passando | ✅ |
| Regressão Sprint 1 mantida | ✅ (GAD-7 + PHQ-9 testados em Sprint 2) |

---

## Como rodar

```bash
.venv/bin/python3 -m pytest tests/neuro_sprint1/ tests/neuro_sprint2/ \
    --cov=araos/specialties/neurodevelopmental \
    --cov-fail-under=95
# Resultado: 238 passed, 98% coverage
```

```bash
# Listar todas as 8 escalas via Python
python -c "
from araos.specialties.neurodevelopmental.scales.builtins import _register_all
from araos.specialties.neurodevelopmental.scales.registry import ScaleRegistry
_register_all()
for s in ScaleRegistry.list():
    print(f'{s.code:10s} {s.target_age_months!s:18s} {s.name}')
"
```

---

## Pendente para Sprint 3 (perfil neurodev + 4 escalas)

Sprint 3 entrega:
- **4 escalas restantes**: ABC, PSQI, AQ, Conners
- **NeurodevelopmentalProfile** com multi-diagnóstico (CID-10 + CID-11)
- **Catálogo versionado de condições** (TEA, TDAH, AH/SD, TOD, etc.)
- **Timeline** alimentada pelos eventos de escalas

---

## Riscos e mitigações

| Risco | Mitigação |
|---|---|
| Versões reduzidas (Vineland, SRS-2) sem T-score | Banner explícito em `spec.description` + `json_schema.description` |
| Custo de licenciamento (SRS-2 oficial, CARS-2, Vineland-3) | Versão reduzida para fins de screening; protocolo original sob licença em produção |
| Sem normatização PT-BR oficial para algumas escalas | Referências marcadas como "validação parcial" ou "adaptação acadêmica" |
| Snap-IV pré-DSM-5 | Mantido como screening (DSM-IV); para DSM-5 usar Vanderbilt em sprint futura |

---

## Aguardando aprovação humana

1. ✅ Revisar este relatório
2. 🟡 Aprovar merge de `feature/neurodevelopmental-sprint-2` → `main`
3. 🟡 Aprovar início de **Sprint 3** (4 escalas + perfil neurodev)
4. 🟡 Considerar demo gravada de 5 min (após aprovação)

---

**Gerado por:** Claude (M3 / Sonnet 4.6) · 2026-07-15
**Plano de referência:** `/home/holzwarth/.claude/plans/vivid-snuggling-moth.md`
**Sprint 1:** `docs/NEURODEVELOPMENTAL_SPRINT1_REPORT.md`
