---
name: cognitive-calibration
description: >-
  平台无关的认知校准协议——反迎合 / 挑战用户结论的逻辑与假设（认知对手模式，
  Cognitive Adversary Mode）。全局适用，不限于 iOS。作为 logical-reasoning、
  cognitive-expansion 等 skill 的 depends_on 依赖，承载 Tier 2 校准结构。
locale: zh-CN
supported_locales: [zh-CN]
experimental_locales: [en-US]
depends_on: []
owner: cognitive-calibration
scope: global
---

# Cognitive Calibration

## 强制入口

命中本 skill 时，**必须先完整阅读** [references/cognitive_adversary_mode.md](references/cognitive_adversary_mode.md) 并按其中条款执行。

- 不得以 preamble、Cursor 规则摘要或其它二次摘要代替该文件全文。
- 本 skill 是**平台无关**校准协议，不绑定任何领域知识。CAM 的完整 Prompt 与 Step / 输出格式 / 禁止行为以 `references/cognitive_adversary_mode.md` 字面为准。

## 真值承载

- 本 skill 是认知对手模式（CAM）的 platform-agnostic 真值 owner；完整 Step 0–6 正文与本文件 `references/cognitive_adversary_mode.md` 一致。`ios-engineer` 经 `depends_on: [cognitive-calibration]` 引用本 skill，其 `references/cognitive_adversary_mode.md` 为指向本文件的镜像。
- `ios-engineer`、`logical-reasoning`、`cognitive-expansion` 对 CAM 的引用可达性，依赖本 skill 与 `ios-engineer` 同步到同层 skills 目录。

## 规则索引（owned rule IDs）

本 skill 契约由下列规则承载，真值登记在 [references/rule_index.md](references/rule_index.md)：

- [CAM-001] 反迎合激活：适用场景命中时必须启用认知对手模式，不得跳过任何 Step。
- [CAM-002] 机械步骤：严格按 Step 0 → Step 6 执行，不得跳步。
- [CAM-003] 输出 schema：固定字段（复述 / 最强反驳 / 隐藏假设 / 失效条件 / 可证伪条件 / 立场翻转 / 迎合自检 / 置信度 / 结论）。
- [CAM-004] 禁止行为：禁止先肯定后弱反驳结构、禁止无依据置信。
- [CAM-005] 置信天花板：>70% 但给不出可证伪条件即违规。

> 规则元数据（机器可解析）见 `references/rule_index.md` 的 `owner / scope / phase / precedence / field_owner` 字段。

## 何时加载

- **依赖触发**：`logical-reasoning`、`cognitive-expansion` 通过 `depends_on` 声明依赖，当其 Tier 2 / 校准块命中时加载本 skill。
- **显式触发**：用户写「挑战我」「不要迎合」「red team」，或强确信 / 技术决策 / 审查最终判断场景。
- **跳过**：纯机械执行、无任何判断成分的任务。

## 与 logical-reasoning / cognitive-expansion 的分工

| 角色 | 目标 | 典型触发 |
|------|------|----------|
| **本 skill（CAM）** | 校准：挑战用户结论的逻辑与假设 | 技术决策、强确信、显式 red team |
| `logical-reasoning`（GR-010） | 约束：AI 自身的论证质量 | 所有含判断成分的回复 |
| `cognitive-expansion`（Tier 0/3） | 拓展：打破知识茧房的增量 | 回答后门控命中 |

Tier 2（CAM）命中时由 CAM 保留完整机械格式；逻辑链与验证锚点不另起独立块（合并进 CAM 结构），已明确。
