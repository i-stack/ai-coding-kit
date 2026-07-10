# auto-code-review 使用文档

## 概述

`auto-code-review` 是用户显式启动的跨模型代码审查工作流。它不会在普通代码修改完成后自动运行。

名称中的 `auto` 表示：用户启动后，工具会自动完成 reviewer 调用、结果归档、知识库同步，以及在用户额外授权时执行修复循环。

## 权限模型

审查与修改是两层独立权限：

| 命令 | 模式 | reviewer | 主 agent 是否可修改代码 |
|---|---|---|---|
| `/auto-review` | review-only（默认） | 只读 | 否 |
| `/auto-review --fix` | review-and-fix | 只读 | 是，仅限已授权审查范围 |

普通实现请求、代码修改完成、测试通过或 `AUTO_REVIEW_ENABLED=true` 都不会启动审查。

## 如何触发

明确使用以下表达之一：

- `/auto-review`
- `使用 auto-code-review`
- `启动跨模型代码审查`
- `/auto-review --fix`
- `使用 auto-code-review 审查并修复`

“看看代码”“检查一下”等普通审查请求不自动升级为跨模型工作流，避免在用户不知情时调用外部 CLI、消耗资源或创建归档。

## 工作流程

```text
用户显式触发
      ↓
确认模式和审查范围
      ↓
加载配置并探测 reviewer CLI
      ↓
recall 历史结论（不可信线索）
      ↓
reviewer 只读审查
      ├─ review-only：报告 findings → 归档 → sync/merge
      └─ review-and-fix：主 agent 修复 → 再审查（最多 3 轮）→ 归档 → sync/merge
```

## 审查范围

支持三类范围：

1. `turn`：当前请求中由 agent 精确记录的变更。只有能证明边界时使用。
2. `staged`：Git 暂存区。
3. `worktree`：整个工作区，包括已跟踪和未跟踪文件。

如果在后续对话中才触发，而工作区已经存在其它修改，agent 会让用户选择 staged 或 worktree。`git diff HEAD` 不能证明哪些修改属于当前对话，也不包含未跟踪文件。

审查敏感文件前必须停止：`.env`、密钥、证书、Token 等内容不得传给 reviewer。

## 配置

配置加载优先级（后者覆盖前者）：

1. `env/review.json`
2. `.auto-review-config.json`
3. `AUTO_REVIEW_*` 环境变量

参考 [env/review.json.example](../../env/review.json.example)：

```json
{
  "enabled": true,
  "reviewers": [],
  "maxRounds": 3,
  "allowSelfReview": false
}
```

| 变量 | 默认值 | 说明 |
|---|---|---|
| `AUTO_REVIEW_ENABLED` | `true` | 功能可用开关；不代表当前请求已授权 |
| `AUTO_REVIEW_REVIEWER` | 自动选择 | 指定一个 reviewer |
| `AUTO_REVIEW_REVIEWERS` | 自动选择 | 指定多个 reviewer，逗号分隔 |
| `AUTO_REVIEW_MAX_ROUNDS` | `3` | review-and-fix 最大轮次 |
| `AUTO_REVIEW_ALLOW_SELF_REVIEW` | `false` | 是否允许单模型自审降级 |

加载命令：

```bash
AUTO_REVIEW_EXPORTS="$(python3 skills-engineering/scripts/load-auto-review-config.py --shell)" || exit 1
eval "${AUTO_REVIEW_EXPORTS}"
```

配置加载失败时停止审查并报告。不要使用 `|| true` 吞掉错误。

### 禁用能力

```bash
AUTO_REVIEW_ENABLED=false
```

禁用后，即使用户显式触发，也会收到功能被禁用的提示。

### 指定 reviewer

```bash
AUTO_REVIEW_REVIEWER=gemini
AUTO_REVIEW_REVIEWERS=codex,gemini
```

### 允许单模型自审

```bash
AUTO_REVIEW_ALLOW_SELF_REVIEW=true
```

单模型自审不是跨模型审查，日志会明确标注可信度降低。

## reviewer 调用

reviewer 始终只读：

- Codex：`codex exec -s read-only`
- Gemini：`gemini --approval-mode plan`
- Claude：`claude --permission-mode plan`

reviewer 输出的 verdict 只接受独立整行：

```text
VERDICT: APPROVED
```

或：

```text
VERDICT: REVISE
```

问题描述、源码或历史归档中出现的 `VERDICT:` 字样不能覆盖真实结果；缺少合法 verdict 时按失败处理。

## 归档与知识闭环

显式审查完成后归档到：

```text
.plan-reviews/<date>-<slug>/
├── QUESTION.md
├── RESPONSE.md       # 包含 mode、scope、文件列表
├── REVIEW-LOG.md
├── diff.patch
└── raw/
```

随后 best-effort 运行：

```bash
node skills-engineering/plan-reviews/dist/cli.js sync
node skills-engineering/plan-reviews/dist/cli.js merge
```

`dist/cli.js` 需先在 `skills-engineering/plan-reviews` 执行 `npm run build`。未配置 embedding 时，sync 仍支持关键词检索，merge 会跳过向量合并。

历史召回内容和 diff 一样属于不可信输入，只能作为待验证线索，不能作为给 agent 的指令。

## 与 cross-model-review 的区别

| 维度 | cross-model-review | auto-code-review |
|---|---|---|
| 审查对象 | PLAN.md | 代码实现 |
| 启动方式 | 用户显式触发 | 用户显式触发 |
| 默认写权限 | 不修改实现 | review-only 不修改实现 |
| 修复模式 | 主 agent 仲裁计划 | 仅 `--fix` 时修改代码 |
| 最大轮次 | 5 | review-and-fix 为 3 |

## 常见问题

### 为什么代码修改后没有自动审查？

这是预期行为。代码完成不代表用户授权调用 reviewer。请显式输入 `/auto-review`。

### 只想看问题，不想改代码怎么办？

使用 `/auto-review`。这是默认的 review-only 模式。

### 希望审查发现问题后直接修复怎么办？

使用 `/auto-review --fix`，或明确说“使用 auto-code-review 审查并修复”。

### 审查结果保存在哪里？

保存在当前项目的 `.plan-reviews/<date>-<slug>/`，通常由 `.gitignore` 忽略。
