#!/usr/bin/env bash
# detect-review-clis.sh — 探测可用的 reviewer CLI（codex/gemini/claude），输出 JSON。
# 供 cross-model-review skill 的 CMR-001 使用。
# 只做 command -v + --version，不做登录探测。
#
# 输出格式：
# {"clis":[...],"available_count":N}
#
# 每个 CLI 对象：
# {"name":"<cli>","available":<bool>,"path":"<path>","version":"<ver>","readonly_flag":"<flag>","noninteractive_flag":"<flag>"}

set -uo pipefail

json_escape() {
  local s="$1"
  s="${s//\\/\\\\}"
  s="${s//\"/\\\"}"
  printf '%s' "$s"
}

probe_cli() {
  local name="$1" version_flag="$2" readonly_flag="$3" noninteractive_flag="$4"
  local path version

  path="$(command -v "$name" 2>/dev/null || true)"
  if [[ -z "$path" ]]; then
    printf '{"name":"%s","available":false}' "$name"
    return 0
  fi

  version="$("$name" "$version_flag" 2>/dev/null | head -1 | tr -d '\r' || true)"
  printf '{"name":"%s","available":true,"path":"%s","version":"%s","readonly_flag":"%s","noninteractive_flag":"%s"}' \
    "$name" \
    "$(json_escape "$path")" \
    "$(json_escape "$version")" \
    "$(json_escape "$readonly_flag")" \
    "$(json_escape "$noninteractive_flag")"
}

main() {
  local codex gemini claude count=0

  codex="$(probe_cli "codex" "--version" "-s read-only" "exec")"
  [[ "$codex" == *'"available":true'* ]] && ((count++)) || true

  gemini="$(probe_cli "gemini" "--version" "--approval-mode plan" "-p")"
  [[ "$gemini" == *'"available":true'* ]] && ((count++)) || true

  claude="$(probe_cli "claude" "--version" "--permission-mode plan" "-p")"
  [[ "$claude" == *'"available":true'* ]] && ((count++)) || true

  printf '{"clis":[%s,%s,%s],"available_count":%d}\n' \
    "$codex" "$gemini" "$claude" "$count"
}

main "$@"
