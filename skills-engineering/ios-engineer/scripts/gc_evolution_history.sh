#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

HISTORY_DIR="evolution/history"
PROPOSALS_DIR="evolution/proposals"
APPROVALS_DIR="evolution/approvals"
ACTIVE_VERSION_FILE="evolution/active_version.json"
KEEP_RECENT="${KEEP_RECENT:-10}"

DRY_RUN=false
while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run) DRY_RUN=true; shift ;;
    -h|--help)
      echo "Usage: bash scripts/gc_evolution_history.sh [--dry-run]"
      echo ""
      echo "Clean up old evolution artifacts, keeping:"
      echo "  - Most recent ${KEEP_RECENT} history versions"
      echo "  - Current active version (always protected)"
      echo "  - Most recent ${KEEP_RECENT} proposals and their validations/approvals"
      echo ""
      echo "Options:"
      echo "  --dry-run  List what would be deleted without actually deleting"
      exit 0
      ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

# ── Phase 1: Determine which history versions to keep/delete ──

if [ ! -d "$HISTORY_DIR" ]; then
  echo "No history directory found: ${HISTORY_DIR}"
  exit 0
fi

if [ -f "$ACTIVE_VERSION_FILE" ]; then
  ACTIVE_VERSION="$(ruby -rjson -e 'puts JSON.parse(File.read(ARGV[0]))["active_version"]' "$ACTIVE_VERSION_FILE")"
else
  echo "No active_version.json found, aborting GC"
  exit 0
fi

# Collect all version dirs
tmpfile="$(mktemp)"
trap 'rm -f "$tmpfile"' EXIT

for dir in "$HISTORY_DIR"/v[0-9]*/; do
  [ -d "$dir" ] || continue
  dirname="$(basename "$dir")"
  if ! echo "$dirname" | grep -qE '^v[0-9]+(-[A-Za-z0-9]+)*$'; then
    continue
  fi
  num="$(echo "$dirname" | sed 's/^v//; s/-.*//' | sed 's/^0*//')"
  num="${num:-0}"
  echo "$num $dirname" >> "$tmpfile"
done

if [ ! -s "$tmpfile" ]; then
  echo "No versioned history directories found"
  exit 0
fi

sorted_dirs=($(sort -k1 -n -r "$tmpfile" | awk '{print $2}'))
total="${#sorted_dirs[@]}"

protected_file="$(mktemp)"
trap 'rm -f "$tmpfile" "$protected_file"' EXIT

echo "$ACTIVE_VERSION" >> "$protected_file"

count=0
for v in "${sorted_dirs[@]}"; do
  if [ "$count" -lt "$KEEP_RECENT" ]; then
    echo "$v" >> "$protected_file"
  fi
  count=$((count + 1))
done

# ── Phase 2: Map proposals → history versions, determine which proposals to clean ──

export GC_ROOT_DIR="$ROOT_DIR"
export GC_PROTECTED_FILE="$protected_file"
export GC_DRY_RUN="$DRY_RUN"

ruby <<'RUBY'
require 'json'
require 'set'

ROOT_DIR = ENV['GC_ROOT_DIR']
PROTECTED_FILE = ENV['GC_PROTECTED_FILE']
DRY_RUN = ENV['GC_DRY_RUN'] == "true"

HISTORY_DIR = File.join(ROOT_DIR, "evolution/history")
PROPOSALS_DIR = File.join(ROOT_DIR, "evolution/proposals")
APPROVALS_DIR = File.join(ROOT_DIR, "evolution/approvals")

# Load protected history versions
protected_versions = if File.exist?(PROTECTED_FILE)
  File.readlines(PROTECTED_FILE).map(&:strip).reject(&:empty?).to_set
else
  Set.new
end

# Collect all history versions (kept and deleted)
all_history_versions = []
Dir.glob(File.join(HISTORY_DIR, "v*/")).sort.each do |dir|
  name = File.basename(dir)
  next unless name.match?(/^v\d+(-[A-Za-z0-9]+)*$/)
  all_history_versions << name
end

# Build map: proposal_slug → set of history versions that reference it
proposal_to_versions = Hash.new { |h, k| h[k] = Set.new }
all_history_versions.each do |ver|
  meta_file = File.join(HISTORY_DIR, ver, "metadata.json")
  next unless File.exist?(meta_file)
  begin
    meta = JSON.parse(File.read(meta_file))
    source = meta["source"]
    next unless source && source.start_with?("proposal:")
    slug = source.sub(/\Aproposal:/, "")
    proposal_to_versions[slug] << ver
  rescue JSON::ParserError
    # Skip malformed metadata
  end
end

# Determine which proposals/approvals to keep vs delete
# Rule: Keep if ANY linked history version is kept, OR if not linked to any history (WIP)
proposals_to_delete = []
proposals_to_keep = []
approvals_to_delete = []
approvals_to_keep = []
orphan_proposals = []  # not linked to any history → always keep

Dir.glob(File.join(PROPOSALS_DIR, "*.md")).sort.each do |file|
  slug = File.basename(file, ".md")

  if proposal_to_versions.key?(slug)
    # Linked to history versions — check if ALL linked versions are being deleted
    linked_versions = proposal_to_versions[slug]
    all_deleted = linked_versions.all? { |v| !protected_versions.include?(v) }
    if all_deleted
      proposals_to_delete << slug
      approvals_to_delete << slug
    else
      proposals_to_keep << slug
      approvals_to_keep << slug
    end
  else
    # Not linked to any history — work-in-progress, always keep
    orphan_proposals << slug
    proposals_to_keep << slug
    # Check if approval exists
    approval_file = File.join(APPROVALS_DIR, "#{slug}.json")
    if File.exist?(approval_file)
      approvals_to_keep << slug
    end
  end
end

# Also find approvals without corresponding proposals (stale orphans)
Dir.glob(File.join(APPROVALS_DIR, "*.json")).sort.each do |file|
  slug = File.basename(file, ".json")
  proposal_file = File.join(PROPOSALS_DIR, "#{slug}.md")
  unless File.exist?(proposal_file)
    approvals_to_delete << slug unless approvals_to_delete.include?(slug)
  end
end

# ── Output report ──

puts ""
puts "=== Proposals & Approvals GC ==="
puts "Linked proposals (to any history): #{proposal_to_versions.size}"
puts "Orphan proposals (no history link, WIP): #{orphan_proposals.size}"
puts "Proposals to keep: #{proposals_to_keep.uniq.size}"
puts "Proposals to delete: #{proposals_to_delete.uniq.size}"
puts "Approvals to keep: #{approvals_to_keep.uniq.size}"
puts "Approvals to delete: #{approvals_to_delete.uniq.size}"
puts ""

if proposals_to_delete.empty? && approvals_to_delete.empty?
  puts "No orphan proposals or approvals to clean up."
else
  proposals_to_delete.uniq.each do |slug|
    file = File.join(PROPOSALS_DIR, "#{slug}.md")
    # Show which deleted versions reference it
    versions = proposal_to_versions[slug].to_a.sort_by { |v| v.sub(/^v/, "").to_i }
    ver_list = versions.map { |v| "#{v}(deleted)" }.join(", ")
    if DRY_RUN
      puts "  [WOULD DELETE PROPOSAL] #{file}  (linked to: #{ver_list})"
    else
      puts "  [DELETE PROPOSAL] #{file}  (linked to: #{ver_list})"
      File.unlink(file) if File.exist?(file)
    end
  end

  approvals_to_delete.uniq.each do |slug|
    file = File.join(APPROVALS_DIR, "#{slug}.json")
    if DRY_RUN
      puts "  [WOULD DELETE APPROVAL] #{file}"
    else
      puts "  [DELETE APPROVAL] #{file}"
      File.unlink(file) if File.exist?(file)
    end
  end
end

# Output list of kept orphans (for transparency)
unless orphan_proposals.empty?
  puts ""
  puts "WIP proposals (no history yet, always kept): #{orphan_proposals.size}"
end
RUBY

# ── Phase 3: History snapshot GC (must run AFTER ruby because ruby reads metadata.json) ──

would_delete=0
would_keep=0
for v in "${sorted_dirs[@]}"; do
  if grep -qx "$v" "$protected_file"; then
    would_keep=$((would_keep + 1))
  else
    would_delete=$((would_delete + 1))
  fi
done

echo ""
echo "=== Evolution History GC ==="
echo "Active version: $ACTIVE_VERSION"
echo "Keep recent: $KEEP_RECENT"
echo "Total versions found: $total"
echo ""

deleted=0
kept=0
for v in "${sorted_dirs[@]}"; do
  if grep -qx "$v" "$protected_file"; then
    echo "  [KEEP]  $HISTORY_DIR/$v"
    kept=$((kept + 1))
  else
    echo "  [DELETE] $HISTORY_DIR/$v"
    if ! $DRY_RUN; then
      rm -rf "$HISTORY_DIR/$v"
    fi
    deleted=$((deleted + 1))
  fi
done

echo ""
if $DRY_RUN; then
  echo "DRY RUN: Would delete $deleted history version(s), keep $kept history version(s)"
else
  echo "Done: Deleted $deleted history version(s), kept $kept history version(s)"
fi

# ── Phase 4: Prune proposals / validations / approvals to KEEP_RECENT newest ──
# Fixes unbounded growth: the bulk of evolution artifacts lives in these three
# dirs, and they were never pruned before. Keep only the newest KEEP_RECENT
# proposals; drop older proposals and any validation/approval not matching a
# kept proposal (orphans included).

echo ""
echo "=== Proposals / Validations / Approvals GC (keep newest $KEEP_RECENT) ==="

export GC_ROOT_DIR="$ROOT_DIR"
export GC_KEEP_RECENT="$KEEP_RECENT"
export GC_DRY_RUN="$DRY_RUN"

ruby <<'RUBY'
require 'set'

ROOT = ENV['GC_ROOT_DIR']
KEEP = ENV['GC_KEEP_RECENT'].to_i
DRY  = ENV['GC_DRY_RUN'] == 'true'

PROPOSALS   = File.join(ROOT, "evolution/proposals")
VALIDATIONS = File.join(ROOT, "evolution/validations")
APPROVALS   = File.join(ROOT, "evolution/approvals")

kept = Dir.glob(File.join(PROPOSALS, "*.md"))
           .map { |f| File.basename(f, ".md") }
           .sort
           .last(KEEP)
           .to_set

puts "Kept proposals (newest #{KEEP}): #{kept.size}"

Dir.glob(File.join(PROPOSALS, "*.md")).each do |f|
  slug = File.basename(f, ".md")
  next if kept.include?(slug)
  puts DRY ? "  [WOULD DELETE PROPOSAL] #{f}" : "  [DELETE PROPOSAL] #{f}"
  File.unlink(f) unless DRY
end

[ [VALIDATIONS, "json"], [APPROVALS, "json"] ].each do |dir, ext|
  Dir.glob(File.join(dir, "*.#{ext}")).each do |f|
    slug = File.basename(f, ".#{ext}")
    next if kept.include?(slug)
    puts DRY ? "  [WOULD DELETE] #{f}" : "  [DELETE] #{f}"
    File.unlink(f) unless DRY
  end
end

puts "Remaining -> proposals: #{Dir.glob(File.join(PROPOSALS,'*.md')).size}, " \
     "validations: #{Dir.glob(File.join(VALIDATIONS,'*.json')).size}, " \
     "approvals: #{Dir.glob(File.join(APPROVALS,'*.json')).size}"
RUBY
