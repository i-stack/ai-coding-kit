#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

echo "[1/9] Validate YAML structure"
ruby -e 'require "yaml"; YAML.load_file("SKILL.md"); YAML.load_file("agents/openai.yaml"); puts "YAML OK"'

echo "[2/9] Validate SKILL.md size"
line_count="$(wc -l < SKILL.md | tr -d ' ')"
if [ "$line_count" -gt 500 ]; then
  echo "SKILL.md too long: ${line_count} lines"
  exit 1
fi
echo "SKILL.md lines: ${line_count}"

echo "[3/9] Validate referenced files exist"
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

echo "[4/9] Validate layering guardrails"
if rg -q '^## (调用预算|重试与限流|上下文压缩|防循环退出条件|输出要求)$' references/root_cause_enforcement.md; then
  echo "root_cause_enforcement.md should not define MCP control sections"
  exit 1
fi

if rg -q '^## (核心原则|排障标准流程|调用预算|重试与限流|防循环退出条件)$' references/examples.md; then
  echo "examples.md should not define root-cause or MCP control sections"
  exit 1
fi

echo "Layering guardrails OK"

echo "[5/9] Validate internal markdown links"
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

echo "[6/9] Validate no orphan references"
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

echo "[7/9] Validate unique ownership + retired word regression"
ruby <<'RUBY'
# pattern => [expected_owner_basename, description]
UNIQUE_OWNERS = {
  /传输错误.*状态码错误.*解码错误.*鉴权错误.*业务错误.*展示错误/m => ['domain_modeling.md', '错误分层 6 层枚举'],
  /Time Profiler[^\n]{0,30}[：:][^\n]*定位[^\n]*CPU/m => ['observability_logging.md', '完整性能取证工具用途定义（Time Profiler: 定位 CPU）'],
  /审查结论\s*\n[^\n]*不可合入[^\n]*可合入[\s\S]*?严重问题[\s\S]*?一般问题[\s\S]*?验证缺口[\s\S]*?最终要求/m => ['review_checklists.md', 'findings-first 完整骨架定义'],
}

# 退役词：模式 => 说明
RETIRED_TERMS = {
  /错误[^\n]{0,30}协议层|协议层[^\n]{0,30}错误/m => '"协议层" 作为错误分层名已退役（Issue D2），改用 "状态码错误"',
}

violations = 0

UNIQUE_OWNERS.each do |pattern, (owner, desc)|
  Dir.glob('references/*.md').sort.each do |file|
    next if File.basename(file) == owner
    content = File.read(file)
    if content =~ pattern
      puts "Unique ownership violated: #{desc} (应只在 #{owner}) 却在 #{file} 出现"
      violations += 1
    end
  end
end

RETIRED_TERMS.each do |pattern, desc|
  Dir.glob('references/*.md').sort.each do |file|
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

echo "[8/9] Validate snapshot consistency with active version"
if [ "${SKIP_SNAPSHOT_CONSISTENCY:-0}" = "1" ]; then
  echo "Skipped (SKIP_SNAPSHOT_CONSISTENCY=1)"
else
  bash scripts/check_snapshot_consistency.sh
fi

echo "[9/9] Run behavior validation scenarios"
if [ "${SKIP_BEHAVIOR_VALIDATION:-0}" = "1" ]; then
  echo "Skipped (SKIP_BEHAVIOR_VALIDATION=1)"
else
  SKIP_SNAPSHOT_CONSISTENCY=1 bash scripts/run_behavior_validation.sh
fi

echo "Base validation passed"
