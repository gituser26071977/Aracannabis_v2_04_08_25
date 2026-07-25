# ADR-0008: KnowledgeGraph Materialization Strategy

| | |
|---|---|
| **Status** | 📋 Proposto (2026-07-22) |
| **Data** | 2026-07-22 |
| **Autor** | AraOS Architecture Board |
| **Decisor** | AraOS Architecture Board |
| **Impacto** | Persistence Layer · Knowledge Engine |
| **Substitui** | Premissa implícita anterior ("SQL replica invariantes de domínio") |
| **Constitucionalidade** | Não viola Constituição · Alinhado com ADR-0005, ADR-0006, AS-004 Draft 0.1 |
| **Foundation Freeze** | Não modifica Foundation Freeze (AS-000/001/002, ASM-001, ADR-0001..0006) |

---

## 1. Contexto

O Architecture Freeze v1.0 (2026-07-21) declara explicitamente em
`docs/ARCHITECTURE_FREEZE_REPORT.md:216-222`:

> **Próximas Etapas NÃO Autorizadas:**
> ❌ Materialized Graph permanece fora do escopo até ADR formal.

Esta proibição existe porque a materialização de um grafo relacional
introduz duplicação de invariantes (invariantes enforced pelo domínio
em `KnowledgeGraph.__post_init__` precisariam ser duplicados em FKs
SQL) e adiciona camadas de sincronização que comprometem replay
byte-identical.

Sprint 4.5 (Infrastructure Layer) precisa persistir `KnowledgeGraph`
como parte do `SQLKnowledgeRepository`. A pergunta concreta é:

> Como persistir `KnowledgeGraph` na camada SQL sem violar o Architecture
> Freeze, sem duplicar invariantes, e preservando replay determinístico?

---

## 2. Decisão

Adotamos **Opção A — JSON Blob Único** como estratégia padrão para
persistência do `KnowledgeGraph`:

1. **Tabela única** `knowledge_graphs` com coluna `graph_json` (JSONB).
2. **`graph_json` armazena** o output de `KnowledgeGraph.to_canonical_dict()`
   usando os parâmetros canônicos validados
   (`sort_keys=True, ensure_ascii=False, separators=(",", ":"), default=str`).
3. **Reconstruct** via constructor frozen do `KnowledgeGraph`, não
   via `from_canonical_dict()` (que não existe no domínio).
4. **Nenhuma tabela adicional** (`knowledge_graph_nodes`,
   `knowledge_graph_edges`) é criada por padrão.
5. **Referential integrity** permanece exclusivamente no domínio
   (enforced por `KnowledgeGraph.__post_init__` linhas 180-195).

**Opção B (Tabelas Materializadas)** permanece rejeitada por default.
Apenas pode ser autorizada por ADR-0009 (futuro), mediante justificativa
explícita (ex.: dashboard de navegação com queries SQL sobre vizinhança).

---

## 3. Justificativa

### 3.1 Por que Opção A é a escolha correta

**A. Replay byte-identical preservado.**

A serialização canônica produz um único blob determinístico por
KnowledgeGraph. `state_hash` é `SHA-256(canonical_dict)` excluindo
`graph_id` (UUID efêmero) e `built_at` (wall-clock). Persistir o blob
literal preserva replay sem necessidade de recomposição SQL.

**B. Invariantes não duplicadas.**

`KnowledgeGraph.__post_init__` valida referential integrity (todo
`edge.source_node_id` e `edge.target_node_id` deve existir em
`graph.nodes`). Esta validação é executada uma única vez no domínio.
Em SQL, o equivalente exigiria:

```sql
FOREIGN KEY (source_node_id) REFERENCES knowledge_graph_nodes(node_id),
FOREIGN KEY (target_node_id) REFERENCES knowledge_graph_nodes(node_id)
```

mas isso **duplica** invariantes em duas camadas (domínio + SQL) e
qualquer divergência entre elas seria fonte de bugs.

**C. Projeção é read-only (ADR-0005).**

`KnowledgeGraph` é uma projeção read-only do `ClinicalGenome`. Não há
update incremental nem queries relacionais sobre o grafo no caso de
uso atual. Materialização em tabelas separadas só faz sentido se houver
queries SQL sobre vizinhança/path/BFS — o que **não é requerido** por
Sprint 4.5 nem pelo manifesto público.

**D. Composite PK + tenant isolation já cobertos.**

A tabela `knowledge_graphs` usa PK `(tenant_id, graph_id)` e contém
apenas dados de um único paciente (`graph_id = sha256(tenant|patient)[:12]`).
Cross-tenant queries são impossíveis pela estrutura da PK.

### 3.2 Por que Opção B seria problemática (rejeitada)

**A. Duplicação de invariantes.**

Domínio: `KnowledgeGraph.__post_init__` valida referential integrity.
SQL: FKs `knowledge_graph_nodes → knowledge_graphs` + composite FKs
em edges. **Duas fontes de verdade** para a mesma invariante.

**B. Sync lag.**

Materialização requer rebuild from event stream. Lag entre evento
emitido e projeção atualizada. Não há mecanismo de reconciliação
canônica para grafos.

**C. Bloat de migration.**

+ 2 tabelas × ~10 colunas cada + 4 indexes + composite FK constraints
= ~50 linhas de schema adicional + testes de migração proporcional.

**D. Requer ADR-0009 (futuro).**

Se dashboard ou ML feature futura exigir queries SQL sobre grafo
(neighborhood, path, centralidade), um ADR-0009 específico deverá
justificar a quebra desta decisão. Não antecipar.

---

## 4. Detalhamento Técnico

### 4.1 Schema SQL (Opção A)

```sql
CREATE TABLE knowledge_graphs (
    tenant_id        VARCHAR(36) NOT NULL,
    graph_id         VARCHAR(64) NOT NULL,
    patient_id       VARCHAR(36) NOT NULL,
    state_hash       VARCHAR(64) NOT NULL,
    graph_json       JSONB NOT NULL,
    built_at         TIMESTAMPTZ NOT NULL,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at       TIMESTAMPTZ NULL,
    PRIMARY KEY (tenant_id, graph_id),
    CONSTRAINT fk_knowledge_graphs_tenant
        FOREIGN KEY (tenant_id)
        REFERENCES araos_organizations(id)
        ON DELETE NO ACTION  -- LGPD/audit compliance
);

CREATE INDEX REDACTED
    ON knowledge_graphs (tenant_id, state_hash);

CREATE INDEX ix_knowledge_graphs_tenant_patient
    ON knowledge_graphs (tenant_id, patient_id);

CREATE INDEX REDACTED
    ON knowledge_graphs (tenant_id, built_at DESC);
```

### 4.2 Mapper (Infraestrutura)

```python
# araos/clinical/knowledge/infrastructure/mappers.py

def graph_to_json(graph: KnowledgeGraph) -> dict:
    """Serializa KnowledgeGraph lossless para JSONB.

    Usa to_canonical_dict() do domínio (já validado em Sprint 4.4.5).
    """
    return graph.to_canonical_dict()


def graph_from_json(row) -> KnowledgeGraph:
    """Reconstruct KnowledgeGraph a partir de row SQL.

    NÃO usa from_canonical_dict() (não existe no domínio).
    Reconstrói via constructor frozen.
    """
    payload = row.graph_json
    return KnowledgeGraph(
        graph_id=row.graph_id,
        tenant_id=row.tenant_id,
        patient_id=row.patient_id,
        nodes=tuple(GraphNode.from_dict(n) for n in payload["nodes"]),
        edges=tuple(GraphEdge.from_dict(e) for e in payload["edges"]),
        built_at=row.built_at,
        state_hash=row.state_hash,
    )
```

### 4.3 Repository (Sprint 4.5 W1.3)

```python
class SQLKnowledgeRepository(KnowledgeRepository):
    def save_graph(self, graph: KnowledgeGraph) -> None:
        assert graph.tenant_id == self._tenant_id
        row = self._session.get(
            KnowledgeGraphModel,
            (self._tenant_id, graph.graph_id),
        )
        if row is None:
            row = KnowledgeGraphModel(
                tenant_id=self._tenant_id,
                graph_id=graph.graph_id,
            )
            self._session.add(row)
        row.graph_json = graph_to_json(graph)
        row.state_hash = graph.state_hash
        row.built_at = graph.built_at
        row.patient_id = graph.patient_id
        # NÃO self._session.commit()  # UoW owns transaction

    def load_graph(self, graph_id: str) -> KnowledgeGraph | None:
        row = self._session.get(
            KnowledgeGraphModel,
            (self._tenant_id, graph_id),
        )
        if row is None or row.deleted_at is not None:
            return None
        return graph_from_json(row)
```

### 4.4 Verificação de Equivalência Semântica

Sprint 4.5 W2.3 inclui `test_shadow_compare.py` que valida:

```python
def REDACTED(graph_inmemory):
    repo_memory = InMemoryKnowledgeRepository.for_testing("tA")
    repo_sql = SQLKnowledgeRepository(session, "tA")
    
    repo_memory.save_graph(graph_inmemory)
    repo_sql.save_graph(graph_inmemory)
    
    g_memory = repo_memory.load_graph(graph_inmemory.graph_id)
    g_sql = repo_sql.load_graph(graph_inmemory.graph_id)
    
    assert g_memory.to_canonical_dict() == g_sql.to_canonical_dict()
    assert g_memory.state_hash == g_sql.state_hash
```

---

## 5. Consequências

### 5.1 Positivas

- ✅ Replay byte-identical preservado (state_hash estável através de SQL).
- ✅ Invariantes enforced uma única vez (no domínio).
- ✅ Schema simples (1 tabela, 1 coluna JSONB).
- ✅ Migration reversível trivial (DROP TABLE).
- ✅ Composite PK garante tenant isolation estruturalmente.
- ✅ Zero risco de cross-tenant leak (FK para `araos_organizations`).

### 5.2 Negativas (aceitas)

- ⚠️ Queries SQL sobre grafo (neighborhood, path) **não são possíveis**
  via SQL puro. Requer ADR-0009 se for requisito futuro.
- ⚠️ Rebuild a partir do event stream requer re-hidratação completa do
  blob. Mas rebuild é raro (após corruption ou schema change).
- ⚠️ `graph_json` pode crescer (5 NodeTypes × 7 EdgeTypes × N genes
  × N correlations × N hypotheses). Estimativa: ~10-50 KB por graph.
  Aceitável para JSONB PostgreSQL.

### 5.3 Neutras

- ➖ Mappers (`graph_to_json`/`graph_from_json`) vivem em
  `araos/clinical/knowledge/infrastructure/` — não violam Pure Domain.
- ➖ `KnowledgeGraph.to_canonical_dict()` é o contrato canônico
  (já validado em Sprint 4.4.5). Não há duplicação de formato JSON.

---

## 6. Alternativas Consideradas

### 6.1 Opção B — Tabelas Materializadas (REJEITADA por default)

```sql
CREATE TABLE knowledge_graph_nodes (
    tenant_id VARCHAR(36) NOT NULL,
    graph_id  VARCHAR(64) NOT NULL,
    node_id   VARCHAR(64) NOT NULL,
    node_type VARCHAR(32) NOT NULL,
    entity_id VARCHAR(64) NOT NULL,
    attrs_json JSONB,
    PRIMARY KEY (tenant_id, graph_id, node_id),
    FOREIGN KEY (tenant_id, graph_id)
        REFERENCES knowledge_graphs(tenant_id, graph_id)
        ON DELETE CASCADE
);

CREATE TABLE knowledge_graph_edges (
    tenant_id VARCHAR(36) NOT NULL,
    graph_id  VARCHAR(64) NOT NULL,
    edge_id   VARCHAR(64) NOT NULL,
    edge_type VARCHAR(32) NOT NULL,
    source_node_id VARCHAR(64) NOT NULL,
    target_node_id VARCHAR(64) NOT NULL,
    attrs_json JSONB,
    weight DOUBLE PRECISION,
    PRIMARY KEY (tenant_id, graph_id, edge_id),
    FOREIGN KEY (tenant_id, graph_id, source_node_id)
        REFERENCES knowledge_graph_nodes(tenant_id, graph_id, node_id),
    FOREIGN KEY (tenant_id, graph_id, target_node_id)
        REFERENCES knowledge_graph_nodes(tenant_id, graph_id, node_id)
);
```

**Rejeitada por:** duplicação de invariantes + sync lag + bloat + ADR
adicional necessário.

### 6.2 Opção C — Múltiplas tabelas parciais (REJEITADA)

Uma tabela por NodeType (5 tabelas) + uma por EdgeType (7 tabelas).
Total: 12 tabelas. Rejeitada por explosão combinatória sem benefício.

### 6.3 Opção D — Graph database separado (Neo4j, etc.) (REJEITADA)

Adicionar stack de infra. Viola "manter SQLAlchemy/PostgreSQL".
Requeria ADR separado. Não considerado para Sprint 4.5.

---

## 7. Decisões Abertas / Trabalho Futuro

### 7.1 ADR-0009 (CONDICIONAL)

Se um requisito futuro surgir (ex.: dashboard de navegação no grafo
com queries SQL sobre vizinhança, ML feature de graph neural networks,
ou auditoria de paths causais), ADR-0009 deverá:

1. Documentar o requisito concreto que justifica materialização.
2. Avaliar custo/benefício entre Opção B vs graph database.
3. Definir estratégia de sincronização entre blob e tabelas.
4. Especificar testes de equivalência contínua.

**Sem ADR-0009, Opção B permanece proibida.**

### 7.2 Performance Baseline (Sprint 4.5 deliverable)

`docs/PERFORMANCE_BASELINE.md` deve medir:

- Latência `load_graph` (cold + warm cache).
- Tamanho médio do `graph_json` para 12 pacientes × 84 correlações
  (referência: demo Sprint 4.4).
- Tempo de serialização canônica.

Se latência > 100ms p95 para grafos típicos, avaliar JSONB
compression ou lazy-loading de edges.

---

## 8. Conformidade

| Foundation | Compatível? | Notas |
|---|---|---|
| AS-000 Language Specification | ✅ | Termos canônicos preservados |
| AS-001 Clinical Gene | ✅ | Não modificado |
| AS-002 Clinical Expression | ✅ | Não modificado |
| AS-004 Draft 0.1 (Clinical Knowledge) | ✅ | Knowledge Graph model (§11) preserva canonical_dict + state_hash |
| ASM-001 Meta Model | ✅ | 16 seções canônicas respeitadas |
| ADR-0001 Clinical Event Engine | ✅ | Replay determinístico preservado |
| ADR-0005 Clinical Genome Pivot | ✅ | KnowledgeGraph permanece projection read-only |
| ADR-0006 Normative Conflict Resolution | ✅ | Hierarquia normativa respeitada; este ADR é nível 4 |
| Architecture Freeze v1.0 | ✅ | §3 "Mudanças Proibidas" não violada |

---

## 9. Aprovação

**Status:** Proposto.

**Bloqueios para aceitação:**

1. Revisão por AraOS Architecture Board.
2. Validação contra ADR-0006 matriz de precedência.
3. Confirmação que nenhum requisito de Sprint 4.5+ exige Opção B.

**Próximo passo após aceitação:**

1. Sprint 4.5 W1.4 implementa schema conforme §4.1.
2. Mappers conforme §4.2.
3. SQLKnowledgeRepository conforme §4.3.
4. Test shadow_compare conforme §4.4.

---

## Histórico de Revisões

| Versão | Data | Mudança |
|---|---|---|
| 0.1 | 2026-07-22 | Redação inicial. Proposta Opção A (JSON blob) como padrão. |

---

> **Foundation Freeze respeitada.**
> **Architecture Freeze v1.0 preservada.**
> **Replay determinístico mantido.**
> **Opção A (JSON blob) selecionada como padrão para KnowledgeGraph persistence.**