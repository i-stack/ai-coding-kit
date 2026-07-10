#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

if [ $# -lt 1 ]; then
  echo "Usage: bash scripts/extract_usage_audit.sh <transcript-file>"
  echo "Parses all <usage-audit>...</usage-audit> blocks and appends them to evolution/usage/usage.jsonl."
  echo "Resilient: valid blocks are written; any invalid block is skipped with a warning (ledger never poisoned)."
  exit 1
fi

input="$1"

if [ ! -f "$input" ]; then
  echo "Input file not found: ${input}"
  exit 1
fi

LEDGER_FILE="evolution/usage/usage.jsonl"
LOCK_DIR="evolution/usage/usage.jsonl.lock"
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

cleanup() {
  rmdir "$LOCK_DIR" 2>/dev/null || true
}
trap cleanup EXIT

ruby -rjson - "$input" "$LEDGER_FILE" <<'RUBY'
input_path, ledger_path = ARGV
text = File.read(input_path)
index_path = "references/rule_index.md"

ALLOWED_TOOLS = %w[codex claude-code cursor manual other].freeze
ALLOWED_TASK_TYPES = %w[layout parameter-pass-through concurrency review migration mcp-control notifications privacy persistence storekit extensions other].freeze
ALLOWED_OUTCOMES = %w[pass partial fail].freeze
ALLOWED_SIGNALS = ["none", "修正表达", "新增能力", "合并重复", "退役规则"].freeze
ID_FORMAT = /\A[A-Z]+-\d{3}\z/

active_ids = []
File.foreach(index_path) do |line|
  match = line.match(/\A\|\s*([A-Z]+-\d{3})\s*\|\s*active\s*\|/)
  active_ids << match[1] if match
end

blocks = text.scan(/<usage-audit>(.*?)<\/usage-audit>/m).map { |m| m[0] }

if blocks.empty?
  puts "No <usage-audit> blocks found in #{input_path}"
  exit 0
end

REQUIRED_KEYS = %w[tool task-type prompt-summary expected-rules hit-rules outcome evolution-signal].freeze

valid = []
skipped = []  # [block_no, reason]

blocks.each_with_index do |body, idx|
  block_no = idx + 1
  errs = []
  data = {}
  body.each_line do |raw_line|
    line = raw_line.strip
    next if line.empty?
    if (m = line.match(/\A([a-z][a-z-]*):\s*(.*)\z/))
      data[m[1]] = m[2]
    else
      errs << "line '#{line}' does not match 'key: value'"
    end
  end

  REQUIRED_KEYS.each do |k|
    errs << "missing key '#{k}'" unless data.key?(k)
  end
  if REQUIRED_KEYS.any? { |k| !data.key?(k) }
    skipped << [block_no, errs.join("; ")]
    next
  end

  errs << "tool '#{data['tool']}' not in #{ALLOWED_TOOLS.inspect}" unless ALLOWED_TOOLS.include?(data["tool"])
  errs << "task-type '#{data['task-type']}' not in #{ALLOWED_TASK_TYPES.inspect}" unless ALLOWED_TASK_TYPES.include?(data["task-type"])
  errs << "outcome '#{data['outcome']}' not in #{ALLOWED_OUTCOMES.inspect}" unless ALLOWED_OUTCOMES.include?(data["outcome"])
  errs << "evolution-signal '#{data['evolution-signal']}' not in #{ALLOWED_SIGNALS.inspect}" unless ALLOWED_SIGNALS.include?(data["evolution-signal"])

  ps = data["prompt-summary"]
  unless ps.length.between?(5, 200)
    errs << "prompt-summary length must be 5-200 chars (got #{ps.length})"
  end

  expected = data["expected-rules"].split(",").map(&:strip).reject(&:empty?)
  hit = data["hit-rules"].split(",").map(&:strip).reject(&:empty?)
  (expected + hit).each do |rid|
    unless rid =~ ID_FORMAT
      errs << "rule_id '#{rid}' violates format"
      next
    end
    unless active_ids.include?(rid)
      errs << "rule_id '#{rid}' not in rule_index.md active set"
    end
  end

  if errs.empty?
    deviations = (data["deviations"] || "").split(";").map(&:strip).reject(&:empty?)
    session_id_raw = data["session-id"]
    session_id = (session_id_raw.nil? || session_id_raw.strip.empty?) ? nil : session_id_raw.strip

    valid << {
      "tool" => data["tool"],
      "session_id" => session_id,
      "prompt_summary" => ps,
      "task_type" => data["task-type"],
      "expected_rules" => expected,
      "hit_rules" => hit,
      "missed_rules" => expected.reject { |r| hit.include?(r) },
      "deviations" => deviations,
      "outcome" => data["outcome"],
      "evolution_signal" => data["evolution-signal"]
    }
  else
    skipped << [block_no, errs.join("; ")]
  end
end

now = Time.now.strftime("%Y-%m-%dT%H:%M:%S%z")

if valid.empty?
  if skipped.empty?
    puts "No <usage-audit> blocks found in #{input_path}"
  else
    warn "Skipped #{skipped.length} invalid block(s); ledger NOT modified:"
    skipped.each { |bno, reason| warn "  - block #{bno}: #{reason}" }
  end
  # Exit 0 even with only-skipped blocks so the caller (ledger-sync) can
  # advance its transcript offset instead of retrying the same bad block forever.
  exit 0
end

File.open(ledger_path, "a") do |f|
  valid.each do |entry|
    f.puts(JSON.generate({ "time" => now }.merge(entry)))
  end
end

if skipped.empty?
  puts "Appended #{valid.length} entries to #{ledger_path}"
else
  warn "Appended #{valid.length} valid entr(y/ies); skipped #{skipped.length} invalid block(s):"
  skipped.each { |bno, reason| warn "  - block #{bno}: #{reason}" }
end
RUBY
