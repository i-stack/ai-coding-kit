#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

INDEX_FILE="references/rule_index.md"
SKILL_FILE="SKILL.md"

if [ ! -f "$INDEX_FILE" ]; then
  echo "Missing rule index: ${INDEX_FILE}"
  exit 1
fi

if [ ! -f "$SKILL_FILE" ]; then
  echo "Missing skill file: ${SKILL_FILE}"
  exit 1
fi

ruby <<'RUBY'
require "json"

skill_file = "SKILL.md"
index_file = "references/rule_index.md"
scenario_dir = "evolution/scenarios"

ID_FORMAT = /\A[A-Z]+-\d{3}\z/
ALLOWED_STATUS = %w[active retired deprecated].freeze

violations = []

# ---- Parse SKILL.md inline IDs ----
skill_ids = []
File.foreach(skill_file).with_index(1) do |line, lineno|
  line.scan(/\[([A-Z]+-\d{3})\]/).each do |match|
    skill_ids << { id: match[0], line: lineno }
  end
end

skill_id_set = skill_ids.map { |e| e[:id] }
skill_id_uniq = skill_id_set.uniq

if skill_id_set.length != skill_id_uniq.length
  dupes = skill_id_set.group_by { |id| id }.select { |_, v| v.length > 1 }
  dupes.each do |id, occurrences|
    locs = skill_ids.select { |e| e[:id] == id }.map { |e| "line #{e[:line]}" }.join(", ")
    violations << "#{skill_file}: duplicate ID #{id} (#{locs})"
  end
end

skill_id_set = skill_id_uniq.to_set rescue skill_id_uniq

skill_id_uniq.each do |id|
  unless id =~ ID_FORMAT
    violations << "#{skill_file}: ID '#{id}' violates format ^[A-Z]+-\\d{3}$"
  end
end

# ---- Parse rule_index.md table rows ----
# Match table rows whose first cell is an ID-shaped token, second cell is status.
# Format: |  ID  |  status  |  ...
index_entries = []
File.foreach(index_file).with_index(1) do |line, lineno|
  m = line.match(/\A\|\s*([A-Z]+-\d{3})\s*\|\s*([A-Za-z][A-Za-z0-9-]*)\s*\|/)
  next unless m
  index_entries << { id: m[1], status: m[2], line: lineno }
end

if index_entries.empty?
  violations << "#{index_file}: no rule rows parsed (expected '| ID | status | ... |')"
end

index_id_set = index_entries.map { |e| e[:id] }
index_id_uniq = index_id_set.uniq

if index_id_set.length != index_id_uniq.length
  dupes = index_id_set.group_by { |id| id }.select { |_, v| v.length > 1 }
  dupes.each do |id, _|
    locs = index_entries.select { |e| e[:id] == id }.map { |e| "line #{e[:line]}" }.join(", ")
    violations << "#{index_file}: duplicate ID #{id} (#{locs})"
  end
end

# ---- Status enum check ----
index_entries.each do |entry|
  unless ALLOWED_STATUS.include?(entry[:status])
    violations << "#{index_file}:#{entry[:line]}: status '#{entry[:status]}' not in #{ALLOWED_STATUS.inspect}"
  end
end

# ---- Bidirectional set equality ----
skill_set = skill_id_uniq.sort
index_set = index_id_uniq.sort

missing_in_index = skill_set - index_set
missing_in_skill = index_set - skill_set

missing_in_index.each do |id|
  violations << "Mismatch: SKILL.md has '#{id}' but rule_index.md does not"
end

missing_in_skill.each do |id|
  status = index_entries.find { |e| e[:id] == id }&.dig(:status)
  if status == "retired" || status == "deprecated"
    # Retired IDs are expected to be absent from SKILL.md — skip.
    next
  end
  violations << "Mismatch: rule_index.md has '#{id}' (status=#{status || 'unknown'}) but SKILL.md does not"
end

# ---- Retired IDs must NOT appear in SKILL.md ----
retired_ids = index_entries.select { |e| %w[retired deprecated].include?(e[:status]) }.map { |e| e[:id] }
retired_ids.each do |id|
  if skill_id_uniq.include?(id)
    violations << "Retired/deprecated ID '#{id}' still present in SKILL.md — remove inline reference"
  end
end

# ---- Scenario rule_id references ----
active_ids = index_entries.select { |e| e[:status] == "active" }.map { |e| e[:id] }.to_set
all_index_ids = index_id_uniq.to_set

if Dir.exist?(scenario_dir)
  Dir.glob(File.join(scenario_dir, "*.json")).sort.each do |file|
    begin
      data = JSON.parse(File.read(file))
    rescue JSON::ParserError
      # Spec validator handles parse errors; skip here.
      next
    end

    %w[expected_hits failure_signals].each do |section|
      entries = data[section]
      next unless entries.is_a?(Array)
      entries.each_with_index do |entry, idx|
        next unless entry.is_a?(Hash) && entry.key?("rule_id")
        rid = entry["rule_id"]
        unless rid.is_a?(String) && rid =~ ID_FORMAT
          violations << "#{file}: #{section}[#{idx}].rule_id '#{rid.inspect}' violates format"
          next
        end
        unless all_index_ids.include?(rid)
          violations << "#{file}: #{section}[#{idx}].rule_id '#{rid}' not found in rule_index.md"
          next
        end
        unless active_ids.include?(rid)
          violations << "#{file}: #{section}[#{idx}].rule_id '#{rid}' references retired/deprecated rule"
        end
      end
    end
  end
end

if violations.empty?
  puts "Rule IDs OK (#{skill_id_uniq.length} IDs in SKILL.md, #{index_id_uniq.length} in rule_index.md, #{active_ids.length} active)"
  exit 0
else
  puts "Rule ID validation failed:"
  violations.each { |v| puts "  - #{v}" }
  exit 1
end
RUBY
