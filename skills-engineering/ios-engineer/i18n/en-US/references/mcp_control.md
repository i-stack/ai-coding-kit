<!-- last-verified: 2026-06 -->
# MCP & Tool Call Control

> This is an English mirror of the authoritative Chinese `references/mcp_control.md`.
> In case of discrepancies, the Chinese source takes precedence.

## Table of Contents
- Usage Rules
- Auto Problem Normalization
- Call Budget
- Sub-agent Routing
- Retry & Rate Limiting
- Context Compression
- Anti-loop Exit Conditions
- iOS Scenario MCP Priority Mapping

## Usage Rules
- When involving MCP, search, log evidence gathering, multi-round troubleshooting, or complex tool calls, this file must be used.
- Goal is to reduce ineffective tool calls, limit context bloat, and avoid repeatedly trying the same path.
- This file only constrains execution budget and stop-loss conditions; does not redefine root-cause analysis and output templates.

## Call Budget
Tool calls have no hard total limit; converge by the following actionable constraints:
- Only continue expanding calls when new evidence has been obtained. "New evidence" definition: error information unseen in the last call, new log lines, new code files, new data fields, or specific facts that can falsify/confirm the current hypothesis. Merely "thinking of new search terms" does not count as new evidence.
- Same-type tool consecutive calls at most 2 times, e.g., consecutive searches, consecutively opening multiple pages with no new information, consecutively reading same-type logs.
- Only 1 main investigation direction allowed at a time; at most 1 backup direction retained.
- When reading files, read the most relevant, shortest-path files first; do not scan entire directories or batch-read large files first.

## Sub-agent Routing
- When workload is large, context consumption is high, and user has explicitly allowed sub-agents, prefer delegating independent exploration, review, or verification tasks to sub-agents; avoid filling main context with large amounts of logs, search results, and file contents.
- Only route tasks that can be independently closed-loop, e.g., batch file inspection, cross-reference repeated rule scanning, test failure log categorization, solution cross-review; main agent retains root-cause judgment, final decision, code integration, and user communication.
- Do not delegate the most blocking critical path to sub-agents; if the next step must depend on that result, main agent should complete it locally or wait for sub-agent return before continuing.
- Input to sub-agents must have clear boundaries: task goal, allowed read scope, output format, files not to be modified; when code modification is involved, file ownership must be explicit to avoid parallel conflicts.
- After sub-agent returns, main agent must verify whether its conclusions are evidence-supported; only bring valid evidence and conclusions back to main context.

## Retry & Rate Limiting
- After the same tool with the same parameters fails twice, must not retry a third time identically. "Failure" definition: returns empty results, returns identical result to last time, command exits non-zero, or result is irrelevant to current hypothesis.
- If continuing to try, must first change one condition: parameters, scope, entry point, evidence source, or hypothesis direction.
- After two consecutive searches with no new evidence, stop searching; first summarize known facts and gaps.
- After two consecutive reads of different files still cannot support current hypothesis, step back and re-examine root-cause hypothesis.

## Context Compression
- After 2 to 3 consecutive rounds, compress to four sections before continuing:
  - Phenomenon
  - Known facts
  - Eliminated items
  - Next step
- After compression, do not re-introduce invalidated hypotheses, closed branches, and irrelevant historical background.

## Anti-loop Exit Conditions
When any of the following conditions are met, must switch direction or pause the current path:
- Same path validation failed 2 times.
- Same search direction had no new evidence for 2 consecutive times.
- Same file modified back and forth around the same issue 2 times with no validation progress.
- Same root-cause hypothesis cannot explain new phenomena or new evidence.

## Output Requirements
- After tool calls, conclusions should be output first: what new evidence was obtained, what was eliminated, what is the next step.
- If current path is stopped due to budget or anti-loop rules, must explicitly explain the stop reason.

## iOS Scenario MCP Priority Mapping
When iOS engineering tasks involve build / API contract / design mock comparison / repository evidence gathering, **prefer calling corresponding MCP**; do not directly compose raw commands or compare visually. MCP list is subject to the host's currently injected tools (Claude Code / Cursor / Codex synced via `env/secrets.json` + `env/mcp/*.json` + `env/platforms/*.json`, see repository [env/](../../../env/) data directory and [sync/](../../../sync/) tool directory); current iOS engineering related items:

| Scenario | Priority MCP | Common Alternative | Trigger Keywords |
|------|---------|---------------|-----------|
| Xcode build / Archive / Simulator / Install / Run tests / Read Build Settings | `XcodeBuildMCP` | Directly compose `xcodebuild` / `xcrun simctl` / `xcodebuild test` multiple times | Build / Archive / IPA / Simulator / Run tests / Build Settings |
| API field alignment / DTO field mapping / error code contract / API schema validation | `apifox` | Screenshot of API / build DTO from memory / visual field comparison | DTO / Field mapping / Error code / API contract |
| Repository PR / Issue / commit evidence / cross-repo code reference | `github` | High-frequency `gh pr view` / `gh issue list` / `gh api` | PR review / Issue association / Cross-repo context |
| Design mock comparison / visual walkthrough / UI restoration comparison | `lanhu` | Screenshot + visual pixel comparison | Design mock / Restoration / Visual walkthrough |
| Web / hybrid container H5 debugging / Web UI automation | `playwright` | Manual clicking + console screenshots | H5 debugging / Web verification / Automated clicking |
| Cross-directory file retrieval (only when project files are in sync directory outside `~/Desktop/`) | `filesystem` | Multiple `find` / directory switching | Cross-project file retrieval |

Call constraints (simultaneously effective with rest of this document; no exemption):
- MCP tools count toward "same-type tool consecutive calls at most 2 times" limit; do not bypass [Call Budget](#call-budget) and [Anti-loop Exit Conditions](#anti-loop-exit-conditions).
- Same MCP tool with same parameters must not retry identically a third time after 2 failures; first change conditions or fall back to manual path, and explain fallback reason in output.
- MCP call results consolidated in "new evidence / eliminated / next step" format; consistent with other tools.
- When host has not currently injected corresponding MCP (server not visible in tool list), must not pretend to call; prompt user to check `sync/` synchronization status and fall back to original means; **do not fabricate results silently**.
- MCP selection is routing preference, not iron rule: when MCP response speed is significantly slower than raw commands, or MCP capability does not cover current subtask (e.g., XcodeBuildMCP does not support private build phase), fallback is allowed but must explicitly explain "fallback reason".
- `xcodebuild` / `xcrun simctl` command examples appearing in other refs are all fallback examples for when MCP is unavailable, MCP capability does not cover, or need to be solidified into CI scripts; in interactive iOS engineering troubleshooting, these examples must not be interpreted as bypassing this section's MCP priority mapping default path.
