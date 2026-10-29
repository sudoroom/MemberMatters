#!/bin/bash -e -o pipefail

# ================= Config =================
BACKUPS_ROOT=/opt/member-matters/postgres/backups   # parent dir holding dated backup folders
DATA_DIR=/opt/member-matters/postgres/data
WAL_DIR=/opt/member-matters/postgres/wal_archive
CONTAINER=docker-mm-postgres-1
# Path as seen INSIDE the container (must match your docker volume mount)
CONTAINER_WAL_DIR=/var/lib/postgresql/wal_archive

# ============ 1. List base backups ============
echo "🔍 Available base backups in $BACKUPS_ROOT:"
mapfile -t BACKUPS < <(find "$BACKUPS_ROOT" -maxdepth 1 -mindepth 1 -type d \
    -exec test -f '{}/base.tar.gz' \; -print | sort)

if [ ${#BACKUPS[@]} -eq 0 ]; then
    echo "❌ No base backups found (folders containing base.tar.gz)." >&2
    exit 1
fi

for i in "${!BACKUPS[@]}"; do
    printf '  [%d] %s\n' "$((i+1))" "$(basename "${BACKUPS[$i]}")"
done

read -rp "Select base backup [1-${#BACKUPS[@]}]: " choice
if ! [[ "$choice" =~ ^[0-9]+$ ]] || (( choice < 1 || choice > ${#BACKUPS[@]} )); then
    echo "❌ Invalid selection." >&2
    exit 1
fi
BACKUP_FOLDER="${BACKUPS[$((choice-1))]}"
echo "✅ Using backup: $BACKUP_FOLDER"

# ====== 2. Prompt for point-in-time (UTC) ======
# Default guess: backup timestamp + 15 min (folder named YYYY-MM-DD_HH-MM-SS)
bn=$(basename "$BACKUP_FOLDER")
default_time=$(date -u -d "${bn/_/ }" -Iseconds 2>/dev/null \
    | sed 's/T/ /; s/+00:00//' | awk '{print $1" "$2}' )
[[ -n "$default_time" ]] && default_time="$default_time" || default_time="$(date -u '+%Y-%m-%d %H:%M:%S')"

echo "⏰ Enter recovery target time (UTC, format: 'YYYY-MM-DD HH:MM:SS')"
read -rp "Recovery time [$default_time]: " RECOVERY_TIME
RECOVERY_TIME=${RECOVERY_TIME:-$default_time}
echo "✅ Recovery target: $RECOVERY_TIME (UTC)"

# ============ 3. Perform the restore ============
echo "🛑 Stopping container..."
docker stop "$CONTAINER"

echo "🧹 Cleaning old data..."
rm -rf "${DATA_DIR:?}"/*
rm -rf "${WAL_DIR:?}"/*
mkdir -p "$DATA_DIR" "$WAL_DIR"

echo "📦 Extracting base backup..."
tar -xzvf "$BACKUP_FOLDER/base.tar.gz" -C "$DATA_DIR"

echo "🔁 Restoring WAL archive..."
cp -r "$BACKUP_FOLDER"/wal_archive/* "$WAL_DIR/"

echo "📜 Writing recovery settings (PG12+: postgresql.auto.conf + recovery.signal)..."
cat >> "$DATA_DIR/postgresql.auto.conf" <<EOF
restore_command = 'cp $CONTAINER_WAL_DIR/%f %p'
recovery_target_time = '$RECOVERY_TIME'
recovery_target_action = 'pause'
EOF

touch "$DATA_DIR/recovery.signal"

echo "🚀 Starting PostgreSQL..."
docker start "$CONTAINER"

echo "✅ Recovery started — check logs: docker logs -f $CONTAINER"
