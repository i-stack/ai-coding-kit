#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

LEDGER_FILE="evolution/usage/usage.jsonl"
RULE_INDEX_FILE="references/rule_index.md"

if [ ! -f "$LEDGER_FILE" ]; then
  echo "Usage ledger missing (treated as empty): ${LEDGER_FILE}"
  exit 0
fi

if [ ! -f "$RULE_INDEX_FILE" ]; then
  echo "Missing rule index: ${RULE_INDEX_FILE}"
  exit 1
fi

ruby <<'RUBY'
require "json"
require "set"

ledger_path = "evolution/usage/usage.jsonl"
index_path = "references/rule_index.md"

ALLOWED_TOOLS = %w[codex claude-code cursor manual other].to_set.freeze
ALLOWED_TASK_TYPES = %w[layout parameter-pass-through concurrency review migration mcp-control other].to_set.freeze
ALLOWED_OUTCOMES = %w[pass partial fail].to_set.freeze
ALLOWED_SIGNALS = ["none", "修正表达", "新增能力", "合并重复", "退役规则"].to_set.freeze
ID_FORMAT = /\A[A-Z]+-\d{3}\z/
TIME_FORMAT = /\A\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}([+-]\d{4}|Z)\z/

REQUIRED_FIELDS = %w[
  time tool session_id prompt_summary task_type
  expected_rules hit_rules missed_rules deviations
  outcome evolution_signal
].freeze

active_ids = Set.new
File.foreach(index_path) do |line|
  m = line.match(/\A\|\s*([A-Z]+-\d{3})\s*\|\s*active\s*\|/)
  active_ids << m[1] if m
end

violations = []
total_lines = 0

File.foreach(ledger_path).with_index(1) do |raw, lineno|
  raw = raw.strip
  next if raw.empty?
  total_lines += 1

  begin
    entry = JSON.parse(raw)
  rescue JSON::ParserError => e
    violations << "line #{lineno}: invalid JSON — #{e.message}"
    next
  end

  unless entry.is_a?(Hash)
    violations << "line #{lineno}: must be a JSON object"
    next
  end

  REQUIRED_FIELDS.each do |f|
    unless entry.key?(f)
      violations << "line #{lineno}: missing required field '#{f}'"
    end
  end
  next if REQUIRED_FIELDS.any? { |f| !entry.key?(f) }

  # time
  unless entry["time"].is_a?(String) && entry["time"] =~ TIME_FORMAT
    violations << "line #{lineno}: time '#{entry['time']}' must match ISO8601 with TZ"
  end

  # tool
  unless ALLOWED_TOOLS.include?(entry["tool"])
    violations << "line #{lineno}: tool '#{entry['tool']}' not in #{ALLOWED_TOOLS.to_a.inspect}"
  end

  # session_id
  unless entry["session_id"].nil? || entry["session_id"].is_a?(String)
    violations << "line #{lineno}: session_id must be string or null"
  end

  # prompt_summary
  ps = entry["prompt_summary"]
  if !ps.is_a?(String)
    violations << "line #{lineno}: prompt_summary must be a string"
  elsif !ps.length.between?(5, 200)
    violations << "line #{lineno}: prompt_summary length must be 5-200 chars (got #{ps.length})"
  end

  # task_type
  unless ALLOWED_TASK_TYPES.include?(entry["task_type"])
    violations << "line #{lineno}: task_type '#{entry['task_type']}' not in #{ALLOWED_TASK_TYPES.to_a.inspect}"
  end

  # expected_rules / hit_rules — arrays of active rule_ids
  %w[expected_rules hit_rules].each do |field|
    arr = entry[field]
    unless arr.is_a?(Array)
      violations << "line #{lineno}: #{field} must be an array"
      next
    end
    arr.each do |rid|
      unless rid.is_a?(String) && rid =~ ID_FORMAT
        violations << "line #{lineno}: #{field} entry '#{rid.inspect}' must match ^[A-Z]+-\\d{3}$"
        next
      end
      unless active_ids.include?(rid)
        violations << "line #{lineno}: #{field} entry '#{rid}' not in rule_index.md active set"
      end
    end
  end

  # missed_rules consistency
  expected = entry["expected_rules"]
  hit = entry["hit_rules"]
  missed = entry["missed_rules"]
  if expected.is_a?(Array) && hit.is_a?(Array) && missed.is_a?(Array)
    expected_diff = expected.reject { |r| hit.include?(r) }
    if missed.sort != expected_diff.sort
      violations << "line #{lineno}: missed_rules #{missed.inspect} != expected_rules - hit_rules #{expected_diff.inspect}"
    end
  end

  # deviations
  deviations = entry["deviations"]
  unless deviations.is_a?(Array) && deviations.all? { |d| d.is_a?(String) }
    violations << "line #{lineno}: deviations must be array of strings"
  end

  # outcome
  unless ALLOWED_OUTCOMES.include?(entry["outcome"])
    violations << "line #{lineno}: outcome '#{entry['outcome']}' not in #{ALLOWED_OUTCOMES.to_a.inspect}"
  end

  # evolution_signal
  unless ALLOWED_SIGNALS.include?(entry["evolution_signal"])
    violations << "line #{lineno}: evolution_signal '#{entry['evolution_signal']}' not in #{ALLOWED_SIGNALS.to_a.inspect}"
  end
end

if violations.empty?
  puts "Usage ledger OK (#{total_lines} entries, #{active_ids.length} active rule IDs)"
  exit 0
else
  puts "Usage ledger validation failed:"
  violations.each { |v| puts "  - #{v}" }
  exit 1
end
RUBY
