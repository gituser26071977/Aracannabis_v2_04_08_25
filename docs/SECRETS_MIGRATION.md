# Guia de Migração de Secrets para Produção

## 🚨 PROBLEMA DETECTADO

O arquivo `.env` atual contém **secrets inseguros** que NÃO PODEM ser usados em produção:

```
❌ JWT_SECRET_KEY=super_secret_key_12345  → INSEGURO!
❌ SECRET_KEY=another_super_secret_key_67890  → INSEGURO!
❌ SMTP_PASSWORD=S@iArapath12345S@i  → EXPOSTO!
❌ OPENAI_API_KEY=sk-proj-...  → EXPOSTO!
❌ DEEPSEEK_API_KEY=sk-...  → EXPOSTO!
```

---

## ✅ SOLUÇÃO: Migração Segura em 3 Passos

### Passo 1: Gerar Secrets Seguros

```bash
# 1. Gerar JWT_SECRET_KEY (32+ caracteres)
python3 -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_urlsafe(32))"

# 2. Gerar SECRET_KEY (32+ caracteres)
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))"

# 3. Gerar WEBHOOK_SECRET_KEY (32+ caracteres)
python3 -c "import secrets; print('WEBHOOK_SECRET_KEY=' + secrets.token_urlsafe(32))"
```

**Exemplo de output**:
```
JWT_SECRET_KEY=REDACTED
SECRET_KEY=REDACTED
WEBHOOK_SECRET_KEY=REDACTED
```

### Passo 2: Criar Novo `.env` Seguro

1. **Backup do `.env` atual**:
   ```bash
   cp .env .env.backup
   ```

2. **Criar novo `.env` baseado no `.env.example`**:
   ```bash
   cp .env.example .env
   ```

3. **Editar `.env` e substituir `CHANGE_ME` pelos valores gerados**:
   ```env
   # Segurança
   JWT_SECRET_KEY=<VALOR_GERADO_PASSO_1>
   SECRET_KEY=<VALOR_GERADO_PASSO_1>
   WEBHOOK_SECRET_KEY=<VALOR_GERADO_PASSO_1>
   
   # Email
   SMTP_PASSWORD=<SUA_SENHA_SMTP_REAL>
   
   # LLMs (se necessário)
   OPENAI_API_KEY=<SUA_CHAVE_OPENAI>
   DEEPSEEK_API_KEY=<SUA_CHAVE_DEEPSEEK>
   ```

### Passo 3: Validar Configuração

```bash
# Executar script de validação
python3 scripts/validate_env.py
```

**Output esperado**:
```
✅ Validação PASSOU - Ambiente configurado corretamente
```

---

## 🔒 PRODUÇÃO: Configuração Segura na Hostinger

### Opção A: Variáveis de Ambiente via Painel Hostinger

1. Acesse o painel da Hostinger
2. Vá em **Configurações → Variáveis de Ambiente**
3. Adicione cada variável manualmente:
   - `JWT_SECRET_KEY` = `<valor_gerado>`
   - `SECRET_KEY` = `<valor_gerado>`
   - `WEBHOOK_SECRET_KEY` = `<valor_gerado>`
   - `SMTP_PASSWORD` = `<senha_smtp>`
   - etc.

4. **NÃO subir arquivo `.env` para produção**

### Opção B: Docker Secrets (Recomendado)

1. **Criar arquivo de secrets** (fora do Git):
   ```bash
   # Em /secrets (fora do projeto)
   mkdir -p /secrets
   echo "xK8v2P9mQ4..." > /secrets/jwt_secret_key
   echo "wT5uR7pQ9m..." > /secrets/secret_key
   echo "yU4tR6eW8q..." > /secrets/webhook_secret_key
   echo "senha_smtp" > /secrets/smtp_password
   ```

2. **Atualizar `docker-compose.prod.yml`**:
   ```yaml
   services:
     siap-api:
       secrets:
         - jwt_secret_key
         - secret_key
         - webhook_secret_key
         - smtp_password
       environment:
         JWT_SECRET_KEY_FILE: /run/secrets/jwt_secret_key
         SECRET_KEY_FILE: /run/secrets/secret_key
         WEBHOOK_SECRET_KEY_FILE: /run/secrets/webhook_secret_key
         SMTP_PASSWORD_FILE: /run/secrets/smtp_password
   
   secrets:
     jwt_secret_key:
       file: /secrets/jwt_secret_key
     secret_key:
       file: /secrets/secret_key
     webhook_secret_key:
       file: /secrets/webhook_secret_key
     smtp_password:
       file: /secrets/smtp_password
   ```

3. **Atualizar `config.py` para ler secrets**:
   ```python
   def get_secret(key):
       """Lê secret de arquivo ou env var"""
       file_path = os.environ.get(f"{key}_FILE")
       if file_path and os.path.exists(file_path):
           with open(file_path) as f:
               return f.read().strip()
       return os.environ.get(key)
   
   JWT_SECRET_KEY = get_secret("JWT_SECRET_KEY")
   SECRET_KEY = get_secret("SECRET_KEY")
   ```

---

## 📋 Checklist de Segurança

Antes de fazer deploy em produção:

- [ ] Gerar novos secrets com mínimo de 32 caracteres
- [ ] Substituir `JWT_SECRET_KEY` e `SECRET_KEY` inseguros
- [ ] Gerar e configurar `WEBHOOK_SECRET_KEY`
- [ ] Atualizar senhas de SMTP (sem padrões)
- [ ] Remover chaves de API expostas do `.env`
- [ ] Adicionar `.env` ao `.gitignore` (se ainda não estiver)
- [ ] Validar com `python3 scripts/validate_env.py`
- [ ] Confirmar que `.env` com secrets NÃO está no Git:
  ```bash
  git status # .env NÃO deve aparecer
  ```
- [ ] Configurar variáveis de ambiente no servidor de produção
- [ ] Testar aplicação após migração
- [ ] Revogar chaves antigas de API (se foram expostas)

---

## ⚠️ ATENÇÃO: Chaves Expostas

Se você já commitou o `.env` com secrets no Git:

### 1. Remover do Histórico
```bash
# Instalar git-filter-repo
pip install git-filter-repo

# Remover .env do histórico
git filter-repo --path .env --invert-paths

# Force push (CUIDADO!)
git push origin --force --all
```

### 2. REVOCAR Chaves Expostas

- **OPENAI_API_KEY**: Acessar https://platform.openai.com/api-keys → Revogar chave antiga → Gerar nova
- **DEEPSEEK_API_KEY**: Acessar painel DeepSeek → Revogar chave → Gerar nova
- **JWT_SECRET_KEY**: Gerar novo (irá deslogar todos os usuários - avisar!)
- **SMTP_PASSWORD**: Alterar senha do email no provedor

### 3. Adicionar `.gitignore`

```bash
# Criar/atualizar .gitignore
cat >> .gitignore << 'EOF'

# Secrets e ambiente
.env
.env.local
.env.*.local
.env.production
.env.production.local
*.pem
*.key
/secrets/

EOF
```

---

## 🧪 Testar Ambiente Seguro

1. **Validar configuração**:
   ```bash
   python3 scripts/validate_env.py
   ```

2. **Testar autenticação JWT**:
   ```bash
   curl -X POST http://localhost:5002/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"usuario": "drtest", "senha": "test123"}'
   ```

3. **Testar webhook WhatsApp**:
   ```bash
   curl -X POST http://localhost:5002/api/crew-ai/whatsapp-webhook \
     -H "Content-Type: application/json" \
     -H "X-Webhook-Secret: <SEU_WEBHOOK_SECRET>" \
     -d '{"messages": [{"from": "5511999999999@c.us", "body": "teste", "id": "123"}]}'
   ```

---

## 📚 Referências

- [OWASP Secrets Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_CheatSheet.html)
- [Docker Secrets](https://docs.docker.com/engine/swarm/secrets/)
- [12 Factor App - Config](https://12factor.net/config)
