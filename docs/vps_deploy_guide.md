# Guia de Deploy na VPS Hostinger com Debian 12

Este guia fornece instruções detalhadas para conectar-se à sua VPS da Hostinger e realizar o deploy da aplicação Aracannabis Prontuário.

## 1. Conectar-se à VPS via SSH

```bash
# Substitua USER pelo seu nome de usuário e IP_ADDRESS pelo endereço IP da sua VPS
ssh USER@IP_ADDRESS
```

Se você estiver usando uma chave SSH (recomendado):
```bash
ssh -i /caminho/para/sua/chave_privada USER@IP_ADDRESS
```

## 2. Atualizar o Sistema

```bash
# Atualizar a lista de pacotes
sudo apt update

# Atualizar todos os pacotes instalados
sudo apt upgrade -y

# Instalar pacotes essenciais
sudo apt install -y git curl wget nano unzip
```

## 3. Instalar Dependências

```bash
# Instalar Python e ferramentas relacionadas
sudo apt install -y python3 python3-pip python3-venv

# Instalar PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# Instalar Nginx
sudo apt install -y nginx

# Instalar Certbot para SSL
sudo apt install -y certbot python3-certbot-nginx

# Instalar Node.js e npm
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
```

## 4. Configurar o PostgreSQL

```bash
# Entrar no shell do PostgreSQL
sudo -u postgres psql

# Criar banco de dados e usuário (execute dentro do shell do PostgreSQL)
CREATE DATABASE aracannabis;
CREATE USER aracannabis_user WITH PASSWORD 'sua_senha_segura';
GRANT ALL PRIVILEGES ON DATABASE aracannabis TO aracannabis_user;

# Sair do shell do PostgreSQL
\q
```

## 5. Configurar o Diretório da Aplicação

```bash
# Criar diretório para a aplicação
sudo mkdir -p /var/www/aracannabis
sudo chown -R $USER:$USER /var/www/aracannabis
```

## 6. Transferir Arquivos para a VPS

### Opção 1: Clonar do GitHub (se você seguiu as instruções do github_setup.md)

```bash
# Navegar para o diretório da aplicação
cd /var/www/aracannabis

# Clonar o repositório (substitua USER pelo seu nome de usuário do GitHub)
git clone https://github.com/SEU_USUARIO/aracannabis-prontuario.git .
```

### Opção 2: Transferir arquivos diretamente via SCP

Execute estes comandos no seu computador local, não na VPS:

```bash
# Criar um arquivo compactado do projeto
cd /caminho/para/aracannabis_project/Manus_PRONTUARIO
tar -czvf aracannabis.tar.gz .

# Transferir o arquivo para a VPS
scp aracannabis.tar.gz USER@IP_ADDRESS:/var/www/aracannabis/

# Voltar para a VPS e descompactar
ssh USER@IP_ADDRESS
cd /var/www/aracannabis
tar -xzvf aracannabis.tar.gz
rm aracannabis.tar.gz
```

## 7. Configurar o Backend

```bash
# Navegar para o diretório da aplicação
cd /var/www/aracannabis

# Criar diretórios para backend e frontend se não existirem
mkdir -p backend
mkdir -p frontend

# Mover arquivos Python para o diretório backend
mv app.py config.py models.py routes backend/
mv *.py backend/ 2>/dev/null || true

# Criar ambiente virtual Python
cd backend
python3 -m venv venv
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
pip install gunicorn

# Criar arquivo .env
cp .env.example .env
nano .env
```

Edite o arquivo .env com suas configurações:
```
FLASK_ENV=production
FLASK_APP=app.py
DATABASE_URL=postgresql://aracannabis_user:sua_senha_segura@localhost:5432/aracannabis
JWT_SECRET_KEY=sua_chave_jwt_secreta
SECRET_KEY=sua_chave_secreta
```

## 8. Configurar o Frontend

```bash
# Navegar para o diretório frontend
cd /var/www/aracannabis/frontend

# Mover arquivos JavaScript para o diretório frontend
mv /var/www/aracannabis/*.js /var/www/aracannabis/frontend/ 2>/dev/null || true

# Criar estrutura de diretórios
mkdir -p src/{components,pages,contexts,services}
mkdir -p public

# Instalar dependências
npm install

# Construir o frontend
npm run build
```

## 9. Configurar o Nginx

```bash
# Criar arquivo de configuração do Nginx
sudo nano /etc/nginx/sites-available/aracannabis
```

Cole o conteúdo do arquivo nginx.conf, substituindo "your_domain.com" pelo seu domínio real.

```bash
# Criar link simbólico para habilitar o site
sudo ln -s /etc/nginx/sites-available/aracannabis /etc/nginx/sites-enabled/

# Verificar a configuração do Nginx
sudo nginx -t

# Reiniciar o Nginx
sudo systemctl restart nginx
```

## 10. Configurar SSL com Certbot

```bash
# Obter certificado SSL (substitua example.com pelo seu domínio)
sudo certbot --nginx -d example.com
```

## 11. Configurar o Serviço Systemd

```bash
# Criar arquivo de serviço
sudo nano /etc/systemd/system/aracannabis.service
```

Cole o conteúdo do arquivo aracannabis.service.

```bash
# Recarregar o systemd
sudo systemctl daemon-reload

# Habilitar o serviço para iniciar na inicialização
sudo systemctl enable aracannabis

# Iniciar o serviço
sudo systemctl start aracannabis

# Verificar o status do serviço
sudo systemctl status aracannabis
```

## 12. Verificar o Deploy

1. Acesse seu domínio no navegador (https://seu-dominio.com)
2. Verifique se a aplicação está funcionando corretamente
3. Teste o login e outras funcionalidades

## Solução de Problemas

### Verificar logs do Nginx
```bash
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log
```

### Verificar logs do serviço
```bash
sudo journalctl -u aracannabis.service -f
```

### Reiniciar serviços
```bash
sudo systemctl restart aracannabis
sudo systemctl restart nginx
```

### Verificar status do banco de dados
```bash
sudo systemctl status postgresql
```

## Manutenção

### Atualizar a aplicação
```bash
# Navegar para o diretório da aplicação
cd /var/www/aracannabis

# Puxar as alterações mais recentes (se estiver usando Git)
git pull

# Atualizar o backend
cd backend
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart aracannabis

# Atualizar o frontend
cd ../frontend
npm install
npm run build
```

### Backup do banco de dados
```bash
# Criar backup do banco de dados
sudo -u postgres pg_dump aracannabis > /var/backups/aracannabis_$(date +%Y%m%d).sql
```
