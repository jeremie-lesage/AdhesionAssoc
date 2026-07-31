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
#
# `-pbkdf2 -iter 600000 -md sha256` : sans ces options, OpenSSL retombe sur
# EVP_BytesToKey, soit MD5 avec UNE seule itération — la dérivation ne coûte alors
# qu'un hachage MD5 par mot de passe candidat, et une attaque par dictionnaire hors
# ligne tourne à des milliards d'essais par seconde sur GPU. AES-256-CBC est
# correct, mais la clé ne vaut que ce que vaut la dérivation.
#
# RESTAURATION : openssl enc -d -aes-256-cbc -pbkdf2 -iter 600000 -md sha256 -in FICHIER.enc -pass env:ENCRYPTION_PASSWORD | gunzip
#
# Les archives produites AVANT ce durcissement restent lisibles, mais seulement
# sans ces options — ne pas les perdre en changeant la procédure :
# RESTAURATION (archives d'avant le durcissement) : openssl enc -d -aes-256-cbc -in FICHIER.enc -pass env:ENCRYPTION_PASSWORD | gunzip
#
# Les deux commandes ci-dessus sont exécutées par
# backend/tests/test_backup_script.py : elles sont vérifiées, pas seulement écrites.
openssl enc -aes-256-cbc -salt -pbkdf2 -iter 600000 -md sha256 -in "$BACKUP_GZ_FILE" -out "$BACKUP_ENC_FILE" -pass env:ENCRYPTION_PASSWORD

if [ $? -ne 0 ]; then
  echo "Encryption failed! Check ENCRYPTION_PASSWORD."
  exit 1
fi
echo "Backup encrypted: $BACKUP_ENC_FILE"

# 4. Transfer the encrypted backup over SFTP
#
# Historique : le transfert passait par `curl … ftp://`, donc `USER`/`PASS` en ASCII
# sur le réseau à chaque exécution horaire du cron — un observateur sur le chemin
# (opérateur, machine compromise du même segment) capturait FTP_PASSWORD, puis
# téléchargeait ou supprimait tous les dumps. FTPS a été essayé et écarté : le
# cluster OVH répond « 500 This security scheme is not implemented » à AUTH TLS
# comme à AUTH SSL. SFTP, lui, fonctionne — tout passe dans le tunnel SSH.
#
# `sshpass -e` lit le mot de passe dans SSHPASS plutôt que sur la ligne de commande,
# où `ps` l'exposerait à tout le conteneur. BatchMode n'est PAS utilisé : il
# désactiverait l'authentification par mot de passe.
#
# `known_hosts` sur le volume /backups (déjà persistant) : sans vérification d'hôte
# durable, un intermédiaire pourrait se faire passer pour le serveur et récupérer le
# mot de passe — la Vuln 6 par un autre chemin. `accept-new` enregistre la clé à la
# première connexion puis refuse tout changement. Pour supprimer même ce risque
# initial, pré-remplir le fichier depuis le VPS :
#   docker compose exec db_backup sh -c 'ssh-keyscan -H "$FTP_SERVER" > /backups/.ssh_known_hosts'
KNOWN_HOSTS="$BACKUP_DIR/.ssh_known_hosts"
touch "$KNOWN_HOSTS"

# Chemin RELATIF : en FTP, "/backup" désignait un dossier du chroot du compte ; en
# SFTP il viserait la racine du serveur, où le compte n'a rien à écrire.
SFTP_PATH="${FTP_PATH#/}"

# Batch dans un fichier plutôt que sur stdin (`-b -`) : sshpass alloue un pty pour
# répondre à l'invite de mot de passe, et le laisser se disputer stdin avec le
# heredoc est une source de blocage connue.
# `-mkdir` (préfixe `-`) n'interrompt pas le batch si le dossier existe déjà :
# c'est l'équivalent du `--ftp-create-dirs` de curl.
SFTP_BATCH_FILE="$BACKUP_DIR/.sftp_batch"
cat > "$SFTP_BATCH_FILE" <<SFTP_BATCH
-mkdir $SFTP_PATH
put $BACKUP_ENC_FILE $SFTP_PATH/
bye
SFTP_BATCH

SSHPASS="$FTP_PASSWORD" sshpass -e sftp \
  -o StrictHostKeyChecking=accept-new \
  -o UserKnownHostsFile="$KNOWN_HOSTS" \
  -b "$SFTP_BATCH_FILE" "$FTP_USER@$FTP_SERVER"
SFTP_STATUS=$?
rm -f "$SFTP_BATCH_FILE"

if [ $SFTP_STATUS -eq 0 ]; then
  echo "Backup successfully transferred to sftp://$FTP_SERVER/$SFTP_PATH/"
else
  echo "SFTP transfer failed!"
  exit 1
fi

# Remove old backups (e.g., keep last 7 days) - adjust as needed for encrypted files
find "$BACKUP_DIR" -type f -name "*.sql.gz.enc" -mtime +7 -delete
