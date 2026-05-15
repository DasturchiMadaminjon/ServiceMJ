#!/bin/bash
# Ma'lumotlar bazasini zaxiralash skripti
# Fayl nomi: backup_db.sh

DATE=$(date +%Y-%m-%d_%H-%M-%S)
BACKUP_DIR="/app/backups"
FILE_NAME="db_backup_$DATE.sql"

# Papka mavjudligini tekshirish
mkdir -p $BACKUP_DIR

# Bazani nusxalash (PostgreSQL)
echo "Bazani nusxalash boshlandi: $FILE_NAME"
docker exec servicehub-db-1 pg_dump -U admin servicehub_db > $BACKUP_DIR/$FILE_NAME

# Eski nusxalarni o'chirish (7 kundan eskilari)
find $BACKUP_DIR -type f -name "*.sql" -mtime +7 -delete

echo "Zaxira muvaffaqiyatli saqlandi: $BACKUP_DIR/$FILE_NAME"
