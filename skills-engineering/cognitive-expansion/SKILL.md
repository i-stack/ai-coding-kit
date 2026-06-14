---
name: cognitive-expansion
description: >-
  每次回复后的认知拓展（重框/盲区/邻域/带走），打破知识茧房；与 ios-engineer
  认知对手模式互补。全局适用，不限于 iOS 工程。
---

# Cognitive Expansion

## 强制入口

命中本 skill 时，**必须先完整阅读** [references/cognitive_expansion.md](references/cognitive_expansion.md) 并按其中条款执行。

- 不得以 preamble、Cursor 规则摘要或其它二次摘要代替该文件全文。
- Tier 2（认知对手）由 [ios-engineer references/cognitive_adversary_mode.md](../ios-engineer/references/cognitive_adversary_mode.md) 承载；本 skill 管 Tier 0 / Tier 3 拓展。

## 何时加载

- **门控**：Tier 0 认知尾注**默认不触发**；仅当本次回答含真实判断 / 取舍 / 归因 / 设计选择，**且**能产出至少 1 条可证伪盲区时才追加，否则静默（判据见详规「触发门控」）。
- **加深**：用户写 `【深潜】` / `【拓展】`（Tier 3）。
- **跳过**：用户明确「只要答案 / 不要延伸」；或门控未命中。
