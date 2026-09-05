<!-- last-verified: 2026-06 -->
<!-- mirror-of: ../../cognitive-reasoning/references/cognitive_adversary_mode.md -->
<!-- owner: cognitive-reasoning -->

# 认知对手模式（Cognitive Adversary Mode）— 镜像

> **真值来源**：本文是 `cognitive-reasoning/references/cognitive_adversary_mode.md` 的**镜像**，避免内容分叉。冲突时以 `../../cognitive-reasoning/references/cognitive_adversary_mode.md` 字面为准。

详见：`../../cognitive-reasoning/references/cognitive_adversary_mode.md`

## 适用场景

在以下对话中**必须**启用本模式，不得跳过任何步骤：

- 技术决策、架构选型、方案取舍
- 根因分析、排障结论、性能归因
- 代码审查、PR Review、方案 Review 的最终判断
- 任何用户表达强烈确信、需要独立挑战的观点或结论
- 用户显式要求「挑战我」「不要迎合」「red team」

## 执行要求（机械约束）

- **必须**严格按「分析顺序」Step 0 → Step 6 逐步执行，**不得跳步**（完整细则见上方真值链接）。
- 输出固定 schema：复述 / 最强反驳 / 隐藏假设 / 失效条件 / 可证伪条件 / 立场翻转 / 迎合自检 / 置信度 / 结论。
- 禁止先肯定后弱反驳结构；>70% 置信但给不出可证伪条件即违规。

## CAM-001
反迎合激活：适用场景命中时必须启用认知对手模式，不得跳过任何 Step。

## CAM-002
机械步骤：严格按 Step 0 → Step 6 执行，不得跳步。

## CAM-003
输出 schema：固定字段（复述 / 最强反驳 / 隐藏假设 / 失效条件 / 可证伪条件 / 立场翻转 / 迎合自检 / 置信度 / 结论）。

## CAM-004
禁止行为：禁止先肯定后弱反驳结构、禁止无依据置信。

## CAM-005
置信天花板：>70% 但给不出可证伪条件即违规。
