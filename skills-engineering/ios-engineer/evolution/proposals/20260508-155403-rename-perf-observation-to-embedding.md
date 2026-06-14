# Skill Evolution Proposal

## Metadata
- Proposal ID: 20260508-155403-rename-perf-observation-to-embedding
- Created At: 2026-05-08 15:54:03 +0800
- Active Version At Creation: v49

## 问题信号
- v47 SKILL.md 审查发现 [ROUTE-009] 和 [ROUTE-010] 关键词「性能观测」重叠：
  - ROUTE-009 主读 observability_logging.md，关键词含"性能观测"
  - ROUTE-010 主读 performance_optimization.md，在"需要量化指标追加"时拉 observability_logging.md
- 用户输入"性能观测"两条规则都会触发，且两者都会牵到 observability_logging.md，区别只在"是否需要先看性能优化主线"。语义边界模糊，属于自进化触发信号「表达不清导致执行结果偏移」。
- 语义梳理：
  - "性能**观测**" = 观察性能（偏诊断），更贴近 ROUTE-010 性能问题主线
  - "性能**埋点**" = 给性能指标打埋点（偏基建），专属 ROUTE-009 可观测性主线
  - 用"性能埋点"替换"性能观测"后，ROUTE-009 的入口词集聚焦于"如何打点 / 如何记录"，与 ROUTE-010 的"如何诊断 / 如何优化"形成清晰分工。

## 变更类型
- 修正表达（保留 ROUTE-009、ROUTE-010 两个 ID，不退役、不替代；只把 ROUTE-009 的一个关键词从"性能观测"改为"性能埋点"）

## 变更内容
- 修改文件：
  - `SKILL.md` 第 43 行：[ROUTE-009] 的关键词列表把"性能观测"替换为"性能埋点"，其它关键词（日志 / 可观测性 / 必记字段 / 排障取证）和主读 ref 不变。
- 不修改：
  - `references/rule_index.md` 的 ROUTE-009 摘要（已经是 "日志 / 可观测性 / 必记字段 / 排障取证"，未包含"性能观测"词；摘要本就是压缩版，不需要随关键词原文变动）。
  - [ROUTE-010] 及其关键词、主读与追加 ref。
  - observability_logging.md 本身内容。
- 替代或合并旧规则：无（ROUTE-009 ID 沿用）

## 预期收益
- "性能观测"这个有二义的词从 SKILL.md 消失，不再同时落在两条 ROUTE 的关键词里。
- ROUTE-009（打点 / 基建）和 ROUTE-010（诊断 / 优化）的职责边界显化；用户描述"要给启动慢加监控" → ROUTE-010；描述"要把哪些字段记录下来" → ROUTE-009。
- SKILL.md 行数不变。

## 验证
- 结构校验：
  - `bash scripts/validate_rule_ids.sh` 保持通过（ID 不动，仅关键词文字替换）。
  - `SKIP_SNAPSHOT_CONSISTENCY=1 bash scripts/validate_skill_evolution.sh` 12 步全绿。
- 场景回放：
  - 6 个固定场景（layout / parameter-pass-through / concurrency / review / migration / mcp-control）不涉及 ROUTE-009 / ROUTE-010 的直接路由；本提案不改任何 IR / SYM / OUT，不改主读 ref；预期全部 pass。
- 残留风险：
  - 若之前用户真实任务里用"性能观测"描述过需求、并被路由到 ROUTE-009，本提案后同句表述会落到 ROUTE-010（"性能"关键词优先）。这是**设计内的**语义迁移，不是 bug；如果迁移后发现 ROUTE-010 加载的 ref 组合不够，由 ROUTE-010 的"需要量化指标追加 observability_logging.md"兜底。

## 状态
- promoted
