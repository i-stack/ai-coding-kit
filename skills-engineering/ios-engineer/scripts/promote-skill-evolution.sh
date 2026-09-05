#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

if [ $# -lt 2 ]; then
  echo "Usage: bash scripts/promote-skill-evolution.sh <new-version> <source> [proposal-file]"
  echo "Example: bash scripts/promote-skill-evolution.sh v2 proposal:20260403-fix-root-cause evolution/proposals/20260403-fix-root-cause.md"
  exit 1
fi

new_version="$1"
source_ref="$2"
proposal_file="${3:-}"

# 字段白名单校验
if [[ ! "$new_version" =~ ^v[0-9]+(-[A-Za-z0-9]+)*$ ]]; then
  echo "Invalid new_version format (expected ^v[0-9]+(-[A-Za-z0-9]+)*$): ${new_version}"
  exit 1
fi

if [[ ! "$source_ref" =~ ^[A-Za-z0-9:_./-]{1,200}$ ]]; then
  echo "Invalid source_ref format (expected ^[A-Za-z0-9:_./-]{1,200}$): ${source_ref}"
  exit 1
fi

if [ -n "$proposal_file" ]; then
  if [[ ! "$proposal_file" =~ ^evolution/proposals/[0-9]{8}-[0-9]{6}-[A-Za-z0-9_-]+\.md$ ]]; then
    echo "Invalid proposal_file format: ${proposal_file}"
    exit 1
  fi
fi

history_dir="evolution/history/${new_version}"
snapshot_dir="${history_dir}/snapshot"

if [ -e "$history_dir" ]; then
  echo "Version already exists: ${new_version}"
  exit 1
fi

if [ -n "$proposal_file" ]; then
  if [ ! -f "$proposal_file" ]; then
    echo "Missing proposal file: ${proposal_file}"
    exit 1
  fi

  proposal_status="$(ruby - "$proposal_file" <<'RUBY'
proposal_file = ARGV[0]
lines = File.readlines(proposal_file)
status_index = lines.find_index { |line| line.strip == "## 状态" }
abort("Missing status section") unless status_index
value_index = status_index + 1
abort("Missing status value") unless value_index < lines.length
print lines[value_index].sub(/^- /, "").strip
RUBY
)"

  if [ "$proposal_status" != "approved" ]; then
    echo "Proposal is not approved: ${proposal_status}"
    exit 1
  fi

  proposal_id="$(basename "$proposal_file" .md)"
  approval_file="evolution/approvals/${proposal_id}.json"
  if [ ! -f "$approval_file" ]; then
    echo "Missing approval record: ${approval_file}"
    exit 1
  fi
fi

SKIP_SNAPSHOT_CONSISTENCY=1 bash scripts/validate-skill-evolution.sh

# Evidence-class promotion gate (usage_ledger.md §7b): a rule may only be
# promoted on independently_replayed evidence, not observed ratio. If a proposal
# file is supplied, run the gate; a FAIL (non-zero) aborts promotion.
if [ -n "$proposal_file" ]; then
  if ! bash scripts/check-skill-promotion-readiness.sh "$proposal_file"; then
    echo "Promotion BLOCKED by evidence_class gate (need >=3 independently_replayed entries per affected rule + critical scenarios)."
    exit 1
  fi
fi

mkdir -p "$snapshot_dir"
cp SKILL.md "${snapshot_dir}/SKILL.md"
cp -R agents "${snapshot_dir}/agents"
cp -R references "${snapshot_dir}/references"
cp -R scripts "${snapshot_dir}/scripts"

# 用 ruby JSON.pretty_generate 安全写入 metadata
ruby -rjson -e '
  data = {
    "version" => ARGV[0],
    "promoted_at" => Time.now.strftime("%Y-%m-%dT%H:%M:%S%z"),
    "source" => ARGV[1]
  }
  File.write(ARGV[2], JSON.pretty_generate(data) + "\n")
' "$new_version" "$source_ref" "${history_dir}/metadata.json"

# 用 ruby JSON.pretty_generate 安全写入 active_version
ruby -rjson -e '
  data = {
    "active_version" => ARGV[0],
    "status" => "active",
    "promoted_at" => Time.now.strftime("%Y-%m-%dT%H:%M:%S%z"),
    "source" => ARGV[1],
    "notes" => "Promoted after passing base evolution validation."
  }
  File.write("evolution/active_version.json", JSON.pretty_generate(data) + "\n")
' "$new_version" "$source_ref"

if [ -n "$proposal_file" ]; then
  bash scripts/update-skill-proposal-status.sh "$proposal_file" promoted >/dev/null
fi

if [ "${SKIP_EVOLUTION_GC:-0}" != "1" ]; then
  # Dry-run first to surface deletion count before committing
  gc_dry="$(bash scripts/gc-evolution-history.sh --dry-run 2>/dev/null)" || true
  delete_count="$(echo "$gc_dry" | grep -c '\[DELETE\]' || true)"
  if [ "${delete_count:-0}" -gt 0 ]; then
    echo "Note: GC will remove ${delete_count} old history snapshot(s). Set SKIP_EVOLUTION_GC=1 before this script to skip GC." >&2
  fi
  if ! bash scripts/gc-evolution-history.sh; then
    echo "Warning: evolution history GC failed; promotion already completed. Run scripts/gc-evolution-history.sh manually." >&2
  fi
fi

echo "Promoted ${new_version}"
