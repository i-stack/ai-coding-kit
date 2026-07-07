# auto-code-review 使用文档

## 概述

`auto-code-review` 是一个自动代码审查 skill，在 AI 生成代码后自动调用跨模型审查，循环修复直到通过，最终归档到 `.plan-reviews` 目录。

## 工作原理

```
用户提问 → AI 生成代码 → 自动触发审查 → reviewer 审查 → 发现问题？
                                                      ↓ 是
                                              主 agent 修复 → 再次审查（循环）
                                                      ↓ 否（或达到 MAX_ROUNDS）
                                              归档到 .plan-reviews/
```

## 触发条件

### 自动触发

主 agent 生成代码修改后自动执行，无需用户干预。触发条件：

- 回复中包含代码修改（非 .md 文件）
- 非 trivial 改动（排除：单行注释、格式化、typo 修复）
- 有可用 reviewer CLI（codex/gemini/claude）

### 用户触发

用户可以说：
- `auto-review`
- `审查代码`
- `review 一下`
- `检查一下代码`

### 跳过条件

- 纯文档更新（只有 .md 文件变更）
- trivial 改动（< 5 行非空白变更）
- 用户明确"不用审查" / "直接实施"
- 无可用 reviewer CLI 且单模型降级被禁用

## 配置选项

### 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `AUTO_REVIEW_REVIEWER` | 自动选择 | 指定单个 reviewer（codex/gemini/claude） |
| `AUTO_REVIEW_REVIEWERS` | 自动选择 | 指定多个 reviewer（逗号分隔） |
| `AUTO_REVIEW_MAX_ROUNDS` | `3` | 审查轮次上限 |
| `AUTO_REVIEW_ALLOW_SELF_REVIEW` | `true` | 是否允许单模型自审降级 |

### 示例

```bash
# 只使用 codex 作为 reviewer
AUTO_REVIEW_REVIEWER=codex

# 使用 codex 和 gemini 并行审查
AUTO_REVIEW_REVIEWERS=codex,gemini

# 最多审查 5 轮
AUTO_REVIEW_MAX_ROUNDS=5

# 禁用单模型自审（无可用 reviewer 时跳过审查）
AUTO_REVIEW_ALLOW_SELF_REVIEW=false
```

## 审查流程

### 1. 检测代码变更

```bash
git diff --name-only HEAD  # 获取变更文件列表
git diff HEAD              # 获取完整 diff
```

### 2. 探测可用 reviewer

```bash
bash skills-engineering/scripts/detect-review-clis.sh
```

### 3. 调用 reviewer（只读模式）

- **Codex**: `codex exec -s read-only`
- **Gemini**: `gemini -p ... --approval-mode plan`
- **Claude**: `claude -p ... --permission-mode plan`

### 4. 解析审查结果

reviewer 输出：
- `VERDICT: APPROVED` → 无 CRITICAL/HIGH 问题，进入归档
- `VERDICT: REVISE` → 存在问题，主 agent 仲裁并修复

### 5. 循环修复

主 agent 根据审查意见修复代码 → 再次调用 reviewer → 循环直到 APPROVED 或达到 MAX_ROUNDS。

### 6. 归档

审查完成后自动归档到 `.plan-reviews/<date>-<slug>/`：

```
.plan-reviews/2026-07-07-login-fix/
├── QUESTION.md           # 用户原始问题
├── RESPONSE.md           # AI 代码回复摘要
├── REVIEW-LOG.md         # 审查日志
├── diff.patch            # 变更 diff
└── raw/                  # reviewer 原始输出
    ├── codex-round1.json
    └── gemini-round1.json
```

## 单模型降级模式

当只有一个 reviewer CLI 可用时，进入单模型降级模式：

- 使用同一模型但切换为对抗式审查 prompt
- 在 REVIEW-LOG.md 顶部添加 WARNING 标注
- 审查可信度降低，建议安装其他 reviewer CLI

禁用降级：
```bash
AUTO_REVIEW_ALLOW_SELF_REVIEW=false
```

## Deadlock 处理

当 MAX_ROUNDS 用尽仍未通过审查时：

- 输出 deadlock 报告，列出所有未解决问题
- 主 agent 给出反立场
- 交用户裁决，**不假装 approved**

## 与 cross-model-review 的区别

| 维度 | cross-model-review | auto-code-review |
|------|-------------------|------------------|
| 审查对象 | PLAN.md（实现计划） | 代码实现 |
| 触发方式 | 用户手动 | 自动 |
| MAX_ROUNDS | 5 | 3 |
| 前置条件 | 需要 PLAN.md | 无前置 |
| 使用场景 | 实施前审查计划 | 实施后审查代码 |

## 完整工作流

```
复杂任务：problem-analysis → plan-grill → cross-model-review → 实施 → [auto-code-review] → 归档
简单任务：直接回答 → 实施 → [auto-code-review] → 归档
```

auto-code-review 是流程的最后一环，确保实施质量。

## 常见问题

### Q: 为什么我的代码修改没有触发审查？

检查以下条件：
1. 是否有可用 reviewer CLI（codex/gemini/claude）？
2. 变更是否非 trivial（> 5 行非空白变更）？
3. 是否只有 .md 文件变更？
4. 用户是否说了"不用审查"？

### Q: 如何指定特定的 reviewer 模型？

设置环境变量：
```bash
AUTO_REVIEW_REVIEWER=codex  # 只使用 codex
```

### Q: 如何禁用自动审查？

在回复中说"不用审查"或"直接实施"，或设置：
```bash
AUTO_REVIEW_ALLOW_SELF_REVIEW=false
```

### Q: 审查结果保存在哪里？

`.plan-reviews/<date>-<slug>/` 目录，默认加入 `.gitignore`。
