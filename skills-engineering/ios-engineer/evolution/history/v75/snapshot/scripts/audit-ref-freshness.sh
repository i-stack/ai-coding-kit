#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

STALE_MONTHS="${STALE_MONTHS:-12}"
CRITICAL_MONTHS="${CRITICAL_MONTHS:-18}"

if [[ ! "$STALE_MONTHS" =~ ^[0-9]+$ ]] || [[ ! "$CRITICAL_MONTHS" =~ ^[0-9]+$ ]]; then
  echo "STALE_MONTHS / CRITICAL_MONTHS must be non-negative integers"
  exit 2
fi

if [ "$STALE_MONTHS" -gt "$CRITICAL_MONTHS" ]; then
  echo "STALE_MONTHS ($STALE_MONTHS) must be <= CRITICAL_MONTHS ($CRITICAL_MONTHS)"
  exit 2
fi

ruby - "$STALE_MONTHS" "$CRITICAL_MONTHS" <<'RUBY'
require "date"

stale_months = ARGV[0].to_i
critical_months = ARGV[1].to_i

now = Date.today
header_re = /\A<!--\s*last-verified:\s*(\d{4})-(\d{2})\s*-->\s*\z/

results = []

Dir.glob("references/*.md").sort.each do |file|
  first_line = File.open(file, &:gets).to_s
  if (m = first_line.match(header_re))
    year, month = m[1].to_i, m[2].to_i
    begin
      verified = Date.new(year, month, 1)
    rescue ArgumentError
      results << { file: file, status: "INVALID", months: nil, verified: "#{m[1]}-#{m[2]}" }
      next
    end
    months_diff = (now.year - verified.year) * 12 + (now.month - verified.month)
    status =
      if months_diff > critical_months
        "CRITICAL"
      elsif months_diff > stale_months
        "STALE"
      else
        "FRESH"
      end
    results << { file: file, status: status, months: months_diff, verified: verified.strftime("%Y-%m") }
  else
    results << { file: file, status: "UNDATED", months: nil, verified: nil }
  end
end

priority = { "CRITICAL" => 0, "UNDATED" => 1, "INVALID" => 2, "STALE" => 3, "FRESH" => 4 }
results.sort_by! { |r| [priority[r[:status]], -(r[:months] || 0), r[:file]] }

results.each do |r|
  age = r[:months] ? "#{r[:months]}mo" : "n/a"
  verified = r[:verified] ? r[:verified] : "—"
  printf("[%-8s] %-50s last-verified=%-7s age=%s\n", r[:status], r[:file], verified, age)
end

counts = Hash.new(0)
results.each { |r| counts[r[:status]] += 1 }

puts "---"
puts "FRESH=#{counts['FRESH']} STALE=#{counts['STALE']} CRITICAL=#{counts['CRITICAL']} UNDATED=#{counts['UNDATED']} INVALID=#{counts['INVALID']}"
puts "thresholds: STALE>#{stale_months}mo, CRITICAL>#{critical_months}mo (override via STALE_MONTHS / CRITICAL_MONTHS env)"

bad = counts["CRITICAL"] + counts["UNDATED"] + counts["INVALID"]
exit(bad > 0 ? 1 : 0)
RUBY
