#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

LEDGER_FILE="evolution/usage/usage.jsonl"
LOCK_DIR="evolution/usage/usage.jsonl.lock"
RULE_INDEX_FILE="references/rule_index.md"

usage() {
  cat <<'USAGE'
Usage: bash scripts/append_usage_entry.sh \
  --tool <codex|claude-code|cursor|manual|other> \
  --task-type <layout|parameter-pass-through|concurrency|review|migration|mcp-control|other> \
  --prompt-summary "<5-200 char Chinese summary>" \
  --expected-rules "ID1,ID2,..." \
  --hit-rules "ID1,..." \
  [--deviations "txt1;txt2;..."] \
  [--outcome <pass|partial|fail>] \
  [--evolution-signal <none|修正表达|新增能力|合并重复|退役规则>] \
  [--session-id <id>]
USAGE
  exit 1
}

tool=""
task_type=""
prompt_summary=""
expected_rules_raw=""
hit_rules_raw=""
deviations_raw=""
outcome="pass"
evolution_signal="none"
session_id=""

while [ $# -gt 0 ]; do
  case "$1" in
    --tool) tool="$2"; shift 2 ;;
    --task-type) task_type="$2"; shift 2 ;;
    --prompt-summary) prompt_summary="$2"; shift 2 ;;
    --expected-rules) expected_rules_raw="$2"; shift 2 ;;
    --hit-rules) hit_rules_raw="$2"; shift 2 ;;
    --deviations) deviations_raw="$2"; shift 2 ;;
    --outcome) outcome="$2"; shift 2 ;;
    --evolution-signal) evolution_signal="$2"; shift 2 ;;
    --session-id) session_id="$2"; shift 2 ;;
    -h|--help) usage ;;
    *) echo "Unknown arg: $1"; usage ;;
  esac
done

if [ -z "$tool" ] || [ -z "$task_type" ] || [ -z "$prompt_summary" ] || [ -z "$expected_rules_raw" ] || [ -z "$hit_rules_raw" ]; then
  echo "Missing required argument."
  usage
fi

mkdir -p "$(dirname "$LEDGER_FILE")"
[ -f "$LEDGER_FILE" ] || : > "$LEDGER_FILE"

for _ in 1 2 3 4 5 6 7 8 9 10; do
  if mkdir "$LOCK_DIR" 2>/dev/null; then
    break
  fi
  sleep 0.1
done

if [ ! -d "$LOCK_DIR" ]; then
  echo "Failed to acquire ledger lock: ${LOCK_DIR}"
  exit 1
fi

cleanup() { rmdir "$LOCK_DIR" 2>/dev/null || true; }
trap cleanup EXIT

now="$(date '+%Y-%m-%dT%H:%M:%S%z')"

ruby -rjson - "$tool" "$task_type" "$prompt_summary" "$expected_rules_raw" "$hit_rules_raw" "$deviations_raw" "$outcome" "$evolution_signal" "$session_id" "$now" "$RULE_INDEX_FILE" "$LEDGER_FILE" <<'RUBY'
tool, task_type, prompt_summary, expected_raw, hit_raw, deviations_raw,
outcome, evolution_signal, session_id, now, rule_index_path, ledger_path = ARGV

ALLOWED_TOOLS = %w[codex claude-code cursor manual other].freeze
ALLOWED_TASK_TYPES = %w[layout parameter-pass-through concurrency review migration mcp-control other].freeze
ALLOWED_OUTCOMES = %w[pass partial fail].freeze
ALLOWED_SIGNALS = ["none", "修正表达", "新增能力", "合并重复", "退役规则"].freeze
ID_FORMAT = /\A[A-Z]+-\d{3}\z/

errors = []

errors << "tool '#{tool}' not in #{ALLOWED_TOOLS.inspect}" unless ALLOWED_TOOLS.include?(tool)
errors << "task_type '#{task_type}' not in #{ALLOWED_TASK_TYPES.inspect}" unless ALLOWED_TASK_TYPES.include?(task_type)
errors << "outcome '#{outcome}' not in #{ALLOWED_OUTCOMES.inspect}" unless ALLOWED_OUTCOMES.include?(outcome)
errors << "evolution_signal '#{evolution_signal}' not in #{ALLOWED_SIGNALS.inspect}" unless ALLOWED_SIGNALS.include?(evolution_signal)

# prompt_summary length 5-200 (chars, not bytes)
ps_len = prompt_summary.length
errors << "prompt_summary length must be 5-200 chars (got #{ps_len})" unless ps_len.between?(5, 200)

# Active rule_id set from rule_index.md
active_ids = []
File.foreach(rule_index_path) do |line|
  m = line.match(/\A\|\s*([A-Z]+-\d{3})\s*\|\s*active\s*\|/)
  active_ids << m[1] if m
end
active_set = active_ids.to_set rescue active_ids

split = ->(raw) { raw.split(",").map(&:strip).reject(&:empty?) }

expected_rules = split.call(expected_raw)
hit_rules = split.call(hit_raw)
deviations = deviations_raw.split(";").map(&:strip).reject(&:empty?)

(expected_rules + hit_rules).each do |rid|
  errors << "rule_id '#{rid}' violates format ^[A-Z]+-\\d{3}$" unless rid =~ ID_FORMAT
  next unless rid =~ ID_FORMAT
  unless active_ids.include?(rid)
    errors << "rule_id '#{rid}' not in rule_index.md active set"
  end
end

unless errors.empty?
  warn "append_usage_entry validation failed:"
  errors.each { |e| warn "  - #{e}" }
  exit 1
end

# Compute missed_rules = expected - hit (preserve expected order)
hit_set = hit_rules.to_set rescue hit_rules
missed_rules = expected_rules.reject { |r| hit_rules.include?(r) }

entry = {
  "time" => now,
  "tool" => tool,
  "session_id" => session_id.empty? ? nil : session_id,
  "prompt_summary" => prompt_summary,
  "task_type" => task_type,
  "expected_rules" => expected_rules,
  "hit_rules" => hit_rules,
  "missed_rules" => missed_rules,
  "deviations" => deviations,
  "outcome" => outcome,
  "evolution_signal" => evolution_signal
}

line = JSON.generate(entry)
File.open(ledger_path, "a") { |f| f.puts(line) }
puts line
RUBY
