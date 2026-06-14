# Skill Evolution Proposal

## Metadata
- Proposal ID: 20260430-111956-antipattern-verifiable-criteria
- Created At: 2026-04-30 11:19:56 +0800
- Active Version At Creation: v13

## 问题信号
- `anti_patterns.md` 14 个反模式都采用"表现 / 风险 / 修法"三段结构，但"表现"段只列举例子（例如"同时负责渲染、路由、网络、缓存、埋点、权限和状态拼装"），没有量化判断标准。AI 读完无法机械判断"当前代码是否命中该反模式"。
- 使用规则 L13-14 "不得淡化为'个人风格差异'"、"必须说明它破坏了哪一层边界、会引发什么风险、应该如何重构" 是口号式表达，没有指明"如何识别"的操作标准。
- 缺少判断标准会导致两种失败模式：
  - 过度触发：AI 把任何大一点的 ViewController 都标为 Massive；
  - 漏触发：AI 看到真正 Massive 但因为没有阈值犹豫不下判断。

## 变更类型
- 修正表达：给 14 个反模式每条补一行"识别条件"（量化阈值 / 代码特征 / 可机械判断的条件）；修正"使用规则"使其指向识别条件而不是口号。

## 变更内容
- 修改文件：`references/anti_patterns.md`
  - 重写 "使用规则" 节（L12-14）：
    - 退役 L13 "发现以下反模式时，必须直接指出，不得淡化为'个人风格差异'"（口号）。
    - 退役 L14 "识别到反模式后，必须说明它破坏了哪一层边界、会引发什么风险、应该如何重构"（无判断标准）。
    - 新增：
      - "先按每条反模式的'识别条件'判定是否命中；未达到条件不贴标签。"
      - "命中后按'表现 → 识别条件 → 风险 → 修法'四段输出；修法必须指向可验证的代码改动。"
  - 为 14 个反模式每条在"表现"和"风险"之间插入一行 **"识别条件"**，内容如下：
    1. **Massive ViewController / Massive ViewModel**：`识别条件：同一类型同时承担 ≥ 3 类职责（例如渲染 + 网络 + 路由 + 埋点）；或单类行数 > 600；或成员变量 > 20。`
    2. **伪模块化**：`识别条件：存在跨模块直接访问 internal / private 实现；或 SPM 包之间循环依赖；或模块 public API 占比 > 50%。`
    3. **万能 Manager**：`识别条件：同一类型承担 ≥ 3 种不同职责（网络 + 缓存 + 业务 + 状态同步）；或包含 ≥ 2 个需要锁保护的共享状态；或被 ≥ 10 个调用方持有为单例。`
    4. **散落式 Task {}**：`识别条件：Task {} 出现在 UIView / Cell / 工具类；或该 Task 缺少对应的 cancel 触发链路；或 Task 修改共享状态但无归属对象（持有方不能回答"谁取消"）。`
    5. **DispatchQueue.main.async 掩盖时序问题**：`识别条件：新增 main.async 的 commit / PR 注释只写"修 crash / 白屏"而未解释为何原路径不在主线程；或连续多层 main.async 嵌套；或 async 后闭包捕获对象在非主线程已 dealloc 的证据。`
    6. **滥用 @unchecked Sendable**：`识别条件：添加 @unchecked Sendable 的位置无"内部同步保证"注释；或该类含可变 var 属性但无 lock / actor 保护；或该类跨多个任务并发写。`
    7. **状态源散落**：`识别条件：同一语义状态（例如"已登录"、"正在加载"、"已选中"）在 ≥ 2 个对象中独立维护；或 UI 层需要手动 "sync" 多处状态。`
    8. **写死尺寸修布局**：`识别条件：出现硬编码约束常量 ≥ 50 或字体大小 ≥ 13 的魔法值；或原本应由 intrinsicContentSize 决定的维度被硬写；或布局修复 commit 只改数字不改层级。`
    9. **不稳定的列表身份**：`识别条件：list item 的 id 使用 indexPath / 数组 index / 可变字段（如 unreadCount / status / updatedAt）；或 item 更新时 identity 发生变化。`
    10. **字符串拼装请求**：`识别条件：URL / Query / Header 使用 "+" 或 string interpolation 拼接 ≥ 3 处；或相同接口的 URL 拼装逻辑出现在 ≥ 2 个文件。`
    11. **错误透传到 UI**：`识别条件：UI 代码直接展示 error.localizedDescription / error.debugDescription；或用户可见提示中出现 HTTP status code / NSError domain。`
    12. **盲目重试**：`识别条件：写操作（POST / PUT / DELETE）存在自动重试；或重试缺少 max attempts 或 backoff；或业务错误（4xx business fail）被纳入重试范围。`
    13. **主线程做重活**：`识别条件：Time Profiler 显示主线程单次调用耗时 > 16 ms（掉帧）或 > 100 ms（卡顿）；或 cellForItem / scrollViewDidScroll / layoutSubviews 中执行 decode / JSON parse / sort 等 O(n) 以上操作。`
    14. **为了性能牺牲正确性**：`识别条件：使用缓存但未定义失效条件；或 catch 块吞异常无日志；或刷新代码被注释为"性能原因暂时跳过"；或"避免重复请求"导致数据脏读。`
    15. **现象即根因**：`识别条件：修复 PR / commit 描述停留在"修了 xxx 崩溃"/"防御 xxx nil"，未说明"为什么 xxx 会发生"；或修复点是崩溃栈最后一帧而未回溯调用链。`
    16. **补丁式修复**：`识别条件：修复代码只新增 if / guard / 空值检查 / try-catch 兜底，未删除或改变错误来源；或修复后相同输入路径仍可能触发相同错误。`
- 替代或合并旧规则：
  - 14 条反模式的"表现"段保留不动（示例仍有价值）；新增的"识别条件"段是对"表现"的量化补强。
  - 使用规则 L13-L14 口号退役，替换为指向识别条件的操作指引。

## 预期收益
- AI 读完 anti_patterns.md 后可机械判断"当前代码是否命中某反模式"，不再依赖自由裁量。
- 过度触发（把任何大类都标为 Massive）和漏触发（看到明显 Massive 但犹豫）两种失败模式都能通过识别条件避免。
- 文件行数从 202 增加到约 235（每条 +2 行识别条件 + 使用规则重写），但 actionable 密度显著提升。
- 审查任务场景（review）输出更具体：不再写"这个类太大了建议重构"，而是"单类 820 行 + 5 类职责，已命中 Massive ViewController 识别条件"。

## 验证
- 结构校验：
  - `SKILL.md` frontmatter 合法，行数 ≤ 500（本提案不改 SKILL.md）。
  - `SKILL.md` 引用的所有 `references/*.md` 文件存在。
  - `root_cause_enforcement.md` / `examples.md` 分层守卫不受影响。
- 场景回放：
  - 场景 `review`：用户输入"review 这个改动"。期望 AI 在遇到大类时引用识别条件（例如"行数 820 > 600 阈值 + 职责 4 类"），而不是模糊的"建议拆分"。
  - 新增隐式验证：AI 面对 UIViewController 时应明确说明是否命中 Massive 阈值，不命中时不贴标签。
- 残留风险：
  - 阈值（600 行、20 成员、50pt 约束常量、16ms / 100ms 主线程耗时等）是行业经验值，不同项目规模可能需要校准。若后续在真实任务中发现阈值偏离项目实际，单独提案调整。
  - 部分识别条件依赖静态分析（数数行数、数职责数），部分依赖运行时数据（Time Profiler）。AI 在没有运行时数据时可能只用静态识别条件，这是可接受的退化。

## 状态
- promoted
