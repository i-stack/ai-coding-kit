#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

usage() {
  cat <<'USAGE'
Usage: bash scripts/validate.sh [OPTIONS]

Unified validation entry for ios-engineer skill evolution pipeline.

Options:
  --all          Run all validation steps (default)
  --quick        Run fast checks only: YAML, line count, ref existence, rule IDs
  --scenarios    Validate scenario specs exclusively
  --links        Validate internal markdown links exclusively
  --ledger       Validate usage ledger exclusively
  --ids          Validate rule IDs exclusively
  --skip-snapshot  Skip snapshot consistency check
  --skip-behavior  Skip behavior validation scenarios

Exit 0: all validations pass
Exit 1: any validation step fails
USAGE
  exit 1
}

ALL=true
QUICK=false
SCENARIOS=false
LINKS=false
LEDGER=false
IDS=false
SKIP_SNAPSHOT="${SKIP_SNAPSHOT_CONSISTENCY:-0}"
SKIP_BEHAVIOR="${SKIP_BEHAVIOR_VALIDATION:-0}"

while [ $# -gt 0 ]; do
  case "$1" in
    --all) ALL=true; shift ;;
    --quick) QUICK=true; ALL=false; shift ;;
    --scenarios) SCENARIOS=true; ALL=false; shift ;;
    --links) LINKS=true; ALL=false; shift ;;
    --ledger) LEDGER=true; ALL=false; shift ;;
    --ids) IDS=true; ALL=false; shift ;;
    --skip-snapshot) SKIP_SNAPSHOT=1; shift ;;
    --skip-behavior) SKIP_BEHAVIOR=1; shift ;;
    -h|--help) usage ;;
    *) echo "Unknown option: $1"; usage ;;
  esac
done

run_step() {
  local num="$1"; shift
  local desc="$1"; shift
  echo "[${num}] ${desc}"
  "$@"
}

failures=0

if $QUICK; then
  echo "=== Quick Validation ==="

  run_step "1/4" "Validate YAML structure" bash -c \
    'ruby -e "require \"yaml\"; YAML.load_file(\"SKILL.md\"); YAML.load_file(\"agents/openai.yaml\"); puts \"YAML OK\""'

  run_step "2/4" "Validate SKILL.md line count" bash -c \
    'lines=$(wc -l < SKILL.md | tr -d " "); [ "$lines" -le 500 ] && echo "$lines lines OK" || { echo "FAIL: $lines > 500"; exit 1; }'

  run_step "3/4" "Validate ref existence" bash scripts/validate_scenario_specs.sh <<<'skip'

  # Quick ref check: all references/*.md mentioned in SKILL.md exist
  missing=0
  while IFS= read -r path; do
    [ -z "$path" ] && continue
    if [ ! -f "$path" ]; then
      echo "Missing reference: $path"
      missing=1
    fi
  done < <(rg -o 'references/[A-Za-z0-9_./-]+\.md' SKILL.md | sort -u)
  if [ "$missing" -ne 0 ]; then
    echo "FAIL: missing references"
    ((failures++)) || true
  else
    echo "Reference files OK"
  fi

  run_step "4/4" "Validate rule IDs" bash scripts/validate_rule_ids.sh
fi

if $SCENARIOS; then
  echo "=== Scenario Validation ==="
  run_step "S1" "Validate scenario specs" bash scripts/validate_scenario_specs.sh
  run_step "S2" "Validate internal markdown links" bash -c \
    'ruby <<'"'"'RUBY'"'"'
broken = 0
Dir.glob("references/*.md").sort.each do |file|
  File.foreach(file).with_index(1) do |line, lineno|
    line.scan(/\[([^\]]*)\]\(([^)]+)\)/) do |_text, link|
      next if link =~ /\A(https?|mailto):/i
      path = link.split("#", 2).first.to_s
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
puts "Internal links OK"
RUBY'
fi

if $LINKS; then
  echo "=== Link Validation ==="
  run_step "L1" "Validate internal markdown links" bash -c \
    'ruby <<'"'"'RUBY'"'"'
broken = 0
Dir.glob("references/*.md").sort.each do |file|
  File.foreach(file).with_index(1) do |line, lineno|
    line.scan(/\[([^\]]*)\]\(([^)]+)\)/) do |_text, link|
      next if link =~ /\A(https?|mailto):/i
      path = link.split("#", 2).first.to_s
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
puts "Internal links OK"
RUBY'
fi

if $LEDGER; then
  echo "=== Ledger Validation ==="
  run_step "LD1" "Validate usage ledger" bash scripts/validate_usage_ledger.sh
fi

if $IDS; then
  echo "=== Rule ID Validation ==="
  run_step "ID1" "Validate rule IDs" bash scripts/validate_rule_ids.sh
fi

if $ALL; then
  echo "=== Full Validation Pipeline ==="
  SKIP_SNAPSHOT_CONSISTENCY="$SKIP_SNAPSHOT" \
    SKIP_BEHAVIOR_VALIDATION="$SKIP_BEHAVIOR" \
    bash scripts/validate_skill_evolution.sh
  exit $?
fi

if [ "$failures" -gt 0 ]; then
  echo "FAILED: ${failures} step(s) failed"
  exit 1
fi

echo "All checks passed"
