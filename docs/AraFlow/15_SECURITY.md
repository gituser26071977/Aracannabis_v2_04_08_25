# AraFlow — Segurança e LGPD

> **Versão:** 0.1.0
> **Data:** 2026-06-24
> **Owner:** DPO + Security Lead
>
> O AraFlow lida com **dados sensíveis de saúde** e, por isso, precisa de um programa de segurança robusto desde o MVP. Este documento cobre segurança técnica, privacidade, LGPD/GDPR, gestão de incidentes e controles de acesso.

---

## Sumário

1. Princípios
2. Classificação de dados
3. Controles de acesso (autenticação/autorização)
4. Criptografia
5. Segurança em redes
6. Segurança em aplicações
7. Segurança em infraestrutura
8. Privacidade por padrão
9. LGPD — direitos do titular
10. LGPD — bases legais
11. LGPD — operações de tratamento
12. Consentimento
13. Retenção e exclusão
14. Auditoria
15. Gestão de incidentes
16. Gestão de fornecedores
17. Programa de segurança
18. Threat modeling
19. Testes de segurança
20. Conformidade regulatória

---

## 1. Princípios

1. **Privacy by design.** Privacidade desde a concepção.
2. **Defense in depth.** Múltiplas camadas de proteção.
3. **Least privilege.** Mínimo acesso necessário.
4. **Zero trust.** Nunca confiar por padrão.
5. **Auditabilidade.** Tudo logado e imutável.
6. **Transparência.** Usuário sabe o que acontece com seus dados.
7. **Safety by design.** Segurança clínica é tão importante quanto segurança técnica.

---

## 2. Classificação de dados

| Categoria | Sensibilidade | Exemplos |
|-----------|---------------|----------|
| **Pessoal identificável** | Alta | Nome, e-mail, telefone |
| **Saúde (clínico)** | Muito alta | Escalas, sessões, prescrições |
| **Comportamental** | Média | Padrões de uso, preferências |
| **Técnico** | Baixa | Logs, telemetria |
| **Público** | Nenhuma | Conteúdo da biblioteca |

> Dados clínicos são tratados como **dados sensíveis pela LGPD** (art. 5º, II).

---

## 3. Controles de acesso

### 3.1 Autenticação
- SSO via AraOS.
- MFA recomendado (TOTP, WebAuthn).
- Sessões: curta duração; refresh token rotativo.
- Bloqueio após 5 tentativas erradas.

### 3.2 Autorização (RBAC)

| Papel | Recursos |
|-------|----------|
| **Paciente** | Próprios dados apenas |
| **Profissional** | Pacientes com vínculo ativo |
| **Admin (limitado)** | Apenas dados não clínicos (anonimizados) |
| **Sistema** | Apenas o necessário para tarefas específicas |

### 3.3 Autorização contextual

- Profissional só vê pacientes com vínculo ativo.
- Mesmo profissional, vínculo encerrado: sem acesso.
- Logs de qualquer acesso a dados clínicos.

---

## 4. Criptografia

### 4.1 Em repouso

| Dado | Algoritmo |
|------|-----------|
| Banco de dados | AES-256 (transparent encryption) |
| Backups | AES-256 |
| Arquivos (audio, anexos) | AES-256 (S3 SSE) |
| Campos sensíveis específicos | AES-256 application-level |

### 4.2 Em trânsito

| Canal | Protocolo |
|-------|-----------|
| Cliente ↔ API | TLS 1.3 |
| API ↔ banco | TLS 1.3 |
| Interna (VPC) | mTLS (Fase 3) |

### 4.3 Chaves

- KMS gerenciado (AWS KMS / GCP KMS).
- Rotação anual.
- Separação por ambiente.
- Sem chaves em código ou env vars.

---

## 5. Segurança em redes

| Controle | Aplicação |
|----------|-----------|
| **WAF** | OWASP Top 10 + rate limit |
| **DDoS protection** | Cloudflare / AWS Shield |
| **VPC privada** | Banco sem IP público |
| **Security groups** | Mínimo necessário |
| **mTLS interno** | Serviços se autenticam mutuamente |
| **IP allowlist (admin)** | IPs conhecidos |

---

## 6. Segurança em aplicações

### 6.1 OWASP Top 10 — mitigações

| Risco | Mitigação |
|-------|-----------|
| Injection | ORM/queries parametrizadas; validação rigorosa |
| Broken auth | SSO + MFA + rotação de token |
| Sensitive data exposure | Criptografia + minimização |
| XXE | Parsers seguros (configurações restritivas) |
| Broken access control | RBAC + ABAC + testes |
| Security misconfig | Hardening + scanning contínuo |
| XSS | Sanitização; CSP; frameworks seguros |
| Insecure deserialization | Validação rigorosa |
| Vulnerable components | SBOM + SCA em CI |
| Insufficient logging | Logging central + alertas |

### 6.2 Validação de entrada

- Toda entrada validada (schema).
- Rejeitar entrada malformada (400).
- Logs de tentativas suspeitas.

### 6.3 Headers de segurança

```
Strict-Transport-Security: max-age=31536000; includeSubDomains
Content-Security-Policy: default-src 'self'; ...
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: microphone=(), camera=()
```

### 6.4 Sessões

- Tokens curtos (15 min para ações sensíveis).
- Refresh tokens rotativos.
- Revogação central.
- Logout invalida refresh.

---

## 7. Segurança em infraestrutura

### 7.1 Servidores

- Hardening CIS Benchmark.
- Patch mensal.
- SSH só por chave.
- Sem login root.

### 7.2 Containers

- Imagens base mínimas (Alpine, distroless).
- Scan de vulnerabilidades em CI.
- Sem segredos em imagens.
- Read-only filesystem.

### 7.3 CI/CD

- Pipeline auditado.
- Segredos em vault.
- Assinatura de imagens (cosign).
- Deploy apenas via CI.

### 7.4 Monitoramento

- Logs centralizados (CloudWatch / Stackdriver).
- Detecção de anomalia.
- Alertas em tempo real.
- Retenção de logs de segurança: 12 meses.

---

## 8. Privacidade por padrão

| Configuração | Padrão |
|--------------|--------|
| Telemetria | Opt-in |
| Compartilhamento com profissional | Opt-in |
| Pesquisa clínica | Opt-in |
| Cookies não essenciais | Não usar |
| Localização | Coletar apenas se opt-in |
| Notificações | Apenas se opt-in |

### 8.1 Minimização

- Coletar apenas o necessário.
- Revisar periodicamente.
- Remover dados não usados.

### 8.2 Privacy by design checklist

- [ ] Consentimento explícito
- [ ] Finalidade documentada
- [ ] Retenção definida
- [ ] Acesso restrito
- [ ] Logs auditáveis
- [ ] Exportação fácil
- [ ] Exclusão fácil

---

## 9. LGPD — direitos do titular

O AraFlow implementa **todos** os direitos do art. 18 da LGPD:

| Direito | Implementação |
|---------|---------------|
| **Confirmação** | Verificação de existência de tratamento |
| **Acesso** | Tela "Seus dados" + exportação |
| **Correção** | Edição de perfil + suporte |
| **Anonimização** | Opção de anonimização (sem excluir conta) |
| **Portabilidade** | Exportação JSON/PDF |
| **Eliminação** | Direito ao esquecimento |
| **Informação** | Política de privacidade clara |
| **Revogação de consentimento** | Toggle em consentimentos |
| **Revisão de decisão automatizada** | Explicabilidade de IA |

---

## 10. LGPD — bases legais

| Tratamento | Base legal |
|------------|-----------|
| Cadastro e autenticação | Execução de contrato |
| Sessões prescritas | Execução de contrato + tutela da saúde |
| Telemetria técnica | Legítimo interesse |
| Analytics de produto | Consentimento |
| Pesquisa clínica | Consentimento específico |
| Marketing | Consentimento |

> Todas documentadas no **RIPD** (Relatório de Impacto à Proteção de Dados).

---

## 11. LGPD — operações de tratamento

| Operação | Finalidade | Dados | Retenção |
|----------|-----------|-------|----------|
| Cadastro | Identificação | Nome, e-mail | Enquanto conta ativa + 60m após exclusão (logs) |
| Sessão | Tratamento clínico | Protocolo, duração, escores | 24 meses |
| Escala clínica | Avaliação | Respostas, escore | Enquanto conta ativa + 60m anonimizado |
| Telemetria | Melhoria do produto | Eventos de uso | 6 meses |
| Auditoria | Segurança e regulação | Logs | 60 meses |

---

## 12. Consentimento

### 12.1 Fluxo

```
Apresentação clara
  ↓
Linguagem acessível
  ↓
Opt-in por categoria
  ↓
Registro com timestamp
  ↓
Possibilidade de revogação
```

### 12.2 Granularidade

| Categoria | Opt-in |
|-----------|--------|
| Termos de uso | Obrigatório |
| Política de privacidade | Obrigatório |
| Uso clínico | Obrigatório (se usar prescrição) |
| Compartilhamento com profissional | Opt-in |
| Analytics de uso | Opt-in |
| Pesquisa clínica | Opt-in |

### 12.3 Registro

Todo consentimento gera `consent_log` com:
- Versão do termo.
- Texto completo exibido.
- Timestamp.
- Origem (onboarding, settings, invite).

---

## 13. Retenção e exclusão

### 13.1 Retenção

- Vide `13_DATABASE_MODEL.md` § 11.
- Política revisada anualmente.

### 13.2 Exclusão

1. Usuário solicita exclusão.
2. Período de carência: **60 dias** (reversível).
3. Após 60 dias: exclusão definitiva.
4. Dados pseudonimizados em logs regulatórios podem permanecer.

### 13.3 Anonimização

- Para dados de pesquisa, anonimização irreversível.
- Sem possibilidade de reversão.

---

## 14. Auditoria

### 14.1 Logs auditáveis

Toda ação sobre dado clínico gera `audit_log`:
- Quem acessou.
- Quando.
- O que fez.
- IP, dispositivo.

### 14.2 Imutabilidade

- `audit_log` é append-only.
- Storage separado (WORM) se necessário.
- Retenção: 60 meses.

### 14.3 Acesso aos logs

- Apenas DPO e segurança.
- Logs de leitura dos próprios logs (meta).

---

## 15. Gestão de incidentes

### 15.1 Classificação

| Severidade | Definição | SLA resposta |
|-----------|-----------|--------------|
| **P0** | Vazamento de dados clínicos | 1h |
| **P1** | Indisponibilidade > 30 min | 2h |
| **P2** | Bug crítico | 24h |
| **P3** | Bug menor | 7 dias |

### 15.2 Processo

1. Detecção (monitoramento + reporte).
2. Triagem.
3. Contenção.
4. Erradicação.
5. Recuperação.
6. Pós-mortem.
7. Comunicação (ANPD + titulares, se aplicável).

### 15.3 Comunicação à ANPD

- Vazamento que cause risco: comunicação em **2 dias úteis** (LGPD art. 48).
- Titulares afetados: comunicação imediata.

### 15.4 Plano de resposta

- Runbooks atualizados.
- Treinamento trimestral.
- Tabletop exercises semestrais.

---

## 16. Gestão de fornecedores

| Fornecedor | Dados compartilhados | Avaliação |
|-----------|----------------------|----------|
| Hospedagem | Todos | ISO 27001 + DPA |
| Analytics | Eventos anonimizados | DPA + privacy review |
| IA | Texto opt-in | Privacy review |
| Música | Nada | — |
| Wearables | Biofeedback opt-in | DPA + privacy review |

> Todos com **DPA** (Data Processing Agreement) assinado.

---

## 17. Programa de segurança

### 17.1 Estrutura

- **DPO** (encarregado de dados).
- **Security Lead**.
- **Compliance Lead**.
- **Engenharia** (todos com treinamento).

### 17.2 Treinamento

- Onboarding: LGPD + segurança.
- Anual: reciclagem.
- Simulados: phishing, social engineering.

### 17.3 Revisões

- Código: PR com 1+ reviewer; lint de segurança.
- Trimestral: threat model review.
- Anual: auditoria externa.

---

## 18. Threat modeling

### 18.1 Metodologia
- **STRIDE** por feature nova.
- Atualização a cada sprint relevante.
- Revisão por security lead.

### 18.2 Ameaças principais

| Ameaça | Mitigação |
|--------|-----------|
| Account takeover | MFA + detecção de anomalia |
| Data exfiltration | DLP + rate limit + alertas |
| Insider threat | Least privilege + audit |
| Vulnerabilidade em dependência | SCA + patch rápido |
| Phishing ao paciente | Educação + 2FA obrigatório |
| Vazamento de banco | Encryption + segmentação |

---

## 19. Testes de segurança

### 19.1 Tipos

| Tipo | Frequência |
|------|-----------|
| **SAST** | Toda PR |
| **DAST** | Semanal |
| **SCA** | Diária |
| **Pen test** | Anual + após mudanças grandes |
| **Bug bounty** | Fase 3 |

### 19.2 Cobertura mínima

- Toda feature nova: testes de segurança.
- Toda API: testes de autorização.
- Toda tela: validação de entrada/saída.

---

## 20. Conformidade regulatória

### 20.1 LGPD

- 100% conformidade desde MVP.
- RIPD atualizado anualmente.
- DPO nomeado e contatável.

### 20.2 GDPR (Fase 3, expansão UE)

- Compatibilidade desde o design (princípios similares).
- DPO europeu (se aplicável).

### 20.3 ANVISA

- MVP: classificar como **software de bem-estar** (wellness device).
- Fase 2-3: avaliar enquadramento como **software como dispositivo médico (SaMD)**.
- Revisão jurídica contínua.

### 20.4 Outras

- HIPAA-like practices (mesmo sem escopo EUA).
- Resolução CFM 2.314/2022 (telemedicina) — referência, mesmo AraFlow não sendo telemedicina.

---

## 21. Controles operacionais (resumo)

| Categoria | Controle |
|-----------|----------|
| **Identidade** | SSO + MFA |
| **Acesso** | RBAC + ABAC |
| **Dados** | Criptografia em repouso e trânsito |
| **Rede** | WAF + DDoS + VPC privada |
| **Aplicação** | OWASP + SAST/DAST |
| **Infraestrutura** | Hardening + scanning |
| **Monitoramento** | Logs + alertas 24/7 |
| **Resposta** | Runbooks + plano + simulados |
| **Privacidade** | Privacy by design + LGPD |
| **Compliance** | RIPD + DPA + auditoria |

---

*Segurança é um processo, não um produto. Cuide sempre.*