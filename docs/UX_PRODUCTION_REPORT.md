# UX PRODUCTION REPORT — Perspectiva do Médico (First-Time User)

**Data:** 2026-06-24
**Persona:** Dr(a). Novo(a) — clínico geral, 35-55 anos, pouca fluência digital. Primeiro acesso ao AraOS.
**Método:** Walkthrough mental completo: cadastro → login → dashboard → paciente → consulta → prescrição → encerramento.

---

## 1. JOURNEY MAP — Os primeiros 5 minutos

| Etapa | Tempo | Ação | O que vê | Como se sente |
|---|---|---|---|---|
| 0 | 0:00 | Recebe e-mail de convite | Link `https://aracannabis.../definir-senha?token=abc123...` | Confiante |
| 1 | 0:30 | Abre link | Tela DefinePassword com **token exposto no console.log** | Confuso (F12 mostra token!) |
| 2 | 1:00 | Define senha | Aceita, redireciona | OK |
| 3 | 1:30 | Login | Tela com gradient claro bonito | OK |
| 4 | 2:00 | **Primeiro login falha** | `setMessage('Erro: ' + error.message)` mostra `Network Error` | **Perdido** |
| 5 | 2:30 | Tenta de novo | Login OK, vai para Dashboard | Alívio |
| 6 | 3:00 | Dashboard carrega | `@keyframes fadeInUp` redefinido 2×, ícones que não renderizam | "Hmm, isso parece amador" |
| 7 | 3:30 | Clica em "Pacientes" | Tela com tabs desabilitadas sem motivo | "Por que está desabilitado?" |
| 8 | 4:00 | Clica em "Novo Paciente" | Formulário longo com `Email` (inglês) misturado com `e-mail` | Hesitante |
| 9 | 4:30 | Submete paciente | `alert()` do browser aparece: "Paciente criado!" | **Desconfortável** ("isso é um sistema de verdade?") |
| 10 | 5:00 | Vai para Prescrição | Vê tabs `📝 📊 ⚖️ 🧬 🌿 📋` com emojis misturados com Material Icons | "Mistura esquisita" |

**Diagnóstico:** Em **5 minutos** o médico passou por:
- 1 falha de segurança (`console.log` token)
- 1 erro técnico exposto (`Network Error`)
- 1 mensagem amadora (`alert()`)
- 3 sinais de "MVP não finalizado"

---

## 2. OS 7 ASSASSINOS DE CONFIANÇA (Top of mind)

### 2.1 🚨 ASSASSINO #1 — Vazamento de credencial
**Quando:** define senha
**O que vê:** abre DevTools → vê `console.log` com o token de reset na tela
**Impacto:** Destrói confiança. Médico pensa: "se o sistema vaza meu próprio token, o que mais ele vaza?"
**Severidade:** P0 (segurança + percepção)

### 2.2 🚨 ASSASSINO #2 — `alert()` do browser
**Quando:** salva paciente, importa arquivo, valida produto
**O que vê:** janela cinza do Windows/Mac com `OK` no meio de UI moderna
**Impacto:** Quebra a quarta parede. "Isso é um SaaS ou um sistema da época do Windows 98?"
**Severidade:** P1 (UX)

### 2.3 🚨 ASSASSINO #3 — Texto sem acento
**Quando:** navega em qualquer tela (especialmente Cannabis, Billing, Pagamento)
**O que vê:** `"Condicao Medica Principal"`, `"Nao definido"`, `"Nao foi possivel"`
**Impacto:** Parece sistema feito por IA ou traduzido às pressas. Falta de cuidado.
**Severidade:** P1 (percepção de qualidade)

### 2.4 🚨 ASSASSINO #4 — Loading infinito
**Quando:** API `/planos/` ou `/api/crewai` demora
**O que vê:** spinner que nunca termina (sem timeout) ou tela em branco
**Impacto:** Médico fecha a aba. "Não funciona."
**Severidade:** P0 (UX bloqueante)

### 2.5 🚨 ASSASSINO #5 — Botão "Editar" que não faz nada
**Quando:** clica em Edit no AIDashboard (4 botões)
**O que vê:** nada acontece
**Impacto:** "O sistema está quebrado?"
**Severidade:** P0 (UX bloqueante)

### 2.6 🚨 ASSASSINO #6 — TODO placeholder visível
**Quando:** abre Catálogo
**O que vê:** botão "Novo Produto" que ao clicar mostra `{/* TODO: abrir modal */}`
**Impacto:** "Isso não foi terminado. Posso confiar no resto?"
**Severidade:** P0 (percepção de incompletude)

### 2.7 🚨 ASSASSINO #7 — `"(mock)"` na UI
**Quando:** abre Billing
**O que vê:** coluna `Valor: R$ 99 (mock)` em produção
**Impacto:** "Isso é demo? Estou num ambiente de testes?"
**Severidade:** P0 (percepção crítica em fluxo de pagamento)

---

## 3. TELAS POR APARÊNCIA

### 3.1 🔴 Aparência de MVP (NÃO prontas para produção)

| Tela | Arquivo | Sintomas |
|---|---|---|
| Login | `App.js` | Background hardcoded, sem dark mode, IconButtons sem aria |
| Dashboard | `InternalDashboard.js` | Keyframes duplicados, ícones não renderizam |
| Cannabis | `CatalogoPage.js`, `SugestaoPrescricao.js` | TODO visível, 23 strings sem acento, `JSON.stringify` em UI |
| AI Chat | `AIChatPage.js` | WebSocket hardcoded, cores hardcoded, animações locais |
| AI Dashboard | `AIDashboard.js` | Grid quebrado (`md={2.4}`), 4 botões sem onClick |
| Billing | `BillingPage.js`, `PagamentoPage.js` | "(mock)" visível, faturamento hardcoded R$ 99, PT-BR quebrado |
| Plans | `PlanosPage.js` | Tela vazia se API falha, cor como único indicador |
| Landing | `LandingPage.js` | Dead link `/security`, cores hardcoded, gradient off-theme |

### 3.2 🟡 Aparência intermediária (próximas do pronto, ajustes finos)

| Tela | Arquivo | O que falta |
|---|---|---|
| Pacientes | `PatientList.js`, `PacientesPage.js` | aria-labels, `alt` em Avatar, `overflowX` em mobile |
| Consultas | `CalendarioConsultas.js` | `alert(response.message)` → Snackbar |
| Prontuário | `PatientDetailPage.js` | Hierarquia visual de tabs (emojis vs Icons) |
| Prescrições | `PrescriptionPanel.js` | "Receita" vs "Prescrição" no mesmo arquivo |
| Exames | `ExameManager.js` | Loading state com texto |
| Secretária | `AssociationPage.js` | Breadcrumbs padronizados |
| Módulos | `ModulosPage.js` | Loading skeleton, mensagens de erro polidas |
| LGPD | `SecurityPage.js` | Banner ativo, dados sensíveis |

### 3.3 🟢 Aparência pronta para produção

| Tela | Arquivo | Por que está OK |
|---|---|---|
| Definição de Senha | `DefinePasswordPage.js` | Layout limpo (exceto console.log) |
| Verify Email | `VerifyEmailPage.js` | Simples, funcional |
| Terms | `TermsPage.js` | Texto jurídico, foco em leitura |
| Privacy Policy | `PrivacyPolicy.js` | Idem |
| 404 catch-all | (NÃO EXISTE — precisa criar) | — |

---

## 4. OS 7 ROTEIROS QUE O MÉDICO FAZ E O QUE ENCONTRA

### 4.1 Roteiro "Admitir paciente"
1. Login → OK
2. Dashboard → "irônico: ícones não renderizam, keyframes duplicados"
3. Clica "Pacientes" → tab "Inativos" disabled sem motivo
4. "Novo Paciente" → form com `Email` (inglês)
5. Submit → `alert("Paciente criado!")` ← amador

**Veredicto:** 3/5 passos têm fricção evitável.

### 4.2 Roteiro "Prescrever cannabis"
1. Abre Paciente → Prescrição
2. Vê tabs `📝 📊 ⚖️ 🧬 🌿 📋` (emojis misturados com Icons)
3. Vai para Cannabis → vê `SugestaoPrescricao.js` inteiro sem acento
4. "Consultando Farmaceutico..." ← sem acento
5. Botão "Obter Sugestoes" ← sem acento

**Veredicto:** Toda a vertical Cannabis parece inacabada.

### 4.3 Roteiro "Configurar IA"
1. Vai para Configurações IA
2. AIDashboard mostra `md={2.4}` quebrado em Grid
3. 4 botões "Editar Agente" não fazem nada
4. Tenta salvar agente → JSON.stringify em TextField

**Veredicto:** Tela inteira é placeholder.

### 4.4 Roteiro "Assinar plano"
1. Clica "Planos" → tela carrega
2. Vê 3 cards com cores diferentes (vermelho/azul/verde) como único diferenciador
3. API `/planos/` falha → tela vazia sem retry
4. Botão "Assinar" → se carregando, mostra só spinner

**Veredicto:** Fluxo de monetização parece demo.

### 4.5 Roteiro "Ver billing"
1. Abre Billing → vê `R$ 99 (mock)` em coluna
2. Tenta ver fatura → "Nenhum(a) faturamento gerado" sem ilustração

**Veredicto:** Billing inteiro é placeholder.

### 4.6 Roteiro "Importar pacientes em lote"
1. BatchImportPage → `setInterval` SEM cleanup (memory leak)
2. Upload de arquivo → `alert("Importação iniciada")`
3. Espera progresso → sem feedback claro

**Veredicto:** Ferramenta importante parece hack.

### 4.7 Roteiro "Acessar chat IA"
1. AIChatPage → tenta conectar WebSocket `ws://localhost:8765`
2. Falha silenciosa (ou erro técnico exposto)
3. Payload `message vs mensagem` causa inconsistência

**Veredicto:** Feature inacessível.

---

## 5. OS 5 MOMENTOS "UAU" (POSITIVOS)

Não é só crítica — também há pontos fortes:

1. **ThemeContext.js** — sistema de design bem estruturado com paletas light/dark alinhadas, 11 keyframes globais, 24 sombras customizadas. Bom alicerce.
2. **`autoHideDuration={6000}`** consistente em todos os Snackbars (uniformidade).
3. **Interceptor 401** em `services/api.js:76-85` — limpa localStorage e redireciona corretamente.
4. **Padrão "Nenhum(a) + contexto"** em empty states — textualmente consistente.
5. **CSRF + JWT** bem gerenciados em `services/api.js:13-60`.

---

## 6. MÉTRICAS PERCEBIDAS

| Métrica | Valor percebido |
|---|---|
| Confiança inicial | 6/10 (boa UI no login, mas cai rápido) |
| Confiança após 5 min | 3/10 (vazamentos + alert + TODO) |
| Confiança após 15 min | 4/10 (algumas telas funcionam) |
| Probabilidade de voltar amanhã | 60% (público-alvo pode tolerar; novos usuários não) |
| NPS estimado | -10 a +10 (prejudicado pelos mocks e placeholders) |
| Probabilidade de indicar a colega | 25% |
| Reclamações esperadas/semana | 5-10 ("isso não funciona") |

---

## 7. RECOMENDAÇÕES PRIORITÁRIAS POR PERSONA

### 7.1 Médico (usuário primário)
- **P0:** Remover `console.log` com token, remover `alert()`, consertar WebSocket AI Chat, corrigir 4 botões Edit.
- **P1:** Corrigir PT-BR sem acento (especialmente Cannabis/Billing), criar ErrorBoundary, criar rota 404.

### 7.2 Administrador da clínica
- **P0:** Remover "(mock)" do Billing, remover R$ 99 hardcoded.
- **P1:** Padronizar tabelas, criar Empty States com CTA.

### 7.3 Secretária
- **P0:** Limpar `TODO: Substituir por Selector` em StockPage.
- **P1:** Padronizar Breadcrumbs em fluxos de associação.

### 7.4 Desenvolvedor (manutenção)
- **P1:** Remover código morto (~3.770 linhas em 21 arquivos).
- **P2:** Consolidar keyframes duplicados, padronizar borderRadius.

---

## 8. CONCLUSÃO

O AraOS tem **fundações sólidas** mas a **primeira impressão derruba a confiança** do médico. Em 5 minutos ele encontra 7 sinais de "MVP inacabado".

**Recomendação:** antes de qualquer release público, executar **Onda P0** (ver `FRONTEND_BACKLOG.md`) que elimina os 7 assassinos de confiança. Estimativa: **1 sprint**.

A experiência do médico pode ir de 3/10 para **7/10** com correções focadas em segurança, conteúdo PT-BR e eliminação de placeholders/alert/console.log.
