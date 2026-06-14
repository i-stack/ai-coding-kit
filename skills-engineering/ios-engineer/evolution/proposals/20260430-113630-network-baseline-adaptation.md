# Skill Evolution Proposal

## Metadata
- Proposal ID: 20260430-113630-network-baseline-adaptation
- Created At: 2026-04-30 11:36:30 +0800
- Active Version At Creation: v17

## 问题信号
- `architecture_and_network.md` L76 "底层使用 `URLSession + async/await`" 作为无条件强制要求，与既有仓库实际技术基线冲突。
- 以 Bajoseek 项目为例：AGENTS.md 明确指出使用 CocoaPods + 已有 `BajoSeekNetWork` 自研网络层 + SSE 流式管线；这些既有实现不一定基于原生 `URLSession + async/await`，可能混用 callback、Combine、自定义传输抽象。
- 当 AI 在该项目内做局部网络改动（例如新增一个请求、修一个字段、调整重试策略）时，读到"底层必须 URLSession + async/await"会误判为需要迁移底层实现，违背 SKILL.md 核心铁律 L13 最小修复。
- 同类问题会出现在任何使用 Alamofire、Moya、自研网络框架的既有项目。

## 变更类型
- 修正表达：把"底层必须"改为"新建 vs 既有" 分流，避免把技术栈选择强制化。

## 变更内容
- 修改文件：`references/architecture_and_network.md`
  - 修改 "强制要求" L76 第二条：
    - 原：`底层使用 URLSession + async/await。`
    - 改为：`新建独立网络能力优先使用 URLSession + async/await（或项目已统一的等价抽象）；既有网络层（例如自研 NetworkManager、Alamofire、Combine-based 抽象）按现有抽象扩展，不在局部改动中顺手迁移底层实现。底层迁移必须单独立项，参考 [migration_strategy.md](migration_strategy.md)。`
  - 保留其他强制要求条款不变（统一请求抽象 / 解码策略集中 / 错误分层建模 / 日志记录请求标识）—— 这些是跨实现的通用约束。
- 替代或合并旧规则：
  - "底层必须 URLSession + async/await" 语义退役，由"新建 vs 既有"分流版本承担。
  - 新规则显式引用 migration_strategy.md，把"底层迁移"归到迁移场景而不是日常改动场景。

## 预期收益
- AI 在 Bajoseek / Alamofire / 自研网络层项目中做局部网络改动时不再误判为需要底层迁移，符合最小修复铁律。
- 新建项目或独立模块仍能按"优先 URLSession + async/await"的默认方向执行。
- 迁移场景显式归到 migration_strategy.md，避免日常改动被迁移门禁牵连。

## 验证
- 结构校验：
  - `SKILL.md` frontmatter 合法，行数 ≤ 500（本提案不改 SKILL.md）。
  - `SKILL.md` 引用的所有 `references/*.md` 文件存在。
  - `root_cause_enforcement.md` / `examples.md` 分层守卫不受影响。
- 场景回放：
  - 新增隐式验证（Bajoseek 语境）：用户输入"在 BajoSeekNetWork 里加一个新的 API 请求"。期望 AI 按既有 `BajoSeekNetWork` 抽象扩展，不建议迁移到 URLSession + async/await。
  - 场景 `migration`：用户输入"准备把网络层迁到 async/await"。期望 AI 识别为迁移任务，命中 migration_strategy.md 的阶段化迁移规则。
- 残留风险：
  - "新建 vs 既有"判断依赖 AI 识别当前代码上下文，若 AI 在没有代码上下文的对话中回答"如何设计网络层"这类抽象问题，可能仍需补充"默认方向 vs 既有约束"的明确提问。

## 状态
- promoted
