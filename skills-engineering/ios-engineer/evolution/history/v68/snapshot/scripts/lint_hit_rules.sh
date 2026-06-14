#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

if [ $# -lt 1 ]; then
  echo "Usage: bash scripts/lint_hit_rules.sh <transcript-file>"
  echo ""
  echo "Verifies that hit-rules declared in <usage-audit> blocks have textual anchors"
  echo "in the surrounding response text. Covers IR-001 / IR-002 / IR-004 / IR-006 / IR-008 / IR-010 / IR-011"
  echo "(those with template-field anchors). Other rule IDs are reported UNSUPPORTED."
  echo ""
  echo "Exit 0: no FAIL (UNSUPPORTED does not fail)"
  echo "Exit 1: any FAIL or input error"
  exit 1
fi

input="$1"

if [ ! -f "$input" ]; then
  echo "Input file not found: ${input}"
  exit 1
fi

ruby - "$input" <<'RUBY'
input_path = ARGV[0]
text = File.read(input_path)

SIGNALS = {
  "IR-001" => {
    check: ->(t) { !!(t =~ /\p{Han}/u) },
    desc: "中文字符存在"
  },
  "IR-002" => {
    check: ->(t) { !!(t =~ /^前置确认\s*$/m) },
    desc: "独立「前置确认」段标题"
  },
  "IR-004" => {
    check: ->(t) {
      four = %w[结论 为什么 修法 验证].all? { |k| t =~ /^#{Regexp.escape(k)}\s*$/m }
      findings = %w[审查结论 严重问题 一般问题 验证缺口 最终要求].all? { |k| t.include?(k) }
      four || findings
    },
    desc: "四段式（结论/为什么/修法/验证）或 findings-first 5 段全部存在"
  },
  "IR-006" => {
    check: ->(t) { !!(t =~ /^版本前提\s*$/m) },
    desc: "独立「版本前提」段标题"
  },
  "IR-008" => {
    check: ->(t) {
      t =~ /残留风险声明/ && t =~ /已覆盖/ && t =~ /未覆盖/ && t =~ /残留风险/
    },
    desc: "残留风险声明 + 已覆盖/未覆盖/残留风险 三字段全部存在"
  },
  "IR-010" => {
    check: ->(t) {
      has_block = !!(t =~ /^逻辑链\s*$/m)
      fields = ["事实/证据", "推断", "结论强度", "可证伪/缺口"].all? do |k|
        t =~ /^#{Regexp.escape(k)}[：:]\s*\S+/m
      end
      inference = !!(t =~ /因为[\s\S]{0,160}所以|不确定|缺口|推测|待验证/)
      has_block && fields && inference
    },
    desc: "独立「逻辑链」块 + 事实/证据、推断、结论强度、可证伪/缺口四字段 + 推理或不确定性标记"
  },
  "IR-011" => {
    check: ->(t) {
      %w[复述 最强反驳 隐藏假设 失效条件 可证伪条件 立场翻转 迎合自检 置信度 结论].all? { |k| t.include?(k) }
    },
    desc: "认知对手模式九段标题全部存在"
  }
}

blocks = []
text.scan(/<usage-audit>(.*?)<\/usage-audit>/m) do
  m = Regexp.last_match
  blocks << { start: m.begin(0), end_pos: m.end(0), body: m[1] }
end

if blocks.empty?
  puts "No <usage-audit> blocks found in #{input_path}"
  exit 0
end

results = []
prev_end = 0
blocks.each do |blk|
  region = text[prev_end...blk[:start]]

  task_line = blk[:body].lines.find { |l| l.strip.start_with?("task-type:") }
  task = task_line ? task_line.sub(/^[^:]+:\s*/, "").strip : "?"

  hit_line = blk[:body].lines.find { |l| l.strip.start_with?("hit-rules:") }
  hits = hit_line ? hit_line.sub(/^[^:]+:\s*/, "").strip.split(",").map(&:strip).reject(&:empty?) : []

  hits.each do |rid|
    if SIGNALS.key?(rid)
      ok = SIGNALS[rid][:check].call(region)
      results << { status: ok ? "PASS" : "FAIL", task: task, rule: rid, desc: SIGNALS[rid][:desc] }
    else
      results << { status: "UNSUPPORTED", task: task, rule: rid, desc: "no textual signal mapped" }
    end
  end

  prev_end = blk[:end_pos]
end

results.each do |r|
  puts "[#{r[:status]}] #{r[:task]} #{r[:rule]}: #{r[:desc]}"
end

pass_n = results.count { |r| r[:status] == "PASS" }
fail_n = results.count { |r| r[:status] == "FAIL" }
unsup_n = results.count { |r| r[:status] == "UNSUPPORTED" }

puts "---"
puts "PASS=#{pass_n} FAIL=#{fail_n} UNSUPPORTED=#{unsup_n}"

exit(fail_n > 0 ? 1 : 0)
RUBY
