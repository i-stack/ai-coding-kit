#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

active_version="$(ruby -rjson -e 'print JSON.parse(File.read("evolution/active_version.json"))["active_version"]')"

if [[ ! "$active_version" =~ ^v[0-9]+(-[A-Za-z0-9]+)*$ ]]; then
  echo "Invalid active_version in evolution/active_version.json: ${active_version}"
  exit 1
fi

snapshot_dir="evolution/history/${active_version}/snapshot"

if [ ! -d "$snapshot_dir" ]; then
  echo "Missing snapshot dir for active version: ${snapshot_dir}"
  exit 1
fi

drift=0

check_path() {
  local rel="$1"
  local snapshot_path="${snapshot_dir}/${rel}"
  local current_path="${rel}"

  if [ ! -e "$snapshot_path" ] || [ ! -e "$current_path" ]; then
    echo "Missing path for comparison: snapshot=${snapshot_path} current=${current_path}"
    drift=1
    return
  fi

  if [ -f "$snapshot_path" ]; then
    if ! diff -q "$snapshot_path" "$current_path" >/dev/null 2>&1; then
      echo "Drift: ${rel}"
      drift=1
    fi
  else
    local diff_out
    diff_out="$(diff -rq "$snapshot_path" "$current_path" 2>&1 || true)"
    if [ -n "$diff_out" ]; then
      echo "$diff_out" | sed "s|^|Drift: |"
      drift=1
    fi
  fi
}

check_path "SKILL.md"
check_path "agents"
check_path "references"
check_path "scripts"

if [ "$drift" -ne 0 ]; then
  echo "Snapshot consistency FAILED: working tree differs from active snapshot ${active_version}"
  echo "Hint: if this drift is intentional, promote a new version via the proposal flow."
  exit 1
fi

echo "Snapshot consistency OK: active=${active_version}"
