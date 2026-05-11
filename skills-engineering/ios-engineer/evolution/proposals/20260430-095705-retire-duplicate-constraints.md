# Skill Evolution Proposal

## Metadata
- Proposal ID: 20260430-095705-retire-duplicate-constraints
- Created At: 2026-04-30 09:57:05 +0800
- Active Version At Creation: v2

## 问题信号
- SKILL.md 主文件 L78-80/L83/L94-95 共 6 条"强制纪律"与 `domain_modeling.md`、`swift_concurrency.md`、`ui_state_patterns.md`、`layout_and_ui.md`、`architecture_and_network.md`、`networking_patterns.md`、`observability_logging.md` 存在直接重复。
  - L79 "谁创建、谁持有、谁取消、何时释放" 与 `swift_concurrency.md:28` "谁创建、谁持有、谁取消、何时结束" 几乎原文。
  - L80 "不用多个布尔值拼状态" 同义约束出现在 `domain_modeling.md:69/96`、`ui_state_patterns.md:15`、`layout_and_ui.md:116` 共 4 处。
  - L83 参数透传约束与 `architecture_and_network.md:23-29` 的"参数透传与数据来源"完整重复；`review_checklists.md:14` 有对应检查项。
- SKILL.md L99-102 "交付门禁"四条（并发/迁移/发布/性能门禁）与对应 reference 中已有的验证要求和清单重复。
- SKILL.md L111-116 "快速检查"六条全部在 `review_checklists.md` 六维清单中覆盖，作为自我提醒列表对 skill agent 没有独立驱动力，只增加主文件体积和规则不一致的维护面。

## 变更类型
- 退役规则：移除主文件中与 reference 重复的纪律、门禁、快速检查条目；职责下沉到对应 reference，场景规则已建立引用链路。

## 变更内容
- 修改文件：`SKILL.md`
  - 退役 "强制纪律" 中 L78（DTO/Entity/ViewState/ErrorModel 分层，已在 `domain_modeling.md` + `terminology.md`）。
  - 退役 "强制纪律" 中 L79（异步四问，已在 `swift_concurrency.md`）。
  - 退役 "强制纪律" 中 L80（不用多个布尔值拼状态，已在 `domain_modeling.md` + `ui_state_patterns.md` + `layout_and_ui.md`）。
  - 退役 "强制纪律" 中 L83（参数透传完整调用链，已在 `architecture_and_network.md` + `review_checklists.md`）。
  - 退役 "强制纪律" 中 L94（网络边界/缓存/重试/鉴权/错误分层/幂等，已在 `architecture_and_network.md` + `networking_patterns.md`）。
  - 退役 "强制纪律" 中 L95（日志/埋点/性能观测/排障取证，已在 `observability_logging.md`）。
  - 退役 "交付门禁" 中 L99-102（并发/迁移/发布/性能四条细则，对应约束全部在 `swift_concurrency.md`、`migration_strategy.md`、`build_release_and_ci.md`、`performance_optimization.md`），保留 L103 作为全局输出门禁（声明"已覆盖、未覆盖、残留风险"）。
  - 退役 "快速检查" 整节（L110-116），不替换为新检查；read：`review_checklists.md` 覆盖所有六维。
- 替代或合并旧规则：
  - 退役条款的全部职责在本提案 Metadata.Active Version v2 时已由对应 reference 持有，无需再在 SKILL.md 重复。
  - 场景规则与首步分流 v2 已建立完整引用链路，任务分流时仍能命中对应 reference。
- 保留不改动：
  - "强制纪律" 保留 L77（分层边界/依赖注入/单向数据流/模块治理，跨多份文档的总纲）、L81-82（UI 布局硬编码/priority(999) 禁用，虽与 `layout_and_ui.md` 有覆盖关系但本次提案不处理 UI 风格维度）、L84-93（Swift 编码风格，用户未批准本轮下沉，保留原位）、L96（规则变更元约束）。
  - "交付门禁" 仅保留 L103 全局输出门禁。
  - 其他章节（核心职责、场景规则、输出模板、首步分流、执行流程、测试体系、参考资料加载规则）不改。

## 预期收益
- SKILL.md 预计从 116 行减少到约 94 行（减少 22 行），上下文每次加载节省约 500 字的重复规则。
- 消除主文件与 reference 之间的同义多份定义，降低未来修改规则时只改一处的不一致风险。
- 主文件中铁律、场景规则、输出模板、分流、纪律层次更清晰，不再把单条细则混入主纪律。
- `review_checklists.md` 成为代码审查检查项的单一来源，主文件"快速检查"退役后读者不再面临两份互相不同步的检查清单。

## 验证
- 结构校验：
  - `SKILL.md` frontmatter 合法，行数 ≤ 500。
  - `SKILL.md` 引用的所有 `references/*.md` 文件存在（引用集本次提案不增不减）。
  - `root_cause_enforcement.md` / `examples.md` 分层守卫不受影响。
  - 对比 SKILL.md 旧版 v2 与新版，被退役的 6+4+6 条规则无一例外在 reference 中有等价或更完整的覆盖。
- 场景回放：
  - 场景 `review`：用户输入"review 这个改动，重点看有没有隐藏回归"。期望命中 `review_checklists.md` 六维清单，不再依赖 SKILL.md 的"快速检查"。
  - 场景 `parameter-pass-through`：用户输入"修一下 A 类这个方法。新增字段 currentModel，但它现在在 A 里拿不到，B 里也没有"。期望通过场景规则命中 `architecture_and_network.md` 的参数透传小节，不再依赖 SKILL.md 的 L83 铁律。
- 残留风险：
  - 未处理的 L81-82 仍与 `layout_and_ui.md` 有潜在重复，需后续单独提案评估。
  - 未处理的 L84-93 Swift 风格规则未下沉，主文件仍混入风格约束；需后续"风格下沉"提案处理。
  - 未处理的 L25-26"当前架构"专项规则仍在场景规则节内，下沉到 `architecture_and_network.md` 为后续"当前架构专项下沉"提案范围。
  - 未处理的 L19（最小修复） vs L25（Code Review 级别指出问题）场景冲突，需在下沉"当前架构"规则时一并解决。

## 状态
- promoted
