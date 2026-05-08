#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

LEDGER_FILE="evolution/usage/usage.jsonl"
RULE_INDEX_FILE="references/rule_index.md"

usage() {
  cat <<'USAGE'
Usage: bash scripts/summarize_usage_ledger.sh [options]

Aggregate evolution/usage/usage.jsonl into a human-readable summary plus
proposal-candidate signals. Read-only: never modifies the ledger or repo.

Options:
  --since YYYY-MM-DD   Only include entries with time >= this date
  --tool <slug>        Only include entries with this tool value
  --json               Emit JSON instead of markdown
  --output FILE        Write to FILE instead of stdout
  -h, --help           Show this help

Thresholds (hardcoded, change in source if needed):
  missed_rule >= 3       => surfaced as proposal signal
  task_type=other >= 5   => surfaced as missing-scenario signal
  deviation count >= 2   => surfaced as stable failure mode
  tool hit_rate diff >= 0.4 (each tool >= 5 expected for that rule)
                         => surfaced as tool divergence
USAGE
}

since=""
tool_filter=""
emit_json=0
output_path=""

while [ $# -gt 0 ]; do
  case "$1" in
    --since) since="$2"; shift 2 ;;
    --tool) tool_filter="$2"; shift 2 ;;
    --json) emit_json=1; shift ;;
    --output) output_path="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown arg: $1" >&2; usage >&2; exit 1 ;;
  esac
done

if [ ! -f "$LEDGER_FILE" ]; then
  msg="No entries yet (ledger empty: ${LEDGER_FILE} missing)"
  if [ -n "$output_path" ]; then echo "$msg" > "$output_path"; else echo "$msg"; fi
  exit 0
fi

if [ ! -f "$RULE_INDEX_FILE" ]; then
  echo "Missing rule index: ${RULE_INDEX_FILE}" >&2
  exit 1
fi

ruby - "$LEDGER_FILE" "$RULE_INDEX_FILE" "$since" "$tool_filter" "$emit_json" "$output_path" <<'RUBY'
require "json"
require "date"

ledger_path, index_path, since_str, tool_filter, emit_json_str, output_path = ARGV
emit_json = emit_json_str == "1"

# Thresholds
MISSED_RULE_THRESHOLD = 3
TASK_TYPE_OTHER_THRESHOLD = 5
DEVIATION_THRESHOLD = 2
TOOL_DIVERGENCE_THRESHOLD = 0.4
MIN_TOOL_SAMPLE_SIZE = 5

# Build rule_id -> summary map
rule_summary = {}
File.foreach(index_path) do |line|
  m = line.match(/\A\|\s*([A-Z]+-\d{3})\s*\|\s*active\s*\|\s*([^|]+?)\s*\|/)
  rule_summary[m[1]] = m[2].strip if m
end

since_date = since_str.empty? ? nil : (Date.parse(since_str) rescue nil)
if !since_str.empty? && since_date.nil?
  warn "Invalid --since '#{since_str}', expected YYYY-MM-DD"
  exit 1
end

raw_entries = []
malformed = 0
File.foreach(ledger_path).with_index(1) do |line, lineno|
  line = line.strip
  next if line.empty?
  begin
    raw_entries << JSON.parse(line)
  rescue JSON::ParserError
    warn "line #{lineno}: malformed JSON skipped (run validate_usage_ledger.sh to repair)"
    malformed += 1
  end
end

# Apply filters
entries = raw_entries.select do |e|
  next false if tool_filter != "" && e["tool"] != tool_filter
  if since_date
    begin
      ed = Date.parse(e["time"])
      next false if ed < since_date
    rescue
      next false
    end
  end
  true
end

if entries.empty?
  msg =
    if raw_entries.empty?
      "No entries yet (ledger empty)"
    else
      "No entries match filter (since=#{since_str.empty? ? '*' : since_str}, tool=#{tool_filter.empty? ? '*' : tool_filter})"
    end
  out = output_path.empty? ? $stdout : File.open(output_path, "w")
  out.puts(msg)
  out.close unless out == $stdout
  exit 0
end

# --- Aggregations ---
by_tool = Hash.new { |h, k| h[k] = { "entries" => 0, "pass" => 0, "partial" => 0, "fail" => 0 } }
by_task_type = Hash.new { |h, k| h[k] = { "entries" => 0, "pass" => 0 } }
rule_stats = Hash.new { |h, k| h[k] = { "expected" => 0, "hit" => 0, "miss" => 0 } }
deviation_counts = Hash.new(0)
tool_rule_hit = Hash.new { |h, k| h[k] = Hash.new { |hh, kk| hh[kk] = { "expected" => 0, "hit" => 0 } } }

entries.each do |e|
  tool = e["tool"]
  by_tool[tool]["entries"] += 1
  by_tool[tool][e["outcome"]] += 1 if %w[pass partial fail].include?(e["outcome"])

  by_task_type[e["task_type"]]["entries"] += 1
  by_task_type[e["task_type"]]["pass"] += 1 if e["outcome"] == "pass"

  expected = e["expected_rules"] || []
  hit = e["hit_rules"] || []
  missed = e["missed_rules"] || []

  expected.each do |rid|
    rule_stats[rid]["expected"] += 1
    tool_rule_hit[tool][rid]["expected"] += 1
  end
  hit.each do |rid|
    rule_stats[rid]["hit"] += 1
    tool_rule_hit[tool][rid]["hit"] += 1
  end
  missed.each { |rid| rule_stats[rid]["miss"] += 1 }

  (e["deviations"] || []).each { |d| deviation_counts[d] += 1 }
end

# --- Proposal signals ---
signals = []

# 1. Missed rule frequency
missed_freq = rule_stats.select { |_, v| v["miss"] >= MISSED_RULE_THRESHOLD }
                       .sort_by { |_, v| -v["miss"] }
missed_freq.each do |rid, v|
  signals << {
    "kind" => "missed_rule",
    "rule_id" => rid,
    "summary" => rule_summary[rid] || "(unknown)",
    "miss_count" => v["miss"],
    "note" => "#{rid} (#{rule_summary[rid] || '(unknown)'}) 在 #{v['miss']} 个任务中 missed —— 规则表达不清或路由不够触发？建议 review 该规则与对应 ref。"
  }
end

# 2. task_type=other
other_count = (by_task_type["other"] || {})["entries"] || 0
if other_count >= TASK_TYPE_OTHER_THRESHOLD
  signals << {
    "kind" => "task_type_other",
    "count" => other_count,
    "note" => "task_type=other 累计 #{other_count} 条 —— 当前 6 个固定场景可能漏覆盖了一类常见任务，建议看 prompt_summary 找模式后扩 validation_scenarios.md。"
  }
end

# 3. Deviation frequency
hot_deviations = deviation_counts.select { |_, c| c >= DEVIATION_THRESHOLD }
                                 .sort_by { |_, c| -c }
hot_deviations.each do |text, c|
  signals << {
    "kind" => "deviation",
    "text" => text,
    "count" => c,
    "note" => "「#{text}」出现 #{c} 次 —— 稳定失败模式，建议在相关 ref 加更明确的检查项。"
  }
end

# 4. Tool divergence
tools_present = tool_rule_hit.keys
divergence = []
all_rule_ids = rule_stats.keys
all_rule_ids.each do |rid|
  rates = []
  tools_present.each do |t|
    expected = tool_rule_hit[t][rid]["expected"]
    hit = tool_rule_hit[t][rid]["hit"]
    next if expected < MIN_TOOL_SAMPLE_SIZE
    rate = hit.to_f / expected
    rates << [t, rate, expected, hit]
  end
  next if rates.length < 2
  rates.sort_by! { |_, r, _, _| -r }
  high = rates.first
  low = rates.last
  diff = (high[1] - low[1]).abs
  next if diff < TOOL_DIVERGENCE_THRESHOLD
  divergence << {
    "rule_id" => rid,
    "summary" => rule_summary[rid] || "(unknown)",
    "high_tool" => high[0],
    "high_rate" => (high[1] * 100).round(0),
    "low_tool" => low[0],
    "low_rate" => (low[1] * 100).round(0),
    "diff_pct" => (diff * 100).round(0)
  }
end
divergence.sort_by! { |d| -d["diff_pct"] }
divergence.each do |d|
  signals << {
    "kind" => "tool_divergence",
    "rule_id" => d["rule_id"],
    "summary" => d["summary"],
    "note" => "#{d['rule_id']} 在 #{d['high_tool']} 命中率 #{d['high_rate']}%，#{d['low_tool']} 命中率 #{d['low_rate']}%（差 #{d['diff_pct']}%）—— 工具差异显著，可能 prompt 注入语境不同或一端做了更深的求证。",
    "data" => d
  }
end

# --- Time window summary ---
times = entries.map { |e| Date.parse(e["time"]) rescue nil }.compact.sort
window_from = times.first&.to_s || "?"
window_to = times.last&.to_s || "?"

summary = {
  "window_from" => window_from,
  "window_to" => window_to,
  "tool_filter" => tool_filter.empty? ? "all" : tool_filter,
  "since_filter" => since_str.empty? ? "*" : since_str,
  "total_entries" => entries.length,
  "malformed_lines" => malformed,
  "thresholds" => {
    "missed_rule" => MISSED_RULE_THRESHOLD,
    "task_type_other" => TASK_TYPE_OTHER_THRESHOLD,
    "deviation" => DEVIATION_THRESHOLD,
    "tool_divergence" => TOOL_DIVERGENCE_THRESHOLD,
    "min_tool_sample_size" => MIN_TOOL_SAMPLE_SIZE
  },
  "by_tool" => by_tool.sort_by { |_, v| -v["entries"] }.to_h,
  "by_task_type" => by_task_type.sort_by { |_, v| -v["entries"] }.to_h,
  "rule_stats" => rule_stats.sort_by { |_, v| -v["expected"] }.to_h,
  "top_missed" => missed_freq.map { |rid, v| { "rule_id" => rid, "summary" => rule_summary[rid] || "(unknown)", "miss_count" => v["miss"] } },
  "top_deviations" => hot_deviations.map { |t, c| { "text" => t, "count" => c } },
  "proposal_signals" => signals
}

# --- Render ---
def pct(part, total)
  return "—" if total == 0
  "#{(part.to_f / total * 100).round(0)}%"
end

if emit_json
  rendered = JSON.pretty_generate(summary)
else
  lines = []
  lines << "# Usage Ledger Summary"
  lines << "- 时间窗：#{summary['window_from']} ~ #{summary['window_to']}"
  lines << "- 时间过滤：#{summary['since_filter']}"
  lines << "- 工具过滤：#{summary['tool_filter']}"
  lines << "- 总条目：#{summary['total_entries']}"
  lines << "- 跳过非法行：#{summary['malformed_lines']}" if summary["malformed_lines"] > 0
  lines << ""

  lines << "## 按工具"
  lines << ""
  lines << "| tool | entries | pass% | partial% | fail% |"
  lines << "|------|---------|-------|----------|-------|"
  summary["by_tool"].each do |t, v|
    lines << "| #{t} | #{v['entries']} | #{pct(v['pass'], v['entries'])} | #{pct(v['partial'], v['entries'])} | #{pct(v['fail'], v['entries'])} |"
  end
  lines << ""

  lines << "## 按 task_type"
  lines << ""
  lines << "| task_type | entries | pass% |"
  lines << "|-----------|---------|-------|"
  summary["by_task_type"].each do |tt, v|
    line = "| #{tt} | #{v['entries']} | #{pct(v['pass'], v['entries'])} |"
    line += " ← signal" if tt == "other" && v["entries"] >= TASK_TYPE_OTHER_THRESHOLD
    lines << line
  end
  lines << ""

  lines << "## 命中频率（按 expected 出现次数降序）"
  lines << ""
  lines << "| rule_id | 摘要 | expected | hit | hit_rate |"
  lines << "|---------|------|----------|-----|----------|"
  summary["rule_stats"].each do |rid, v|
    rate = v["expected"] == 0 ? "—" : "#{(v['hit'].to_f / v['expected'] * 100).round(0)}%"
    lines << "| #{rid} | #{rule_summary[rid] || '(unknown)'} | #{v['expected']} | #{v['hit']} | #{rate} |"
  end
  lines << ""

  unless summary["top_missed"].empty?
    lines << "## Top missed rules（miss count ≥ #{MISSED_RULE_THRESHOLD}）"
    lines << ""
    lines << "| rule_id | 摘要 | miss count |"
    lines << "|---------|------|------------|"
    summary["top_missed"].each do |m|
      lines << "| #{m['rule_id']} | #{m['summary']} | #{m['miss_count']} |"
    end
    lines << ""
  end

  unless summary["top_deviations"].empty?
    lines << "## Top deviations（count ≥ #{DEVIATION_THRESHOLD}，完全相等聚合）"
    lines << ""
    lines << "| 偏差描述 | count |"
    lines << "|----------|-------|"
    summary["top_deviations"].each do |d|
      lines << "| #{d['text']} | #{d['count']} |"
    end
    lines << ""
  end

  lines << "## 提案候选信号"
  lines << ""
  lines << "> 阈值：missed_rule ≥ #{MISSED_RULE_THRESHOLD} / task_type=other ≥ #{TASK_TYPE_OTHER_THRESHOLD} / 同一 deviation ≥ #{DEVIATION_THRESHOLD} / 工具间 hit_rate 差 ≥ #{(TOOL_DIVERGENCE_THRESHOLD * 100).round(0)}%（每端最少 #{MIN_TOOL_SAMPLE_SIZE} 条样本）"
  lines << "> 触发不等于必须建提案；只是值得一看。"
  lines << ""
  if signals.empty?
    lines << "_（暂无超过阈值的信号）_"
  else
    signals.each do |s|
      lines << "- ⚠️ #{s['note']}"
    end
  end

  rendered = lines.join("\n") + "\n"
end

if output_path.empty?
  print rendered
else
  File.write(output_path, rendered)
  warn "Wrote #{rendered.bytesize} bytes to #{output_path}"
end
RUBY
