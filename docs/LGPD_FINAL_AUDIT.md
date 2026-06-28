# LGPD FINAL AUDIT — MISSÃO 17

**Data:** 2026-06-25
**Modo:** EXECUTE (somente leitura)
**Pergunta-chave:** "O sistema atende LGPD operacionalmente?"

---

## 1. Veredito executivo

> **NÃO — em estado atual, o sistema NÃO atende LGPD operacionalmente.**
> Há **6 P0** com risco direto de sanção da ANPD, e o **direito ao esquecimento (art. 18, VI) NÃO está implementado**.

---

## 2. Matriz de conformidade por princípio LGPD

| # | Princípio (Art.) | Status | Evidência |
|---|------------------|--------|-----------|
| 1 | **Finalidade** (art. 6, I) | 🟢 OK | Models têm `finalidade` em alguns lugares |
| 2 | **Necessidade** (art. 6, II) | 🟡 Parcial | Coleta de dados além do necessário (telefone, endereço) |
| 3 | **Transparência** (art. 6, VI) | 🟢 OK | `routes/lgpd.py:82-90` retorna política |
| 4 | **Segurança** (art. 46) | 🔴 **FALHA** | PII em logs, sem criptografia de campos sensíveis |
| 5 | **Prevenção** (art. 46) | 🔴 **FALHA** | P0-01, P0-02 path traversal |
| 6 | **Não discriminação** (art. 6, IX) | 🟢 OK | N/A |
| 7 | **Responsabilização** (art. 50) | 🟡 Parcial | LogAtividade existe, mas incompleto |
| 8 | **Consentimento** (art. 7º, I) | 🟡 Parcial | `routes/lgpd.py:35-80` permite registro, mas não bloqueia ativação sem consent |
| 9 | **Revogação** (art. 8º, §5º) | 🟡 Parcial | Endpoint existe, mas não há `data_revogacao` automática |
| 10 | **Direito ao esquecimento** (art. 18, VI) | 🔴 **FALHA TOTAL** | Sem endpoint de exclusão real; dados ficam órfãos |
| 11 | **Portabilidade** (art. 18, V) | 🟡 Parcial | `routes/import_export.py` exporta CSV/JSON, mas sem formato estruturado padrão |
| 12 | **Retenção** (art. 16) | 🔴 **FALHA** | Sem política de retenção implementada; dados indefinidos |
| 13 | **Anonimização** (art. 12) | 🟡 Parcial | `services/anonymization_service/app/crypto.py` existe; uso esparso |
| 14 | **Auditoria** (art. 37) | 🟡 Parcial | LogAtividade, mas não audit log imutável |
| 15 | **Encarregado (DPO)** | 🟡 Parcial | Email de contato existe mas sem fluxo estruturado |

---

## 3. Achados P0 (Bloqueiam compliance)

### LGPD-01 — Senha em texto puro em logs (CONFIRMADO)

**Arquivo:** `routes/auth.py:86, 103, 117-122`
**Violação:** Art. 46 (segurança e prevenção) + Art. 6, X (cuidado com dados pessoais)
**Evidência:**
```python
print(f"DEBUG LOGIN - Senha sanitizada: '{senha}'", flush=True)
logger.info(f"LOGIN ATTEMPT - Identificador: {identifier}, Senha length: {len(senha)}")
```

### LGPD-02 — Path traversal em download de Laudo (CONFIRMADO)

**Arquivo:** `routes/hc_report.py:37-46`
**Violação:** Art. 46 (prevenção de danos) + Art. 18 (segurança)
**Impacto:** Atacante lê prontuários de outros pacientes (PHI).

### LGPD-03 — `exames/arquivos/<filename>` sem autenticação (CONFIRMADO)

**Arquivo:** `routes/exames.py:277-284`
**Violação:** Art. 46 + Art. 18, I (confirmação de existência de tratamento)
**Impacto:** Qualquer pessoa com URL lê exames de qualquer tenant.

### LGPD-04 — Direito ao esquecimento NÃO implementado

**Arquivo:** `routes/lgpd.py` (inteiro)
**Violação:** Art. 18, VI
**Evidência:** Endpoint `/direitos-titular/<int:paciente_id>` (linha 92) **apenas registra solicitação** — não executa exclusão. Comentário `routes/lgpd.py:126`: `# Aqui seria implementada a lógica para processar a solicitação`.

**Risco:** ANPD pode multar em até 2% do faturamento (art. 52, II) por não atender art. 18.

### LGPD-05 — `data_revogacao` ausente em `models.Paciente` (CONFIRMADO)

**Arquivos:** `RELATORIO_TESTE_CARGA_2026_06.md:3.1` já documentava bug; `routes/lgpd.py:115-120` seta `data_revogacao` mas coluna pode não existir
**Evidência:** `(psycopg2.errors.UndefinedColumn) column pacientes.data_revogacao does not exist`
**Violação:** Art. 8º, §5º (revogação)
**Impacto:** API quebra com 500 ao tentar registrar revogação.

### LGPD-06 — Criptografia de PHI em repouso não verificada

**Arquivo:** Schema do banco não auditado para `pgcrypto`/encryption-at-rest
**Evidência:** `models.py` declara `cpf` como `String`, sem `EncryptedType`
**Violação:** Art. 46 (medidas de segurança)
**Risco:** Dump de banco expõe CPF/diagnósticos em texto claro.

---

## 4. Achados P1

| # | Achado | Art. LGPD | Evidência |
|---|--------|-----------|-----------|
| 7 | Logs contêm `detalhes` com texto livre do usuário em `routes/lgpd.py:120` | Art. 46 | Texto pode incluir nome, CPF |
| 8 | `print()` em `routes/pacientes.py:281` loga `data` com PHI | Art. 46 | Print de payload JSON |
| 9 | Cookie de sessão não `httpOnly` | Art. 46 | `X-CSRF-Token` cookie é JS-acessível |
| 10 | `ALLOWED_ORIGINS` expõe IP interno (192.168.0.104) | Art. 46 | `security_config.py:133-134` |
| 11 | Anonimização só aplicada em `ai_clinical.py`, não em `ai_chat_simples.py` | Art. 12 | PHI vai para LLM sem anonimizar |
| 12 | Retenção indefinida (sem `created_at` purge job) | Art. 16 | Nenhum script de limpeza |

---

## 5. Audit Log: gap analysis

**Esperado (art. 37 + art. 50):**
- Quem acessou PHI, quando, de onde
- Imutável (append-only)
- Retenção de pelo menos 5 anos para prontuários

**Real:**
- `LogAtividade` model existe, com `profissional_id`, `acao`, `detalhes`
- Mas:
  - Sem registro de **IP** de quem acessou
  - Sem registro de **timestamp** preciso (UTC vs local)
  - Sem imutabilidade (rows podem ser `UPDATE`/`DELETE`)
  - Sem retenção explícita
- `routes/lgpd.py:21-26` cria log mas só para `Consulta`, não para **Visualizar** ou **Exportar** prontuário

**Risco:** ANPD pode exigir comprovação de audit log em incidente — atual é insuficiente.

---

## 6. Direito ao esquecimento (art. 18, VI) — gap completo

**O que deveria existir:**
```python
# Pseudocódigo
DELETE /api/paciente/me
  - Solicita confirmação (2FA)
  - Marca paciente.data_exclusao = now()
  - Anonimiza: nome → "PACIENTE_EXCLUIDO_<id>", cpf → NULL, email → NULL
  - Mantém: exames, prescrições (obrigação legal art. 16)
  - Registra log de exclusão
  - Envia confirmação por email
```

**O que existe:**
```python
# routes/lgpd.py:115
log = LogAtividade(...)  # ← só registra intenção
db.session.commit()  # ← nada é excluído
return jsonify({'message': 'Solicitação registrada'})  # ← status: 'em_analise'
```

**Não há prazo de resposta configurado** (art. 18, §5º: "imediatamente" se complica, máx 15 dias).

---

## 7. Respondendo a pergunta 2

> **2. Existe risco real de vazamento entre tenants?**
> **SIM — risco ALTO e IMEDIATO.**
>
> - **P0-09** (`skip_tenant=True` × 4 em `ai_chat_simples.py`): médico de Tenant A acessa prontuário de Tenant B passando `paciente_id` no body.
> - **P0-08** (tenant_lib filtra só SELECT): INSERT/UPDATE/DELETE manual sem `associacao_id` cria registro órfão.
> - **P0-02** (`exames/arquivos/<filename>`): exames de qualquer tenant sem auth.
> - **P0-01** (path traversal em `hc_report/download`): laudos de qualquer tenant.
>
> Cenário de exploit: médico malicioso de Associação A enumera IDs 1-1000 de pacientes de outras Associações via `GET /api/cannabis/...?paciente_id=X` (rota em `routes/cannabis.py:50-86` com `skip_tenant=True` em chamadas internas).

---

## 8. Recomendações (NÃO executadas)

1. **Bloquear produção** até P0 LGPD corrigidos
2. Implementar direito ao esquecimento com 2FA e anonimização real
3. Adicionar `EncryptedType` do `sqlalchemy-utils` para `cpf`, `cns`, `endereco`
4. Audit log imutável com `created_at`, `ip_origem`, `user_agent`, hash chain
5. Política de retenção: exames e prescrições por 20 anos (CFM 1.821/2007), demais 5 anos
6. DPO nomeado com email público + fluxo de resposta a titulares ≤15 dias
