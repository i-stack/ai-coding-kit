<!-- last-verified: 2026-06 -->
# Architecture & Networking Layer Design

> This is an English mirror of the authoritative Chinese `references/architecture_and_network.md`.
> In case of discrepancies, the Chinese source takes precedence.

## Applicable Scenarios
For the following tasks:
- Designing new modules, business domain splitting, dependency governance
- Designing Repository / Service / UseCase / Coordinator
- Planning networking layer, caching layer, authentication, retry, and error handling
- Reviewing Controller bloat, coupling issues, unclear boundaries
- User consulting on "current architecture", evaluation, or evolution suggestions

This file handles **implementation-type** architecture design and refactoring patterns. **Assessment-type** output (architecture checkup / health scoring / systemic risk identification / refactoring roadmap) belongs to [architecture_analysis.md](architecture_analysis.md).

## Current Architecture Consulting
- When users ask about "current architecture", must provide valuable analysis based on the project's actual architecture, real code organization, dependency directions, state flow, and boundary division; allowed to directly adopt "Code Review" level strictness to point out structural issues, fragility, and evolution risks — no conservative softening.
- When users ask about "current architecture" but information is incomplete, must first explicitly propose what supplementary information is needed to complete the judgment, rather than filling context based on guesses or assuming missing premises.
- Routing boundary (resolving the apparent conflict between "minimal fix vs. aggressively pointing out"):
  - **Architecture assessment / consulting output** mode: when users ask "current architecture", "any problems", "evolution direction", "is it reasonable" and other assessment questions, aggressively point out structural issues per §1 without softening due to boundary concerns.
  - **Implementing code changes** mode: when users request "change this method", "fix this bug", "add this field" and other specific changes, comply with SKILL.md core iron rule "first give minimal verifiable fix, do not propose full module rewrite, architecture overhaul, or large-scale refactoring first"; architecture-level suggestions only mentioned as residual risk or future direction, not mixed into current changes.
  - When tasks mix both modes (e.g., "fix this bug and also look at the architecture"), must first complete the minimal fix loop, then output architecture assessment in a separate paragraph — do not bundle architecture advice with fixes.

## Architecture Mandatory Principles
### Layer Responsibilities
- `ViewController` / `SwiftUI View`: only responsible for rendering, user input forwarding, and route triggering.
- `ViewModel` / `Presenter`: responsible for UI state orchestration; does not directly hold UIKit / SwiftUI view objects.
- `UseCase` / `Interactor`: carries business rules and use case orchestration.
- `Repository`: aggregates remote, local cache, and persistence access.
- `Service` / `APIClient`: only concerned with request sending, decoding, and underlying communication.
- Layer names follow the project's existing architecture; do not force transformation to `MVVM` just because it appears in rules. What must truly be satisfied is that UI, state orchestration, business rules, data access, and infrastructure responsibilities are distinguishable, testable, and replaceable.

### Dependency Direction
- UI layer depends on business abstractions, not reverse-depending on concrete implementations.
- High-level modules must not import low-level implementation details.
- Inject dependencies through constructors; container injection only for assembly, not for hiding dependencies.
- Cross-module communication preferably through protocols, routing capabilities, UseCase / Repository abstractions, or project's existing intermediary mechanisms; do not mandate "middleware" as a required form, and do not allow bypassing boundaries to directly access the other side's internal implementation.

### Parameter Pass-through & Data Source
- When adding new fields, method parameters, constructor parameters, or state values, first confirm which layer its true source belongs to; do not default to intermediate layers "casually adding a variable".
- If a value needs to be passed from upstream to downstream consumers, must complete the chain along the call path: data source -> mapping layer -> construction point -> holder -> usage point.
- Before making changes, explicitly point out where the chain break occurs: who should have created it, who should have held it, who currently isn't continuing to pass it through.
- Must not just add properties to the terminal class, add same-named parameters to intermediate classes, or temporarily pass null to make local compilation pass.
- If the pass-through chain spans multiple modules or layers, must simultaneously check whether naming semantics, nullability, default value strategy, and test coverage still hold.
- If the current layer cannot obtain the value, prefer tracing back to the true owner and creation point, then decide whether to pass through, rebuild the boundary, or refactor dependencies.

### Modularity Principles
- Organize by `Feature` + `Core`; prohibit accumulation by `Utils`, `Manager`, `Base`.
- SPM module boundaries must clearly define public API; avoid excessive `public`.
- "Cross-module direct access to internal implementation" smuggling is not allowed.
- Module splitting must first define stable input/output, module owner, and dependency direction; splitting packages just to reduce file length is not effective modularity.
- Base layer only holds cross-business stable capabilities; business base layer only holds business abstractions shared by multiple businesses; business component layer must not reverse-pollute the base layer.

## Typical Directory Structure
```text
App
Features/
Core/
SharedUI/
Infrastructure/
```

Constraints:
- `Features` collaborate through protocols or routing capabilities.
- `Core` holds stable abstractions and general capabilities; no concrete business logic.
- `Infrastructure` holds networking, database, logging, analytics, and other implementation details.

## Architecture Selection Rules
### UIKit Projects
- Medium-to-large projects use `MVVM + Coordinator` or `Clean Architecture`.
- When page state is complex, business orchestration is heavy, and test requirements are high, introduce `UseCase` and `Repository`.

### SwiftUI Projects
- Use state-driven design; strictly control the number of state sources.
- Avoid stuffing navigation, side effects, and network requests directly into View.
- For complex business pages, retain ViewModel / UseCase layering; prohibit stuffing business logic near `body`.

## Networking Layer Design
### Basic Structure
Recommended chain (complete chain defined in one place; other files reference here):

```text
Endpoint -> RequestBuilder -> APIClient -> Decoder/DTO -> Repository/Mapper -> Entity -> UseCase -> ViewModel/ViewState
```

Responsibilities per stage:
- **Endpoint**: defines path / method / Header / Body schema.
- **RequestBuilder**: constructs `URLRequest` (or project's existing network abstraction's equivalent request object).
- **APIClient**: sends requests, receives responses, layered error conversion.
- **Decoder/DTO**: decodes response byte stream into DTO data transfer objects (interface transport structure).
- **Repository/Mapper**: maps DTO to Entity business entities; aggregates remote / cache / persistence.
- **Entity**: business semantic structure, detached from transport details.
- **UseCase**: business use case orchestration (necessary for complex business scenarios; simple CRUD may omit).
- **ViewModel/ViewState**: UI state orchestration and rendering structure.

### Mandatory Requirements
- Unified request abstraction; prohibit scattered hand-written URL, Header, Query.
- New independent networking capabilities prefer `URLSession + async/await` (or project's unified equivalent abstraction); existing networking layer (e.g., custom `NetworkManager`, Alamofire, Combine-based abstractions) extends existing abstractions; do not opportunistically migrate underlying implementations in local changes. Underlying migration must be a standalone project, refer to [migration_strategy.md](migration_strategy.md).
- Decoding strategy centrally configured, e.g., date format, key conversion, null value compatibility.
- Error layering must comply with [domain_modeling.md](domain_modeling.md) "ErrorModel Modeling Rules" (6 layers: transport / status code / decoding / auth / business / display); APIClient layer responsible for converting the first 3 error layers to ErrorModel.
- Logs must record request identifier, duration, status code, key context, but must not leak sensitive information.

> File division: chain responsibilities + stage description see "Basic Structure" above; networking pattern details (pagination / retry / cache / auth refresh / upload-download / idempotency dedup / common anti-patterns) see [networking_patterns.md](networking_patterns.md); error layering see [domain_modeling.md](domain_modeling.md) "ErrorModel Modeling Rules". This file only retains networking layer **architecture boundaries** and cross-layer **safety rules**.

## Authentication & Security
- Use Keychain for credential storage.
- Sensitive logs desensitized; avoid printing complete Token, phone number, ID number, etc.

## Testability Requirements
- Repository, Service, Clock, Feature Flag, Store must all be replaceable.
- ViewModel / UseCase input/output must be unit-testable; do not depend on real network.
- Networking layer tests at minimum cover: success, timeout, cancellation, decoding failure, authentication failure.
- When adding new module boundaries or public API, must explain the minimal test surface: unit tests cover business rules, integration tests cover cross-module call chains, UI / snapshot validation covers visible state changes.

## Common Anti-Patterns
- ViewController directly sends requests, parses JSON, concatenates analytics.
- ViewModel directly imports UIKit / SwiftUI and manipulates controls.
- Scattered `URL(string:)`, string routes, and magic Headers everywhere.

> Universal `NetworkManager` and error-passthrough-to-UI anti-patterns (with identification criteria / risks / fixes) see [anti_patterns.md](anti_patterns.md) §1 "Universal Manager" and §4 "Error Passthrough to UI".

## Solution Review Checklist
- [ ] Are layer responsibilities clear; is there boundary crossing?
- [ ] Are dependencies protocol-oriented; replaceable and mockable?
- [ ] Are module boundaries stable; is public API minimized?
- [ ] Does the networking layer uniformly abstract requests, decoding, errors, and logs?
- [ ] Are caching, retry, and authentication based on business semantics rather than temporary patches?
- [ ] Is the design easy to test, extend, and troubleshoot?
- [ ] Are public API, module communication methods, test surfaces, and CI gates explained synchronously with boundary changes?
