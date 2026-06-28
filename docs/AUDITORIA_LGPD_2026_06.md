# Auditoria de Conformidade LGPD — AraOS SIAP

**Data:** 2026-06-22
**Escopo:** Backend Flask (rotas, models, serviços de anonimização, patient portal)
**Lei:** LGPD — Lei nº 13.709/2018 + Regulamentação ANPD
**Método:** Análise estática + leitura do código de rotas/middleware
**Total de achados:** 28 (8 críticos, 9 altos, 7 médios, 4 baixos)

---

## Sumário Executivo

**Veredito: NÃO CONFORME.** O sistema possui infraestrutura básica (blueprint `routes/lgpd.py`, serviço de anonimização, modelo de consentimento para profissionais), mas **viola 6 dos 10 princípios LGPD** de forma direta, com risco real de autuação da ANPD (multa de até 2% do faturamento ou R$ 50 milhões por infração).

As maiores violações são:
1. **Consentimento do paciente** não é coletado diretamente do titular (art. 8º)
2. **Direitos do titular** (art. 18, IV anonimização e VI eliminação) sem endpoint para o próprio paciente
3. **Política de privacidade** é mock — não há termo real visível
4. **Transferência internacional** para DeepSeek/Zhipu sem DPA documentado
5. **DPO não designado** (obrigatório para controladores que tratam dados sensíveis em escala — art. 41)
6. **Dados sensíveis em texto plano** no DB (sem criptografia em repouso — art. 46)

---

## Conformidade por Princípio

| # | Princípio (art. 6º LGPD) | Status | Notas |
|---|---------------------------|--------|-------|
| 1 | Finalidade | 🟡 Parcial | Finalidades implícitas; sem dicionário formal |
| 2 | Necessidade | 🟠 Não conforme | Campos excessivos, logs com PII |
| 3 | Transparência | 🔴 Não conforme | Sem termo visível ao paciente |
| 4 | Segurança | 🟠 Não conforme | PII em texto plano no DB |
| 5 | Prevenção | 🟠 Parcial | Anonimização só para IA; cripto instável |
| 6 | Consentimento | 🔴 Não conforme | Sem aceite explícito do titular; granular "tudo-ou-nada" |
| 7 | Direitos do titular | 🔴 Não conforme | Faltam endpoints de anonimização, eliminação, revogação pelo paciente |
| 8 | Retenção | 🟠 Parcial | Soft delete só em algumas tabelas; sem job automatizado |
| 9 | Transferência internacional | 🔴 Não conforme | Envio a provedores na China/EUA sem DPA/RIPD; DPO não designado |
| 10 | Registro de operações | 🟠 Parcial | Logs existem mas faltam leitura individual e exports |

---

## Top 10 Ações (ordenadas por risco legal)

| # | Ação | Impacto regulatório | Esforço |
|---|------|---------------------|---------|
| 1 | Publicar termo de consentimento versionado e exigi-lo no `patient_register` (art. 9º) | Multa por coleta sem base legal | 1 sprint |
| 2 | Criar endpoints `/api/patient/me/*` para exercício dos direitos do art. 18 (export, correção, anonimização, eliminação, revogação) | Multa por obstrução de direitos | 2 sprints |
| 3 | Designar DPO e publicar contato (art. 41) | Multa administrativa | 1 dia |
| 4 | Criptografar PII em repouso (CPF, CNS, e-mail, endereço, data_nascimento) com Fernet envelope (art. 46) | Multa por falha de segurança | 2 sprints |
| 5 | Elaborar RIPD (Relatório de Impacto à Proteção de Dados) para tratamento com IA (art. 38) | Obrigatório quando há dados sensíveis + IA | 1 sprint |
| 6 | Documentar DPA/SCC com DeepSeek/Zhipu/Google ou migrar para Ollama local (art. 33-36) | Multa por transferência ilegal | 1 sprint |
| 7 | Substituir hard delete de paciente por soft delete + anonimização progressiva após período legal (CFP/CRM = 20 anos) | Multa por descumprimento de obrigação de retenção setorial | 1 sprint |
| 8 | Tornar consentimento granular por finalidade (consentimento_ia, consentimento_pesquisa, etc.) | Alinhamento ao art. 8º, §2º | 1 sprint |
| 9 | Implementar job mensal de retenção de logs (manter 5 anos; expurgar após) | Art. 37 + art. 16 | 3 dias |
| 10 | Criar endpoint para titular revogar consentimento diretamente (art. 18, IX) | Alinhamento ao art. 18 | 2 dias |

---

## Achados Detalhados

### 🔴 CRÍTICOS (8) — risco direto de autuação

#### C1. Política de privacidade é mock
- **Arquivo:** `routes/lgpd.py:82-90` (`obter_politica_privacidade`)
- **Comportamento:** Retorna apenas `{titulo, ultima_atualizacao, versao, url}` sem texto. URL `/politica-privacidade` não existe no backend.
- **Violação:** Art. 6º, VI (transparência) + art. 9º (informação ao titular).
- **Recomendação:** Hospedar texto integral do termo em rota servida (HTML/Markdown) com versionamento.

#### C2. Auto-cadastro de paciente sem aceite de termo
- **Arquivo:** `routes/patient_auth.py:26-147` (`patient_register`)
- **Comportamento:** Auto-cadastro via CPF não exige aceite de termo de consentimento nem exibe quais dados serão coletados.
- **Violação:** Art. 8º (consentimento) + art. 11º (dados sensíveis sem destaque).
- **Recomendação:** Bloquear ativação da conta até aceite explícito + IP + UA + `politica_versao`.

#### C3. Portal do paciente sem informação sobre coleta
- **Arquivo:** `routes/patient_portal.py` (todo)
- **Comportamento:** Paciente não vê quais dados foram coletados, por quê, nem o termo aceito.
- **Violação:** Art. 6º, VI (transparência).

#### C4. Consentimento do paciente gerenciado APENAS pelo profissional
- **Arquivos:** `models.py:211-215` (campos `consentimento_lgpd`, `data_consentimento`) + `routes/lgpd.py:35-80` (registrar_consentimento)
- **Comportamento:** Somente o profissional registra o consentimento; paciente não consegue aceitar/revogar diretamente.
- **Violação:** Art. 8º + art. 18, IX (revogação).
- **Recomendação:** Criar endpoint `/api/patient/me/consentimento` para o titular.

#### C5. Consentimento não-granular ("tudo ou nada")
- **Arquivo:** `routes/lgpd.py:35-80`
- **Comportamento:** Aceita `data['consentimento']` direto, sem separar finalidades (pesquisa, IA, marketing, comunicação).
- **Violação:** Art. 8º, §2º (consentimento específico e destacado em finalidades específicas).

#### C6. Dados sensíveis sem consentimento específico
- **Arquivos:** `models.py:217-219` (campos `tdah_positivo`, `depressao_positivo`) + `routes/lgpd.py`
- **Comportamento:** Coleta de dados de saúde sem aceite destacado.
- **Violação:** Art. 11º, I (dado sensível de saúde exige consentimento específico).
- **Recomendação:** Exigir aceite explícito para "dados de saúde" antes de salvar.

#### C7. Anonimização (art. 18, IV) sem endpoint para titular
- **Comportamento:** Não existe endpoint para titular solicitar anonimização.
- **Violação:** Art. 18, IV.
- **Recomendação:** Criar `POST /api/patient/me/anonimizar` (bloqueante, idempotente) que anonimiza identificadores e mantém apenas dados clínicos agregados.

#### C8. Eliminação (art. 18, VI) só para profissional
- **Arquivo:** `routes/pacientes.py:548-587` (`excluir_paciente`)
- **Comportamento:** Hard delete só permitido ao profissional responsável. Paciente não pode solicitar exclusão. Conflita com CFP/CRM (manter prontuário 20 anos) — exige regra explícita.
- **Violação:** Art. 18, VI.
- **Recomendação:** Implementar `POST /api/patient/me/solicitar-eliminacao` com workflow: elimina dados não-clínicos; prontuário é anonimizado (mantém base legal art. 16, "exercício regular de direitos em processo").

---

### 🟠 ALTOS (9) — risco significativo

| # | Arquivo:Linha | Descrição | Recomendação |
|---|---------------|-----------|--------------|
| A1 | `models.py:193-197` | CPF, e-mail, telefone, endereço em texto puro | Criptografar com Fernet/AES-256 + envelope encryption |
| A2 | `routes/patient_auth.py:128-129` | Senha e PII na mesma tabela, sem segregação | Tabela `pacientes_auth` separada |
| A3 | `routes/import_export.py:53-137` | Export só para profissional, não para titular | Criar `/api/patient/me/export` |
| A4 | `services/anonymization_service/app/crypto.py:5-17` | Chave ausente em prod gera temporária silenciosa | Abortar startup se chave faltando |
| A5 | `services/anonymization_service/app/anonymizer.py:62-72` | MD5 para token (cripto inadequada) | Trocar para SHA-256 truncado |
| A6 | `services/llm_gateway/app/providers/deepseek.py` | Envio para api.deepseek.com (China) sem SCC | Documentar DPA ou usar Ollama |
| A7 | `routes/pacientes.py:548-587` | Hard delete viola CFP/CRM (20 anos) | Soft delete + anonimização progressiva |
| A8 | `models.py:764-788` | `LogAtividade` sem política de retenção | Job mensal de expurgo após 5 anos |
| A9 | `routes/pacientes.py:281,381` | `print(to_dict())` com CPF, e-mail, endereço → stdout | Remover ou usar logger com mascaramento |

---

### 🟡 MÉDIOS (7)

| Arquivo:Linha | Descrição | Recomendação |
|---------------|-----------|--------------|
| `models.py:191-230` (classe `Paciente`) | Sem dicionário de finalidades por campo | Adicionar docstring/comentário por coluna |
| `models.py:207-210` (`foto_*`) | Foto do paciente (potencial biométrico) sem consentimento específico | Documentar finalidade + consentimento destacado |
| `models.py:217-219` | `tdah_positivo`, `depressao_positiva` (dados sensíveis) sem consentimento específico | Consentimento destacado para saúde |
| `routes/pacientes.py:284-306` | Cadastro coleta 12+ campos sem marcar opcionais | Tornar opcionais; remover duplicidade `diagnostico`/`condicao_medica` |
| `routes/lgpd.py:21-27` | Logs LGPD sem IP nem UA | Adicionar `request.remote_addr` + `request.user_agent.string` |
| `services/anonymization_service/app/main.py:30-43` | Anonimização só para IA — não em logs/exports | Aplicar em todos os caminhos de saída |
| `routes/patient_auth.py:21-24` | Validação só de formato (11 dígitos) | Algoritmo de dígito verificador + mascaramento |

---

### 🟢 BAUXOS (4)

- `docs/ARAOS_ARQUITETURA_ESTRATEGICA.md:772` — DPO listado como "item futuro", não operacionalizado
- `routes/patient_auth.py:175-187` — Sem política de força de senha (Zxcvbn / NIST 800-63B)
- `routes/pacientes.py:748-775` — Foto servida sem `X-Content-Type-Options: nosniff`
- `migrations/versions/83c3e98787e1_*` — `deleted_at` adicionado em profissionais/associações mas NÃO em `Paciente`

---

## Mapeamento Direitos do Titular (art. 18)

| Direito | Endpoint atual? | Endpoint para paciente? | Status |
|---------|-----------------|------------------------|--------|
| I — Confirmação da existência | ✅ `patient_auth.verify-cpf` (público, vaza enumeração) | ✅ | 🟡 |
| II — Acesso aos dados | ✅ `patient_portal` (parcial) | 🟡 falta anamnese/access-log | 🟡 |
| II — Acesso (export) | ✅ profissional (import_export) | ❌ | 🔴 |
| III — Correção | ✅ profissional (PUT robusto) | 🟡 só telefone/endereço | 🟡 |
| IV — Anonimização | ❌ interno IA | ❌ | 🔴 |
| V — Portabilidade | ✅ profissional (JSON/CSV) | ❌ | 🔴 |
| VI — Eliminação | ✅ profissional (hard delete) | ❌ | 🔴 |
| VII — Informação sobre entidades públicas | ❌ | ❌ | 🔴 |
| VIII — Informação sobre possibilidade de não fornecer consentimento | ❌ | ❌ | 🔴 |
| IX — Revogação do consentimento | ✅ profissional (`data_revogacao` mas nunca escrita) | ❌ | 🔴 |

---

## Plano de Adequação em 4 Fases (90 dias)

### Fase 1 (30 dias) — Estancar vazamentos
- C1, C2, C3, C4, C5, C6: termo versionado + aceite obrigatório
- A1: criptografar PII em repouso
- A4, A5: estabilizar crypto
- Designar DPO (3)

### Fase 2 (30 dias) — Direitos do titular
- C7, C8, A3: criar 5 endpoints `/api/patient/me/*`
- A9: remover `print(to_dict())`
- 5: granularidade de consentimento

### Fase 3 (30 dias) — Documentação e governança
- 5: RIPD
- 6: DPA/SCC ou migração para Ollama
- 9: job de retenção de logs
- 7: substituir hard delete por soft delete + workflow

### Fase 4 (contínuo) — Melhoria operacional
- Auditoria trimestral automatizada (pytest + bandit + pip-audit)
- Treinamento da equipe em LGPD
- DPO realiza revisão anual
- Monitoramento contínuo de logs com DLP

---

## Glossário LGPD

- **Titular:** pessoa natural a quem se referem os dados pessoais (no caso, o paciente)
- **Controlador:** pessoa física/jurídica que decide sobre o tratamento (no caso, a clínica)
- **Operador:** pessoa física/jurídica que realiza o tratamento em nome do controlador (ex.: VisualSmartFlow)
- **Encarregado/DPO:** pessoa indicada pelo controlador para atuar como canal de comunicação com a ANPD e titulares
- **Dado pessoal:** informação relacionada a pessoa natural identificada ou identificável
- **Dado pessoal sensível:** dado sobre origem racial, convicção religiosa, opinião política, dado genético, biométrico, dado de saúde, etc.
- **RIPD:** Relatório de Impacto à Proteção de Dados Pessoais (art. 38)
- **SCC:** Standard Contractual Clauses (cláusulas-padrão contratuais para transferência internacional — art. 33, III)

---

**Gerado por:** Claude (MiniMax-M3) · 2026-06-22 · Auditoria read-only
