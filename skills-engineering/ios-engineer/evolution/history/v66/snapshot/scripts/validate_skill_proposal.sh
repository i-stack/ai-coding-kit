#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

if [ $# -lt 1 ]; then
  echo "Usage: bash scripts/validate_skill_proposal.sh <proposal-file> [scenario-slug ...]"
  echo "Example: bash scripts/validate_skill_proposal.sh evolution/proposals/20260403-fix.md layout parameter-pass-through"
  exit 1
fi

proposal_file="$1"
shift || true

# 字段白名单校验
if [[ ! "$proposal_file" =~ ^evolution/proposals/[0-9]{8}-[0-9]{6}-[A-Za-z0-9_-]+\.md$ ]]; then
  echo "Invalid proposal_file format: ${proposal_file}"
  exit 1
fi

if [ ! -f "$proposal_file" ]; then
  echo "Missing proposal file: ${proposal_file}"
  exit 1
fi

for slug in "$@"; do
  if [[ ! "$slug" =~ ^[a-z0-9][a-z0-9-]{0,50}$ ]]; then
    echo "Invalid scenario slug format: ${slug}"
    exit 1
  fi
done

proposal_id="$(basename "$proposal_file" .md)"
timestamp="$(date '+%Y-%m-%dT%H:%M:%S%z')"
record_file="evolution/validations/${proposal_id}.json"
tmp_output="$(mktemp)"

set +e
SKIP_SNAPSHOT_CONSISTENCY=1 bash scripts/validate_skill_evolution.sh >"$tmp_output" 2>&1
exit_code=$?
set -e

if [ "$exit_code" -eq 0 ]; then
  status="validated"
else
  status="rejected"
fi

active_version="$(ruby -rjson -e 'print JSON.parse(File.read("evolution/active_version.json"))["active_version"]')"

# 用 ruby JSON.pretty_generate 安全写入全部字段
ruby -rjson - "$proposal_id" "$proposal_file" "$timestamp" "$status" "$exit_code" "$active_version" "$tmp_output" "$record_file" "$@" <<'RUBY'
proposal_id, proposal_file, timestamp, status, exit_code, active_version, tmp_output_path, record_file, *slugs = ARGV

scenario_records = slugs.reject(&:empty?).map do |slug|
  {
    "scenario" => slug,
    "result" => "pending",
    "hits" => [],
    "deviations" => [],
    "improvements" => []
  }
end

scenario_status = scenario_records.empty? ? "not_run" : "pending"
base_validation_output = File.read(tmp_output_path)

data = {
  "proposal_id" => proposal_id,
  "proposal_file" => proposal_file,
  "validated_at" => timestamp,
  "status" => status,
  "exit_code" => exit_code.to_i,
  "active_version" => active_version,
  "base_validation_output" => base_validation_output,
  "promotion_readiness" => "not_ready",
  "scenario_validation_status" => scenario_status,
  "scenario_records" => scenario_records
}

File.write(record_file, JSON.pretty_generate(data) + "\n")
RUBY

rm -f "$tmp_output"

bash scripts/update_skill_proposal_status.sh "$proposal_file" "$status" >/dev/null
cat "$record_file"

if [ "$exit_code" -ne 0 ]; then
  exit "$exit_code"
fi
