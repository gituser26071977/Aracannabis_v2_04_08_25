# Como adicionar este projeto ao GitHub como repositório privado

Siga estas etapas para adicionar o projeto Aracannabis Prontuário ao seu GitHub como um repositório privado:

## 1. Criar um novo repositório privado no GitHub

1. Acesse [GitHub](https://github.com) e faça login na sua conta
2. Clique no botão "+" no canto superior direito e selecione "New repository"
3. Preencha o nome do repositório (ex: "aracannabis-prontuario")
4. Adicione uma descrição (opcional)
5. Selecione "Private" para tornar o repositório privado
6. Não inicialize o repositório com README, .gitignore ou licença
7. Clique em "Create repository"

## 2. Inicializar o repositório Git local e fazer o primeiro commit

```bash
# Navegue até o diretório do projeto
cd /caminho/para/aracannabis_project/Manus_PRONTUARIO

# Inicialize o repositório Git
git init

# Adicione todos os arquivos ao staging
git add .

# Faça o primeiro commit
git commit -m "Estrutura inicial do projeto"
```

## 3. Conectar o repositório local ao GitHub e fazer push

```bash
# Adicione o repositório remoto (substitua 'seu-usuario' pelo seu nome de usuário do GitHub)
git remote add origin https://github.com/seu-usuario/aracannabis-prontuario.git

git remote add origin https://github.com/gituser26071977/aracannabis-prontuario.git

# Faça o push para o GitHub (a branch principal agora é chamada 'main' no GitHub)
git push -u origin main
```

Se a branch principal for chamada 'master' em vez de 'main', use:

```bash
git push -u origin master
```

## 4. Verificar se o repositório está privado

1. Acesse seu repositório no GitHub
2. Clique na aba "Settings"
3. Role para baixo até a seção "Danger Zone"
4. Verifique se "Change repository visibility" está definido como "Private"

## 5. Atualizar o script de deploy

Após criar o repositório, atualize o arquivo `deploy.sh` com a URL do seu repositório:

```bash
# Abra o arquivo deploy.sh
nano deploy.sh

# Atualize a variável GIT_REPO com a URL do seu repositório
# Exemplo:
# GIT_REPO="https://github.com/seu-usuario/aracannabis-prontuario.git"
```

## 6. Gerenciar acesso ao repositório (opcional)

Se você precisar dar acesso a outras pessoas:

1. Acesse seu repositório no GitHub
2. Clique na aba "Settings"
3. Clique em "Manage access" no menu lateral
4. Clique em "Invite a collaborator"
5. Digite o nome de usuário ou e-mail da pessoa e defina o nível de acesso
