# auto-code-review Agent 调用指南

## 一句话描述

AI 生成代码后自动调用跨模型审查，循环修复直到通过，归档到 .plan-reviews。支持可配置 reviewer 模型，单模型时降级为自审模式。

## 何时调用

- **自动触发**：主 agent 生成代码修改后自动执行（无需用户关键词）。
- **用户触发**：用户说 `auto-review` / `审查代码` / `review 一下` / `检查一下代码`。
- **前置**：代码修改已完成（git diff 可获取变更）。

## 关键行为

1. 阅读 `SKILL.md` + `references/auto_code_review.md` 全文。
2. 检测代码变更（排除 .md 文件和 trivial 改动）。
3. 探测可用 reviewer CLI（`detect-review-clis.sh` 或直接 `command -v`）。
4. 构造审查输入：diff + 变更文件列表 + 变更摘要。
5. 调用 reviewer（只读模式）：codex `-s read-only`、gemini `--approval-mode plan`、claude `--permission-mode plan`。
6. 解析 verdict：APPROVED → 归档；REVISE → 仲裁并修复 → 下一轮。
7. MAX_ROUNDS=3 不收敛 → deadlock，交用户裁决。
8. 自动归档到 `.plan-reviews/<date>-<slug>/`：QUESTION.md + RESPONSE.md + REVIEW-LOG.md + diff.patch + raw/。

## 不调用的情况

- 纯文档更新（只有 .md 文件变更）
- trivial 改动（< 5 行非空白变更）
- 用户明确"不用审查" / "直接实施"
- 无可用 reviewer CLI 且 `AUTO_REVIEW_ALLOW_SELF_REVIEW=false`

## 配置选项

| 环境变量 | 默认值 | 含义 |
|---|---|---|
| `AUTO_REVIEW_REVIEWER` | 自动选择 | 指定单个 reviewer（codex/gemini/claude） |
| `AUTO_REVIEW_REVIEWERS` | 自动选择 | 指定多个 reviewer（逗号分隔） |
| `AUTO_REVIEW_MAX_ROUNDS` | `3` | 审查轮次上限 |
| `AUTO_REVIEW_ALLOW_SELF_REVIEW` | `true` | 是否允许单模型自审降级 |

## 与 cross-model-review 的区别

| 维度 | cross-model-review | auto-code-review |
|---|---|---|
| 审查对象 | PLAN.md（实现计划） | 代码实现 |
| 触发方式 | 用户手动 | 自动 |
| MAX_ROUNDS | 5 | 3 |
| 前置条件 | 需要 PLAN.md | 无前置 |
