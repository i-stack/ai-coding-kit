#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

if [ $# -lt 2 ]; then
  echo "Usage: bash scripts/approve_skill_promotion.sh <proposal-file> <approved-by>"
  echo 'Example: bash scripts/approve_skill_promotion.sh evolution/proposals/20260403-fix.md "approved-by-user"'
  exit 1
fi

proposal_file="$1"
approved_by="$2"

# 字段白名单校验
if [[ ! "$proposal_file" =~ ^evolution/proposals/[0-9]{8}-[0-9]{6}-[A-Za-z0-9_-]+\.md$ ]]; then
  echo "Invalid proposal_file format: ${proposal_file}"
  exit 1
fi

if [ ! -f "$proposal_file" ]; then
  echo "Missing proposal file: ${proposal_file}"
  exit 1
fi

if [[ ! "$approved_by" =~ ^[A-Za-z0-9_@.-]{1,100}$ ]]; then
  echo "Invalid approved_by format (expected ^[A-Za-z0-9_@.-]{1,100}$): ${approved_by}"
  exit 1
fi

proposal_id="$(basename "$proposal_file" .md)"
record_file="evolution/validations/${proposal_id}.json"
approval_file="evolution/approvals/${proposal_id}.json"

if [ ! -f "$record_file" ]; then
  echo "Missing validation record: ${record_file}"
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

if [ "$proposal_status" != "ready_to_promote" ]; then
  echo "Proposal is not ready_to_promote: ${proposal_status}"
  exit 1
fi

# 用 ruby JSON.pretty_generate 安全写入
ruby -rjson -e '
  data = {
    "proposal_id" => ARGV[0],
    "proposal_file" => ARGV[1],
    "approved_at" => Time.now.strftime("%Y-%m-%dT%H:%M:%S%z"),
    "approved_by" => ARGV[2],
    "status" => "approved"
  }
  File.write(ARGV[3], JSON.pretty_generate(data) + "\n")
' "$proposal_id" "$proposal_file" "$approved_by" "$approval_file"

bash scripts/update_skill_proposal_status.sh "$proposal_file" approved >/dev/null
cat "$approval_file"
