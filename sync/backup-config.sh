#!/usr/bin/env bash
# Backup and restore env/config.json.
#
# Usage:
#   bash sync/backup-config.sh backup    — create timestamped backup
#   bash sync/backup-config.sh restore   — restore latest backup to env/config.json
#   bash sync/backup-config.sh list      — list backups
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CONFIG_JSON="$REPO_ROOT/env/config.json"
BACKUP_DIR="$HOME/.ai-coding-kit-backups"

cmd="${1:-list}"

case "$cmd" in
  backup)
    mkdir -p "$BACKUP_DIR"
    if [ ! -f "$CONFIG_JSON" ]; then
      echo "[backup] $CONFIG_JSON does not exist — nothing to back up." >&2
      exit 1
    fi
    ts="$(date +%Y%m%d_%H%M%S)"
    dest="$BACKUP_DIR/config_${ts}.json"
    cp "$CONFIG_JSON" "$dest"
    chmod 600 "$dest"
    echo "[backup] Saved: $dest"

    # Keep last 10 backups, remove older ones
    keep=$(ls -1t "$BACKUP_DIR"/config_*.json 2>/dev/null | head -10)
    for f in "$BACKUP_DIR"/config_*.json; do
      if ! echo "$keep" | grep -qF "$f"; then
        rm "$f"
        echo "[backup] Pruned old: $f"
      fi
    done
    ;;

  restore)
    latest=$(ls -1t "$BACKUP_DIR"/config_*.json 2>/dev/null | head -1)
    if [ -z "$latest" ]; then
      echo "[backup] No backups found in $BACKUP_DIR" >&2
      exit 1
    fi
    if [ -f "$CONFIG_JSON" ]; then
      echo "[backup] $CONFIG_JSON already exists. Overwrite? (y/N)"
      read -r answer
      if [ "$answer" != "y" ] && [ "$answer" != "Y" ]; then
        echo "[backup] Aborted."
        exit 0
      fi
    fi
    cp "$latest" "$CONFIG_JSON"
    chmod 600 "$CONFIG_JSON"
    echo "[backup] Restored $latest → $CONFIG_JSON"
    ;;

  list)
    if [ -d "$BACKUP_DIR" ]; then
      echo "Backups in $BACKUP_DIR:"
      ls -1th "$BACKUP_DIR"/config_*.json 2>/dev/null || echo "  (none)"
    else
      echo "No backups yet. Run: bash sync/backup-config.sh backup"
    fi
    ;;

  *)
    echo "Usage: bash sync/backup-config.sh [backup|restore|list]" >&2
    exit 1
    ;;
esac
