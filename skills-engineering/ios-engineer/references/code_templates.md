<!-- last-verified: 2026-11 -->
# 产线代码模板

## 使用规则
- 需要给出实现方案时，从本文件选择最接近的模板再落地到具体业务。
- 模板只提供稳定骨架，不替代业务建模、错误语义和测试策略。
- 使用模板时，必须同时说明哪些部分是通用骨架，哪些部分需要按业务改写。
- 本文件内所有 `Feature*` 命名的类型（`FeatureEntity`、`FeatureRemoteDataSourceProtocol`、`FeatureCacheProtocol` 等）以及与具体业务解耦的协议占位（如 `LoggerProtocol`）均为**占位命名**，业务侧需替换为真实类型或定义对应协议；模板直接复制并不保证可编译。
- 使用本文件模板落地到产线的代码交付（PR 描述 / 合入说明 / 交付报告），必须附带一个独立的"残留风险声明"块，固定三字段：已覆盖 / 未覆盖 / 残留风险（履行 GR-008）。三字段必须作为独立段落字面存在，不允许只写"已测试"或省略未覆盖项。与 [examples.md](examples.md) "残留风险声明"段字段对齐，保证四段式输出与产线代码交付两侧字段一致。

## 目录
- ViewModel 模板
- UseCase 模板
- Repository 模板
- APIClient 模板
- Coordinator 模板
- Actor 模板
- SwiftUI propertyWrapper 选型
- 依赖注入三选一
- 并发模型选型

## ViewModel 模板
适用于：
- SwiftUI 状态驱动页面（默认 Observation）
- UIKit MVVM / iOS 16 及以下（ObservableObject）
- 列表、表单、详情页状态编排

> 版本前提：iOS 17+ / Swift 5.9+ 用 `@Observable`；视图持有实例用 `@State`。iOS 16 及以下或 UIKit Combine 路径用 `ObservableObject` + `@Published`。

iOS 17+ Observation：

```swift
import Foundation
import Observation

@MainActor
@Observable
final class FeatureViewModel {
    private(set) var viewState: ViewState = .idle

    private let useCase: FeatureUseCaseProtocol
    @ObservationIgnored private var loadTask: Task<Void, Never>?

    init(useCase: FeatureUseCaseProtocol) {
        self.useCase = useCase
    }

    deinit {
        loadTask?.cancel()
    }

    func load() {
        loadTask?.cancel()
        loadTask = Task { [weak self] in
            guard let self else { return }
            self.viewState = .loading

            do {
                let output = try await self.useCase.execute()
                guard !Task.isCancelled else { return }
                self.viewState = .loaded(output)
            } catch is CancellationError {
                return
            } catch {
                self.viewState = .failed(.from(error))
            }
        }
    }
}

extension FeatureViewModel {
    enum ViewState: Equatable {
        case idle
        case loading
        case loaded(FeatureOutput)
        case failed(ViewError)
    }
}
```

SwiftUI 持有方式：`@State private var viewModel = FeatureViewModel(useCase: useCase)`。不要把 `loadTask` 放进 Observation 跟踪；用 `@ObservationIgnored`。

iOS 16 及以下 / UIKit Combine：

```swift
import Combine
import Foundation

@MainActor
final class FeatureViewModel: ObservableObject {
    @Published private(set) var viewState: ViewState = .idle

    private let useCase: FeatureUseCaseProtocol
    private var loadTask: Task<Void, Never>?

    init(useCase: FeatureUseCaseProtocol) {
        self.useCase = useCase
    }

    deinit {
        loadTask?.cancel()
    }

    func load() {
        loadTask?.cancel()
        loadTask = Task { [weak self] in
            guard let self else { return }
            self.viewState = .loading

            do {
                let output = try await self.useCase.execute()
                guard !Task.isCancelled else { return }
                self.viewState = .loaded(output)
            } catch is CancellationError {
                return
            } catch {
                self.viewState = .failed(.from(error))
            }
        }
    }
}

extension FeatureViewModel {
    enum ViewState: Equatable {
        case idle
        case loading
        case loaded(FeatureOutput)
        case failed(ViewError)
    }
}
```

要求：
- ViewModel 只编排状态，不做网络细节和持久化细节。
- 任务必须可取消。
- 错误必须映射为 UI 可消费的语义。

## UseCase 模板
适用于：
- 业务规则聚合
- 多数据源编排
- 领域层输入输出建模

```swift
import Foundation

protocol FeatureUseCaseProtocol {
    func execute() async throws -> FeatureOutput
}

struct FeatureUseCase: FeatureUseCaseProtocol {
    private let repository: FeatureRepositoryProtocol

    init(repository: FeatureRepositoryProtocol) {
        self.repository = repository
    }

    func execute() async throws -> FeatureOutput {
        let entity = try await repository.fetch()
        return FeatureOutput(entity: entity)
    }
}
```

要求：
- UseCase 承载业务规则，不承载 UI 逻辑。
- 输入输出必须显式建模。

## Repository 模板
适用于：
- 远端 + 本地缓存聚合
- 解耦 Service 与业务层

```swift
import Foundation

protocol FeatureRepositoryProtocol {
    func fetch() async throws -> FeatureEntity
}

struct FeatureRepository: FeatureRepositoryProtocol {
    private let remote: FeatureRemoteDataSourceProtocol
    private let cache: FeatureCacheProtocol
    private let logger: LoggerProtocol

    init(
        remote: FeatureRemoteDataSourceProtocol,
        cache: FeatureCacheProtocol,
        logger: LoggerProtocol
    ) {
        self.remote = remote
        self.cache = cache
        self.logger = logger
    }

    func fetch() async throws -> FeatureEntity {
        // 缓存读：区分"未命中 / 损坏 / 读失败"，不用 try? 静默吞错
        do {
            if let cached = try cache.read() {
                return cached
            }
        } catch {
            // 缓存读失败：必须记录；本模板选择降级到 remote
            // 业务若不允许降级（例如离线首屏），改为 throw error
            logger.error("cache read failed, falling back to remote: \(error)")
        }

        let entity = try await remote.fetch()

        // 缓存写：失败必须记录，但成功路径已获得数据，不阻塞返回
        // 业务若要求强一致，改为 throw
        do {
            try cache.write(entity)
        } catch {
            logger.error("cache write failed: \(error)")
        }

        return entity
    }
}
```

要求：
- Repository 屏蔽数据来源差异。
- 缓存策略必须按业务语义定义，不得静默污染状态：缓存读失败不得压成单一 nil 分支，必须显式记录并给出降级决策（降级 / throw）；缓存写失败必须记录（哪怕不阻塞返回）。
- `try?` 只适用于"失败即忽略、业务不关心原因"的场景；缓存路径不在此范围。

## APIClient 模板
适用于：
- `URLSession + async/await`
- 强类型错误建模

```swift
import Foundation

protocol APIClientProtocol {
    func send<T: Decodable>(_ endpoint: Endpoint<T>) async throws -> T
}

struct APIClient: APIClientProtocol {
    private let session: URLSession
    private let decoder: JSONDecoder

    init(
        session: URLSession = .shared,
        decoder: JSONDecoder = JSONDecoder()
    ) {
        self.session = session
        self.decoder = decoder
    }

    func send<T: Decodable>(_ endpoint: Endpoint<T>) async throws -> T {
        let request = try endpoint.makeURLRequest()
        let data: Data
        let response: URLResponse

        do {
            (data, response) = try await session.data(for: request)
        } catch is CancellationError {
            throw CancellationError()
        } catch let error as URLError where error.code == .cancelled {
            throw CancellationError()
        } catch {
            throw NetworkError.transport(error)
        }

        guard let httpResponse = response as? HTTPURLResponse else {
            throw NetworkError.invalidResponse
        }

        guard 200..<300 ~= httpResponse.statusCode else {
            throw NetworkError.httpStatus(httpResponse.statusCode)
        }

        do {
            return try decoder.decode(T.self, from: data)
        } catch {
            throw NetworkError.decoding(error)
        }
    }
}
```

要求：
- 请求构建、发送、解码、错误分层必须分清。
- 不得在 APIClient 中混入业务降级逻辑。

## Coordinator 模板
适用于：
- UIKit 导航编排
- Feature 路由解耦

```swift
import UIKit

protocol Coordinator: AnyObject {
    func start()
}

final class FeatureCoordinator: Coordinator {
    private let navigationController: UINavigationController
    private let factory: FeatureSceneFactoryProtocol

    init(
        navigationController: UINavigationController,
        factory: FeatureSceneFactoryProtocol
    ) {
        self.navigationController = navigationController
        self.factory = factory
    }

    func start() {
        let viewController = factory.makeFeatureScene()
        navigationController.pushViewController(viewController, animated: true)
    }
}
```

要求：
- 页面不直接拼装下一个页面。
- Coordinator 负责路由，不承载业务计算。

## Actor 模板
适用于：
- 共享可变状态隔离
- Token 刷新、内存缓存、请求去重

```swift
import Foundation

actor FeatureStore<Value: Sendable> {
    private var storage: Value

    init(initialValue: Value) {
        self.storage = initialValue
    }

    func read() -> Value {
        storage
    }

    func update(_ transform: @Sendable (inout Value) -> Void) {
        transform(&storage)
    }
}
```

要求：
- actor 只承担隔离职责，不扩大为万能容器。
- 需要跨域传递的数据必须保持语义清晰。

## SwiftUI propertyWrapper 选型
适用于：
- SwiftUI 状态归属决策
- 父子视图数据流向选择
- 跨视图共享状态建模

> 版本前提：iOS 17+ / Swift 5.9+（Observable 宏可用）；iOS 16 及以下退回 ObservableObject + @StateObject。详见 [ui_state_patterns.md](ui_state_patterns.md) 与 IR-006 版本声明铁律。

| 包装器 | 拥有权 | 适用场景 | 典型反模式 |
|--------|--------|----------|------------|
| `@State` | 视图按 identity 持有；同一 identity 的 body 重算不会重置 | 临时本地 UI 状态；iOS 17+ 也可持有由该视图拥有的 `@Observable` 引用 | 把跨页面 source of truth 无边界地塞入局部状态 |
| `@Binding` | 引用上层 `@State` / `@Bindable` | 子视图需要写回父级状态 | 通过 `@Binding` 跨多层透传（应抽 ViewModel） |
| `@StateObject` (iOS 14+) | 视图持有 ObservableObject 实例 | 视图生命周期内拥有的 ViewModel / Store（iOS 16 及以下） | 在中间视图 `@StateObject` 重建 ViewModel，导致状态被吞 |
| `@ObservedObject` | 外部传入 ObservableObject | 由父视图注入的共享对象 | 在父视图用 `@ObservedObject` 创建实例（视图重建会重新构造） |
| `@Bindable` (iOS 17+) | 引用 `@Observable` 类 | 子视图需对 `@Observable` 对象的属性做 binding | 与旧 ObservableObject 混用 |
| `@Observable` 宏 (iOS 17+) | 类型提供 Observation；所有权仍由存储位置决定 | 新代码的可观察模型；视图拥有实例时通常以 `@State` 保存，外部注入时直接传入 | 用普通计算属性反复创建实例，导致 identity 和状态丢失 |
| `@Environment` / `@EnvironmentObject` | 环境注入 | 跨多层共享的服务 / 主题 / 路由 | 把业务领域模型塞 environment（隐式依赖难追溯） |
| `@SceneStorage` / `@AppStorage` | 系统持久化 | UI 偏好持久化（不放领域数据） | 用 `@AppStorage` 存敏感数据或大对象 |

选择决策树：
- 仅当前视图临时数据 → `@State`
- 视图拥有的 ViewModel：iOS 17+ → `@Observable` + `@State`；iOS 16 及以下 → `ObservableObject` + `@StateObject`
- 父视图传入的 Observable → `@ObservedObject`（旧）/ 直接传入（新，需要 binding 时在子视图使用 `@Bindable`）
- 跨多层共享 → `@Environment` (注入服务) / 路由结构体；避免 `@EnvironmentObject` 隐式依赖
- 持久化偏好 → `@AppStorage`；持久化领域数据 → 走 Repository + 持久化层

## 依赖注入三选一
适用于：
- ViewModel / UseCase / Repository 构造时注入协议依赖
- 测试时替换为 stub / fake

| 方式 | 适用场景 | 优势 | 代价 | 何时拒绝 |
|------|----------|------|------|----------|
| **构造注入**（默认） | 生命周期明确、创建点可控的业务依赖 | 编译期检查、依赖显式、可测试 | 顶层组装位置代码可能增长（Composition Root） | 循环依赖必须先拆；框架反序列化创建的对象可能需要其他入口 |
| **属性注入**（var + Optional） | SwiftUI 的 `@Environment` 注入、UIKit storyboard 反序列化场景 | 兼容框架限制 | 初始化时可空，运行时若忘注入则崩 | 业务可控范围内能改构造注入就别用 |
| **容器 / Service Locator**（Resolver / Factory / Swinject） | 依赖图复杂且手写 Composition Root 已经形成可量化维护成本 | 集中注册、自动解析 | 编译期检查弱、依赖关系隐式、易隐藏循环依赖 | 没有依赖图、启动校验和测试替换方案时拒绝 |

强制规则：
- 永远先写构造注入。只有当 Composition Root 手写组装代码超出维护阈值时才考虑容器。
- 容器引入必须配套：依赖关系图谱文档 + 容器配置可测试 + 启动时全量解析校验（fail fast，避免运行时才发现缺注册）。
- 单例 / `static shared` 不算注入；它是隐式全局依赖，禁止在 ViewModel / UseCase / Repository 层直接持有，必须通过协议从构造器传入（即便上层注入的就是 `.shared`）。
- 谨慎使用 `@propertyWrapper Injected`：只有能静态定位注册、显式覆盖测试依赖且启动时验证完整依赖图时才接受；否则优先构造注入。

落地示例（构造注入）：
```swift
import Combine

final class ExampleFeatureViewModel: ObservableObject {
    private let useCase: FeatureUseCaseProtocol
    private let logger: LoggerProtocol

    init(useCase: FeatureUseCaseProtocol, logger: LoggerProtocol) {
        self.useCase = useCase
        self.logger = logger
    }
}
```

## 并发模型选型
适用于：
- 新代码选择并发模型
- 旧 callback / Combine 代码迁移决策

> 版本前提：iOS 15+ / Swift 5.5+ 可直接使用 async/await；更低部署版本按工程 toolchain、back deployment 能力和依赖约束评估。`Sendable` / actor isolation 的诊断强度由 Swift language mode 与 Strict Concurrency Checking 设置共同决定，Swift 6 模式默认按完整数据竞争安全规则检查。详见 [swift_concurrency.md](swift_concurrency.md)。

| 模型 | 适用场景 | 优势 | 代价 | 何时拒绝 |
|------|----------|------|------|----------|
| **async/await + child task** | 默认选择：一次性请求、有限步骤、需要取消 | 作用域内结构化并发、错误用 throw | 顶层 `Task {}` 是 unstructured task，生命周期仍需显式拥有和取消 | 长生命周期事件流 → 用 AsyncSequence 或 Combine |
| **AsyncSequence / AsyncStream** | 数据流（WebSocket / 通知 / 长轮询）、需结构化并发取消 | 与 async/await 一致的取消模型、背压可控 | 早期 iOS 版本支持差；需要操作符时 API 远不如 Combine 丰富 | 需要 debounce / throttle / merge / zip 等复杂操作 → 暂用 Combine |
| **Combine** | 已有 Combine 代码、复杂事件流操作符、UIKit 老路径桥接 | 操作符丰富、与 UIKit `@Published` 集成成熟 | subscription 生命周期需显式管理，与严格并发隔离衔接成本较高 | 新的一次性异步流程优先 async/await；既有事件流无需为迁移而重写 |
| **callback / completion handler** | Objective-C API、委托式框架或尚未提供 async 接口的 SDK | 兼容性好 | 易遗漏调用、错误处理松散、Sendable 风险大 | 对外可稳定暴露 async 接口且无需保留回调契约时，优先桥接为 async API |
| **GCD（DispatchQueue）** | 与既有队列隔离、barrier、底层 C/Objective-C 库或精确 QoS 集成 | 历史成熟、QoS 可控 | 与 Swift 并发隔离衔接成本高 | 新业务状态优先 actor；保留 GCD 时明确队列所有权与跨域边界 |
| **OperationQueue** | 需要暂停、恢复、依赖图、进度观察或 Objective-C 互操作的任务系统 | 任务依赖图、可观察进度 | 与 async/await 集成成本较高 | 仅需作用域内并行聚合时优先 `TaskGroup` |

新代码默认顺序：
1. async/await + Task → 一次性流程
2. AsyncSequence / AsyncStream → 事件流
3. Combine → 仅当 2 表达不下且必须复杂操作符
4. callback → 仅 bridging
5. GCD / OperationQueue → 几乎不选

迁移决策：详见 [migration_strategy.md](migration_strategy.md) "callback 转 async/await" 与 [swift_concurrency.md](swift_concurrency.md)；本表只做选型，不展开迁移步骤。
