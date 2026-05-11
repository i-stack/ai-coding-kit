# Swift 编码风格

## 使用规则
- 涉及命名、声明顺序、访问控制、强制解包、嵌套深度、代码结构、并发写法一致性等编码风格问题时，按本文件规则输出审查意见或代码。
- 本文件只沉淀风格层约束；架构边界、状态归属、并发隔离、UI 布局等问题归对应专题文档。
- 审查代码或产出代码时，若违反本文件条款，必须明确指出并给出修正方向。

## 属性声明与位置
- 属性声明除非确有必要（例如必须立即初始化、纯值语义数据、并发安全要求等），否则优先使用 `lazy var` 声明。
- 属性统一放在当前 `class` 的最下面，避免初始化分散和可见性交错。

## `self` 前缀
- 变量与方法调用默认使用 `self.` 前缀。
- 前缀不是为了消歧义而存在，而是为了让"当前作用域属性 vs 局部变量"在阅读时一目了然，避免后期新增同名变量造成隐性覆盖。

## 访问控制
- 默认显式声明访问控制：优先最小可见性（例如 `private`、`private(set)`），避免不必要的对外暴露。
- 跨模块公开成员必须显式写 `public` 或 `package`，不得用默认 `internal` 代替有意图的公开声明。

## 禁止崩溃类 API
- 禁止强制解包、强转与断言式崩溃（例如 `!`、`as!`、`fatalError`），除非明确写出不可变前提与失败代价。
- 若必须崩溃，必须在代码附近注释说明"前提是什么、失败代价是什么、为什么不能走错误路径"。

## 嵌套深度与早退出
- 控制嵌套深度：优先使用 `guard` 做前置条件早退出，避免多层 `if` / `switch` 嵌套。
- 单个函数缩进层级一般不超过 3 层；超过时优先拆函数或抽取子过程，而不是继续加分支。

## 代码结构顺序
- 固定代码结构顺序：`typealias` / `enum` -> 初始化 -> public API -> private helpers。
- 协议实现放在对应 `extension` 中分组，不与主体类混写。
- `IBOutlet` / `IBAction` 若存在，与协议 extension 一样单独分组。

## 命名
- Bool 类型以 `is` / `has` / `can` 前缀，例如 `isLoading`、`hasUnreadMessages`、`canSubmit`。
- 异步 / 并发相关方法用清晰动词短语表达意图，例如 `refreshFeed()`、`cancelInflightRequests()`，不使用 `doXxx`、`handleXxx` 这类模糊动词。
- 避免含糊缩写：`mgr`、`ctrl`、`tmp`、`val` 在新代码中一律禁止，保留已有缩写时不扩散到新模块。
- 禁止使用 `Snapshot`、`快照` 及同类命名，统一采用更贴近业务语义的名称（例如 `pinnedFollowUpIdentifier`、`savedDraft`、`pendingOrder`）。

## 并发写法一致性
- 并发边界写清楚：UI 更新策略统一（例如 `@MainActor` 或明确切主线程），避免同一模块混用多种写法导致边界不清。
- 选定一种写法后，同一模块内不允许 `@MainActor` 与 `DispatchQueue.main.async` / `MainActor.run {}` 等写法混用；需要切换时必须整体迁移，不得局部补丁。
- 相关并发设计规则见 [swift_concurrency.md](swift_concurrency.md)。

## 常见反模式
- 为图省事把所有属性声明为 `var`，不声明 `private(set)` 或 `let`。
- 用 `!` 取消编译警告而不分析失败前提。
- `guard` 被嵌套 `if` 吞没，早退出逻辑反而藏在更深的缩进里。
- 协议实现散落在类主体内，读者无法一眼看出哪些是协议契约。
- Bool 名称没有前缀（`loading`、`error`），读者看不出是状态标志还是值。
- 同一个模块里同时使用 `@MainActor`、`DispatchQueue.main.async`、`MainActor.run {}`，UI 更新边界失控。
