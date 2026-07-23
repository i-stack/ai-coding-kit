---
name: cognitive-expansion
description: >-
  每次回复后的认知拓展（重框/盲区/邻域/带走），打破知识茧房；与 ios-engineer
  认知对手模式互补。全局适用，不限于 iOS 工程。
locale: zh-CN
supported_locales: [zh-CN]
---

# Cognitive Expansion

## 强制入口

命中本 skill 时，**必须先完整阅读** [references/cognitive_expansion.md](references/cognitive_expansion.md) 并按其中条款执行。

- 不得以 preamble、Cursor 规则摘要或其它二次摘要代替该文件全文。
- Tier 2（认知对手）由 [ios-engineer references/cognitive_adversary_mode.md](../ios-engineer/references/cognitive_adversary_mode.md) 承载；本 skill 管 Tier 0 / Tier 3 拓展。
- 同步依赖：本 skill 通过相对路径引用 `../ios-engineer/references/cognitive_adversary_mode.md`；同步到各端时，需确保 `ios-engineer` skill 也同步到同层 skills 目录（如 `~/.claude/skills/ios-engineer`），否则该链接失效。**条件性**：仅当 ios-engineer 已同步到同层 skills 目录时，Tier 2 链接可用；非 iOS 环境（未同步 ios-engineer）下，本 skill 仅提供 Tier 0 / Tier 3，Tier 2 需用户显式加载 ios-engineer，不得因链接不可达而中断 Tier 0/3。

## 何时加载

- **门控**：Tier 0 认知尾注**默认不触发**；仅当本次回答含真实判断 / 取舍 / 归因 / 设计选择，**且**能产出至少 1 条可证伪盲区时才追加，否则静默（判据见详规「触发门控」）。
- **加深**：用户写 `【深潜】` / `【拓展】`（Tier 3）。
- **跳过**：用户明确「只要答案 / 不要延伸」；或门控未命中。

## 规则索引（owned rule IDs）

本 skill 的契约由下列 `CE-NNN` 规则承载，真值登记在 [references/rule_index.md](references/rule_index.md)。形态校准示例（before/after 与退化标本）见 [references/examples.md](references/examples.md)。行为门禁 `scripts/validate-skill-behavior.sh` 的 Check 2 校验二者 ID 集合双向一致（SKILL.md 声明的 ID 均被定义；rule_index.md 中 active 行均被 SKILL.md 声明）。

- [CE-001] Tier 0 触发门控：双条件（有判断成分 且 能产出≥1 条可证伪盲区）同时成立才追加认知尾注，否则静默不写。
- [CE-002] 重框：把问题提升为更一般判断/学习问题；纯执行任务写「重框略」。
- [CE-003] 盲区（可证伪硬判据）：1 条隐藏假设/遗漏维度/误区，须含（假设 X）+（可观测触发 Y）+（若 Y 则 X 错的否定条件）；写不出整段不写。
- [CE-004] 邻域（机制相关）：1 条相邻领域对照，须与当前问题机制相关，禁同技术栈换词重复主文。
- [CE-005] 带走：1 条可复用自检问句或 if-then 规则，禁鸡汤。
- [CE-006] Tier 0/Tier 2 互斥：认知对手（Tier 2）命中时输出完整校准结构，不再单独写 Tier 0；该互斥同时扩展到 preamble 轻量校准段（CAM 激活时由 CAM 完整结构承载，见 cognitive-calibration 段）。
- [CE-007] 深潜·心智模型：模型名 + 1 句如何用于本问题。
- [CE-008] 深潜·跨域类比：非本技术栈、机制对齐的 1 个类比；须点名被映射机制、禁陈词/换词类比（护栏见 references/cognitive_expansion.md §Tier 3）。
- [CE-009] 深潜·验证动作：7 天内可做的 1 个具体动作。
- [CE-010] 迎合自检：写完过三问（邻域非换词 / 带走非鸡汤 / 盲区可证伪）。
- [CE-011] 跳过条件：用户「只要答案/不要延伸」或门控未命中即不写 Tier 0。
- [CE-012] 邻域对照池：从对照池任选 1 条且须与机制相关。
- [CE-013] 与 L2/L0 去重：同轮 logical-reasoning「逻辑链（可证伪/缺口）」或 problem-analysis「问题分析」已发时，盲区须换维度不得复述。
