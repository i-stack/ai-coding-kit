#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

if [ $# -lt 1 ]; then
  echo "Usage: bash scripts/rollback_skill_evolution.sh <version>"
  exit 1
fi

target_version="$1"

# 1. 版本格式白名单
if [[ ! "$target_version" =~ ^v[0-9]+(-[A-Za-z0-9]+)*$ ]]; then
  echo "Invalid version format (must match ^v[0-9]+(-[A-Za-z0-9]+)*$): ${target_version}"
  exit 1
fi

history_dir="evolution/history/${target_version}"
snapshot_dir="${history_dir}/snapshot"

if [ ! -d "$snapshot_dir" ]; then
  echo "Missing snapshot for version: ${target_version}"
  exit 1
fi

# 2. snapshot 完整性预检查
required=("SKILL.md" "agents" "references" "scripts")
for p in "${required[@]}"; do
  if [ ! -e "${snapshot_dir}/${p}" ]; then
    echo "Snapshot incomplete, missing: ${snapshot_dir}/${p}"
    exit 1
  fi
done

# 3. snapshot 复制到临时目录 + 基础预校验
stage_dir="$(mktemp -d)"
cleanup_stage() { rm -rf "$stage_dir"; }
trap cleanup_stage EXIT

cp "${snapshot_dir}/SKILL.md" "${stage_dir}/SKILL.md"
cp -R "${snapshot_dir}/agents" "${stage_dir}/agents"
cp -R "${snapshot_dir}/references" "${stage_dir}/references"
cp -R "${snapshot_dir}/scripts" "${stage_dir}/scripts"

ruby -e 'require "yaml"; YAML.load_file(ARGV[0])' "${stage_dir}/SKILL.md" \
  || { echo "Staged SKILL.md YAML invalid"; exit 1; }

staged_lines="$(wc -l < "${stage_dir}/SKILL.md" | tr -d ' ')"
if [ "$staged_lines" -gt 500 ]; then
  echo "Staged SKILL.md too long: ${staged_lines} lines"
  exit 1
fi

# 4. 当前文件移到备份，再把暂存区 move 成正式位置；失败自动恢复
backup_dir="$(mktemp -d)"
restore_backup() {
  for item in SKILL.md agents references scripts; do
    if [ -e "${backup_dir}/${item}" ]; then
      rm -rf "${item}"
      mv "${backup_dir}/${item}" "./${item}"
    fi
  done
}

trap 'restore_backup; cleanup_stage; rm -rf "$backup_dir"' ERR

for item in SKILL.md agents references scripts; do
  if [ -e "$item" ]; then
    mv "$item" "${backup_dir}/${item}"
  fi
done

mv "${stage_dir}/SKILL.md" SKILL.md
mv "${stage_dir}/agents" agents
mv "${stage_dir}/references" references
mv "${stage_dir}/scripts" scripts

# 5. 完整 validate
if ! bash scripts/validate_skill_evolution.sh; then
  echo "Validation failed after rollback. Restoring backup..."
  for item in SKILL.md agents references scripts; do
    rm -rf "$item"
    if [ -e "${backup_dir}/${item}" ]; then
      mv "${backup_dir}/${item}" "./${item}"
    fi
  done
  rm -rf "$backup_dir"
  exit 1
fi

# 6. active_version.json 通过 ruby JSON 序列化
ruby -rjson -e '
  data = {
    "active_version" => ARGV[0],
    "status" => "active",
    "promoted_at" => Time.now.strftime("%Y-%m-%dT%H:%M:%S%z"),
    "source" => "rollback",
    "notes" => "Rolled back to archived stable snapshot."
  }
  File.write("evolution/active_version.json", JSON.pretty_generate(data) + "\n")
' "$target_version"

# 7. 清理备份
rm -rf "$backup_dir"
trap - ERR

echo "Rolled back to ${target_version}"
