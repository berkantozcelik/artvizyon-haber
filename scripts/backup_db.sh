#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$HOME/artvizyon-haber"
DB_PATH="$PROJECT_DIR/db.sqlite3"
BACKUP_DIR="$HOME/db_backups/artvizyon-haber"
timestamp=$(date +"%Y%m%d_%H%M%S")
backup_path="$BACKUP_DIR/db_${timestamp}.sqlite3"

mkdir -p "$BACKUP_DIR"
if [ ! -f "$DB_PATH" ]; then
  echo "Database not found: $DB_PATH" >&2
  exit 1
fi

cp "$DB_PATH" "$backup_path"
