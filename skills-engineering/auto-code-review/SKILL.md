---
name: auto-code-review
description: 自动代码审查——AI 生成代码后自动调用跨模型审查，循环修复直到通过，归档到 .plan-reviews。支持可配置 reviewer 模型，单模型时降级为自审模式。
---

# Auto Code Review

## 强制入口

命中本 skill 时，**必须先完整阅读** [references/auto_code_review.md](references/auto_code_review.md) 并按其中条款执行。

- 不得以 preamble、Cursor 规则摘要或其它二次摘要代替该文件全文。
- 本 skill 在代码生成后自动触发，无需用户显式调用。

## 八条核心规则

- [ACR-001] **自动触发**：主 agent 生成包含代码修改的回复后，自动检测是否有可用 reviewer CLI（codex/gemini/claude）。有则进入审查流程，无则跳过（静默降级，不阻断用户工作流）。
- [ACR-002] **审查范围**：只审查本次回复中新增/修改的代码。主 agent 将变更文件列表 + diff 作为审查输入，不审查未变更代码。
- [ACR-003] **reviewer 只读**：复用现有 CLI adapter 架构（codex `-s read-only`、gemini `--approval-mode plan`、claude `--permission-mode plan`）。reviewer 不写代码，只输出审查意见。
- [ACR-004] **修复由主 agent 执行**：reviewer 输出审查意见 → 主 agent 仲裁并修复 → 再调用 reviewer 审查 → 循环。reviewer 永远不直接修改代码。
- [ACR-005] **MAX_ROUNDS=3**：代码审查轮次上限为 3。3 轮后仍有问题则标记为"待人工审查"，不假装通过，输出 deadlock 报告。
- [ACR-006] **自动归档**：审查完成后自动保存到 `.plan-reviews/<date>-<slug>/`，包含原始问题、代码回复、审查日志、diff。归档是强制的，不可跳过。
- [ACR-007] **可配置 reviewer**：支持用户指定 reviewer 模型/CLI。默认自动选择与主 agent 不同 provider 的模型。用户可通过环境变量或参数覆盖默认选择。
- [ACR-008] **单模型降级**：只有一个模型可用时，使用同一模型但切换为对抗式审查 prompt 策略，并在日志中标注"同模型自审，可信度降低"。降级模式不阻断流程。

细则见 [references/auto_code_review.md](references/auto_code_review.md)。

## 何时加载

- **自动触发**：主 agent 生成代码修改后自动加载（无需用户关键词）。
- **用户触发**：用户说 `auto-review` / `审查代码` / `review 一下` / `检查一下代码`。
- **跳过**：
  - trivial 改动（typo、格式化、注释修改、单行配置）
  - 纯文档更新（.md 文件）
  - 用户明确"不用审查" / "直接实施"
  - 无可用 reviewer CLI 且单模型降级被禁用

## 与相邻 skill 的分工

| Skill | 分工 |
|-------|------|
| `plan-grill`（PG-001~005） | 盘问锁定 PLAN.md（Act 1） |
| `cross-model-review`（CMR-001~005） | 跨模型对抗审查 PLAN.md（Act 2） |
| **auto-code-review（本 skill）** | 代码实施后自动审查代码质量（Act 3） |
| `engineering-discipline`（GR-002） | 代码修改时的工程纪律约束 |
| `epistemic-integrity`（GR-011~013） | 审查时的真值接地纪律 |

## 完整工作流

```
复杂任务：problem-analysis → plan-grill → cross-model-review → 实施 → [auto-code-review] → 归档
简单任务：直接回答 → 实施 → [auto-code-review] → 归档
```

auto-code-review 是流程的最后一环，确保实施质量。
