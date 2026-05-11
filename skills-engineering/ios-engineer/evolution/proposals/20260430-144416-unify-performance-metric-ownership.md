# Skill Evolution Proposal

## Metadata
- Proposal ID: 20260430-144416-unify-performance-metric-ownership
- Created At: 2026-04-30 14:44:16 +0800
- Active Version At Creation: v27

## 问题信号
- 按 self_evolution.md v26 新增的跨文件 grep 约束执行全目录扫描，确认**性能指标口径**（指标名 / 触发路径 / 工具清单）同时定义在 `performance_optimization.md` 和 `observability_logging.md` 两份文件：

| 内容 | performance_optimization.md | observability_logging.md |
|---|---|---|
| 指标清单（启动/首屏/帧率/主线程/内存/耗时） | L17 + L5-L8 散落 | L56-61 集中定义 |
| 触发路径（冷/热启动/滚动/后台切前台） | L18 | L53 |
| 工具清单（Instruments / Memory Graph / OSLog / MetricKit / Time Profiler / Core Animation / Points of Interest） | L19 简略 + L55-59 详细 | L54 简略 |

- 两处视角略不同（observability 是 "观测口径"，performance 是 "优化决策流"），但**指标名和工具名完全重复**。
- 后续修改指标口径（例如新增"WebView 加载耗时"或 FPS 阈值调整）时需要两处同步，容易漂移。
- `performance_optimization.md` 的真正独立价值在 "如何根据指标决策优化"（L13 阈值规则 + L22-47 SwiftUI / UIKit / 启动 / 内存专项优化），指标和工具清单不是它的核心贡献。

## 变更类型
- 合并重复：指标采集口径（什么指标 / 如何量化 / 用什么工具采集）单一归属 `observability_logging.md`；`performance_optimization.md` 改为引用 + 聚焦优化决策流。

## 变更内容
- 修改文件：`references/performance_optimization.md`
  - 修改 "性能排查顺序"（L16-20）：
    - 原 4 步把"明确指标 / 确定路径 / 工具取证 / 定位主因"混在一起。
    - 改为引用 + 决策流：
      ```
      ## 性能排查顺序
      1. **先取证**：按 [observability_logging.md](observability_logging.md) "性能观测" 的指标口径 + 工具选择采集数据，明确当前指标值 + 触发路径。
      2. **对照阈值**：用上文"总原则"的阈值（> 16 ms 掉帧 / > 100 ms 卡顿 / 重复计算 > 20% / body 重算 > 60Hz）判定是否命中优化必要。
      3. **选主因**：定位到一个主因（主线程阻塞 / 过度刷新 / 重复计算 / 资源浪费 / 内存热点），按本文件下方对应专项（SwiftUI / UIKit / 启动 / 内存）做针对性优化。
      4. **前后对比**：用同一指标口径重新采集，确认指标下降且无行为回归。
      ```
  - 退役 "常用工具"（L54-59）整节，由 `observability_logging.md` "性能观测" 小节承担。替换为一行引用：
    ```
    ## 工具选择
    性能取证工具（Instruments / Time Profiler / Core Animation / Allocations / Leaks / Memory Graph / Points of Interest / OSLog / MetricKit）的用途和采集方式见 [observability_logging.md](observability_logging.md) "性能观测"。本文件不重复维护工具清单。
    ```
  - 其他小节（适用场景 / 总原则 / SwiftUI 优化要点 / UIKit 优化要点 / 启动优化 / 内存治理 / 常见反模式 / 验证清单）不改。
- 不修改 `references/observability_logging.md`（已是完整归属）。

## 替代或合并旧规则
- `performance_optimization.md` "性能排查顺序" 4 步中的"明确指标 / 工具取证"两步语义退役，替换为引用 observability_logging.md + 对照阈值 + 选主因 + 前后对比的决策流。
- `performance_optimization.md` "常用工具" 整节（6 行）退役，由 observability_logging.md "性能观测" 承担。
- 保留 `performance_optimization.md` 的独立价值：阈值决策（L13）、SwiftUI / UIKit / 启动 / 内存专项优化动作、常见反模式、验证清单。

## 预期收益
- 性能指标口径从"两处分散维护"变为"observability_logging.md 单一归属"。未来新增指标、调整阈值只改一处。
- `performance_optimization.md` 职责更聚焦：观测口径外链，自己专注"如何根据指标决策优化方向"，与 observability_logging.md 形成"采集 → 决策"的清晰协作。
- 文件行数 `performance_optimization.md` 从 74 减到约 66，净 -8 行；两文件合计不变但重复消除。
- 符合 self_evolution v26 新约束——把跨文件共享概念（性能指标 / 工具）规整为单一归属。

## 验证
- 结构校验：
  - `SKILL.md` frontmatter 合法，行数 ≤ 500（本提案不改 SKILL.md）。
  - `SKILL.md` 引用的所有 `references/*.md` 文件存在。
  - `root_cause_enforcement.md` / `examples.md` 分层守卫不受影响。
- 场景回放：
  - 隐式验证（性能任务）：用户问 "启动慢怎么排查" 时，AI 应先引用 observability_logging.md "性能观测" 的指标和工具，再按 performance_optimization.md 的决策流展开优化，不再两处看同一套工具名。
  - 场景 `layout` / `review` 等不受本提案影响，按现有行为执行。
- 残留风险：
  - 阈值决策（L13）仍在 performance_optimization.md，不在 observability_logging.md。阈值是"优化触发条件"而不是"采集口径"，归 performance 是正确的；但如果未来有人想把阈值也挪到 observability，需要另开提案讨论职责边界。
  - performance_optimization.md 的 "适用场景"（L3-9）列出"启动慢 / 首屏慢 / 内存上涨..." 等，与 observability_logging.md 的指标名有字面重合；但这里是"触发 skill 的场景描述"不是"指标定义"，不纳入本提案范围。

## 状态
- promoted
