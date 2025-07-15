#!/bin/sh

# Source the .env file to load environment variables
# Assuming the script runs in a context where /app is the project root
#source /app/docker/.env

BACKUP_DIR="/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_SQL_FILE="$BACKUP_DIR/db_backup_$TIMESTAMP.sql"
BACKUP_GZ_FILE="$BACKUP_DIR/db_backup_$TIMESTAMP.sql.gz"
BACKUP_ENC_FILE="$BACKUP_DIR/db_backup_$TIMESTAMP.sql.gz.enc"

# FTP Details are now loaded from .env
FTP_PATH="/backup" # The folder on the FTP server

mkdir -p "$BACKUP_DIR"

# 1. Perform PostgreSQL dump
PGPASSWORD=$POSTGRES_PASSWORD pg_dump -h db -p 5432 -U $POSTGRES_USER -d $POSTGRES_DB > "$BACKUP_SQL_FILE"

if [ $? -ne 0 ]; then
  echo "PostgreSQL dump failed!"
  exit 1
fi
echo "PostgreSQL dump successful: $BACKUP_SQL_FILE"

# 2. Compress the backup file
gzip "$BACKUP_SQL_FILE"

if [ $? -ne 0 ]; then
  echo "Compression failed!"
  exit 1
fi
echo "Backup compressed: $BACKUP_GZ_FILE"

# 3. Encrypt the compressed backup file
openssl enc -aes-256-cbc -salt -in "$BACKUP_GZ_FILE" -out "$BACKUP_ENC_FILE" -pass env:ENCRYPTION_PASSWORD

if [ $? -ne 0 ]; then
  echo "Encryption failed! Check ENCRYPTION_PASSWORD."
  exit 1
fi
echo "Backup encrypted: $BACKUP_ENC_FILE"

# 4. Transfer the encrypted backup to FTP
curl -u "$FTP_USER:$FTP_PASSWORD" --ftp-create-dirs -T "$BACKUP_ENC_FILE" "ftp://$FTP_SERVER$FTP_PATH/"

if [ $? -eq 0 ]; then
  echo "Backup successfully transferred to ftp://$FTP_SERVER$FTP_PATH/$BACKUP_ENC_FILE"
else
  echo "FTP transfer failed!"
  exit 1
fi

# Remove old backups (e.g., keep last 7 days) - adjust as needed for encrypted files
find "$BACKUP_DIR" -type f -name "*.sql.gz.enc" -mtime +7 -delete
