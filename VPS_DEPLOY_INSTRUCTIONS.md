# Instruções de Deploy no VPS

> Arquivo gerado automaticamente em 2026-06-06
> **Atenção:** Leia TUDO antes de executar no VPS

---

## 🎯 O que foi feito no GitHub

O repositório `main` foi atualizado com:

1. **Sincronização completa** com a versão que já estava no VPS (origin/main)
2. **Seus 2 commits locais** foram integrados:
   - `fix(symptoms)`: Prevenção de crash no Chart.js
   - `feat(chat)`: Scroll automático suave com behavior smooth
3. **Limpeza de segurança**: Removidos 456 arquivos sensíveis do tracking
4. **`.gitignore` atualizado** para proteger credenciais e dados de pacientes

---

## 🚀 Comandos para atualizar o VPS

Conecte-se ao VPS via SSH e execute:

```bash
# 1. Entrar na pasta do projeto
cd ~/Aracannabis_v2_04_08_25   # ou onde o repo está clonado no VPS

# 2. Fazer backup do .env.production atual
cp .env.production .env.production.backup.$(date +%Y%m%d_%H%M%S)

# 3. Atualizar o código do GitHub
git pull origin main

# 4. Reconstruir e reiniciar os containers
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d --build

# 5. Verificar se subiu corretamente
docker-compose -f docker-compose.prod.yml ps
docker-compose -f docker-compose.prod.yml logs -f siap-backend --tail 50
```

---

## ⚠️ IMPORTANTE — Ações no VPS antes do deploy

### 1. Verificar se o `.env.production` NÃO será sobrescrito

O `git pull` pode tentar sobrescrever o `.env.production`. Se isso acontecer:

```bash
# Restaurar o backup do .env.production
git checkout --theirs .env.production   # mantém o do VPS
git reset HEAD .env.production
```

### 2. Se você usa Docker volumes para uploads

Os uploads de exames/pacientes estão em volumes Docker, então NÃO serão perdidos.

### 3. Health check pós-deploy

```bash
# Testar a API
curl -s https://api.aracannabis.com.br/api/status | head -c 200

# Ou se acessar direto no VPS:
curl -s http://localhost:5002/api/status | head -c 200
```

---

## 🔴 URGENTE — Segurança

### Credenciais Google expostas no histórico do Git

Os seguintes arquivos já foram commitados no passado e ainda estão no histórico:

- `REDACTED.apps.googleusercontent.com.json`
- `sgac-490811-4713234e6387.json`

**Você DEVE revogar essas credenciais no Google Cloud Console AGORA:**

1. Acesse: https://console.cloud.google.com/apis/credentials
2. Encontre o OAuth 2.0 Client ID `497371060852-...`
3. Clique em "DELETE" ou "RESET SECRET"
4. Para o Service Account `sgac-490811...`:
   - Vá para IAM & Admin > Service Accounts
   - Delete a chave JSON antiga
   - Crie uma nova chave
   - Atualize o `GOOGLE_APPLICATION_CREDENTIALS` no VPS

---

## 📁 Branches de backup criadas

Caso precise voltar atrás, existem 2 branches locais com backup:

| Branch | Conteúdo |
|--------|----------|
| `backup/local-commits-antes-do-sync` | Seus 2 commits originais |
| `backup/REDACTED` | TODA a working tree bagunçada |

---

## 🔄 Fluxo de trabalho recomendado daqui pra frente

```
LOCAL (desenvolvimento/testes)  →  GITHUB (push)  →  VPS (pull + docker restart)
```

### Regras:
1. **Nunca** commite arquivos `.env`, credenciais ou dados de pacientes
2. Sempre teste localmente antes de fazer push
3. No VPS, sempre faça `git pull` dentro da pasta do projeto
4. Sempre reinicie os containers após o pull

---

## 🆘 Em caso de problema no deploy

Se o VPS quebrar após o `git pull`, você pode voltar ao estado anterior:

```bash
cd ~/Aracannabis_v2_04_08_25
git reset --hard origin/main~1   # volta 1 commit (antes da limpeza)
docker-compose -f docker-compose.prod.yml up -d --build
```

Ou restaure o backup do `.env.production` que você salvou no passo 2.
