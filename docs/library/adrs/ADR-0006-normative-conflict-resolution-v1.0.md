# ADR-0006: Normative Conflict Resolution and Governance

| | |
|---|---|
| **Status** | 📋 Proposto (2026-07-18) |
| **Data** | 2026-07-18 |
| **Autor** | AraOS Architecture Board |
| **Decisor** | AraOS Architecture Board |
| **Impacto** | Cross-cutting · governança normativa |
| **Substitui** | Premissa implícita anterior ("resolver conflito por conversa") |
| **Constitucionalidade** | Não viola Constituição · Alinhado com AS-000 / ASM-001 |
| **Foundation Freeze** | Este ADR declara o congelamento da infraestrutura normativa |

---

## 1. Contexto

A infraestrutura normativa do AraOS atingiu maturidade suficiente para que sua operação seja previsível. Os componentes fixados até 2026-07-18 são:

- **Constituição** (Lex AraOS) — filosofia suprema
- **Papers** — teoria
- **AS-000** Language Specification — vocabulário canônico
- **ASM-001** Specification Meta Model — estrutura dos Standards
- **AS-001** Clinical Gene (Published) — Aggregate Root
- **AS-002** Clinical Expression (Draft) — Value Object
- **AraOS Library** — pipeline de publicação MD/HTML/PDF
- **Maturity Model 9 estados** — ciclo de vida editorial
- **Dependency Graph** — restrição downward-only
- **Traceability Chain** — Constituição → Evidence
- **Machine Readability Model** — JSON conceitual

Componentes em produção, ainda sem conflitos conhecidos, mas com **risco emergente**:

1. **Conflitos latentes** — múltiplos Standards podem usar o mesmo termo com semânticas distintas se não houver regra de desempate.
2. **Depreciação ad-hoc** — sem política explícita, depreciações ocorrerão caso a caso.
3. **Mudanças estruturais** — sem freeze, a tentação de "ajustar a infraestrutura" durante desenvolvimento clínico é alta.
4. **Ambiguidade de papéis** — quem aprova, quem rejeita, quem promove maturidade.
5. **Resolução慢a de conflitos** — sem matriz de precedência, conflitos serão resolvidos por debate político em vez de regra.

Este ADR encerra **definitivamente** a infraestrutura normativa e estabelece as regras para que divergências futuras sejam resolvidas objetivamente.

---

## 2. Decisão

Adotamos **9 regras canônicas** que governam conflitos, depreciação, evolução e governança:

1. **Hierarquia normativa** de 9 níveis (§3)
2. **Matriz de precedência** (§4) que define o vencedor em cada par de conflitos
3. **Resolução de ambiguidades** (§5) para 7 tipos de conflito semântico
4. **Política de depreciação** (§6) com 7 estados formais
5. **Política de evolução** (§7) com SemVer editorial + técnico
6. **Política de governança** (§8) com papéis e competências
7. **Foundation Freeze** (§9) — congelamento oficial da infraestrutura normativa
8. **Confirmação de uso futuro** (§10) — Standards futuros usarão a infraestrutura existente
9. **Mecanismo de revisão** (§11) — como este ADR pode ser ele próprio revisado

---

## 3. Hierarquia Normativa Oficial

```
Nível 1 — Constituição (Lex AraOS)
   ↓
Nível 2 — Manifesto
   ↓
Nível 3 — Papers (Paper I, II, III, …)
   ↓
Nível 4 — ADRs (ADR-0001, ADR-0002, …)
   ↓
Nível 5 — ASM (ASM-001 Specification Meta Model)
   ↓
Nível 6 — AS (AS-001, AS-002, …)
   ↓
Nível 7 — Conformance (tests/conformance/…)
   ↓
Nível 8 — Reference Implementation
   ↓
Nível 9 — Application Code
```

### 3.1 Regra fundamental

> **Nenhum nível inferior pode contradizer um nível superior.**

Quando dois documentos do mesmo nível divergem, aplica-se a Matriz de Precedência (§4).

### 3.2 Caracterização de cada nível

| Nível | Função | Quem cria | Versão |
|---|---|---|---|
| 1 | Lei suprema do domínio | Constituição original | Imutável |
| 2 | Princípios éticos e culturais | AraOS Leadership | Imutável |
| 3 | Desenvolvimento teórico | Pesquisa | SemVer |
| 4 | Decisões arquiteturais | AraOS Architecture Board | SemVer |
| 5 | Estrutura normativa | AraOS Editorial Committee | SemVer |
| 6 | Especificações clínicas | AraOS Editorial Committee | SemVer |
| 7 | Testes de conformidade | Engenharia | Versionado com o AS |
| 8 | Implementações exemplares | Comitê Editorial (reconhece) | Versionado |
| 9 | Código de aplicação | Engenharia | SemVer |

---

## 4. Matriz de Precedência

Esta matriz é **exaustiva** e **definitiva**. Qualquer conflito entre dois documentos SHALL ser resolvido por esta tabela.

| # | Conflito | Vencedor | Ação no perdedor |
|---|---|---|---|
| M1 | Constituição × Manifesto | Constituição | Manifesto revisado para alinhar |
| M2 | Constituição × Paper | Constituição | Paper revisado |
| M3 | Constituição × ADR | Constituição | ADR revisado |
| M4 | Constituição × ASM | Constituição | ASM revisado |
| M5 | Constituição × AS | Constituição | AS revisado |
| M6 | Constituição × Conformance | Constituição | Conformance revisado |
| M7 | Constituição × Code | Constituição | Code corrigido |
| M8 | Manifesto × Paper | Manifesto | Paper revisado |
| M9 | Manifesto × ADR | Manifesto | ADR revisado |
| M10 | Manifesto × AS | Manifesto | AS revisado |
| M11 | Paper × ADR | **ADR** | ADR revisado (Paper é teórico; ADR é decisão concreta) |
| M12 | Paper × ASM | ASM | ASM revisado |
| M13 | Paper × AS | AS | AS revisado |
| M14 | Paper × Code | Code corrigido (Paper é teórico; Code deve refletir AS) |
| M15 | ADR × ASM | ADR | ASM revisado |
| M16 | ADR × AS | **ADR** | AS revisado |
| M17 | ADR × Conformance | ADR | Conformance revisado |
| M18 | ADR × Code | ADR | Code corrigido |
| M19 | ADR × Reference Implementation | ADR | Reference Implementation corrigido |
| M20 | ASM × AS | **ASM** | AS revisado |
| M21 | ASM × Code | ASM | Code corrigido |
| M22 | AS × Conformance | AS | Conformance revisado |
| M23 | AS × Reference Implementation | AS | Reference Implementation corrigido |
| M24 | AS × Code | **AS** | Code corrigido |
| M25 | Conformance × Reference Implementation | Conformance | Reference Implementation corrigido |
| M26 | Conformance × Code | Conformance | Code corrigido |
| M27 | Reference Implementation × Code | Reference Implementation | Code corrigido |
| M28 | **Code × Testes** | **Code** | **Teste corrigido** (Teste reflete comportamento atual do Code) |
| M29 | **Teste × Standard** | **Standard** | **Teste corrigido para refletir o Standard** |
| M30 | Standard × Standard (mesmo nível) | Versão mais recente Published | Versão antiga depreciada |

### 4.1 Regra geral de leitura

A matriz é lida em pares: `Conflito` significa "dois documentos divergem". O **Vencedor** indica qual fonte SHALL prevalecer. O **perdedor** SHALL ser revisado, atualizado ou marcado como deprecated, conforme a natureza da divergência.

### 4.2 Conflitos M11 e M16 — ADR prevalece

> ADR é a **decisão arquitetural concreta e datada**. Paper é **teoria** e pode estar desatualizado. Quando divergem, ADR SHALL prevalecer e Paper SHOULD ser revisado para refletir a decisão.

### 4.3 Conflitos M28 e M29 — cuidado especial

| Conflito | Vencedor | Justificativa |
|---|---|---|
| Code × Teste | Code | Teste reflete comportamento atual do code. Se teste falha, code está errado e deve ser corrigido. |
| Teste × Standard | Standard | Standard é a fonte da verdade. Teste desatualizado SHALL ser corrigido para refletir Standard. |

**Caso degenerado (Code × Standard × Test):** Standard prevalece sempre. Code é corrigido para alinhar ao Standard; teste é corrigido para refletir o Standard corrigido.

---

## 5. Resolução de Ambiguidades

### 5.1 Catálogo de ambiguidades e resolução

| # | Tipo de ambiguidade | Definição | Resolução canônica |
|---|---|---|---|
| A1 | **Conceito indefinido** | Termo usado mas não definido em nenhum documento normativo. | Referenciar Constituição. Se ausente, abrir ADR para definir. Não usar termo em código até definição. |
| A2 | **Conceito duplicado** | Mesmo conceito definido em 2+ documentos. | Documento superior (na hierarquia) prevalece. Inferior referencia o superior. |
| A3 | **Conceito obsoleto** | Conceito definido mas marcado como discontinued. | Marcar como `deprecated`. Abrir ADR para depreciação formal. |
| A4 | **Conflito terminológico** | Termos diferentes para o mesmo conceito. | AS-000 §3 é autoridade. Usar termo canônico; sinônimos vão para glossário. |
| A5 | **Conflito semântico** | Mesmo termo com significados diferentes em contextos diferentes. | AS-000 §3 prevalece; contextos divergentes usam **subcontextos** explícitos (bounded context, namespace). |
| A6 | **Conflito temporal** | Versão antiga vs nova do mesmo documento. | Versão mais recente Published prevalece. Changelog SHALL documentar mudanças. Migration window aplicado. |
| A7 | **Conflito entre versões** | Duas versões ativas simultaneamente. | MAJOR version + SemVer. Versão antiga SHALL ser `deprecated` com migration window. |

### 5.2 Princípio geral

> **Em caso de ambiguidade, a fonte mais alta na hierarquia normativa prevalece.**

A ordem para desempate é: Constituição > Manifesto > Papers > ADRs > ASM > AS > Conformance > Reference Implementation > Code.

Quando há empate no mesmo nível:
1. Versão mais recente Published prevalece.
2. Se Published empate: Technical Review mais recente prevalece.
3. Se empate em maturidade: URN lexicograficamente maior prevalece (regra de desempate determinística).

---

## 6. Política de Depreciação

### 6.1 Estados formais

| Estado | Significado | Consequência |
|---|---|---|
| **Deprecated** | Marcada como obsoleta, mas ainda funcional e testada. | SHALL continuar funcionando e testada até archiving. Documentação SHALL indicar replacement. |
| **Superseded** | Substituída por nova versão ou novo documento. | Antiga SHALL manter URN. Nova referencia `supersedes`. Antiga referencia `superseded_by`. |
| **Archived** | Retirada sem substituição. | Pode ser removida do índice público, mas URN SHALL manter redirect. |

### 6.2 Replacement

- Um Standard/ADR MAY ser substituído por outro via `Replacement`.
- O Standard substituinte SHALL indicar `supersedes: <ID>` no header.
- O Standard substituído SHALL indicar `superseded_by: <ID>` no header.
- A Library SHALL manter ambos até archiving do substituído.

### 6.3 Backward Compatibility

- Mudanças SHOULD preservar compatibilidade descendente.
- Adição de novos requisitos = MINOR.
- Mudança em requisito existente = MAJOR.
- Quebra não-planejada SHALL ser tratada via `Breaking Change` formal (ver §7).

### 6.4 Forward Compatibility

- Implementações MAY antecipar features de versões futuras.
- O Standard SHOULD declarar features experimentais explicitamente.
- Features experimentais NÃO SHALL ser citadas como base de conformidade.

### 6.5 Migration Window

- Período entre deprecação e archiving de um documento.
- **Default: 12 meses** para Standards; **6 meses** para ADRs.
- Aplicável apenas a `Superseded` (não a `Archived` direto).
- Documentado no header do documento deprecated.

---

## 7. Política de Evolução (Change Control)

### 7.1 Tipos de mudança

| Tipo | Significado | Bump de versão | Aprovação |
|---|---|---|---|
| **Editorial** | Typos, clarificações de linguagem, formatação. | Sem bump (commit direto). | Revisor técnico. |
| **Patch** | Correção sem mudança de comportamento. | PATCH (X.Y.Z+1) | Revisor técnico + 1 voto editorial. |
| **Minor** | Adição retrocompatível (novo requisito, novo exemplo). | MINOR (X.Y+1.0) | Comitê Editorial (maioria 2/3). |
| **Major** | Mudança incompatível. | MAJOR (X+1.0.0) | Comitê Editorial (unanimidade). |
| **Breaking Change** | Mudança que quebra contrato existente. | MAJOR (X+1.0.0) | Comitê Editorial (unanimidade) + Migration Plan obrigatório. |

### 7.2 Quebra vs Não-Quebra

**Quebra (MAJOR):**
- Remoção de requisito SHALL.
- Mudança na semântica de requisito existente.
- Mudança em invariante.
- Mudança em verbo normativo (ex: SHOULD → SHALL).

**Não-quebra (MINOR):**
- Adição de novo requisito.
- Adição de novo exemplo.
- Adição de novo axioma.
- Clarificação de texto sem mudança semântica.

**Editorial (sem bump):**
- Correção de typos.
- Reformatação.
- Adição de cross-references.

### 7.3 Regras de transição

- Toda mudança SHALL ser registrada no Version History do documento.
- Mudanças MAJOR SHALL ser acompanhadas de ADR específico.
- Mudanças MAJOR SHALL abrir **Migration Window** mínimo de 6 meses.

---

## 8. Política de Governança

### 8.1 Papéis formais

| Papel | Quem | Responsabilidade |
|---|---|---|
| **Constitutional Guardian** | Líderança AraOS | Guardião da Constituição e Manifesto. Imutabilidade. |
| **Architecture Board** | Arquitetos seniores | Emite ADRs; revoga ADRs obsoletos; resolve conflitos cross-ADR. |
| **Editorial Committee** | Editores + Arquiteto | Aprovação/rejeição de Standards (ASM/AS). Promoção de maturidade. |
| **Engineering Lead** | Engenharia | Aprovação técnica (Technical Review). |
| **Scientific Reviewer** | Pesquisa | Aprovação científica (Scientific Review). |
| **Implementation Curator** | Comitê Editorial | Reconhece Reference Implementations. |

### 8.2 Quem pode fazer o quê

| Ação | Quem autoriza | Quórum |
|---|---|---|
| Aprovar Standard (qualquer nível de maturidade) | Editorial Committee | Maioria 2/3 |
| Rejeitar Standard | Editorial Committee | Maioria 2/3 |
| Substituir Standard | Editorial Committee + Replacement Published | Unanimidade |
| Depreciar Standard/Requirement | Editorial Committee + ADR publicado | Maioria 2/3 |
| Publicar Standard (qualquer maturidade) | Editorial Committee | Maioria 2/3 |
| Promover maturidade Draft → Technical Review | Editorial Committee (revê estrutura) | Maioria simples |
| Promover Technical → Scientific Review | Scientific Reviewer + Editorial Committee | 1 voto científico + maioria 2/3 editorial |
| Promover Scientific → Accepted | Editorial Committee + Scientific Reviewer | Unanimidade |
| Promover Accepted → Published | Editorial Committee | Maioria 2/3 |
| Promover Published → Verified | CI (Conformance Suite passa) | Automático |
| Promover Verified → Reference Implementation | Editorial Committee (reconhece implementação exemplar) | Unanimidade |
| Transição para Superseded | Editorial Committee + Replacement Published | Unanimidade |
| Transição para Archived | Architecture Board | Maioria 2/3 |
| Emendar este ADR (ADR-0006) | Architecture Board + 2/3 Editorial Committee | Maioria 3/4 combinada |

### 8.3 Conflitos de governança

- Disputas entre papéis SHALL ser resolvidas pelo **Architecture Board**.
- Decisões do Architecture Board podem ser apeladas à Liderança AraOS (Constitutional Guardian).
- Apelações NÃO suspendem a decisão durante o processo.

---

## 9. Foundation Freeze — Declaração Oficial

> ### §9.1 Declaração
>
> A partir da aceitação deste ADR-0006, a infraestrutura
> normativa do AraOS está **oficialmente congelada**.

### 9.2 Componentes congelados

| Componente | Status | Bump de versão permitido? |
|---|---|---|
| Constituição (Lex AraOS) | Imutável | ❌ Não |
| Manifesto | Imutável | ❌ Não |
| AS-000 Language Specification | Estável | ✅ Apenas PATCH (typos/clarificações) |
| ASM-001 Specification Meta Model | Estável | ✅ Apenas PATCH (typos/clarificações) |
| AraOS Library pipeline | Estável | ✅ Apenas PATCH |
| Maturity Model 9 estados | Estável | ✅ Apenas PATCH |
| Dependency Graph rules | Estável | ✅ Apenas PATCH |
| Traceability Chain | Estável | ✅ Apenas PATCH |
| Machine Readability model | Estável | ✅ Apenas PATCH |
| Conformance Suite structure | Estável | ✅ Apenas PATCH |
| Requisitos normativos deste ADR-0006 | Estável | ❌ Não (mudanças exigem novo ADR) |

### 9.3 Processo para mudança na infraestrutura congelada

Mudanças na infraestrutura congelada SHALL exigir:

1. **Novo ADR específico** descrevendo a mudança proposta.
2. **Aprovação unânime** do Editorial Committee.
3. **Migration Plan documentado** caso a mudança quebre compatibilidade.
4. **Foundation Thaw explícito** — um ADR declarando o descongelamento.

### 9.4 Foundation Thaw

Em circunstâncias excepcionais (ex: descoberta de bug estrutural grave), o Foundation Freeze pode ser revertido via:

1. ADR específico intitulado `ADR-XXXX: Foundation Thaw — <motivo>`.
2. Aprovação unânime do Architecture Board + 2/3 Editorial Committee.
3. Migration Plan completo.
4. Version bump MAJOR de todos os componentes afetados.

### 9.5 Próximos sprints pertencem ao domínio clínico

> **A partir deste ADR, todos os próximos sprints pertencem exclusivamente ao domínio clínico ou à implementação.**

Isso significa:

- ❌ Novos componentes de infraestrutura normativa não serão criados sem Foundation Thaw.
- ✅ Novos AS podem ser escritos (usando estrutura existente).
- ✅ Implementações concretas podem ser produzidas.
- ✅ Papers podem ser desenvolvidos.
- ✅ ADRs podem ser emitidos (sobre domínio clínico).
- ❌ Mudanças em AS-000, ASM-001, Maturity Model exigem novo ADR + thaw.

---

## 10. Confirmação de Uso Futuro da Infraestrutura Existente

AS-003, AS-004, AS-005, AS-006 e quaisquer Standards futuros:

### 10.1 Usarão a infraestrutura existente SEM modificá-la

| Componente existente | Como AS-003..006 o usará |
|---|---|
| AS-000 §3 (vocabulário) | Termos canônicos referenciados sem redefinição. |
| ASM-001 §1–§17 (estrutura) | 16 seções canônicas seguidas literalmente. |
| ASM-001 §10 (Requirement ID) | IDs no formato `AS-XXX-REQ-NNNN`. |
| ASM-001 §12 (verbos) | RFC 2119 (SHALL, MUST, SHOULD, MAY). |
| ASM-001 §21 (Maturity) | 9 estados com ordem Published→Verified→Reference Implementation. |
| ASM-001 §22 (Dependency) | Apenas dependências downward. |
| ASM-001 §23 (Traceability) | Cadeia completa até Evidence. |
| Library pipeline | Publicação em `docs/library/standards/` via `render_html.py`. |
| Conformance Suite | Estrutura em `tests/conformance/AS-XXX/`. |

### 10.2 Não modificarão a infraestrutura

- ❌ Não criarão novos Maturity States.
- ❌ Não criarão novos verbos normativos.
- ❌ Não criarão novos formatos de Requirement ID.
- ❌ Não criarão novos formatos de URN.
- ❌ Não modificarão AS-000 sem Foundation Thaw.
- ❌ Não modificarão ASM-001 sem Foundation Thaw.

### 10.3 Estenderão (não modificarão) via adição

- ✅ Novos AS serão adicionados conforme catálogo AS-001..006.
- ✅ Novos Requirements serão adicionados com IDs incrementais.
- ✅ Novos Axiomas serão adicionados (apenas no AS específico, não no AS-000).
- ✅ Novos Paperse ADRs serão emitidos sobre domínio clínico.

---

## 11. Mecanismo de Revisão Deste Próprio ADR

### 11.1 Emendas

Este ADR pode ser emendado via:

1. Novo ADR referenciando `ADR-0006` e propondo mudança específica.
2. Quórum: Architecture Board + 2/3 Editorial Committee (maioria 3/4 combinada).
3. A emenda SHALL ser listada no §11.4 deste ADR.

### 11.2 Revogação

Este ADR pode ser revogado apenas por:

1. ADR explícito declarando revogação.
2. Aprovação unânime do Architecture Board + Editorial Committee.
3. Substituto SHALL ser publicado simultaneamente.

### 11.3 Imutabilidade das decisões aqui

As decisões de §3 (Hierarquia), §4 (Matriz), §9 (Foundation Freeze) são **decisões fundacionais** e SHALL ser revistas apenas com:

- Quórum qualificado de 4/5 do Architecture Board.
- 2/3 do Editorial Committee.
- Constitutional Guardian presente na deliberação.

### 11.4 Histórico de emendas

| Versão | Data | Status | Mudanças |
|---|---|---|---|
| 1.0 | 2026-07-18 | Proposto | Redação inaugural. |

---

## 12. Consequências

### 12.1 Positivas

- **Resolução determinística de conflitos** — matriz clara.
- **Foundation Freeze declarado** — infraestrutura protegida contra mudanças casuais.
- **Papéis formais** — quem decide o quê está claro.
- **Migration Window explícito** — depreciações previsíveis.
- **Confirmação de uso futuro** — Standards futuros não inventarão nova infraestrutura.

### 12.2 Negativas

- **Burocracia adicionada** — toda mudança requer ADR formal.
- **Risco de paralisia** — quóruns altos podem bloquear mudanças legítimas.
- **Foundation Thaw necessário** para qualquer correção estrutural.

### 12.3 Mitigações

- **Quóruns altos** são para **mudanças estruturais**, não para mudanças editoriais.
- **Editorial Committee** é simples maioria para mudanças PATCH/MINOR.
- **Foundation Thaw** existe para emergências.

---

## 13. Alternativas Consideradas

### 13.1 "Sem ADR formal; resolver por conversa"

- **Rejeitado.** Leva a decisões inconsistentes e política por trás.
- Solução proposta: matriz + papéis formais.

### 13.2 "ADR-0006 define papéis mas sem matriz"

- **Rejeitado.** Matriz ausente deixa lacunas.
- Solução proposta: matriz exaustiva (§4).

### 13.3 "Foundation Freeze sem Foundation Thaw"

- **Rejeitado.** Sem thaw, bugs estruturais graves são intratáveis.
- Solução proposta: thaw com quórum qualificado.

### 13.4 "Quórum de unanimidade para tudo"

- **Rejeitado.** Paralisia garantida.
- Solução proposta: maioria simples para PATCH/MINOR, maioria qualificada para MAJOR/Breaking.

---

## 14. Apêndices

### 14.1 Apêndice A — Glossário

| Termo | Significado |
|---|---|
| **Normative** | Que tem força de norma; pode ser citado como autoridade. |
| **Precedence** | Ordem de prioridade quando dois documentos divergem. |
| **Supersession** | Substituição formal de um documento por outro. |
| **Deprecation** | Marcação de um componente como obsoleto mas ainda funcional. |
| **Foundation Freeze** | Congelamento oficial da infraestrutura normativa. |
| **Foundation Thaw** | Descongelamento da infraestrutura via ADR específico. |
| **Migration Window** | Período entre deprecação e archiving. |

### 14.2 Apêndice B — Histórico de mudanças

| Versão | Data | Status | Mudanças |
|---|---|---|---|
| 1.0 | 2026-07-18 | Proposto | Redação inaugural. Define hierarquia 9 níveis, matriz de precedência 30 entradas, resolução de 7 tipos de ambiguidade, política de depreciação, change control SemVer + editorial, governança com 6 papéis, Foundation Freeze com Thaw. |

---

**Fim do ADR-0006.**

> Este ADR encerra **definitivamente** a infraestrutura normativa do AraOS.
> Próximos documentos tratarão apenas do domínio clínico ou da implementação.
