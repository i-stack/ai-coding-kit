#!/usr/bin/env bash
# Backup and restore env/mcp/ + env/platforms/ configuration.
#
# Usage:
#   bash sync/scripts/backup-config.sh backup    — create timestamped backup of config dirs
#   bash sync/scripts/backup-config.sh restore   — restore latest backup
#   bash sync/scripts/backup-config.sh list      — list backups
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
MCP_DIR="$REPO_ROOT/env/mcp"
PLATFORMS_DIR="$REPO_ROOT/env/platforms"
BACKUP_CONFIG="$REPO_ROOT/env/backup.json"
DEFAULT_BACKUP_DIR="$HOME/.ai-coding-kit-backups"

resolve_backup_dir() {
  python3 - "$BACKUP_CONFIG" "$DEFAULT_BACKUP_DIR" "$REPO_ROOT" <<'PY'
import json
import os
import sys

config_path, default_dir, repo_root = sys.argv[1:4]

if not os.path.exists(config_path):
    print(default_dir)
    sys.exit(0)

try:
    with open(config_path, encoding="utf-8") as fh:
        cfg = json.load(fh)
except Exception as exc:
    print(f"[backup] Invalid JSON in {config_path}: {exc}", file=sys.stderr)
    sys.exit(1)

if not isinstance(cfg, dict):
    print(f"[backup] {config_path}: root must be a JSON object", file=sys.stderr)
    sys.exit(1)

backup_dir = cfg.get("backupDir", "")
if backup_dir in ("", None):
    print(default_dir)
    sys.exit(0)

if not isinstance(backup_dir, str):
    print(f"[backup] {config_path}: backupDir must be a string", file=sys.stderr)
    sys.exit(1)

backup_dir = os.path.expandvars(os.path.expanduser(backup_dir))
if not os.path.isabs(backup_dir):
    backup_dir = os.path.abspath(os.path.join(repo_root, backup_dir))

print(backup_dir)
PY
}

BACKUP_DIR="$(resolve_backup_dir)"

cmd="${1:-list}"

case "$cmd" in
  backup)
    mkdir -p "$BACKUP_DIR"

    has_files=false
    if [ -d "$MCP_DIR" ] && [ -n "$(ls -A "$MCP_DIR"/*.json 2>/dev/null || true)" ]; then
      has_files=true
    fi
    if [ -d "$PLATFORMS_DIR" ] && [ -n "$(ls -A "$PLATFORMS_DIR"/*.json 2>/dev/null || true)" ]; then
      has_files=true
    fi

    if [ "$has_files" = false ]; then
      echo "[backup] No config files found in env/mcp/ or env/platforms/ — nothing to back up." >&2
      exit 0
    fi

    ts="$(date +%Y%m%d_%H%M%S)"
    dest="$BACKUP_DIR/config_${ts}.tar.gz"

    tar -czf "$dest" -C "$REPO_ROOT/env" mcp platforms 2>/dev/null || true
    chmod 600 "$dest"
    echo "[backup] Saved: $dest"

    # Keep last 10 backups, remove older ones
    keep=$(ls -1t "$BACKUP_DIR"/config_*.tar.gz 2>/dev/null | head -10)
    for f in "$BACKUP_DIR"/config_*.tar.gz; do
      if ! echo "$keep" | grep -qF "$f"; then
        rm "$f"
        echo "[backup] Pruned old: $f"
      fi
    done
    ;;

  restore)
    latest=$(ls -1t "$BACKUP_DIR"/config_*.tar.gz 2>/dev/null | head -1)
    if [ -z "$latest" ]; then
      echo "[backup] No backups found in $BACKUP_DIR" >&2
      exit 1
    fi

    has_existing=false
    [ -d "$MCP_DIR" ] && [ -n "$(ls -A "$MCP_DIR"/*.json 2>/dev/null || true)" ] && has_existing=true
    [ -d "$PLATFORMS_DIR" ] && [ -n "$(ls -A "$PLATFORMS_DIR"/*.json 2>/dev/null || true)" ] && has_existing=true

    if [ "$has_existing" = true ]; then
      echo "[backup] Existing config files found. Overwrite? (y/N)"
      read -r answer
      if [ "$answer" != "y" ] && [ "$answer" != "Y" ]; then
        echo "[backup] Aborted."
        exit 0
      fi
    fi

    tar -xzf "$latest" -C "$REPO_ROOT/env"
    echo "[backup] Restored $latest -> env/mcp/ + env/platforms/"
    ;;

  list)
    if [ -d "$BACKUP_DIR" ]; then
      echo "Backups in $BACKUP_DIR:"
      ls -1th "$BACKUP_DIR"/config_*.tar.gz 2>/dev/null || echo "  (none)"
    else
      echo "No backups yet. Run: bash sync/scripts/backup-config.sh backup"
    fi
    ;;

  *)
    echo "Usage: bash sync/scripts/backup-config.sh [backup|restore|list]" >&2
    exit 1
    ;;
esac
