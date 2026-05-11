# Skill Evolution Proposal

## Metadata
- Proposal ID: 20260430-145330-fix-cross-file-references-DD
- Created At: 2026-04-30 14:53:30 +0800
- Active Version At Creation: v28

## 问题信号
按 self_evolution.md v26 新增的跨文件 grep 约束执行全目录扫描，确认 3 处跨文件引用 / 归属不一致：

### D1：architecture_and_network.md L94 交叉引用范围过大
- 当前 L94："网络模式完整定义（**链路职责** / 分页 / 重试 / 缓存 / 鉴权刷新 / 上传下载 / 幂等去重 / **错误分层** / 常见反模式）全部在 networking_patterns.md"
- 实际三项归属：
  - 链路职责 + 环节说明：`architecture_and_network.md` L70-85（Proposal Z 定的单一来源）
  - 错误分层 6 层：`domain_modeling.md` L73-90（Proposal Q 定的单一来源）
  - 网络模式细则：`networking_patterns.md` 实际归属
- 问题：Proposal BB 升级引用时把范围写得过大，错误地把链路和错误分层也归到 networking_patterns。AI 读到这一行会误以为链路权威在 networking，而实际应该读本文件或 domain_modeling。

### D2：architecture_and_network.md L91 错误分层过时且不一致
- 当前 L91："错误必须分层建模：传输层、协议层、鉴权层、业务层、解码层"（5 层）
- domain_modeling.md L74 权威版本：6 层（传输 / 状态码 / 解码 / 鉴权 / 业务 / 展示）
- 差异：
  - architecture 缺 "展示层"
  - architecture 用 "协议层"（不对应权威版本的 "状态码错误"）
  - 顺序不同
- 成因：Proposal Q（v16）把错误分层归属到 domain_modeling.md 时漏改 architecture L91；后续 Proposal BB（v27）清理 architecture 时把这一行作为 "错误分层建模" 保留，没对照 domain_modeling 验证一致性。AA 规则当时没生效（Q 早于 v26）。

### D3：performance_optimization.md L55 引用目标内容不存在（dead reference）
- 当前 L55："性能取证工具（Instruments / Time Profiler / Core Animation / Allocations / Leaks / Memory Graph / Points of Interest / OSLog / MetricKit）的用途和采集方式见 observability_logging.md 性能观测"
- observability_logging.md L51-54 "性能观测" 节实际内容：
  - "关键路径需要配合 OSLog、Points of Interest 或 MetricKit 观测"（3 个工具仅点名）
  - 指标清单（启动/首屏/帧率/主线程/内存/请求）
  - **完全没有** Instruments / Time Profiler / Core Animation / Allocations / Leaks / Memory Graph 的用途说明
- 成因：Proposal CC（v28）退役 performance_optimization.md 的 "常用工具" 小节并改为引用 observability，但没先 grep 验证 observability 目标内容是否存在。

## 变更类型
- 修正表达（D1、D2）：把 architecture_and_network.md 的两处引用和过时定义改写为指向正确权威位置。
- 合并重复（D3）：把完整工具用途搬到 observability_logging.md "性能观测"，让它成为工具单一归属，使 performance_optimization.md 的引用变为有效引用。

## 变更内容
- 修改文件：`references/architecture_and_network.md`
  - **D1** 重写 L94 交叉引用：
    - 原：`网络模式完整定义（链路职责 / 分页 / 重试 / 缓存 / 鉴权刷新 / 上传下载 / 幂等去重 / 错误分层 / 常见反模式）全部在 networking_patterns.md。本文件只保留网络层架构边界和跨层安全规则。`
    - 改为：`相关文件分工：链路职责 + 环节说明见本文件上方 "基础结构"；网络模式细则（分页 / 重试 / 缓存 / 鉴权刷新 / 上传下载 / 幂等去重 / 常见反模式）见 [networking_patterns.md](networking_patterns.md)；错误分层见 [domain_modeling.md](domain_modeling.md) "ErrorModel 建模规则"。本文件只保留网络层架构边界和跨层安全规则。`
  - **D2** 修改 L91 错误分层：
    - 原：`错误必须分层建模：传输层、协议层、鉴权层、业务层、解码层。`
    - 改为：`错误分层必须遵守 [domain_modeling.md](domain_modeling.md) "ErrorModel 建模规则"（6 层：传输 / 状态码 / 解码 / 鉴权 / 业务 / 展示），APIClient 层负责把前 3 层错误转为 ErrorModel。`
- 修改文件：`references/observability_logging.md`
  - **D3** 扩展 "性能观测" 节，补全工具用途清单（作为工具单一归属）：
    - 在现有 "必须观测的常见指标" 之后新增 "性能取证工具" 小节：
      ```
      ### 性能取证工具（单一归属，其他文件引用此处）
      - **Instruments**：苹果官方性能分析套件，下列工具为其模板实例。
      - **Time Profiler**：定位 CPU 和主线程热点；按调用栈聚合采样，适合找"哪个函数在主线程耗时最长"。
      - **Core Animation**：观察帧率、离屏渲染、混合层和光栅化压力；适合找"滚动卡顿是哪类渲染成本"。
      - **Allocations**：跟踪堆对象分配和释放；适合找"内存为什么涨"。
      - **Leaks**：自动检测内存泄漏；适合找"泄漏点具体在哪个对象"。
      - **Memory Graph**（Xcode Debug Navigator）：可视化对象引用图；适合找"强引用环在哪里"。
      - **Points of Interest + OSLog**：代码中打信号点，在 Instruments 时间轴可见；适合标记关键链路耗时（例如 "首屏开始" → "首屏完成"）。
      - **MetricKit**：线上采集崩溃、卡顿、能耗数据，次日 delivery；适合观察真实用户的性能趋势，不适合本地实时调试。
      ```
- 不修改 `references/performance_optimization.md`（L55 引用现在指向有效内容）。

## 替代或合并旧规则
- D1：architecture L94 原范围过大的引用退役，改为三文件职责明确分工引用。
- D2：architecture L91 过时的 5 层错误分层退役，改为引用 domain_modeling.md 权威 6 层定义。
- D3：工具用途清单从历史位置（performance_optimization.md "常用工具"，v28 已退役）完整迁移到 observability_logging.md "性能观测" 节；performance_optimization.md L55 的引用不变但变为有效引用。

## 预期收益
- architecture_and_network.md 的引用描述与实际文件分工一致，AI 不再被误导"链路和错误分层权威在 networking_patterns"。
- architecture L91 错误分层与 domain_modeling.md 权威版本对齐，消除 5 层 vs 6 层的不一致。
- observability_logging.md "性能观测" 节从"仅列指标"升级为"指标 + 完整工具用途"，真正成为性能观测单一归属。
- 跨文件 grep 约束（AA）首次用于后续清理验证，证明 AA 对 "grep 漏位置" 类问题有效；但也暴露 AA 对 "引用目标不存在" 类问题的盲点，由 Proposal EE 补全。

## 验证
- 结构校验：
  - `SKILL.md` frontmatter 合法，行数 ≤ 500（本提案不改 SKILL.md）。
  - `SKILL.md` 引用的所有 `references/*.md` 文件存在。
  - `root_cause_enforcement.md` / `examples.md` 分层守卫不受影响。
- 场景回放：
  - 场景 `review`：用户输入 "review 这个网络层改动"。期望 AI 按"链路看 architecture、模式看 networking_patterns、错误分层看 domain_modeling"的分工加载，不再误读权威位置。
  - 场景 `performance_optimization` 隐式验证：用户问 "启动慢怎么取证"。期望 AI 引用 observability_logging.md "性能取证工具" 小节，能具体说出 Time Profiler 与 MetricKit 的适用区别，不再是空引用。
  - 隐式验证（错误分层）：用户问 "HTTP 404 错误应该在哪层捕获"。期望 AI 命中 domain_modeling.md 6 层分层的"状态码错误"，不再看到 architecture 的"协议层"旧定义。
- 残留风险：
  - observability_logging.md "性能观测" 节新增约 10 行工具用途，文件总长约 95 行，仍远低于 500 行上限。
  - 工具用途描述基于通用经验值（例如 "Time Profiler 适合主线程热点"），具体项目若使用方式不同需要校准。
  - D2 "APIClient 层负责把前 3 层错误转为 ErrorModel" 是对 domain_modeling L82-87 归属规则的摘要；若 domain_modeling 的归属逻辑后续调整，这里需要同步。

## 状态
- promoted
