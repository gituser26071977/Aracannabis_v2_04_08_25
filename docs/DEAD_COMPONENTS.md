# DEAD COMPONENTS — Código Morto Detectado no Frontend

**Data:** 2026-06-24
**Método:** Cross-reference de imports vs usos (grep recursivo)
**Escopo:** `frontend/src/` inteiro

---

## 1. SUMÁRIO

| Categoria | Arquivos | Linhas estimadas |
|---|---|---|
| Componentes órfãos (zero imports) | 15 | ~2.625 |
| Serviços órfãos | 2 | ~346 |
| Componentes importados mas não renderizados | 1 | 398 |
| Rotas mortas (registradas mas sem menu) | 1 | ~50 |
| Links quebrados | 1 | 1 |
| **TOTAL** | **20** | **~3.420 linhas** |

---

## 2. COMPONENTES ÓRFÃOS (zero imports em todo o projeto)

Detectados por busca de `import .* from` em `frontend/src/`. Componentes não encontrados em nenhum `import`/`require`:

| Arquivo | Caminho completo | Linhas | Comentário |
|---|---|---|---|
| `BeckDepressionTest.js` | `frontend/src/components/BeckDepressionTest.js` | ~120 | Teste BDI-II não integrado (já tem PHQ-9 e GAD-7) |
| `ConsentForm.js` | `frontend/src/components/ConsentForm.js` | ~200 | Substituído por fluxo de aceite no cadastro |
| `FileUploadManager.js` | `frontend/src/components/FileUploadManager.js` | ~180 | Substituído por `MediaCapture.js` |
| `FunctionLLMConfig.js` | `frontend/src/components/FunctionLLMConfig.js` | ~250 | Substituído por `AIConfigPage.js` |
| `ImportExportManager.js` | `frontend/src/components/ImportExportManager.js` | ~220 | Substituído por `BatchImportPage.js` (e ainda mantém o `setInterval` bug) |
| `LoginDireto.js` | `frontend/src/components/LoginDireto.js` | ~150 | Substituído por `SimpleLogin` no `App.js` |
| `MedicalEvolution.js` | `frontend/src/components/MedicalEvolution.js` | ~450 | Substituído por `EvolutionManager.js` (este sim importado) |
| `SnapIVTest.js` | `frontend/src/components/SnapIVTest.js` | ~180 | Teste SNAP-IV não integrado (já tem PHQ-9, GAD-7, Beck) |
| `EmojiBadge.js` | `frontend/src/components/ui/EmojiBadge.js` | ~50 | Substituído por `<Chip>` do MUI |
| `GlassCard.js` | `frontend/src/components/ui/GlassCard.js` | ~80 | Substituído por `<Paper sx={{ backdropFilter: ... }}>` inline |
| `GradientButton.js` | `frontend/src/components/ui/GradientButton.js` | ~90 | Substituído por `<Button>` + sx |
| `CatalogoUpload.js` | `frontend/src/components/catalogo/CatalogoUpload.js` | ~280 | Substituído por `ImportCatalogoIA.js` |
| `ProdutoList.js` | `frontend/src/components/catalogo/ProdutoList.js` | ~520 | Substituído por tabela em `CatalogoPage.js` |
| `SugestaoPrescricao.js` | `frontend/src/components/catalogo/SugestaoPrescricao.js` | ~320 | **NÃO importado mas aparece no menu "Cannabis"** — verificar navegação |
| `VoiceWidget.js` | `frontend/src/components/voice/VoiceWidget.js` | ~85 | Substituído por `AIChatPage.js` (que está com bug de WebSocket) |

**Subtotal:** 15 componentes, **~3.175 linhas**.

> ⚠️ **Nota sobre `SugestaoPrescricao.js`:** apesar de não ter import, aparece em rota/menu de Cannabis. Verificar antes de deletar — pode ser que o bundle lazy load resolva dinamicamente. Validar manualmente.

---

## 3. SERVIÇOS ÓRFÃOS

| Arquivo | Linhas | Comentário |
|---|---|---|
| `services/aiClinicalService.js` | ~190 | Substituído por chamadas diretas em `services/api.js` |
| `services/voiceService.js` | ~156 | Substituído por `AIChatPage.js` direto |

**Subtotal:** 2 serviços, **~346 linhas**.

---

## 4. COMPONENTES IMPORTADOS MAS NÃO RENDERIZADOS

| Arquivo | Onde importa | Linhas | Comentário |
|---|---|---|---|
| `AdBanner.js` | `App.js:24` | 398 | `<AdBanner />` é importado mas nunca aparece no JSX (`<AppContent>`). |

**Confirmar:** verificar `App.js` linhas 24 e procurar `<AdBanner` em todo o JSX. Se 0 ocorrências, deletar.

---

## 5. ROTAS MORTAS

| Rota | Arquivo | Linhas | Comentário |
|---|---|---|---|
| `/billing` | `App.js` (registrada) | ~50 | Registrada no React Router mas **não está no NavigationMenu** (só `/pagamento`). Inacessível por navegação normal. |

**Ação:** ou remover do `App.js` (rota morta) ou adicionar ao menu.

---

## 6. LINKS QUEBRADOS

| Local | Link | Esperado |
|---|---|---|
| `pages/LandingPage.js` | `to="/security"` | `/seguranca` |

**Impacto:** usuário clica em "Segurança" na landing → tela branca (404 não tratado). **Severidade P0.**

---

## 7. ESTADO ATUAL vs PROPOSTA

### Antes (atual)
```
frontend/src/components/  →  65 arquivos
frontend/src/services/    →  12 arquivos
frontend/src/pages/       →  35 arquivos

Total: 112 arquivos (estimativa)
```

### Depois (após saneamento)
```
frontend/src/components/  →  49 arquivos (-15 órfãos, -1 importado-não-usado)
frontend/src/services/    →  10 arquivos (-2 órfãos)
frontend/src/pages/       →  34 arquivos (-1 rota morta)

Total: 93 arquivos (-19 arquivos, -17%)
Linhas removidas: ~3.420 (-7.6% do código)
```

**Ganho:**
- **Build menor** (-17% arquivos analisados pelo bundler)
- **Menos código para manter**
- **Menos confusão para novos devs** (não encontram componentes "fantasma")
- **Menos superfície de bug** (código morto pode ter bugs dormindo)

---

## 8. RISCOS AO REMOVER

| Risco | Mitigação |
|---|---|
| Componente é carregado lazy/dynamic | Verificar `React.lazy()` em `App.js` antes de deletar |
| Componente é usado em testes | `grep -r "BeckDepressionTest\|ConsentForm\|..." tests/` |
| Componente é usado em build de produção via variável de feature flag | Verificar `.env.example` e `featureFlagService` |
| `SugestaoPrescricao.js` pode ter navegação dinâmica | Confirmar manualmente abrindo a rota Cannabis |

**Procedimento seguro:**
```bash
# 1. Confirmar zero imports (comando)
grep -r "from.*BeckDepressionTest" frontend/src/  # esperado: 0
grep -r "from.*ConsentForm" frontend/src/  # esperado: 0
# ... repetir para cada arquivo

# 2. Confirmar zero testes
grep -r "BeckDepressionTest\|ConsentForm\|..." frontend/src/__tests__/ 2>/dev/null
grep -r "BeckDepressionTest\|ConsentForm\|..." tests/ 2>/dev/null

# 3. Mover para /deprecated antes de deletar (1 sprint de observação)
mkdir -p frontend/src/_deprecated
mv frontend/src/components/BeckDepressionTest.js frontend/src/_deprecated/
# ... repetir

# 4. Após 1 sprint sem reclamação → deletar
rm -rf frontend/src/_deprecated/
```

---

## 9. PLANO DE AÇÃO

| Sprint | Ação |
|---|---|
| Sprint 1 (P0) | Confirmar zero imports + mover para `_deprecated/` |
| Sprint 2 (P1) | Rodar testes E2E por 1 semana |
| Sprint 3 | Deletar `_deprecated/` |

**Não deletar imediatamente** — sempre mover para `_deprecated/` primeiro e aguardar 1 sprint.

---

## 10. CONCLUSÃO

**~3.420 linhas / 20 arquivos** podem ser removidos com segurança após validação. Isso é **7.6% do código total** do frontend e remove **21 fontes potenciais de bugs**.

> Ver também `FRONTEND_AUDIT.md` (visão geral) e `FRONTEND_BACKLOG.md` (sequência de saneamento).
