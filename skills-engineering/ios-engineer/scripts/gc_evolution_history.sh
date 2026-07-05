#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

HISTORY_DIR="evolution/history"
ACTIVE_VERSION_FILE="evolution/active_version.json"
KEEP_RECENT="${KEEP_RECENT:-10}"
MILESTONE_INTERVAL="${MILESTONE_INTERVAL:-10}"

DRY_RUN=false
while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run) DRY_RUN=true; shift ;;
    -h|--help)
      echo "Usage: bash scripts/gc_evolution_history.sh [--dry-run]"
      echo ""
      echo "Clean up old evolution history snapshots, keeping:"
      echo "  - Most recent ${KEEP_RECENT} versions"
      echo "  - Every ${MILESTONE_INTERVAL}th version as milestones (v10, v20, ...)"
      echo "  - Current active version (always protected)"
      echo ""
      echo "Options:"
      echo "  --dry-run  List what would be deleted without actually deleting"
      exit 0
      ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

if [ ! -d "$HISTORY_DIR" ]; then
  echo "No history directory found: ${HISTORY_DIR}"
  exit 0
fi

# Get active version
if [ -f "$ACTIVE_VERSION_FILE" ]; then
  ACTIVE_VERSION="$(ruby -rjson -e 'puts JSON.parse(File.read(ARGV[0]))["active_version"]' "$ACTIVE_VERSION_FILE")"
else
  echo "No active_version.json found, aborting GC"
  exit 0
fi

# Collect all version dirs, extract version number for sorting
tmpfile="$(mktemp)"
trap 'rm -f "$tmpfile"' EXIT

for dir in "$HISTORY_DIR"/v[0-9]*/; do
  [ -d "$dir" ] || continue
  dirname="$(basename "$dir")"
  # Match versions created by promote_skill_evolution.sh: v1, v10, v73, v73-alpha, v73-hotfix
  if ! echo "$dirname" | grep -qE '^v[0-9]+(-[A-Za-z0-9]+)*$'; then
    continue
  fi
  # Extract leading numeric portion for milestone calculation (v73-alpha → 73)
  num="$(echo "$dirname" | sed 's/^v//; s/-.*//' | sed 's/^0*//')"
  num="${num:-0}"
  echo "$num $dirname" >> "$tmpfile"
done

if [ ! -s "$tmpfile" ]; then
  echo "No versioned history directories found"
  exit 0
fi

# Sort by version number descending
sorted_dirs=($(sort -k1 -n -r "$tmpfile" | awk '{print $2}'))
total="${#sorted_dirs[@]}"

# Mark protected versions using a temp file
protected_file="$(mktemp)"
trap 'rm -f "$tmpfile" "$protected_file"' EXIT

# Active version is always protected
echo "$ACTIVE_VERSION" >> "$protected_file"

# Most recent KEEP_RECENT
count=0
for v in "${sorted_dirs[@]}"; do
  if [ "$count" -lt "$KEEP_RECENT" ]; then
    echo "$v" >> "$protected_file"
  fi
  count=$((count + 1))
done

# Milestones (v10, v20, ...) — use only the leading numeric portion for suffixed versions
for v in "${sorted_dirs[@]}"; do
  num="$(echo "$v" | sed 's/^v//; s/-.*//' | sed 's/^0*//')"
  num="${num:-0}"
  if [ "$num" -ge "$MILESTONE_INTERVAL" ] && [ $((num % MILESTONE_INTERVAL)) -eq 0 ]; then
    echo "$v" >> "$protected_file"
  fi
done

echo "=== Evolution History GC ==="
echo "Active version: $ACTIVE_VERSION"
echo "Keep recent: $KEEP_RECENT"
echo "Total versions found: $total"
echo ""

deleted=0
kept=0
for v in "${sorted_dirs[@]}"; do
  if grep -qx "$v" "$protected_file"; then
    echo "  [KEEP]  $HISTORY_DIR/$v"
    kept=$((kept + 1))
  else
    echo "  [DELETE] $HISTORY_DIR/$v"
    if ! $DRY_RUN; then
      rm -rf "$HISTORY_DIR/$v"
    fi
    deleted=$((deleted + 1))
  fi
done

echo ""
if $DRY_RUN; then
  echo "DRY RUN: Would delete $deleted version(s), keep $kept version(s)"
else
  echo "Done: Deleted $deleted version(s), kept $kept version(s)"
fi
