# Skill Evolution Proposal

## Metadata
- Proposal ID: 20260509-104012-route-add-trigger-skip-anchors-per-route
- Created At: 2026-05-09 10:40:12 +0800
- Active Version At Creation: v61

## 问题信号
- 当前 ROUTE-001~018 仅以"关键词枚举"形式给出（"排障 / Bug / 偶现问题 / Crash"），更接近 taxonomy 而非 dispatcher：
  - 看起来像 X 但实际属于 Y 的输入（例如"线上崩了" 看起来是 ROUTE-001，但堆栈在 await 上更适合 ROUTE-007）缺乏明确反例引导；
  - 用户措辞模糊时（"这块越改越乱" 可能命中 ROUTE-002 / ROUTE-003 / ROUTE-007 / ROUTE-015），现有关键词无法区分；
  - 模型在分类首步就走偏，下游 ref 主读、追加策略全部跟着错。
- 横向参照：参考 SKILL（claude-api）frontmatter 描述里 `TRIGGER when: ...` / `SKIP: ...` 格式，对前置识别极为有效。本 skill 缺等价机制。

## 变更类型
- 修正表达（把 ROUTE-001~018 从"关键词枚举"升级为"TRIGGER / SKIP 锚点对"；不新增 / 退役任何 ID）

## 变更内容
- 修改文件：
  - SKILL.md：
    - ROUTE-001~018 每条 bullet 下追加两个子项：
      - `TRIGGER:` 2-4 个一眼识别的关键信号（用户措辞 / 输入特征 / 任务形态）。
      - `SKIP:` 1-3 个"看起来像但应去 ROUTE-XXX"的反例。
    - 不动主 bullet 的关键词清单与 ref 主读 / 追加链；只在下方加锚点对。
    - "### 路由优先级" 节末追加一句："分流时先按主关键词过 ROUTE 表，再用每条的 TRIGGER / SKIP 锚点确认；锚点对仅用于消歧，不替代主关键词。"
  - references/rule_index.md：
    - "任务分流 ROUTE-NNN" 表的"摘要"列保持原义不动（避免 SKILL.md 与本表双重维护 TRIGGER / SKIP）；改为在表下方追加一个简短说明："每个 ROUTE 的 TRIGGER / SKIP 锚点对落在 SKILL.md 内对应 bullet 下方；本表"摘要"列只保留主关键词集，避免重复维护。"
    - "## 跨文件共享概念索引" 中"任务分流主关键词集"行的"修改协议"列追加一句："新增 / 调整 ROUTE 的 TRIGGER / SKIP 锚点不改本表摘要列；只有主关键词集变化时才同步本表。"
- 替代或合并旧规则：本提案不替代任何 ID；ROUTE-001~018 的主关键词、ref 主读、追加链均不变，仅在 bullet 下追加锚点对。

## 预期收益
- 分类首步从"关键词模糊匹配"升级为"关键词 + 反例消歧"，分类错误率下降。
- 高频混淆对（ROUTE-001 vs ROUTE-007 / ROUTE-002 vs ROUTE-003 / ROUTE-005 vs ROUTE-007 / ROUTE-010 vs ROUTE-007 等）有明确"看起来像 X 但走 Y"的引导。
- 每条 ROUTE bullet 自包含识别条件，无需读 ref 即可正确路由。

## 验证
- 结构校验：scripts/validate_skill_evolution.sh + scripts/validate_rule_ids.sh + scripts/validate_scenario_specs.sh。
- 场景回放：6 场景结构校验；本提案不改输出行为，但改路由前置识别条件，需要确认现有场景仍按原 ROUTE 主读 ref 命中。
- 残留风险：
  - SKILL.md 行数从 67 升至约 130（仍远低于 500 上限），但单文件信息密度上升；后续如果 ROUTE 数量再扩，需要考虑把锚点对挪到独立 ref。
  - TRIGGER / SKIP 锚点本身需要维护：用户实际输入分布若与锚点不符，会反过来误导分流。需要在 usage_ledger 后续记录里观察 ROUTE 分类偏差信号，作为下一轮提案触发条件。
  - SKIP 中引用的目标 ROUTE 在调整 ROUTE 关键词时可能 stale；rule_index.md 跨文件共享概念已捕获主关键词集变更的同步要求，但 SKIP 引用目标的同步未单列。如果未来频繁出现 SKIP 引用 stale，需要补充 rule_index 修改协议。

## 状态
- promoted
