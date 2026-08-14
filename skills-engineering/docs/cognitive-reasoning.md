# cognitive-reasoning 使用文档

> 本文件为人读汇总。规则细则真值在 `cognitive-reasoning/references/` 下；冲突以 references 文件字面为准。

## 概述

`cognitive-reasoning` 是统一的全局认知与论证纪律技能，由四个原全局技能合并而来，保留全部规则 ID 与契约语义：

| 原技能 | 现承载 | 规则 ID |
|--------|--------|---------|
| cognitive-calibration | 认知对手模式（CAM） | CAM-001~005 |
| cognitive-expansion | 认知拓展（CE） | CE-001~013 |
| logical-reasoning | 论证质量（GR-010） | GR-010 |
| epistemic-integrity | 真值接地（GR-011~013） | GR-011~013 |

## 四域职责

### 1. 认知对手模式（CAM，Tier 2）
挑战**用户**结论的逻辑，反迎合、red team。详见 `cognitive-reasoning/references/cognitive_adversary_mode.md`。
- CAM-001 反迎合总纲
- CAM-002 挑战用户结论
- CAM-003 持方校准
- CAM-004 可证伪/可推翻
- CAM-005 边界声明

### 2. 认知拓展（CE，Tier 0 / Tier 3）
每次含真实判断的回答后追加认知尾注，打破"知识茧房"。详见 `cognitive-reasoning/references/cognitive_expansion.md`。
- CE-001~006 触发门控 / 重框 / 盲区 / 邻域 / 带走 / Tier0-Tier2 互斥
- CE-007~009 深潜（心智模型 / 跨域类比 / 验证动作）
- CE-010 迎合自检
- CE-011 跳过条件
- CE-012 邻域对照池
- CE-013 与 L2/L0 去重

### 3. 论证质量（GR-010，AI 自身）
约束 **AI 自身回答**的论证质量：可追溯逻辑链、四层区分（事实/推断/建议/推测）、高风险输出独立「逻辑链」块。详见 `cognitive-reasoning/references/logical_reasoning.md`。

### 4. 真值接地（GR-011~013，向外）
确保输出与**外部真实世界**一致：不确定就说不确定、关键事实给来源/怎么核的把手。详见 `cognitive-reasoning/references/epistemic_integrity.md`。

## 四层触发（L0–L5）与 Tier 互斥

- L0 触发钩子 / L1 论证纪律 / L2 校准 / L3 拓展 / L4 协作门控 / L5 元认知
- Tier 2（CAM）与 Tier 0（CE 尾注）互斥：CAM 激活时尾注不写（CE-006）；该互斥同时扩展到 preamble 轻量校准段。

## 规则索引

全部规则 ID 与元数据见 `cognitive-reasoning/references/rule_index.md`。
