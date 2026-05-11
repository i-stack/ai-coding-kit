#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

if [ $# -lt 1 ]; then
  echo "Usage: bash scripts/extract_usage_audit.sh <transcript-file>"
  echo "Parses all <usage-audit>...</usage-audit> blocks and appends them to evolution/usage/usage.jsonl."
  echo "Atomic: any block invalid -> entire batch rejected, ledger untouched."
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

cleanup() { rmdir "$LOCK_DIR" 2>/dev/null || true; }
trap cleanup EXIT

ruby -rjson - "$input" "$LEDGER_FILE" <<'RUBY'
require "set"

input_path, ledger_path = ARGV
text = File.read(input_path)
index_path = "references/rule_index.md"

ALLOWED_TOOLS = %w[codex claude-code cursor manual other].to_set.freeze
ALLOWED_TASK_TYPES = %w[layout parameter-pass-through concurrency review migration mcp-control other].to_set.freeze
ALLOWED_OUTCOMES = %w[pass partial fail].to_set.freeze
ALLOWED_SIGNALS = ["none", "修正表达", "新增能力", "合并重复", "退役规则"].to_set.freeze
ID_FORMAT = /\A[A-Z]+-\d{3}\z/

active_ids = Set.new
File.foreach(index_path) do |line|
  m = line.match(/\A\|\s*([A-Z]+-\d{3})\s*\|\s*active\s*\|/)
  active_ids << m[1] if m
end

blocks = text.scan(/<usage-audit>(.*?)<\/usage-audit>/m).map { |m| m[0] }

if blocks.empty?
  puts "No <usage-audit> blocks found in #{input_path}"
  exit 0
end

REQUIRED_KEYS = %w[tool task-type prompt-summary expected-rules hit-rules outcome evolution-signal].freeze

errors = []
parsed = []

blocks.each_with_index do |body, idx|
  block_no = idx + 1
  data = {}
  body.each_line do |raw_line|
    line = raw_line.strip
    next if line.empty?
    if (m = line.match(/\A([a-z][a-z-]*):\s*(.*)\z/))
      data[m[1]] = m[2]
    else
      errors << "block #{block_no}: line '#{line}' does not match 'key: value'"
    end
  end

  REQUIRED_KEYS.each do |k|
    errors << "block #{block_no}: missing key '#{k}'" unless data.key?(k)
  end
  next if REQUIRED_KEYS.any? { |k| !data.key?(k) }

  errors << "block #{block_no}: tool '#{data['tool']}' not in #{ALLOWED_TOOLS.to_a.inspect}" unless ALLOWED_TOOLS.include?(data["tool"])
  errors << "block #{block_no}: task-type '#{data['task-type']}' not in #{ALLOWED_TASK_TYPES.to_a.inspect}" unless ALLOWED_TASK_TYPES.include?(data["task-type"])
  errors << "block #{block_no}: outcome '#{data['outcome']}' not in #{ALLOWED_OUTCOMES.to_a.inspect}" unless ALLOWED_OUTCOMES.include?(data["outcome"])
  errors << "block #{block_no}: evolution-signal '#{data['evolution-signal']}' not in #{ALLOWED_SIGNALS.to_a.inspect}" unless ALLOWED_SIGNALS.include?(data["evolution-signal"])

  ps = data["prompt-summary"]
  unless ps.length.between?(5, 200)
    errors << "block #{block_no}: prompt-summary length must be 5-200 chars (got #{ps.length})"
  end

  expected = data["expected-rules"].split(",").map(&:strip).reject(&:empty?)
  hit = data["hit-rules"].split(",").map(&:strip).reject(&:empty?)
  (expected + hit).each do |rid|
    unless rid =~ ID_FORMAT
      errors << "block #{block_no}: rule_id '#{rid}' violates format"
      next
    end
    unless active_ids.include?(rid)
      errors << "block #{block_no}: rule_id '#{rid}' not in rule_index.md active set"
    end
  end

  deviations = (data["deviations"] || "").split(";").map(&:strip).reject(&:empty?)
  session_id_raw = data["session-id"]
  session_id = (session_id_raw.nil? || session_id_raw.strip.empty?) ? nil : session_id_raw.strip

  parsed << {
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
end

unless errors.empty?
  warn "Extract failed; ledger NOT modified:"
  errors.each { |e| warn "  - #{e}" }
  exit 1
end

now = Time.now.strftime("%Y-%m-%dT%H:%M:%S%z")

File.open(ledger_path, "a") do |f|
  parsed.each do |entry|
    f.puts(JSON.generate({ "time" => now }.merge(entry)))
  end
end

puts "Appended #{parsed.length} entries to #{ledger_path}"
RUBY
