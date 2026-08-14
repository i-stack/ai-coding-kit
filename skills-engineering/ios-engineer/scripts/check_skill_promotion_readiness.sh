#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

if [ $# -lt 1 ]; then
  echo "Usage: bash scripts/check_skill_promotion_readiness.sh <proposal-file>"
  exit 1
fi

proposal_file="$1"

if [[ ! "$proposal_file" =~ ^evolution/proposals/[0-9]{8}-[0-9]{6}-[A-Za-z0-9_-]+\.md$ ]]; then
  echo "Invalid proposal_file format: ${proposal_file}"
  exit 1
fi

if [ ! -f "$proposal_file" ]; then
  echo "Missing proposal file: ${proposal_file}"
  exit 1
fi

proposal_id="$(basename "$proposal_file" .md)"
record_file="evolution/validations/${proposal_id}.json"
approval_file="evolution/approvals/${proposal_id}.json"

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

approval_status="missing"
if [ -f "$approval_file" ]; then
  approval_status="$(ruby -rjson -e 'print JSON.parse(File.read(ARGV[0]))["status"]' "$approval_file")"
fi

promotion_readiness="unknown"
scenario_status="unknown"
if [ -f "$record_file" ]; then
  readout="$(ruby -rjson -e 'data = JSON.parse(File.read(ARGV[0])); print "#{data["promotion_readiness"]}\n#{data["scenario_validation_status"]}"' "$record_file")"
  promotion_readiness="$(printf '%s' "$readout" | sed -n '1p')"
  scenario_status="$(printf '%s' "$readout" | sed -n '2p')"
fi

cat <<EOF
proposal_status=${proposal_status}
promotion_readiness=${promotion_readiness}
scenario_validation_status=${scenario_status}
approval_status=${approval_status}
EOF

if [ "$proposal_status" = "ready_to_promote" ] && [ "$promotion_readiness" = "ready_to_promote" ] && [ "$approval_status" = "missing" ]; then
  echo "hint=Proposal is ready. To authorize promotion, run: bash scripts/approve_skill_promotion.sh ${proposal_file} \"approved-by-user\""
fi

# --- evidence_class promotion gate (see usage_ledger.md §7b) ---
# A rule may only be promoted on independently_replayed evidence, NOT observed ratio.
# Requirement: each affected rule_id needs >= MIN_INDEPENDENT_REPLAYS independently_replayed
# ledger entries, AND all `critical: true` scenarios for those rules must pass.
MIN_INDEPENDENT_REPLAYS=3
LEDGER_FILE="evolution/usage/usage.jsonl"
SCENARIOS_DIR="evolution/scenarios"
VALIDATIONS_DIR="evolution/validations"

gate_result="$(ruby -rjson - "$proposal_file" "$LEDGER_FILE" "$MIN_INDEPENDENT_REPLAYS" "$SCENARIOS_DIR" "$VALIDATIONS_DIR" <<'RUBY'
require "json"
proposal_file, ledger_file, min_replays_s, scenarios_dir, validations_dir = ARGV
min_replays = min_replays_s.to_i

# 1. parse affected rule_ids from proposal (broad scan; matches inline refs like GR-004)
text = File.read(proposal_file)
rule_ids = text.scan(/[A-Z]{2,4}-\d{3}/).uniq

if rule_ids.empty?
  puts "no_rule_ids"
  exit
end

# 2. count independently_replayed entries per rule_id
replays = Hash.new(0)
if File.exist?(ledger_file)
  File.foreach(ledger_file) do |line|
    line.strip!
    next if line.empty?
    begin
      e = JSON.parse(line)
    rescue JSON::ParserError
      next
    end
    next unless e["evidence_class"] == "independently_replayed"
    (e["hit_rules"] || []).each { |r| replays[r] += 1 }
  end
end

insufficient = rule_ids.select { |r| replays[r] < min_replays }

# 3. critical scenarios: read evolution/scenarios/*.json, find `critical: true`
#    scenarios whose expected_hits[].rule_id intersects affected rules, then verify
#    each such scenario slug has a `pass` result in a validation record.
critical_map = Hash.new { |h, k| h[k] = [] }   # rule_id => [slugs]
if Dir.exist?(scenarios_dir)
  Dir.glob(File.join(scenarios_dir, "*.json")).sort.each do |sf|
    data = JSON.parse(File.read(sf)) rescue next
    next unless data["critical"] == true
    slug = data["id"]
    (data["expected_hits"] || []).each do |h|
      rid = h.is_a?(Hash) ? h["rule_id"] : nil
      critical_map[rid] << slug if rid
    end
  end
end
critical_map.each_value(&:uniq!)

affected_critical_rules = rule_ids & critical_map.keys
critical_scenarios = affected_critical_rules.flat_map { |r| critical_map[r] }.uniq

failed_critical = []
unless critical_scenarios.empty?
  records = []
  if Dir.exist?(validations_dir)
    Dir.glob(File.join(validations_dir, "*.json"))
       .reject { |f| f.end_with?(".lock") }
       .sort_by { |f| File.mtime(f) }
       .each do |vf|
      data = JSON.parse(File.read(vf)) rescue next
      (data["scenario_records"] || []).each { |r| records << r }
    end
  end
  critical_scenarios.each do |slug|
    passed = records.any? { |r| r["scenario"] == slug && r["result"] == "pass" }
    failed_critical << slug unless passed
  end
end

out = ["rule_ids=#{rule_ids.join(',')}"]
out << "replays=#{rule_ids.map { |r| "#{r}:#{replays[r]}" }.join(',')}"
out << "critical_scenarios=#{critical_scenarios.join(',')}"
out << "failed_critical=#{failed_critical.join(',')}"
if insufficient.empty? && failed_critical.empty?
  puts "ready|#{out.join('|')}"
elsif !insufficient.empty?
  puts "blocked|insufficient_independent_replays for #{insufficient.join(',')} (min=#{min_replays})|#{out.join('|')}"
else
  puts "blocked|critical_scenarios_not_passed #{failed_critical.join(',')}|#{out.join('|')}"
end
RUBY
)"

case "$gate_result" in
  no_rule_ids)
    echo "evidence_gate=skip (no rule_ids parsed from proposal)"
    ;;
  ready*)
    echo "evidence_gate=PASS ($gate_result)"
    ;;
  blocked*)
    echo "evidence_gate=FAIL ($gate_result)"
    echo "  -> promotion BLOCKED: observed data may not drive promotion; need independently_replayed evidence AND all critical scenarios passed."
    exit 1
    ;;
esac
