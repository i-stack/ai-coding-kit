# auto-code-review Agent 调用指南

## 一句话描述

用户显式启动的跨模型代码审查；默认只读，只有明确 `--fix` 才允许主 agent 修复。

## 何时调用

- 调用：`/auto-review`、`使用 auto-code-review`、`启动跨模型代码审查`。
- 调用并授权修复：`/auto-review --fix`、`审查并修复`。
- 不调用：普通代码生成/修改完成、纯问答、含糊的“看看代码”。

## 关键行为

1. 完整阅读 `SKILL.md` 与 `references/auto_code_review.md`。
2. 确认本轮存在显式触发，并区分 `review-only` / `review-and-fix`。
3. 加载 `env/review.json`、`.auto-review-config.json`、`AUTO_REVIEW_*`；配置不替代用户授权。
4. 确认审查范围：精确的当前请求变更；否则让用户选择 staged 或 worktree。
5. 生成唯一 review package，记录 mode、scope、文件列表、patch 来源、测试状态、selected reviewers 和 expected reviewer count。
6. 历史召回已由全局 `historical-recall` 负责，直接以只读模式调用 reviewer（不再内联 recall）。
7. 每轮冻结 selected reviewers；每个 reviewer 都必须记录 status、raw 路径和合法 verdict。缺席、超时、raw 缺失或非法 verdict 均按未通过处理。
8. `review-only` 只仲裁、报告和归档，不修改代码；不因一轮 APPROVED 自动声明实现 gate 已通过。
9. `review-and-fix` 才允许主 agent 修复并重审，最多 3 轮；同一轮所有 selected reviewers 都 APPROVED 才通过。
10. 归档后 best-effort 执行 sync + merge。

## 不调用的情况

- 普通代码生成或修改完成。
- 用户没有明确指定 auto-code-review 工作流。
- `AUTO_REVIEW_ENABLED=false`。

## 配置选项

优先级：`env/review.json` → `.auto-review-config.json` → `AUTO_REVIEW_*`。

| 环境变量 | 默认值 | 含义 |
|---|---|---|
| `AUTO_REVIEW_ENABLED` | `true` | 能力开关；不代表当前请求已授权 |
| `AUTO_REVIEW_REVIEWER` | 自动选择 | 单个 reviewer |
| `AUTO_REVIEW_REVIEWERS` | 自动选择 | reviewer 列表 |
| `AUTO_REVIEW_MAX_ROUNDS` | `3` | `review-and-fix` 最大轮次 |
| `AUTO_REVIEW_ALLOW_SELF_REVIEW` | `false` | 是否允许单模型降级 |

参考模板：`env/review.json.example`。

归档包含 `QUESTION.md`、`RESPONSE.md`、`REVIEW-LOG.md`、`diff.patch` 与 `raw/`。`REVIEW-LOG.md` 必须能证明每轮 selected reviewer quorum。

## 权限边界

- reviewer 永远只读。
- `/auto-review` 不授权主 agent 写文件。
- `/auto-review --fix` 才授权主 agent 修复当前审查范围内的问题。
- `AUTO_REVIEW_ENABLED=true` 只是功能可用，不是持久授权。

计划审查仍使用 `cross-model-review`。
