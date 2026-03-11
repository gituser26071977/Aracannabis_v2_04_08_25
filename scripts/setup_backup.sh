#!/bin/bash
# Script de Backup Automático para Prontuário e Agrobuds com Criptografia e Upload para Google Drive

BACKUP_DIR="/var/backups/sistemas"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
RETENTION_DAYS=7

# Mude esta senha ou utilize uma variável de ambiente exportada!
ENCRYPTION_PASS="${BACKUP_PASSWORD:-"SenhaSuperForteParaBackup2026"}"

# Nome do remote configurado no rclone (ex: 'gdrive')
RCLONE_REMOTE="gdrive:Backups_Sistemas"

# Cores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}Iniciando rotina de backup Criptografado...${NC}"

# Criar diretório se não existir
mkdir -p "$BACKUP_DIR"

# 1. Backup do Aracannabis Prontuário
echo "Fazendo dump do banco do Aracannabis..."
docker exec aracannabis_db pg_dump -U postgres -d aracannabis > "$BACKUP_DIR/aracannabis_${TIMESTAMP}.sql"

# 2. Backup do Agrobuds (SGAC)
echo "Fazendo dump do banco do Agrobuds..."
docker exec sgac-db pg_dump -U sgac_user -d sgac_data > "$BACKUP_DIR/sgac_${TIMESTAMP}.sql"

# 3. Compactar backups
echo "Compactando backups..."
cd "$BACKUP_DIR"
tar -czf "backup_sistemas_${TIMESTAMP}.tar.gz" aracannabis_${TIMESTAMP}.sql sgac_${TIMESTAMP}.sql

# Remover os arquivos .sql puros
rm aracannabis_${TIMESTAMP}.sql sgac_${TIMESTAMP}.sql

# 4. Criptografar o pacote compactado (AES-256-CBC)
echo "Criptografando arquivo de backup (AES-256)..."
openssl enc -aes-256-cbc -salt -pbkdf2 -in "backup_sistemas_${TIMESTAMP}.tar.gz" -out "backup_sistemas_${TIMESTAMP}.tar.gz.enc" -k "$ENCRYPTION_PASS"

# Remover o pacote não criptografado por segurança
rm "backup_sistemas_${TIMESTAMP}.tar.gz"

# 5. Upload seguro para Google Drive usando rclone
echo "Enviando backup criptografado para o Google Drive..."
if command -v rclone &> /dev/null; then
    rclone copy "$BACKUP_DIR/backup_sistemas_${TIMESTAMP}.tar.gz.enc" "$RCLONE_REMOTE/Prontuario_Agrobuds"
    echo -e "${GREEN}Backup enviado ao Google Drive com sucesso!${NC}"
else
    echo -e "${RED}AVISO: 'rclone' não encontrado. O arquivo foi criptografado apenas localmente.${NC}"
    echo "Instale com: sudo -v ; curl https://rclone.org/install.sh | sudo bash"
    echo "Configure com: rclone config (adicione o Google Drive como 'gdrive')"
fi

# 6. Limpar backups antigos locais (ex: mais velhos que 7 dias)
echo "Limpando backups locais com mais de $RETENTION_DAYS dias..."
find "$BACKUP_DIR" -name "backup_sistemas_*.tar.gz.enc" -type f -mtime +$RETENTION_DAYS -exec rm {} \;

# Se quiser limpar também no Google Drive (cuidado):
# rclone delete --min-age ${RETENTION_DAYS}d "$RCLONE_REMOTE/Prontuario_Agrobuds"

echo -e "${GREEN}Processo de Backup concluído em: $BACKUP_DIR/backup_sistemas_${TIMESTAMP}.tar.gz.enc${NC}"
echo "---------------------------------------------------"
echo "Para descriptografar em caso de emergência, use o comando:"
echo "openssl enc -aes-256-cbc -d -pbkdf2 -in backup_sistemas_*.tar.gz.enc -out resgatado.tar.gz -k SENHA"
echo "---------------------------------------------------"
