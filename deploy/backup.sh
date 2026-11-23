#!/usr/bin/env bash
# Run as root. Pauses both application services while snapshotting persistent data.
set -euo pipefail
app=/opt/rag-service/app
backup_dir=/opt/rag-service/backups
install -d -m 700 "$backup_dir"
archive="$backup_dir/rag-data-$(date +%Y%m%d-%H%M%S).tar.gz"
umask 077
trap 'systemctl start rag-users rag-backend' EXIT
systemctl stop rag-users rag-backend
items=(backend/data backend/.env DjangoUserService/db.sqlite3 DjangoUserService/.env)
tar -czf "$archive" -C "$app" "${items[@]}" -C /var/www rag-media
echo "Backup saved: $archive"
