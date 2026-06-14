# iOS 编码约定

## 使用规则
- 涉及命名、声明顺序、访问控制、强制解包、嵌套深度、代码结构、并发写法一致性、中文术语统一等编码习惯问题时，按本文件规则输出审查意见或代码。
- 本文件只沉淀编码习惯层约束；架构边界、状态归属、并发隔离、UI 布局等问题归对应专题文档。
- 审查代码或产出代码时，若违反本文件条款，必须明确指出并给出修正方向。
- 输出方案、代码审查、排障结论、架构设计、迁移计划时，必须使用本文件统一术语。

## 总体命名规则
- 面向中文叙述时，中文为主，英文为辅。
- 面向 Swift 类型、协议、枚举、文件名、模块名时，保留英文命名。
- Apple 官方框架、语言关键字、协议名、属性包装器保留英文原词。
- 禁止中英文来回切换导致一个概念出现多个别名。
- 同一轮回答中，同一个概念只能使用一种主称呼。
- 需要保留英文术语时，首次出现使用“中文主称呼 + 英文原词”格式，后续固定使用同一称呼。

## Swift 属性声明与位置
- 能 `let` 则 `let`：属性默认不可变，不必要不暴露写入能力。
- 需要延迟构造且初始化依赖运行时上下文（例如需要 `self` 的属性）时才用 `lazy var`；注意 `lazy var` 不是并发安全的，跨任务访问必须说明线程归属或改由 `actor` 持有。
- `var` 属性必须最小化对外可见性：优先 `private(set)`；跨类可写 `var` 必须说明状态归属和写入路径。
- 共享可变状态必须说明隔离策略（`actor` / `@MainActor` / 明确锁）。
- 属性位置建议统一放在类结构末尾（初始化 / public API / private helpers 之后），避免可见性交错。

## `self` 前缀
- 变量与方法调用默认使用 `self.` 前缀。
- 前缀不是为了消歧义而存在，而是为了让“当前作用域属性 vs 局部变量”在阅读时一目了然，避免后期新增同名变量造成隐性覆盖。

## 访问控制
- 默认显式声明访问控制：优先最小可见性（例如 `private`、`private(set)`），避免不必要的对外暴露。
- 跨模块公开成员必须显式写 `public` 或 `package`，不得用默认 `internal` 代替有意图的公开声明。

## 禁止崩溃类 API
- 禁止强制解包、强转与断言式崩溃（例如 `!`、`as!`、`fatalError`），除非明确写出不可变前提与失败代价。
- 若必须崩溃，必须在代码附近注释说明“前提是什么、失败代价是什么、为什么不能走错误路径”。

## 嵌套深度与早退出
- 控制嵌套深度：优先使用 `guard` 做前置条件早退出，避免多层 `if` / `switch` 嵌套。
- 单个函数缩进层级一般不超过 3 层；超过时优先拆函数或抽取子过程，而不是继续加分支。

## 代码结构顺序
- 固定代码结构顺序：`typealias` / `enum` -> 初始化 -> public API -> private helpers。
- 协议实现放在对应 `extension` 中分组，不与主体类混写。
- `IBOutlet` / `IBAction` 若存在，与协议 extension 一样单独分组。

## Swift 命名
- 变量与方法命名统一使用小驼峰，例如 `messageCount`、`refreshFeed()`。
- Bool 类型以 `is` / `has` / `can` 前缀，例如 `isLoading`、`hasUnreadMessages`、`canSubmit`。
- 异步 / 并发相关方法用清晰动词短语表达意图，例如 `refreshFeed()`、`cancelInflightRequests()`，不使用 `doXxx`、`handleXxx` 这类模糊动词。
- 避免含糊缩写：`mgr`、`ctrl`、`tmp`、`val` 在新代码中一律禁止，保留已有缩写时不扩散到新模块。
- 禁止把业务临时状态泛化命名为 `Snapshot` / `快照`（例如把"当前某视图的临时数据"命名为 `XxxSnapshot` 而不给业务语义），改用贴近业务的命名（例如 `pinnedFollowUpIdentifier`、`savedDraft`、`pendingOrder`）。
- **例外**：Apple API 自身的 Snapshot 类型（例如 `NSDiffableDataSourceSnapshot`、`UIViewControllerContextTransitioning.snapshotView`）保留原名不改写；测试框架的 snapshot testing 概念保留原名。

## 并发写法一致性
- 并发边界写清楚：UI 更新策略统一（例如 `@MainActor` 或明确切主线程），避免同一模块混用多种写法导致边界不清。
- 选定一种写法后，同一模块内不允许 `@MainActor` 与 `DispatchQueue.main.async` / `MainActor.run {}` 等写法混用；需要切换时必须整体迁移，不得局部补丁。
- 相关并发设计规则见 [swift_concurrency.md](swift_concurrency.md)。

## 架构与分层术语
| 统一称呼 | 英文原词 | 使用规则 |
|------|------|------|
| 架构边界 | Architecture Boundary | 叙述分层责任时使用 |
| 依赖注入 | Dependency Injection, DI | 首次可写“依赖注入（DI）” |
| 路由协调器 | Coordinator | 类型名保留 `Coordinator`，正文可写“路由协调器（Coordinator）” |
| 用例 | UseCase | 类型名保留 `UseCase` |
| 仓储 | Repository | 类型名保留 `Repository` |
| 服务 | Service | 类型名保留 `Service` |
| 功能模块 | Feature | 叙述业务模块时使用“功能模块”，代码名保留 `Feature` |
| 核心模块 | Core | 叙述基础层时使用“核心模块”，代码名保留 `Core` |

## 建模术语
| 统一称呼 | 英文原词 | 使用规则 |
|------|------|------|
| 传输模型 | DTO | 首次可写“传输模型（DTO）” |
| 领域实体 | Entity | 首次可写“领域实体（Entity）” |
| 页面状态 | ViewState | 首次可写“页面状态（ViewState）” |
| 错误模型 | ErrorModel | 首次可写“错误模型（ErrorModel）” |
| 映射层 | Mapper | 若明确存在独立层，可写“映射层（Mapper）” |

## 并发术语
| 统一称呼 | 英文原词 | 使用规则 |
|------|------|------|
| 主线程隔离 | @MainActor | 叙述规则时使用 |
| Actor 隔离 | actor | 保留关键字原词 |
| 结构化并发 | Structured Concurrency | 叙述并发模型时使用 |
| 取消语义 | Cancellation | 叙述任务取消规则时使用 |
| 可发送语义 | Sendable | 首次可写“可发送语义（Sendable）” |

## UI 与状态术语
| 统一称呼 | 英文原词 | 使用规则 |
|------|------|------|
| 页面状态机 | State Machine | 叙述复杂页面状态流时使用 |
| 空态 | Empty State | 叙述成功但无数据场景 |
| 错误态 | Error State | 叙述失败渲染场景 |
| 加载态 | Loading State | 叙述加载过程 |
| 列表身份 | Identity | 叙述列表稳定标识问题 |

## 网络与数据术语
| 统一称呼 | 英文原词 | 使用规则 |
|------|------|------|
| 请求端点 | Endpoint | 类型名保留 `Endpoint` |
| 请求构建器 | RequestBuilder | 类型名保留 `RequestBuilder` |
| API 客户端 | APIClient | 类型名保留 `APIClient` |
| 幂等 | Idempotency | 叙述写操作安全性时使用 |
| 游标分页 | Cursor-based Pagination | 叙述游标类分页 |
| 页码分页 | Page-based Pagination | 叙述页码类分页 |
| 鉴权刷新 | Token Refresh | 叙述 Token 更新链路 |

## 工程协作术语
| 统一称呼 | 英文原词 | 使用规则 |
|------|------|------|
| 代码审查 | Review | 正文统一写“代码审查”，必要时首次写“代码审查（Review）” |
| 合并请求 | PR | 正文统一写“PR” |
| 模块负责人 | Owner / Ownership | 正文统一写“模块负责人”或“ownership”之一；本 skill 统一写“模块 ownership” |
| 灰度发布 | Rollout | 叙述阶段放量时使用 |
| 回滚条件 | Rollback Condition | 叙述发布失败退出条件时使用 |

## 禁止混用规则
- 不要把 `DTO`、`Entity`、`ViewState`、`ErrorModel` 统称为 `Model`。
- 不要在同一段里混用“控制器”“VC”“ViewController”三种称呼。
- 不要在同一段里混用“代码审查”“Review”“PR Review”三种称呼。
- 不要在同一段里混用“所有权”“ownership”“owner 归属”三种称呼。
- 不要把“页面状态”“业务状态”“组件状态”混成一个“状态”。

## 常见反模式
- 为图省事把所有属性声明为 `var`，不声明 `private(set)` 或 `let`。
- 用 `!` 取消编译警告而不分析失败前提。
- `guard` 被嵌套 `if` 吞没，早退出逻辑反而藏在更深的缩进里。
- 协议实现散落在类主体内，读者无法一眼看出哪些是协议契约。
- Bool 名称没有前缀（`loading`、`error`），读者看不出是状态标志还是值。
- 同一个模块里同时使用 `@MainActor`、`DispatchQueue.main.async`、`MainActor.run {}`，UI 更新边界失控。
