#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

echo "[1/14] Validate YAML structure"
ruby -e 'require "yaml"; YAML.load_file("SKILL.md"); YAML.load_file("agents/openai.yaml"); puts "YAML OK"'

echo "[2/14] Validate SKILL.md size"
line_count="$(wc -l < SKILL.md | tr -d ' ')"
if [ "$line_count" -gt 500 ]; then
  echo "SKILL.md too long: ${line_count} lines"
  exit 1
fi
echo "SKILL.md lines: ${line_count}"

echo "[3/14] Validate referenced files exist"
missing=0
while IFS= read -r path; do
  [ -z "$path" ] && continue
  if [ ! -f "$path" ]; then
    echo "Missing reference: $path"
    missing=1
  fi
done < <(rg -o 'references/[A-Za-z0-9_./-]+\.md' SKILL.md | sort -u)

if [ "$missing" -ne 0 ]; then
  exit 1
fi
echo "Reference files OK"

echo "[4/14] Validate layering guardrails"
if rg -q '^## (调用预算|重试与限流|上下文压缩|防循环退出条件|输出要求)$' references/root_cause_enforcement.md; then
  echo "root_cause_enforcement.md should not define MCP control sections"
  exit 1
fi

if rg -q '^## (核心原则|排障标准流程|调用预算|重试与限流|防循环退出条件)$' references/examples.md; then
  echo "examples.md should not define root-cause or MCP control sections"
  exit 1
fi

echo "Layering guardrails OK"

echo "[5/14] Validate internal markdown links"
ruby <<'RUBY'
broken = 0
Dir.glob('references/*.md').sort.each do |file|
  File.foreach(file).with_index(1) do |line, lineno|
    line.scan(/\[([^\]]*)\]\(([^)]+)\)/) do |_text, link|
      next if link =~ /\A(https?|mailto):/i
      path = link.split('#', 2).first.to_s
      next if path.empty?
      full = File.expand_path(path, File.dirname(file))
      unless File.exist?(full)
        puts "Broken link in #{file}:#{lineno} -> #{link} (resolved: #{full})"
        broken += 1
      end
    end
  end
end
exit 1 if broken > 0
RUBY
echo "Internal links OK"

echo "[6/14] Validate scenario specs"
bash scripts/validate-scenario-specs.sh

echo "[7/14] Validate rule IDs"
bash scripts/validate-rule-ids.sh

echo "[8/14] Validate usage ledger"
bash scripts/validate-usage-ledger.sh

echo "[9/14] Validate no orphan references"
ruby <<'RUBY'
referenced = {}
# SKILL.md 直接引用
File.read('SKILL.md').scan(/references\/([A-Za-z0-9_.-]+\.md)/).each do |match|
  referenced[match[0]] = true
end
# references 内部互引
Dir.glob('references/*.md').each do |file|
  File.read(file).scan(/\(([A-Za-z0-9_.-]+\.md)(?:#[^)]*)?\)/).each do |match|
    referenced[match[0]] = true
  end
end

orphans = []
Dir.glob('references/*.md').sort.each do |file|
  name = File.basename(file)
  orphans << file unless referenced[name]
end

unless orphans.empty?
  puts "Orphan references (not referenced by SKILL.md or any other ref):"
  orphans.each { |f| puts "  #{f}" }
  exit 1
end
RUBY
echo "No orphan references"

echo "[10/14] Validate unique ownership + retired word regression"
ruby <<'RUBY'
# pattern => [expected_owner_basename, description]
UNIQUE_OWNERS = {
  /传输错误.*状态码错误.*解码错误.*鉴权错误.*业务错误.*展示错误/m => ['domain_modeling.md', '错误分层 6 层枚举'],
  /Time Profiler[^\n]{0,30}[：:][^\n]*定位[^\n]*CPU/m => ['observability_logging.md', '完整性能取证工具用途定义（Time Profiler: 定位 CPU）'],
  /审查结论[\s\S]{0,300}?严重问题[\s\S]{0,300}?一般问题[\s\S]{0,300}?验证缺口[\s\S]{0,300}?最终要求/m => ['review_checklists.md', 'findings-first 五段标签完整定义'],
}

# 退役词：模式 => 说明
RETIRED_TERMS = {
  /错误[^\n]{0,30}协议层|协议层[^\n]{0,30}错误/m => '"协议层" 作为错误分层名已退役（Issue D2），改用 "状态码错误"',
}

violations = 0

files_to_check = ['SKILL.md'] + Dir.glob('references/*.md').sort

UNIQUE_OWNERS.each do |pattern, (owner, desc)|
  files_to_check.each do |file|
    next if File.basename(file) == owner
    content = File.read(file)
    if content =~ pattern
      puts "Unique ownership violated: #{desc} (应只在 #{owner}) 却在 #{file} 出现"
      violations += 1
    end
  end
end

RETIRED_TERMS.each do |pattern, desc|
  files_to_check.each do |file|
    content = File.read(file)
    if content =~ pattern
      puts "Retired term regression in #{file}: #{desc}"
      violations += 1
    end
  end
end

exit 1 if violations > 0
RUBY
echo "Unique ownership + retired words OK"

echo "[11/14] Validate threshold doc/script sync"
ruby <<'RUBY'
script_path = "scripts/summarize-usage-ledger.sh"
doc_path = "references/usage_ledger.md"

script_consts = {}
File.foreach(script_path) do |line|
  m = line.match(/^([A-Z_]+_THRESHOLD)\s*=\s*([0-9.]+)\s*$/)
  next unless m
  script_consts[m[1]] = m[2]
end

required = %w[MISSED_RULE_THRESHOLD TASK_TYPE_OTHER_THRESHOLD DEVIATION_THRESHOLD TOOL_DIVERGENCE_THRESHOLD]
missing = required - script_consts.keys
unless missing.empty?
  puts "Missing threshold constants in #{script_path}: #{missing.join(', ')}"
  exit 1
end

doc_consts = {}
File.foreach(doc_path) do |line|
  m = line.match(/^\|\s*`([A-Z_]+_THRESHOLD)`\s*\|\s*([0-9.]+)\s*\|/)
  next unless m
  doc_consts[m[1]] = m[2]
end

doc_missing = required - doc_consts.keys
unless doc_missing.empty?
  puts "Missing threshold rows in #{doc_path} §8: #{doc_missing.join(', ')}"
  exit 1
end

drift = []
required.each do |k|
  if script_consts[k] != doc_consts[k]
    drift << "#{k}: script=#{script_consts[k]} doc=#{doc_consts[k]}"
  end
end
unless drift.empty?
  puts "Threshold drift between #{script_path} and #{doc_path} §8:"
  drift.each { |d| puts "  #{d}" }
  exit 1
end
RUBY
echo "Threshold doc/script sync OK"

echo "[12/14] Validate snapshot consistency with active version"
if [ "${SKIP_SNAPSHOT_CONSISTENCY:-0}" = "1" ]; then
  echo "Skipped (SKIP_SNAPSHOT_CONSISTENCY=1)"
else
  bash scripts/check-snapshot-consistency.sh
fi

echo "[13/14] Run behavior validation scenarios"
if [ "${SKIP_BEHAVIOR_VALIDATION:-0}" = "1" ]; then
  echo "Skipped (SKIP_BEHAVIOR_VALIDATION=1)"
else
  SKIP_SNAPSHOT_CONSISTENCY=1 bash scripts/run-behavior-validation.sh
fi

echo "[14/14] Validate slug list sync (validation_scenarios.md ↔ ALLOWED_TASK_TYPES ↔ CANONICAL_SLUGS)"
ruby <<'RUBY'
scenarios_path    = "references/validation_scenarios.md"
ledger_validator  = "scripts/validate-usage-ledger.sh"
spec_validator    = "scripts/validate-scenario-specs.sh"

# 1. Extract slugs from validation_scenarios.md
# Looks for the line: 建议使用固定场景标识：`slug1`、`slug2`、...
scenario_slugs = []
File.foreach(scenarios_path) do |line|
  if line.include?("建议使用固定场景标识")
    scenario_slugs = line.scan(/`([a-z][a-z0-9-]*)`/).flatten
    break
  end
end
if scenario_slugs.empty?
  puts "FAIL: could not parse slug list from #{scenarios_path}"
  exit 1
end

# 2. Extract ALLOWED_TASK_TYPES from validate-usage-ledger.sh (exclude 'other')
ledger_types = []
File.foreach(ledger_validator) do |line|
  m = line.match(/ALLOWED_TASK_TYPES\s*=\s*%w\[([^\]]+)\]/)
  if m
    ledger_types = m[1].split.reject { |s| s == "other" }
    break
  end
end
if ledger_types.empty?
  puts "FAIL: could not parse ALLOWED_TASK_TYPES from #{ledger_validator}"
  exit 1
end

# 3. Extract CANONICAL_SLUGS from validate-scenario-specs.sh
canonical_slugs = []
in_block = false
File.foreach(spec_validator) do |line|
  in_block = true  if line =~ /CANONICAL_SLUGS\s*=\s*%w\[/
  if in_block
    break if line.include?("].freeze")
    canonical_slugs += line.scan(/\b([a-z][a-z0-9-]+)\b/).flatten
  end
end
if canonical_slugs.empty?
  puts "FAIL: could not parse CANONICAL_SLUGS from #{spec_validator}"
  exit 1
end

errors = []

# scenario_slugs ↔ ledger_types
missing = scenario_slugs - ledger_types
extra   = ledger_types   - scenario_slugs
errors << "In validation_scenarios.md but not ALLOWED_TASK_TYPES: #{missing.join(', ')}" unless missing.empty?
errors << "In ALLOWED_TASK_TYPES but not validation_scenarios.md: #{extra.join(', ')}"   unless extra.empty?

# scenario_slugs ↔ canonical_slugs
missing2 = scenario_slugs - canonical_slugs
extra2   = canonical_slugs - scenario_slugs
errors << "In validation_scenarios.md but not CANONICAL_SLUGS: #{missing2.join(', ')}" unless missing2.empty?
errors << "In CANONICAL_SLUGS but not validation_scenarios.md: #{extra2.join(', ')}"  unless extra2.empty?

if errors.empty?
  puts "Slug sync OK (#{scenario_slugs.length} slugs: #{scenario_slugs.join(', ')})"
else
  errors.each { |e| puts e }
  exit 1
end
RUBY
echo "Slug sync OK"

echo "Base validation passed"
