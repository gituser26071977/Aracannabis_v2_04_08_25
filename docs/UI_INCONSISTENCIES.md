# UI INCONSISTENCIES — Inconsistências de Design System e Conteúdo

**Data:** 2026-06-24
**Escopo:** 4 dimensões — Cores, Tipografia, Espaçamento/Border Radius, Conteúdo (PT-BR / i18n)

---

## 1. CORES

### 1.1 Cores hex hardcoded (fora do `theme.palette`)

#### P0 — Quebra dark mode (30+ ocorrências)

| Local | Hex | Severidade |
|---|---|---|
| `App.js:208,223,254,267,287,289,302,304,308,310,312,313` | `#fff` | P0 |
| `pages/AIChatPage.js:504,656,686,711,733,753` | `#fff` (bolhas de chat) | P0 |
| `components/NavigationMenu.js:179` | `#fff` (header) | P0 |
| `components/AssociationSelector.js:15` | `#fff` | P0 |
| `components/MediaCapture.js:222,258,321,339` | `#fff` | P0 |
| `components/PatientList.js:410` | `#fff` | P0 |
| `components/MedicalEvolution.js:391` | `#fff` | P0 |
| `components/AdBanner.js:250` | `#fff` | P0 |
| `components/FollowupPanel.js:166,180` | `#fff` | P0 |
| `components/DigitalTwinPanel.js:159` | `#fff` | P0 |
| `pages/LandingPage.js:312,421,460,517,748,789,826,843,869` | `#fff` | P0 |
| `pages/PagamentoPage.js:332,360,388` | `#fff` | P0 |
| `pages/CadastroProfissionaisPage.js:573` | `#fff` | P0 |
| `components/PatientDetails.js:410` | `#fff` | P0 |

**Severidade P0:** Estas quebras fazem o dark mode ficar ilegível em TODAS as telas listadas.

#### P1 — Off-theme palette

| Local | Hex | Comentário |
|---|---|---|
| `components/FollowupPanel.js:166,180` | `#667eea`, `#764ba2` | Gradiente roxo fora da paleta "Emerald Cannabis" |
| `pages/patient/PatientLogin.js:117,126,148,151,174,177` | `#81c784`, `#ffcdd2` | Verde/vermelho Material antigo |
| `pages/AIChatPage.js:566` | `#25d366` | Verde WhatsApp (não da paleta) |
| `pages/AIChatPage.js:605,621,627` | `#ffebee` | Rosa claro hardcoded |
| `components/SymptomsChart.js:174` | `#4caf50` | Verde Material 500 |
| `components/EvolutionManager.js:512` | `#4caf50` | Idem |
| `components/EvolutionManager.js:609` | `#2196f3` | Azul Material 500 |
| `pages/InternalDashboard.js:188` | `['#0d7377', '#14a085', '#f5a623', '#e94560', '#2ecc71', '#8884d8']` | Paleta de gráfico não theme-aware |
| `pages/LandingPage.js:406-411` | 6 cores (`#0d7377`, `#f5a623`, `#7B1FA2`, `#c62828`, `#1565c0`, `#2e7d32`) | Cards de especialidade |

#### P1 — Bordas hardcoded

| Local | Hex |
|---|---|
| `components/ImportExportManager.js:383` | `#ddd` |
| `components/SymptomsChart.js:157` | `#ccc` |
| `components/MobileConnectQR.js:145` | `#ddd` |
| `pages/AdminPage.js:580` | `#ccc` |
| `components/AdBanner.js:359` | `#e0e0e0` |
| `components/MedicalEvolution.js:262` | `#e0e8db` |
| `components/ExamChart.js:186` | `#ccc` |
| `components/PrescriptionPanel.js:214,241` | `#e0e0e0`, `#bdbdbd` |
| `components/EvolutionManager.js:512,609` | `#4caf50`, `#2196f3` |
| `pages/AIChatPage.js:494,505,585,621,657,694` | (chat inteiro) |

**Recomendação:** substituir todos por `theme.palette.divider` ou `borderColor: 'divider'`.

#### P2 — Backgrounds hardcoded

| Local | Hex |
|---|---|
| `components/GAD7Test.js:142` | `#fafafa` |
| `pages/AIChatPage.js:495,550,684,695` | `#f5f5f5` |
| `components/MediaCapture.js:258` | `#121212` |
| `pages/patient/PatientLogin.js:64` | `#f5f5f5` |

**Recomendação:** substituir por `bgcolor: 'background.default'` ou `bgcolor: 'action.hover'`.

### 1.2 Cores semânticas (deveriam vir do theme)

| Onde | Deveria ser |
|---|---|
| `pages/PlanosPage.js:242,253,263` (cor do plano) | `theme.palette.primary` etc. |
| `pages/AdminPage.js:498,580` (seleção) | `theme.palette.action.selected` |
| `pages/AIChatPage.js:566` (bolha user) | `theme.palette.primary.main` |

---

## 2. TIPOGRAFIA

### 2.1 `fontSize` hardcoded (P1)

| Local | Valor | Comentário |
|---|---|---|
| `components/PatientList.js:351-357,365,373,378,381` | `'1.1rem'` (11×) | Tabela sobrescreve theme |
| `pages/LandingPage.js:498,515` | `'1.05rem'` | CTAs |
| `components/SymptomsChart.js:140,143,146` | `'0.75rem'` | Texto pré-formatado |
| `components/AssociationSelector.js:45` | `'0.875rem'` | |
| `pages/TrialEndingPage.js:174` | `'1.1rem'` | |
| `pages/MobileUploadPage.js:236` | `'1.1rem'` | |
| `components/NavigationMenu.js:272,417` | `'0.65rem'` | Footer/overlines |
| `components/PatientDetails.js:236,264,292,320` | `'0.85rem'` | Chips |
| `components/PatientList.js:327` | `'1.32rem'` | TextField de busca |
| `components/GAD7Test.js:145` | `'1.2rem'` | Pergunta |

**Recomendação:** theme já define `h1..h6`, `body1`, `body2`, `caption`, `overline`. Usar variantes. Se precisar ajuste fino, criar variantes adicionais no theme em vez de inline.

### 2.2 `fontWeight` inconsistente (P2)

Mistura `'bold'`, `'medium'`, `'normal'`, `400`, `500`, `600`, `700`, `800`.

| Local | Valor atual |
|---|---|
| `pages/PagamentoPage.js:194,234,237` | `'bold'` |
| `pages/PlanosPage.js:138,154,169,176,236,242,253,263` | `'bold'` |
| `pages/TrialEndingPage.js:93` | `800` |
| `pages/TrialEndingPage.js:116,125,134` | `'bold'` |
| `pages/AIDashboard.js:778,867,947,1036` | `'medium'` |
| (theme padrão) | `500` para `subtitle1` etc. |

**Recomendação:** theme define 4 níveis (`light: 300, regular: 400, medium: 500, bold: 700`). Usar sempre string `'medium'`, `'bold'` ou number `500`, `700`.

---

## 3. ESPAÇAMENTO E BORDER RADIUS

### 3.1 Padding em `Paper` (P1)

4 valores diferentes para cards equivalentes:

| Valor | Locais |
|---|---|
| `p: 2` | `FileUploadManager.js:236`, `ProductAIAssistant.js:455`, `ImageViewer.js:263`, `ImportCatalogoIA.js:235`, `CatalogoUpload.js:130,220`, `SugestaoPrescricao.js:290`, `CompartilhamentoPaciente.js:311`, `PagamentoPage.js:426`, `GAD7Test.js:142`, `LoginDireto.js:146` |
| `p: 3` | `AIConfigPage.js:495,651,903,1037`, `ConsentForm.js:47`, `ExameManager.js:378`, `AIDashboard.js:587,648`, `SecurityPage.js:16,58`, `FollowupPanel.js:166,204,259,296,351`, `CombinedChartView.js:47`, `AdBanner.js:175,187` |
| `p: 4` | `DefinePasswordPage.js:51`, `PagamentoPage.js:162`, `VerifyEmailPage.js:45`, `BatchImportPage.js:160`, `ConfiguracaoIAPage.js:98`, `SimpleLogin.js:63` |
| `p: 5` | `TrialEndingPage.js:92`, `patient/PatientLogin.js:103` |

**Recomendação:** padronizar em **3 níveis**:
- `p: 2` para cards compactos (listas, sidebars)
- `p: 3` para cards padrão (dashboards, formulários)
- `p: 4` para telas cheias (login, configurações)

### 3.2 `elevation` em Paper (P1)

5 valores diferentes sem sistema claro:

| Valor | Locais |
|---|---|
| `elevation={0}` | `App.js:255`, `MobileUploadPage.js:182`, `GAD7Test.js:142`, `ExamChart.js:278,289` |
| `elevation={1}` | `AdBanner.js:175,187,313,355`, `LGPDBanner.js:63` |
| `elevation={2}` | `PagamentoPage.js:187,277`, `AIDashboard.js:648,738`, `FollowupPanel.js:166,188,204,259,296,351`, `DigitalTwinPanel.js:159` |
| `elevation={3}` | `AIConfigPage.js:495,651,903,1037`, `DefinePasswordPage.js:51`, `ConsentForm.js:47`, `ExameManager.js:378`, `PagamentoPage.js:162`, `VerifyEmailPage.js:45`, `BatchImportPage.js:160`, `TrialEndingPage.js:92`, `AIDashboard.js:587`, `PacientesPage.js:75`, `SecurityPage.js:16,58`, `CombinedChartView.js:47`, `MedicalEvolution.js:256`, `SimpleLogin.js:63` |
| `elevation={4}` | `ExamChart.js:186` |

**Recomendação:** padronizar em 3 níveis no theme:
```js
elevations: { flat: 0, low: 1, medium: 2, high: 3 }
```

### 3.3 Border radius inconsistente (P1)

Theme define `borderRadius: 12`, mas há 15+ valores diferentes:

| Valor | Locais |
|---|---|
| `'50%'` (círculos) | `App.js:208,223`, `MediaCapture.js:265`, `AIChatPage.js:709,731,751`, `AdminPage.js:498`, `LandingPage.js:310,434,446,746` |
| `'10px'` | `App.js:592,610`, `ThemeContext.js:261,295,716,818,824,869`, `NavigationMenu.js:247` |
| `'12px'` (theme) | `ThemeContext.js:468,517,548,555,699,843,883` |
| `'14px'` | `App.js:338,354,399` (login) |
| `'16px'` | `ThemeContext.js:436,460,639,681,728,855` |
| `'20px'` | `ThemeContext.js:608,667`, `PatientDetails.js:236,264,292,320`, `InternalDashboard.js:51,142` |
| `'22px'` | `AIChatPage.js:683,693` |
| `'24px'` | `App.js:267` (login) |
| Numérico `2/3/4/5/6` | vários |

**Recomendação:** consolidar em escala (`4, 8, 12, 16, 24`) e expor como `theme.shape.borderRadius * N` ou constantes.

### 3.4 Margens em listas de cards (P2)

`mb: 2, mb: 3, mb: 4` varia. Padronizar como `mb: 2` para listas, `mb: 4` entre seções.

---

## 4. CONTEÚDO (PT-BR / i18n)

### 4.1 Acentuação quebrada (P0 — UX bloqueante)

23+ strings sem acento em mensagens críticas (Alert/setError/label):

| Arquivo:Linha | Texto atual | Correto |
|---|---|---|
| `pages/BillingPage.js:57,67` | `'Nao definido'` | `'Não definido'` |
| `pages/PagamentoPage.js:149` | `'Nao foi possivel iniciar o pagamento.'` | `'Não foi possível iniciar o pagamento.'` |
| `pages/PasswordSetupRequestPage.js:20` | `'Nao foi possivel enviar o link.'` | `'Não foi possível enviar o link.'` |
| `pages/DefinePasswordPage.js:31` | `'As senhas nao conferem.'` | `'As senhas não conferem.'` |
| `pages/DefinePasswordPage.js:44` | `'Nao foi possivel definir a senha.'` | `'Não foi possível definir a senha.'` |
| `components/catalogo/SugestaoPrescricao.js:113` | `label="Condicao Medica Principal"` | `label="Condição Médica Principal"` |
| `components/catalogo/SugestaoPrescricao.js:116` | `placeholder="Ansiedade Generalizada, Dor Cronica, Insonia"` | `"Ansiedade Generalizada, Dor Crônica, Insônia"` |
| `components/catalogo/SugestaoPrescricao.js:156` | `... sensiveis aos efeitos psicoativos` | `... sensíveis aos efeitos psicoativos` |
| `components/catalogo/SugestaoPrescricao.js:171` | `label="Preferencia por produtos ricos em CBD"` | `label="Preferência por produtos ricos em CBD"` |
| `components/catalogo/SugestaoPrescricao.js:180,187` | `label="Via de Administracao Preferida"` | `label="Via de Administração Preferida"` |
| `components/catalogo/SugestaoPrescricao.js:189` | `Sem preferencia` | `Sem preferência` |
| `components/catalogo/SugestaoPrescricao.js:208` | `'Consultando Farmaceutico...'` | `'Consultando Farmacêutico...'` |
| `components/catalogo/SugestaoPrescricao.js:220` | `Sugestoes do Agente Farmaceutico` | `Sugestões do Agente Farmacêutico` |
| `components/catalogo/SugestaoPrescricao.js:225` | `Consideracoes Gerais:` | `Considerações Gerais:` |
| `components/catalogo/SugestaoPrescricao.js:248` | `Justificativa Clinica:` | `Justificativa Clínica:` |
| `components/catalogo/SugestaoPrescricao.js:265` | `Precaucoes:` | `Precauções:` |
| `components/catalogo/SugestaoPrescricao.js:267` | `Nenhuma especifica` | `Nenhuma específica` |
| `components/catalogo/SugestaoPrescricao.js:293` | `Recomendacao Farmaceutica` | `Recomendação Farmacêutica` |
| `components/catalogo/SugestaoPrescricao.js:190-193` | `Sublingual (Oleos)`, `Oral (Capsulas)`, `Topica (Cremes)`, `Inalatoria (Vaporizadores)` | `Sublingual (Óleos)`, `Oral (Cápsulas)`, `Tópica (Cremes)`, `Inalatória (Vaporizadores)` |
| `components/PatientDashboard.js:132-133` | `acess ar todo seu histórico` | `acessar todo o seu histórico` (typo + acento) |
| `components/ProductAIAssistant.js:445` | `Confianca: ${confianca}%` | `Confiança: ${confianca}%` |

### 4.2 Termos em inglês em PT-BR (P0 — console.error)

| Local | Texto atual | Correto |
|---|---|---|
| `contexts/AssociationContext.js:49` | `console.error("Failed to fetch user associations", error)` | `console.error("Falha ao buscar associações do usuário", error)` |
| `services/associationService.js:17` | `console.error('Error fetching associations:', error)` | `console.error('Erro ao buscar associações:', error)` |
| `services/associationService.js:29` | `console.error('Error creating association:', error)` | `console.error('Erro ao criar associação:', error)` |

### 4.3 `console.log` em produção (P1)

**209 chamadas totais**. Principais ofensores:

| Local | Conteúdo | Severidade |
|---|---|---|
| `services/api.js:11` | `console.log('API Service configurado com URL:', API_BASE_URL)` | P1 |
| `services/api.js:80` | `console.log('Sessão expirada. Redirecionando para login...')` | P1 |
| `services/api.js:94,99,116-124` (7×) | `console.log/error` com prefixo `AUTH_SERVICE_LOGIN:` | P1 |
| `services/api.js:210,221,224` | `console.log('Enviando dados para API:', paciente)`, `'Resposta da API:'`, `'Erro completo da API:'` | P1 |
| `components/LoginDireto.js:21,28,38,41,56,60` | `console.log('LOGIN_DIRETO:...')` (6×) | P1 |
| `components/LoginDireto.js:78,84` | `console.error('LOGIN_DIRETO:...')` (2×) | P1 |
| `pages/DefinePasswordPage.js:22` | `console.log('DEFINE_PASSWORD: Token:', token, 'UserId:', userId)` | **P0** (vaza PII) |
| `pages/AdminPage.js:763` | `console.log('No subscription found')` | P1 |
| `components/PatientForm.js:95,116,120,124,134` (5×) | console.log em submit | P1 |
| `components/SymptomsManager.js:193,297` | `console.log('Nenhum teste PHQ-9...')`, `'Teste GAD-7 salvo!'` | P1 |
| `components/SymptomsChart.js:27,31,36,40,48,62,84` (7×) | console.log com emojis 🔍 📊 ✅ 🏷️ 🎯 📈 🔄 | P1 |
| `components/DosageLineChart.js:37,40,74` (3×) | console.log | P1 |
| `components/EnhancedCombinedChart.js:43,73` (2×) | console.log | P1 |
| `components/PHQ9Test.js:95` | `console.log('Evolução criada automaticamente...')` | P1 |
| `components/SnapIVTest.js:110` | `console.log('Evolução criada automaticamente para SNAP-IV')` | P1 |
| `components/AdBanner.js:130` | `console.log('Anúncio clicado:', ad.title)` | P1 |

### 4.4 `alert()` em produção (P1)

**23 ocorrências**. Substituir por Snackbar/Alert do MUI.

| Arquivo:Linha | Contexto |
|---|---|
| `pages/AdminPage.js:247,261,455,630,785` | Diversos fluxos admin |
| `pages/MobileUploadPage.js:83,97,113` | Upload mobile |
| `components/EvolutionManager.js:217,266` | Evolução clínica |
| `components/SymptomsManager.js:627,629` | Sintomas |
| `components/ImportExportManager.js:86,99` | Import/export |
| `components/ProductForm.js:40` | Formulário produto |
| `components/CalendarioConsultas.js:191` | **Exibe `response.message` cru do backend** (risco de P0) |
| `components/catalogo/ProdutoList.js:141,143,162,169,177` | Catálogo |
| `pages/patient/PatientRegister.js:71,116` | **Cadastro de paciente (crítico)** |

### 4.5 `JSON.stringify` em UI (P1)

| Local | Problema |
|---|---|
| `services/api.js:119` | `throw new Error(JSON.stringify(error.response.data))` — vaza estrutura |
| `components/SymptomsChart.js:147` | `Dados brutos: {JSON.stringify(sintomasData, null, 2)}` em dev |
| `components/catalogo/ProdutoList.js:516` | `<pre>{JSON.stringify(dialogComparacao.comparacao_tecnica)}</pre>` |
| `components/catalogo/CatalogoUpload.js:225` | `{JSON.stringify(result.detalhes)}` |
| `components/ProductAIAssistant.js:458` | `{JSON.stringify(resultado.produto_sugerido)}` |
| `components/intelligentImport/IntelligentImporter.jsx:378` | `{JSON.stringify(...)}` em UI |
| `pages/AIDashboard.js:1557` | `<TextField value={JSON.stringify(...)} />` |

### 4.6 `error.message` exposto cru (P1)

| Local | Contexto |
|---|---|
| `components/SymptomsChart.js:72` | `setError(\`Erro: ${err.message}\`)` |
| `components/catalogo/ProdutoList.js:143,177` | `alert('Erro: ' + err.message)` |
| `components/LoginDireto.js:85` | `setMessage(\`❌ Erro: ${error.message}\`)` |
| `components/SimpleLogin.js:56` | `setMessage('Erro: ' + error.message)` |
| `pages/AIChatPage.js:240` | `'Erro ao iniciar: ' + err.message` |
| `pages/ModulosPage.js:99,136,149,165` | `err.message || 'Erro...'` |

### 4.7 Emojis em labels (P2 — inconsistência visual)

**133 ocorrências**. Material-UI Icons deveriam substituir.

| Local | Emoji |
|---|---|
| `App.js:329,344` | 👤 🔒 (label de login) |
| `pages/PatientDetailPage.js:196-205` | 📝 📊 ⚖️ 🧬 🌿 📋 (tabs) |
| `components/DosageManager.js:299,300` | 📦 📄 (tabs) |
| `components/intelligentImport/IntelligentImporter.jsx:296-298` | ✅ ❌ 🛈 (tabs) |
| `pages/InternalDashboard.js:225-366` | 📊 👥 💊 📈 🏥 💡 📈 🎯 (stat cards) |
| `pages/PagamentoPage.js:190,256,280,428` | 📋 ✅ 💳 📋 |
| `pages/AIConfigPage.js:479,1006` | 🤖 💡 |
| `pages/PlanosPage.js:139` | 💰 |
| `pages/ConsultasPage.js:10` | 📅 |
| `pages/CatalogoPage.js:95,207` | 📦 📝 |
| `pages/TrialEndingPage.js:109,160,194` | 📊 🚀 💬 |
| `components/AdBanner.js:292` | 💡 |
| `components/LockedFeatureAlert.jsx:77` | 🔒 |
| `components/SymptomsManager.js:504,677` | 📊 📋 ✍️ |
| `pages/AIChatPage.js:25,38,47,221` | 📄 💡 📊 📞 |

### 4.8 Inconsistências terminológicas (P2)

| Termo | Onde aparece | Recomendação |
|---|---|---|
| **Excluir** vs **Remover** | Excluir: entidades; Remover: itens voláteis | Padronizar com glossário |
| **Salvar** (singular) vs **Salvar Configurações** (plural) | `AdminPage.js`, `ConfiguracaoIAPage.js` | Sempre `Salvar` (1 palavra) |
| **Email** (inglês) vs **e-mail** (PT) | `PatientLogin.js`, `ConfiguracaoPrescricaoPage.js` | Padronizar **E-mail** |
| **Prescrição** vs **Receita** | mesmo arquivo `PrescriptionPanel.js:169,192` | **Prescrição** sempre |
| **Anamnese** vs **Coletada via LIA** | `PatientDetailPage.js`, `AnamneseViewer.js` | **Anamnese (LIA)** ou **Anamnese (Manual)** |
| **Paciente** vs **Membro** vs **Usuário** | contextos diferentes | OK (paciente=clínico, membro=associação, usuário=login) |

### 4.9 Capitalização em Chip (P2)

| Local | Atual | Recomendado |
|---|---|---|
| `components/SnapIVTest.js:209-212` | `"PREDOMINANTEMENTE DESATENTA"` no meio de frase | `"predominantemente desatenta"` |
| `pages/PlanosPage.js:228` | `label="MAIS POPULAR"` | `label="Popular"` (consistente com AdminPage.js:506) |

---

## 5. ANIMAÇÕES DUPLICADAS (P1)

**Keyframes redefinidos em cada componente** (CSS bloated):

| Keyframe | Onde duplicado |
|---|---|
| `fadeInUp` | `App.js:136-140`, `pages/InternalDashboard.js:58-62,148-152`, `ThemeContext.js:173-176` (global) |
| `scaleIn` | `App.js:273-276`, `ThemeContext.js:189-192` |
| `shake` | `App.js:316-320`, `ThemeContext.js:220-224` |
| `pulse` / `pulseLive` | `pages/AIChatPage.js:529-535,713-714`, `components/ProductAIAssistant.js:376` (rota Pulse não existe em ThemeContext) |

**Durações inconsistentes:** `0.2s ease`, `0.25s`, `0.3s cubic-bezier`, `0.4s`, `0.5s`, `0.6s`, `1.5s infinite` — 7 durações diferentes.

**Recomendação:** usar SOMENTE as globais do `ThemeContext.js` (11 keyframes já definidos). Padronizar duração em 3 níveis (`fast: 200ms`, `base: 300ms`, `slow: 500ms`).

---

## 6. BREADCRUMBS (P1)

Apenas **3 telas** usam `<Breadcrumbs>`:
- `pages/association/DispensationPage.js:78-86`
- `pages/association/MembersPage.js:81-86`
- `pages/association/StockPage.js:81-89`

**Faltando em fluxos >2 níveis:**
- `PacientesPage` → `PatientDetailPage` → `PatientEditPage`
- `ConfiguracaoIAPage`, `AIConfigPage`, `AIDashboard`
- `AdminPage` (5 tabs sem contexto)
- `MedicalEvolution`, `PrescriptionPanel`, `ExamManager`

**Recomendação:** criar componente `<PageBreadcrumbs trail={[...]} />` reutilizável e aplicar em todas as rotas.

---

## 7. EMPTY STATES (P2)

**Texto é consistente** ("Nenhum(a) + contexto"), mas:
- **Todos usam só `<Alert>` estático** — sem ilustração/ícone grande
- **Maioria sem CTA** (Call-to-Action)

**Recomendação:** criar componente `<EmptyState icon={} title={} description={} action={} />`.

---

## 8. PRIORIZAÇÃO DE SANEAMENTO

| Onda | Foco | Esforço |
|---|---|---|
| **P0** | Acentuação quebrada + token vazado + alert/JSON exposto | 1 sprint |
| **P1** | Cores hardcoded + animações duplicadas + borderRadius + breadcrumbs | 2 sprints |
| **P2** | Emojis → Icons + Empty States + terminologia | 2 sprints |

> Ver `FRONTEND_BACKLOG.md` para sequência exata.
