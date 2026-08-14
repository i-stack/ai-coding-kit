---
name: logical-reasoning
description: 全局论证纪律——可追溯逻辑链、层级分明、因果克制、逻辑链输出块（GR-010）。适用所有工程任务，不限平台。
locale: zh-CN
supported_locales: [zh-CN]
experimental_locales: [en-US]
depends_on: [cognitive-calibration]
---

# Logical Reasoning

## 强制入口

命中本 skill 时，**必须先完整阅读** [references/logical_reasoning.md](references/logical_reasoning.md) 并按其中条款执行。

- 不得以 preamble、Cursor 规则摘要或其它二次摘要代替该文件全文。
- 依赖闭包：本 skill 通过 `depends_on: [cognitive-calibration]` 声明对认知对手模式（CAM）的依赖；CAM 真值承载于 `cognitive-calibration` skill（`cognitive-calibration/references/cognitive_adversary_mode.md`，platform-agnostic owner），`ios-engineer` 仅维护指向该真值的镜像。同步到各端时，需确保 `cognitive-calibration`（及 `ios-engineer`）skill 同步到同层 skills 目录，否则 Tier 2 跳转链接失效。**条件性**：该链接仅在依赖 skill 已同步到同层 skills 目录时可达；非 iOS 环境（未同步 ios-engineer）下，本 skill 的 GR-010 约束本身完整可用，仅"与认知对手模式分工"的 Tier 2 跳转失效，不影响核心论证纪律。

## GR-010 核心规则

- [GR-010] 回复必须具备可追溯的逻辑链；须区分「事实 / 推断 / 建议 / 推测」，不得把未验证推断写成定论；禁止无依据的因果跳跃、循环论证、同一回复内自相矛盾；非显然判断至少标出一步「因为…所以…」；证据不足时标明不确定，不得用流畅措辞伪装确定性。高风险判断时输出须包含独立「逻辑链」块，字段为：事实/证据、推断、结论强度、可证伪/缺口。细则见 [logical_reasoning.md](references/logical_reasoning.md)。

## 何时加载

- **默认**：所有含判断成分的任务。
- **必须输出逻辑链块**：技术决策、架构取舍、根因归因、性能归因、审查最终判断、用户强烈确信或显式要求挑战观点。
- **跳过**：纯机械执行、无任何判断成分的任务。

## 与认知对手模式的分工

| 角色 | 目标 | 典型触发 |
|------|------|----------|
| [认知对手模式](../cognitive-calibration/references/cognitive_adversary_mode.md)（cognitive-calibration） | 校准：挑战用户结论的逻辑与假设 | 技术决策、强确信、显式 red team |
| **本 skill（GR-010）** | 约束：AI 自身的论证质量 | 所有含判断成分的回复 |
