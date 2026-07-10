#!/usr/bin/env bash
# Pre-flight setup checker for the review/workflow skills.
#
# Verifies the external prerequisites that plan-grill (PG-006 history recall)
# and auto-code-review (ACR-001~008) depend on, and reports which reviewer CLIs
# are available. This is ADVISORY only: it never fails (exit 0) so it can be run
# standalone or wired into pre-push without blocking the push. It exists to give
# the user a one-shot "is my review toolchain ready?" answer instead of
# discovering missing pieces mid-review.
#
# Checks:
#   - plan-reviews/dist/cli.js built (else: how to build)
#   - auto-code-review config available (env/review.json | .auto-review-config.json | AUTO_REVIEW_*)
#   - reviewer CLIs discoverable (codex / gemini / claude)
#
# Usage:
#   scripts/verify-review-setup.sh

set -uo pipefail

SE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ROOT="$(cd "${SE_DIR}/.." && pwd)"

echo "=== review toolchain setup ==="

# 1. plan-reviews build artifact (plan-grill PG-006 recall depends on it)
CLI_JS="${SE_DIR}/plan-reviews/dist/cli.js"
if [[ -f "$CLI_JS" ]]; then
  echo "  [ok] plan-reviews/dist/cli.js present (history recall ready)"
else
  echo "  [!] plan-reviews/dist/cli.js MISSING — plan-grill PG-006 recall will silently no-op."
  echo "      build it once with: (cd ${SE_DIR}/plan-reviews && npm install && npm run build)"
fi

# 2. auto-code-review configuration
cfg_found=0
if [[ -f "${ROOT}/env/review.json" ]]; then
  echo "  [ok] auto-code-review config: env/review.json"
  cfg_found=1
fi
if [[ -f "${ROOT}/.auto-review-config.json" ]]; then
  echo "  [ok] auto-code-review config: .auto-review-config.json"
  cfg_found=1
fi
for v in AUTO_REVIEW_ENABLED AUTO_REVIEW_REVIEWERS AUTO_REVIEW_REVIEWER AUTO_REVIEW_MAX_ROUNDS AUTO_REVIEW_ALLOW_SELF_REVIEW; do
  if [[ -n "${!v:-}" ]]; then
    echo "  [ok] auto-code-review config: env ${v} set"
    cfg_found=1
    break
  fi
done
if [[ $cfg_found -eq 0 ]]; then
  echo "  [!] no auto-code-review config found — copy env/review.json.example to env/review.json and fill in."
fi

# 3. reviewer CLIs
# cross-model-review (CMR-001/002) requires >=2 independent provider CLIs.
# "command -v" only proves the binary exists on PATH; it does NOT prove the CLI
# can produce a valid verdict (auth, network, non-interactive mode). So we also
# run a light `--version` probe and only count CLIs that both exist AND respond.
echo "  -- reviewer CLIs (needs >=2 usable independent providers) --"
cli_count=0
for cli in codex gemini claude; do
  if command -v "$cli" >/dev/null 2>&1; then
    if "$cli" --version >/dev/null 2>&1; then
      echo "  [ok] $cli available + --version ok ($(command -v "$cli"))"
      cli_count=$((cli_count + 1))
    else
      echo "  [~] $cli found on PATH but '--version' probe failed — it may not be able to produce a valid verdict."
    fi
  else
    echo "  [ ] $cli not found on PATH"
  fi
done
if [[ $cli_count -lt 2 ]]; then
  echo "  [!] only ${cli_count} usable reviewer CLI(s) — cross-model review needs >=2 independent providers; install a second (e.g. codex + gemini)."
fi

echo "=== done (advisory; exit 0) ==="
exit 0
