# cognitive-calibration Agent 调用指南

## 一句话描述

平台无关的认知校准协议——反迎合 / 挑战用户结论的逻辑与假设（认知对手模式，Cognitive Adversary Mode）。全局适用，不限于 iOS。作为 `logical-reasoning`、`cognitive-expansion` 的 `depends_on` 依赖，承载 Tier 2 校准结构。

## 何时调用

- **依赖触发**：`logical-reasoning` / `cognitive-expansion` 命中 Tier 2 校准时，经 `depends_on` 加载本 skill。
- **显式触发**：用户写「挑战我」「不要迎合」「red team」，或强确信 / 技术决策 / 审查最终判断场景。
- **跳过**：纯机械执行、无任何判断成分的任务。

## 关键行为

1. **[CAM-001]** 适用场景命中时必须启用认知对手模式，不得跳过任何 Step。
2. **[CAM-002]** 严格按 Step 0 → Step 6 执行（细则见 `references/cognitive_adversary_mode.md`）。
3. **[CAM-003]** 输出固定 schema（复述 / 最强反驳 / 隐藏假设 / 失效条件 / 可证伪条件 / 立场翻转 / 迎合自检 / 置信度 / 结论）。
4. **[CAM-004]** 禁止先肯定后弱反驳结构、禁止无依据置信。
5. **[CAM-005]** >70% 置信但给不出可证伪条件即违规。

## 不调用的情况

- 纯机械执行
- 无任何判断成分（纯信息复述）
- 纯主观偏好/创作
