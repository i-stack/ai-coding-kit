<!-- last-verified: 2026-11 -->
# Production Code Templates

> This is an English mirror of the authoritative Chinese `references/code_templates.md`.
> In case of discrepancies, the Chinese source takes precedence.

## Usage Rules
- When implementation solutions are needed, select the closest template from this file and adapt to specific business requirements.
- Templates only provide stable skeletons; they do not replace business modeling, error semantics, or test strategy.
- When using templates, must explain which parts are generic skeletons and which parts need business-specific rewriting.
- All `Feature*` named types in this file (`FeatureEntity`, `FeatureRemoteDataSourceProtocol`, `FeatureCacheProtocol`, etc.) and protocol placeholders decoupled from specific business (e.g., `LoggerProtocol`) are **placeholder names**; business side must replace with real types or define corresponding protocols; direct template copying does not guarantee compilability.
- Production code delivery using templates from this file (PR description / merge notes / delivery report) must include an independent "Residual Risk Statement" block with fixed three fields: Covered / Uncovered / Residual Risk (fulfilling GR-008). Three fields must exist as independent paragraphs literally; writing only "tested" or omitting uncovered items is not allowed. Align with [examples.md](examples.md) "Residual Risk Statement" section fields to ensure four-section output and production code delivery have consistent fields on both sides.

## Table of Contents
- ViewModel Template
- UseCase Template
- Repository Template
- APIClient Template
- Coordinator Template
- Actor Template
- SwiftUI propertyWrapper Selection
- Dependency Injection: Choose One of Three
- Concurrency Model Selection

## ViewModel Template
Applicable to:
- UIKit MVVM
- SwiftUI state-driven pages
- List, form, detail page state orchestration

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

Requirements:
- ViewModel only orchestrates state; does not handle networking or persistence details.
- Tasks must be cancellable.
- Errors must be mapped to UI-consumable semantics.

## UseCase Template
Applicable to:
- Business rule aggregation
- Multi-data-source orchestration
- Domain layer input/output modeling

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

Requirements:
- UseCase carries business rules; does not carry UI logic.
- Input/output must be explicitly modeled.

## Repository Template
Applicable to:
- Remote + local cache aggregation
- Decoupling Service from business layer

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
        // Cache read: distinguish "miss / corrupted / read failure"; do not silently swallow errors with try?
        do {
            if let cached = try cache.read() {
                return cached
            }
        } catch {
            // Cache read failure: must be logged; this template chooses to degrade to remote
            // If business does not allow degradation (e.g., offline first screen), change to throw error
            logger.error("cache read failed, falling back to remote: \(error)")
        }

        let entity = try await remote.fetch()

        // Cache write: failure must be logged, but success path already has data; do not block return
        // If business requires strong consistency, change to throw
        do {
            try cache.write(entity)
        } catch {
            logger.error("cache write failed: \(error)")
        }

        return entity
    }
}
```

Requirements:
- Repository shields data source differences.
- Cache strategy must be defined by business semantics; must not silently pollute state: cache read failure must not be compressed into a single nil branch; must explicitly log and provide degradation decision (degrade / throw); cache write failure must be logged (even if not blocking return).
- `try?` only applicable to "failure means ignore; business does not care about reason" scenarios; cache path is not in this scope.

## APIClient Template
Applicable to:
- `URLSession + async/await`
- Strongly-typed error modeling

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
        let (data, response) = try await session.data(for: request)

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

Requirements:
- Request construction, sending, decoding, and error layering must be separated.
- Do not mix business degradation logic into APIClient.

## Coordinator Template
Applicable to:
- UIKit navigation orchestration
- Feature route decoupling

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

Requirements:
- Pages do not directly assemble the next page.
- Coordinator responsible for routing; does not carry business computation.

## Actor Template
Applicable to:
- Shared mutable state isolation
- Token refresh, in-memory cache, request deduplication

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

Requirements:
- actor only handles isolation responsibility; do not expand into universal container.
- Data that needs cross-domain transfer must maintain clear semantics.

## SwiftUI propertyWrapper Selection
Applicable to:
- SwiftUI state ownership decisions
- Parent-child view data flow selection
- Cross-view shared state modeling

> Version prerequisite: iOS 17+ / Swift 5.9+ (Observable macro available); iOS 16 and below fall back to ObservableObject + @StateObject. See [ui_state_patterns.md](ui_state_patterns.md) and IR-006 version declaration iron rule.

| Wrapper | Ownership | Applicable Scenarios | Typical Anti-Pattern |
|--------|--------|----------|------------|
| `@State` | Held by the view identity; recomputing `body` for the same identity does not reset it | Temporary local UI state; on iOS 17+ it may also hold a view-owned `@Observable` reference | Stuffing a cross-screen source of truth into local state without a boundary |
| `@Binding` | References upper-level `@State` / `@Bindable` | Child view needs to write back to parent state | Propagating `@Binding` across multiple layers (should extract ViewModel) |
| `@StateObject` (iOS 14+) | View owns ObservableObject instance | ViewModel / Store owned within view lifecycle (iOS 16 and below) | Rebuilding ViewModel with `@StateObject` in intermediate views; state gets swallowed |
| `@ObservedObject` | Externally passed ObservableObject | Shared object injected by parent view | Creating instance with `@ObservedObject` in parent view (view rebuild reconstructs it) |
| `@Bindable` (iOS 17+) | References `@Observable` class | Child view needs binding to `@Observable` object properties | Mixing with old ObservableObject |
| `@Observable` macro (iOS 17+) | The type provides Observation; ownership is still decided by where the instance is stored | Observable models in new code; store a view-owned instance in `@State`, pass injected instances directly | Recreating the instance in a computed property, losing identity and state |
| `@Environment` / `@EnvironmentObject` | Environment injection | Services / themes / routes shared across multiple layers | Stuffing business domain models into environment (implicit dependencies hard to trace) |
| `@SceneStorage` / `@AppStorage` | System persistence | UI preference persistence (not domain data) | Using `@AppStorage` for sensitive data or large objects |

Selection decision tree:
- Temporary data for current view only → `@State`
- View-owned ViewModel: iOS 17+ → `@Observable` + `@State`; iOS 16 and below → `ObservableObject` + `@StateObject`
- Observable passed from parent view → `@ObservedObject` (legacy) / pass directly (Observation; use `@Bindable` in the child when bindings are needed)
- Shared across multiple layers → `@Environment` (inject services) / route struct; avoid `@EnvironmentObject` implicit dependencies
- Persist preferences → `@AppStorage`; persist domain data → go through Repository + persistence layer

## Dependency Injection: Choose One of Three
Applicable to:
- Injecting protocol dependencies when constructing ViewModel / UseCase / Repository
- Replacing with stub / fake during testing

| Method | Applicable Scenarios | Advantages | Costs | When to Reject |
|------|----------|------|------|----------|
| **Constructor Injection** (default) | Business dependencies with a clear lifetime and a controllable creation point | Compile-time checking, explicit dependencies, testable | Composition Root assembly code may grow | Circular dependencies must be split first; objects created by framework deserialization may need another entry |
| **Property Injection** (var + Optional) | SwiftUI `@Environment` injection, UIKit storyboard deserialization scenarios | Compatible with framework limitations | Nullable at init time; runtime crash if forgotten to inject | Use constructor injection when possible within business control |
| **Container / Service Locator** (Resolver / Factory / Swinject) | The dependency graph is complex and handwritten Composition Root already has measurable maintenance cost | Centralized registration, auto-resolution | Weak compile-time checking, implicit dependency relationships, easy to hide circular dependencies | Reject when there is no dependency graph, startup validation, or test substitution plan |

Mandatory rules:
- Always write constructor injection first. Only consider containers when Composition Root manual assembly code exceeds maintenance threshold.
- Container introduction must be accompanied by: dependency relationship graph documentation + container configuration testable + startup full-resolution validation (fail fast; avoid discovering missing registrations at runtime).
- Singletons / `static shared` do not count as injection; they are implicit global dependencies; prohibited from being directly held at ViewModel / UseCase / Repository layer; must be passed through constructor via protocol (even if the upper layer injects `.shared`).
- Use `@propertyWrapper Injected` only when registration can be located statically, test dependencies can be overridden explicitly, and the full graph is validated at launch; otherwise prefer constructor injection.

Implementation example (constructor injection):
```swift
final class FeatureViewModel: ObservableObject {
    private let useCase: FeatureUseCaseProtocol
    private let logger: LoggerProtocol

    init(useCase: FeatureUseCaseProtocol, logger: LoggerProtocol) {
        self.useCase = useCase
        self.logger = logger
    }
}
```

## Concurrency Model Selection
Applicable to:
- New code choosing concurrency model
- Old callback / Combine code migration decisions

> Version prerequisite: iOS 15+ / Swift 5.5+ can use async/await directly; lower deployment targets are evaluated against the project toolchain, back-deployment support, and dependency constraints. `Sendable` / actor isolation diagnostic strength is jointly decided by Swift language mode and Strict Concurrency Checking; Swift 6 mode checks full data-race safety by default. See [swift_concurrency.md](swift_concurrency.md).

| Model | Applicable Scenarios | Advantages | Costs | When to Reject |
|------|----------|------|------|----------|
| **async/await + child task** | Default choice: one-shot requests, finite steps, cancellation needed | Structured concurrency inside the scope; errors via throw | A top-level `Task {}` is unstructured and still needs an explicit owner and cancellation | Long-lived event streams → use AsyncSequence or Combine |
| **AsyncSequence / AsyncStream** | Data streams (WebSocket / notifications / long polling), need structured concurrency cancellation | Consistent cancellation model with async/await, backpressure controllable | Early iOS version support poor; operator API far less rich than Combine when needed | Need debounce / throttle / merge / zip and other complex operators → use Combine for now |
| **Combine** | Existing Combine code, complex event stream operators, UIKit legacy path bridging | Rich operators, mature integration with UIKit `@Published` | Subscription lifetime must be managed explicitly; bridging to strict concurrency isolation is costly | Prefer async/await for new one-shot async flows; do not rewrite an existing event stream just to migrate |
| **callback / completion handler** | Must bridge Objective-C API or old SDK | Good compatibility | Easy to miss calls, loose error handling, high Sendable risk | All new code rejected; if must, wrap with `withCheckedThrowingContinuation` to expose async API |
| **GCD (DispatchQueue)** | Rare scenarios still needing manual queue priority / serial barrier control | Historically mature, QoS controllable | Isolated from Swift concurrency, easy to break actor isolation | Almost all rejected; use `Task` + actor instead |
| **OperationQueue** | Complex dependency orchestration, need batch cancellation / pause | Task dependency graph, observable progress | Poor integration with async/await, Sendable risk | Default rejected; use `TaskGroup` to express dependencies |

New code default order:
1. async/await + Task → one-shot flows
2. AsyncSequence / AsyncStream → event streams
3. Combine → only when 2 cannot express and complex operators required
4. callback → only for bridging
5. GCD / OperationQueue → almost never selected

Migration decisions: see [migration_strategy.md](migration_strategy.md) "callback to async/await" and [swift_concurrency.md](swift_concurrency.md); this table only does selection, does not expand migration steps.
