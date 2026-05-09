#!/usr/bin/env bash

# Incrementally extract <usage-audit> blocks from a Claude Code / Codex / Cursor
# transcript JSONL and append them to evolution/usage/usage.jsonl via
# scripts/extract_usage_audit.sh.
#
# Usage: bash scripts/sync_transcript_to_ledger.sh <transcript-jsonl> [session-id]
#
# Re-run safe: maintains a per-transcript line-offset file under
# ~/.claude/hooks/state/ledger-sync/<sha1(path)>.offset so repeated triggers
# (sub-agent Stop, main session Stop) never re-ingest the same block.
#
# Exit codes:
#   0  success (or no new blocks found)
#   1  transcript missing, extract rejected the batch, or internal error
#
# The caller (Claude Code Stop hook glue) should swallow non-zero to avoid
# blocking session end.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

if [ $# -lt 1 ]; then
  echo "Usage: $0 <transcript-jsonl-path> [session-id]" >&2
  exit 1
fi

TRANSCRIPT="$1"
SESSION_ID="${2:-}"

if [ ! -f "$TRANSCRIPT" ]; then
  echo "Transcript not found: $TRANSCRIPT" >&2
  exit 1
fi

STATE_DIR="${CLAUDE_LEDGER_SYNC_STATE_DIR:-$HOME/.claude/hooks/state/ledger-sync}"
mkdir -p "$STATE_DIR"
LOG_FILE="$STATE_DIR/sync.log"

KEY="$(printf '%s' "$TRANSCRIPT" | shasum -a 1 | cut -d' ' -f1)"
OFFSET_FILE="$STATE_DIR/$KEY.offset"

TMPTEXT="$(mktemp -t ledger-sync-XXXXXX)"
trap 'rm -f "$TMPTEXT"' EXIT

# Ruby pass: read JSONL from previous offset onward, concat assistant text blocks
# into TMPTEXT, print new total line count on stdout. If SESSION_ID is provided
# and a <usage-audit> block lacks a session-id line, inject it so the ledger
# entry can be traced back to the originating Claude Code session.
TOTAL_LINES="$(ruby - "$TRANSCRIPT" "$OFFSET_FILE" "$TMPTEXT" "$SESSION_ID" <<'RUBY'
require 'json'

transcript, offset_file, out_path, session_id = ARGV
session_id = nil if session_id.nil? || session_id.strip.empty?
start_line = File.exist?(offset_file) ? File.read(offset_file).strip.to_i : 0
start_line = 0 if start_line < 0

texts = []
total_lines = 0

File.foreach(transcript).with_index do |line, idx|
  total_lines = idx + 1
  next if idx < start_line

  begin
    obj = JSON.parse(line)
  rescue JSON::ParserError
    next
  end

  next unless obj.is_a?(Hash) && obj['type'] == 'assistant'

  msg = obj['message']
  next unless msg.is_a?(Hash)

  content = msg['content']
  case content
  when String
    texts << content
  when Array
    content.each do |item|
      next unless item.is_a?(Hash) && item['type'] == 'text'
      t = item['text']
      texts << t if t.is_a?(String)
    end
  end
end

if session_id
  texts = texts.map do |t|
    t.gsub(/<usage-audit>(.*?)<\/usage-audit>/m) do
      body = Regexp.last_match(1)
      if body =~ /^\s*session-id\s*:/m
        "<usage-audit>#{body}</usage-audit>"
      else
        "<usage-audit>\nsession-id: #{session_id}#{body}</usage-audit>"
      end
    end
  end
end

File.write(out_path, texts.join("\n\n"))
puts total_lines
RUBY
)"

TOTAL_LINES="${TOTAL_LINES:-0}"
PREV_OFFSET="$( [ -f "$OFFSET_FILE" ] && cat "$OFFSET_FILE" || echo 0 )"

if [ ! -s "$TMPTEXT" ]; then
  # No new assistant text since last sync; advance offset and exit quietly.
  echo "$TOTAL_LINES" > "$OFFSET_FILE"
  exit 0
fi

# Feed extracted text to the existing extractor; it is atomic (reject-on-any-bad-block).
if EXTRACT_OUT="$(bash scripts/extract_usage_audit.sh "$TMPTEXT" 2>&1)"; then
  echo "$TOTAL_LINES" > "$OFFSET_FILE"
  {
    printf '[%s] sync ok: transcript=%s prev=%s new=%s session=%s\n' \
      "$(date '+%Y-%m-%d %H:%M:%S')" "$TRANSCRIPT" "$PREV_OFFSET" "$TOTAL_LINES" "$SESSION_ID"
    printf '  extract: %s\n' "$EXTRACT_OUT"
  } >> "$LOG_FILE"
  exit 0
else
  # Do NOT advance offset: extractor rejected the batch, block will be retried.
  {
    printf '[%s] sync failed: transcript=%s prev=%s session=%s\n' \
      "$(date '+%Y-%m-%d %H:%M:%S')" "$TRANSCRIPT" "$PREV_OFFSET" "$SESSION_ID"
    printf '  extract stderr:\n%s\n' "$EXTRACT_OUT"
  } >> "$LOG_FILE"
  exit 1
fi
