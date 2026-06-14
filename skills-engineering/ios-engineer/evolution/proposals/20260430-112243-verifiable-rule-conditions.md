# Skill Evolution Proposal

## Metadata
- Proposal ID: 20260430-112243-verifiable-rule-conditions
- Created At: 2026-04-30 11:22:43 +0800
- Active Version At Creation: v14

## 问题信号
- `performance_optimization.md` L13 "先解决主线程阻塞、重复计算、无效刷新和资源浪费" 无阈值，AI 无法判断何时主线程算阻塞、何时重复计算算过量。
- `mcp_control.md` L21 "只有在已经拿到新证据时才继续扩展预算"——"新证据"未定义，AI 自由裁量。
- `mcp_control.md` L28 "同一个工具、同一参数失败两次后，不得第三次原样重试"——"失败"未定义（编译失败？结果不符？空结果？）。
- `decision_records.md` L85-89 "简化判断规则" 4 条 ("改变模块边界就写决策记录" 等) 使用"改变边界"、"影响多个页面" 等模糊词，无可机械判断条件。
- `build_release_and_ci.md` L28-32 构建问题排查顺序只列层级（"依赖解析 / 编译 / 链接 / 签名"），没有"如何识别当前失败落在哪一层"的错误特征。

## 变更类型
- 修正表达：给 5 处无可验证条件的规则补具体阈值、定义或特征。

## 变更内容
- 修改文件：`references/performance_optimization.md`
  - 修改 L13 "总原则" 第二条：
    - 原：`先解决主线程阻塞、重复计算、无效刷新和资源浪费。`
    - 改为：`按优先级处理：主线程单次调用耗时 > 16 ms（掉帧）或 > 100 ms（卡顿）→ 重复计算成本占总耗时 > 20% → SwiftUI body 重算频率 > 60Hz 或 UIKit cellForItem 调用时有同步 IO → 资源浪费（图片未缓存、对象未复用）。`
- 修改文件：`references/mcp_control.md`
  - 修改 L21 调用预算最后一条：
    - 原：`只有在已经拿到新证据时才继续扩展预算，不因"还没想明白"而无限追加调用。`
    - 改为：`只有在已经拿到新证据时才继续扩展预算。"新证据" 定义：上一次调用未见过的错误信息、新的日志行、新的代码文件、新的数据字段、或能证伪/证实当前假设的具体事实。仅"想到新的搜索词"不算新证据。`
  - 修改 L28 重试与限流首条：
    - 原：`同一个工具、同一参数失败两次后，不得第三次原样重试。`
    - 改为：`同一个工具、同一参数失败两次后，不得第三次原样重试。"失败" 定义：返回空结果、返回与上次完全相同的结果、命令执行非 0 退出、或结果与当前假设无关。`
- 修改文件：`references/decision_records.md`
  - 重写 "简化判断规则" 4 条（L85-89）：
    - 原 4 条口号："若方案会改变模块边界/并发边界/状态归属/影响多个团队或页面，写决策记录。"
    - 改为：
      - `若方案新增、删除或移动公开 API（public / package 修饰符），或改变现有公开 API 的行为语义（返回值类型、异常集、副作用）。`
      - `若方案引入新的并发隔离域（actor / @MainActor / 串行队列），或改变现有隔离策略（例如从 class + lock 改为 actor）。`
      - `若方案移动或合并 ViewState / Entity / 共享状态的真实持有者（source of truth），或将原本由 A 类持有的状态改由 B 类持有。`
      - `若方案要求其他团队的代码同步修改（跨 PR 依赖），或同一 release 内有 ≥ 2 个 Feature 包被改动。`
- 修改文件：`references/build_release_and_ci.md`
  - 重写 "构建问题排查顺序"（L28-32）为带错误特征的表格：
    ```
    | 层级 | 典型错误信号 | 识别特征 |
    | --- | --- | --- |
    | 依赖解析 | `Package.resolved missing` / `version constraint unsolvable` / `pod install` 报 Podfile.lock 冲突 | 错误发生在构建开始前，提示文本包含 "version"、"resolved"、"dependency" |
    | 编译 | `error: cannot find 'Foo' in scope` / `undeclared type` / Swift 类型不匹配 | 错误指向具体源文件与行号，提示 "cannot find"、"undeclared"、"type mismatch" |
    | 链接 | `Undefined symbol: _OBJC_CLASS_$_Foo` / `ld: framework not found` | 错误发生在编译通过后，提示含 "Undefined symbol"、"ld:"、"framework not found" |
    | 签名 | `Code signing error` / `provisioning profile` / `entitlements` 问题 | 错误文本包含 "signing"、"provisioning"、"entitlement"、"team ID" |
    | 打包 | 资源文件 missing / Info.plist 校验失败 / 归档失败 | 错误发生在链接后的归档阶段，提示含 "archive"、"Info.plist"、"resource" |
    | 测试 | XCTest 断言失败 / 测试 target 配置错误 | 错误发生在测试 target 执行阶段，提示含 "XCTAssert"、"test failure" |

    判别流程：从上到下匹配错误信号；命中某层后先解决该层问题再继续构建，不跳跃处理下游。
    ```
- 替代或合并旧规则：
  - 5 处规则原文全部退役，由新版本替代。
  - 新版本保留原规则意图（优先级、预算、判断条件），只把模糊词替换为可机械判断的定义。

## 预期收益
- 5 处规则从"AI 自由裁量"变为"AI 机械判断"。
- mcp_control.md 的预算控制更严格：工具循环将在"新证据"明确缺席时提前停止。
- decision_records.md 的判断规则可执行：重构时 AI 能明确回答"这次改动是否需要写决策记录"。
- build_release_and_ci.md 的构建排查从"列表式指引"变为"错误特征匹配"，AI 读完可直接根据错误文本定位层级。
- performance_optimization.md 的优先级从"无阈值列表"变为"阈值 + 数量比较"。

## 验证
- 结构校验：
  - `SKILL.md` frontmatter 合法，行数 ≤ 500（本提案不改 SKILL.md）。
  - `SKILL.md` 引用的所有 `references/*.md` 文件存在。
  - `root_cause_enforcement.md` / `examples.md` 分层守卫不受影响。
- 场景回放：
  - 场景 `mcp-control`：用户输入"这个偶发问题帮我查一下"。期望 AI 在执行两轮相同搜索后识别"无新证据"并切方向，不无限追加工具调用。
  - 隐式验证：用户问"这个改动要不要写决策记录"时，AI 能按新的 4 条具体条件逐项判断。
- 残留风险：
  - "新证据"、"失败"的定义仍可能在极端案例下有歧义；但比原来"未定义"状态好得多。
  - 构建排查表格依赖错误文本包含特定关键词；若 Xcode 版本或 CI 平台改变错误文本格式，需要更新表格。
  - performance_optimization.md 的阈值（16ms、100ms、20%、60Hz）是行业经验值，具体项目可能需要校准。

## 状态
- promoted
