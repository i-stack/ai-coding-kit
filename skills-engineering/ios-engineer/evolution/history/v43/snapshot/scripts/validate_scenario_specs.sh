#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

SCENARIO_DIR="evolution/scenarios"

if [ ! -d "$SCENARIO_DIR" ]; then
  echo "Missing scenarios directory: ${SCENARIO_DIR}"
  exit 1
fi

ruby <<'RUBY'
require "json"
require "set"

scenario_dir = "evolution/scenarios"

# Canonical slug set; mirrors references/validation_scenarios.md "建议使用固定场景标识".
CANONICAL_SLUGS = %w[
  layout
  parameter-pass-through
  concurrency
  review
  migration
  mcp-control
].freeze

OUTPUT_CONTRACTS = %w[four-segment findings-first free].freeze

REQUIRED_FIELDS = %w[
  id
  version
  category
  input
  primary_refs
  output_contract
  expected_hits
  failure_signals
  scoring
].freeze

violations = []
seen_ids = Set.new

files = Dir.glob(File.join(scenario_dir, "*.json")).sort

if files.empty?
  violations << "No scenario specs found under #{scenario_dir}"
end

files.each do |file|
  basename = File.basename(file, ".json")
  begin
    data = JSON.parse(File.read(file))
  rescue JSON::ParserError => e
    violations << "#{file}: invalid JSON — #{e.message}"
    next
  end

  REQUIRED_FIELDS.each do |field|
    unless data.key?(field)
      violations << "#{file}: missing required field '#{field}'"
    end
  end

  id = data["id"]
  if id.nil? || id.to_s.empty?
    violations << "#{file}: empty id"
  else
    if id != basename
      violations << "#{file}: id '#{id}' does not match filename '#{basename}'"
    end
    unless CANONICAL_SLUGS.include?(id)
      violations << "#{file}: id '#{id}' not in canonical slug set #{CANONICAL_SLUGS.inspect}"
    end
    if seen_ids.include?(id)
      violations << "#{file}: duplicate id '#{id}'"
    else
      seen_ids << id
    end
  end

  if data["version"] != 1
    violations << "#{file}: unsupported version #{data['version'].inspect} (expected 1)"
  end

  input = data["input"]
  if !input.is_a?(String) || input.strip.empty?
    violations << "#{file}: input must be a non-empty string"
  end

  primary_refs = data["primary_refs"]
  if !primary_refs.is_a?(Array) || primary_refs.empty?
    violations << "#{file}: primary_refs must be a non-empty array"
  else
    primary_refs.each do |path|
      unless path.is_a?(String) && File.exist?(path)
        violations << "#{file}: primary_refs entry '#{path}' does not exist"
      end
    end
  end

  contract = data["output_contract"]
  unless OUTPUT_CONTRACTS.include?(contract)
    violations << "#{file}: output_contract '#{contract}' not in #{OUTPUT_CONTRACTS.inspect}"
  end

  hit_keys = []
  expected_hits = data["expected_hits"]
  if !expected_hits.is_a?(Array) || expected_hits.empty?
    violations << "#{file}: expected_hits must be a non-empty array"
  else
    expected_hits.each_with_index do |entry, idx|
      unless entry.is_a?(Hash)
        violations << "#{file}: expected_hits[#{idx}] must be an object"
        next
      end
      key = entry["key"]
      desc = entry["desc"]
      if !key.is_a?(String) || key !~ /\A[a-z0-9][a-z0-9-]*\z/
        violations << "#{file}: expected_hits[#{idx}].key '#{key}' must be lowercase kebab-case"
      else
        hit_keys << key
      end
      if !desc.is_a?(String) || desc.strip.empty?
        violations << "#{file}: expected_hits[#{idx}].desc must be a non-empty string"
      end
    end
  end

  signal_keys = []
  failure_signals = data["failure_signals"]
  if !failure_signals.is_a?(Array) || failure_signals.empty?
    violations << "#{file}: failure_signals must be a non-empty array"
  else
    failure_signals.each_with_index do |entry, idx|
      unless entry.is_a?(Hash)
        violations << "#{file}: failure_signals[#{idx}] must be an object"
        next
      end
      key = entry["key"]
      desc = entry["desc"]
      if !key.is_a?(String) || key !~ /\A[a-z0-9][a-z0-9-]*\z/
        violations << "#{file}: failure_signals[#{idx}].key '#{key}' must be lowercase kebab-case"
      else
        signal_keys << key
      end
      if !desc.is_a?(String) || desc.strip.empty?
        violations << "#{file}: failure_signals[#{idx}].desc must be a non-empty string"
      end
    end
  end

  combined = hit_keys + signal_keys
  if combined.uniq.length != combined.length
    dupes = combined.group_by { |k| k }.select { |_, v| v.length > 1 }.keys
    violations << "#{file}: duplicate key(s) across expected_hits and failure_signals: #{dupes.join(', ')}"
  end

  scoring = data["scoring"]
  if !scoring.is_a?(Hash)
    violations << "#{file}: scoring must be an object"
  else
    %w[pass partial fail].each do |bucket|
      unless scoring[bucket].is_a?(String) && !scoring[bucket].strip.empty?
        violations << "#{file}: scoring.#{bucket} must be a non-empty string"
      end
    end
  end
end

missing_slugs = CANONICAL_SLUGS - seen_ids.to_a
unless missing_slugs.empty?
  violations << "Missing scenario specs for canonical slugs: #{missing_slugs.join(', ')}"
end

if violations.empty?
  puts "Scenario specs OK (#{files.length} files, #{seen_ids.length} canonical slugs covered)"
  exit 0
else
  puts "Scenario spec validation failed:"
  violations.each { |v| puts "  - #{v}" }
  exit 1
end
RUBY
