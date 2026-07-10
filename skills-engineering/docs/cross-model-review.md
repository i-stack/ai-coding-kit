# cross-model-review 使用文档

## 概述

`cross-model-review` 解决 AI 辅助编码的第 2 类失败模式：**计划听起来对，但会崩**。同一个模型既规划又评分无法发现自己的结构盲区——必须靠**跨提供商模型**对抗审查。

本 skill 是 `plan-grill` 的 Act 2：plan-grill 锁定 PLAN.md 后接力本 skill。它基于 `chaseai-yt/grill-me-codex`（MIT 许可）的 Act 2 思路，适配本项目多 adapter 架构（codex / gemini / claude 自动发现）。

## 前置

- `PLAN.md` 必须已由 `plan-grill` 锁定（PG-004 产出）。无 PLAN.md 时先跑 plan-grill。
- 当前环境至少有两个不同 provider 的 reviewer CLI 可用（CMR-001 探测）。

## 何时触发

- **用户触发**：`cross-model-review` / `cross review` / "对抗审查" / "让两个模型审计划" / "model debate" / "stress-test PLAN.md" / "review PLAN.md" / "让 Gemini/Codex/Claude 审一下计划"。
- **接力 plan-grill**：plan-grill 锁定 PLAN.md 后，用户说"让另一个模型审查"则加载本 skill。
- **跳过**：没有 PLAN.md（先跑 plan-grill）；trivial 改动；用户明确"直接实施"；可用 reviewer provider < 2。

## 核心规则（CMR-001 ~ CMR-005）

- **CMR-001 自动发现 reviewer**：直接探测 codex / gemini / claude 三个 CLI 的可用性、版本、non-interactive 与只读模式支持。可用 provider < 2 时停止并提示安装，不伪造 cross-model。
- **CMR-002 推荐组合 + 用户选择**：从可用 CLI 中推荐两个不同 provider 的组合（如 codex + gemini），让用户确认。不静默替用户选死。
- **CMR-003 reviewer 只读**：每个 reviewer 必须以只读模式运行——codex 用 `-s read-only`，gemini 用 `--approval-mode plan`，claude 用 `--permission-mode plan`。reviewer 不写代码，只输出 `VERDICT: APPROVED` 或 `VERDICT: REVISE` + 具体修改建议。原始输出必须落在当前项目根 `.plan-reviews/<date>-<slug>/raw/`，禁止用 `/tmp` 作缓冲。
- **CMR-004 主 agent 仲裁**：每轮收集所有已选 reviewer 的 verdict；原始输出、中间输出和交付日志保存在当前项目根目录下，记录进 `PLAN-REVIEW-LOG.md`。只有全部 `APPROVED` 才能收敛，任一 `REVISE` 都必须仲裁并进入修订 / 下一轮。采纳有证据的批评，拒绝不成立的批评并写明理由。
- **CMR-005 MAX_ROUNDS + deadlock**：到 `MAX_ROUNDS`（默认 5）仍不收敛时，输出 deadlock——列出每个未决点 + 主 agent 的反立场，交给用户裁决。禁止假装 approved。

## 工作流程

```text
PLAN.md 已锁定
      ↓
CMR-001 探测可用 CLI（< 2 则停止）
      ↓
CMR-002 推荐两 provider 组合，用户确认
      ↓
CMR-003 reviewer 只读审查，输出落盘 raw/
      ↓
CMR-004 主 agent 仲裁，写 PLAN-REVIEW-LOG.md
      ├─ 全部 APPROVED → Resolution（问用户：现在实施？）
      └─ 任一 REVISE → 修订 PLAN.md → 下一轮
      ↓
MAX_ROUNDS 用尽未收敛 → deadlock，交用户裁决
```

## reviewer 只读模式命令

| CLI | 只读模式 | 续接会话 |
|-----|----------|----------|
| codex | `codex exec -s read-only` | `codex exec resume <thread_id> -c sandbox_mode="read-only"` |
| gemini | `gemini -p "<prompt>" --approval-mode plan` | `gemini -r <session_id> -p "<prompt>" --approval-mode plan` |
| claude | `claude -p "<prompt>" --permission-mode plan` | `claude --resume <session_id> -p "<prompt>" --permission-mode plan` |

> codex 调用必须以 `< /dev/null` 重定向 stdin，否则非交互式下会永久 hang。每个调用加 600s timeout 守卫。

## 安全规则（要点）

1. reviewer 每轮只读，永不写文件。
2. `< /dev/null` 必需（codex），防静默卡死。
3. 禁止 `/tmp` reviewer 缓冲——证据必须留在当前项目根 `.plan-reviews/.../raw/`。
4. timeout 600s 守卫，超时视为失败并停止。
5. 不 pin model，用 CLI 默认模型（除非用户显式指定）。
6. 循环必在 MAX_ROUNDS 终止。
7. deadlock 不假装 approved，如实标记交用户裁决。

## 与 auto-code-review 的区别

| 维度 | cross-model-review | auto-code-review |
|------|-------------------|------------------|
| 审查对象 | PLAN.md | 代码实现 |
| 启动方式 | 用户显式触发 | 用户显式触发 |
| 默认写权限 | 不修改实现 | review-only 不修改实现 |
| 修复模式 | 主 agent 仲裁计划 | 仅 `--fix` 时修改代码 |
| 最大轮次 | 5 | review-and-fix 为 3 |

## 示例

回归审查示例（登录限流场景）见 [`cross-model-review/examples/regression-login-rate-limit.md`](../cross-model-review/examples/regression-login-rate-limit.md)。

## 常见问题

### 只有一个模型 CLI 可用，能跑吗？

不能。CMR-001 硬门要求至少两个不同 provider 的 CLI，跨模型对抗才有意义。单个 reviewer 会降级为普通单模型审查，不再使用本流程。

### 审查会改我的代码吗？

不会。本 skill 只审查 PLAN.md，两幕期间不写任何代码。修改实现由后续对话或 ios-engineer skill 承接。

### 不收敛怎么办？

到 MAX_ROUNDS（默认 5）仍未全部 APPROVED 即输出 deadlock，列出未决点与你（主 agent）的反立场，由你裁决，绝不假装通过。

### 审查证据存哪里？

reviewer 原始输出、PLAN-REVIEW-LOG.md 都落在当前项目根的 `.plan-reviews/<date>-<slug>/` 下，且该目录默认写入 `.gitignore`（本地工作产物，除非你明确要求纳入版本控制）。
