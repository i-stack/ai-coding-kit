<!-- last-verified: 2026-06 -->
# Domain Modeling

> This is an English mirror of the authoritative Chinese `references/domain_modeling.md`.
> In case of discrepancies, the Chinese source takes precedence.

## Table of Contents
- Usage Rules
- Modeling Layering
- Entity Modeling Rules
- DTO Modeling Rules
- ViewState Modeling Rules
- ErrorModel Modeling Rules
- Mapping Rules
- Common Anti-Patterns

## Usage Rules
- When involving entity design, state design, error design, or data transformation, MUST first define the modeling layering.
- Do NOT use server response structure directly as domain model or UI model.
- Modeling MUST first answer three questions: who holds, who transforms, who consumes.

## Modeling Layering
Fixed four layers:
- DTO: corresponds to interface transport structure
- Entity: corresponds to business semantic structure
- ViewState: corresponds to UI rendering state
- ErrorModel: corresponds to business or UI error semantics

Requirements:
- DTO MUST NOT leak to ViewModel and View.
- Entity MUST NOT carry UIKit / SwiftUI dependencies.
- ViewState MUST NOT reversely pollute Repository and Service.
- ErrorModel MUST NOT directly passthrough底层 `Error` text.

## Entity Modeling Rules
- Entity expresses stable business semantics, not interface noise or temporary UI state.
- Entity uses value semantics with `struct`.
- Entity field names use business language, not copying backend naming noise.
- Entity MUST be testable and comparable; explicitly implement `Equatable` when needed.

Suitable for Entity:
- Users, orders, products, sessions, permissions, amounts, time ranges

Not suitable for Entity:
- Placeholder text
- Cell display text
- Whether a button is disabled
- Raw API pagination fields

## DTO Modeling Rules
- DTO is only responsible for decoding and transport adaptation.
- DTO may retain interface field naming but MUST convert at the boundary.
- DTO does NOT carry business methods or participate in UI decisions.

Suitable for DTO:
- `page`, `pageSize`, `nextCursor`, `rawStatus`, `serverTimestamp`

## ViewState Modeling Rules
- ViewState only expresses UI rendering state.
- ViewState is produced by ViewModel, not directly by Repository.
- ViewState MUST cover empty state, loading state, error state, success state; do NOT only model the success state.

Recommended forms:
- Enum state: `idle / loading / loaded / failed`
- Composite state: list content, refresh state, pagination state, prompt state

Prohibited:
- Mixing ViewState and Entity into one universal model
- Using multiple booleans to compose complex state

> Complete modeling rules for page state machines, list state, form state, and async writeback see [ui_state_patterns.md](ui_state_patterns.md).

## ErrorModel Modeling Rules
- Errors are fixed into 6 layers, in flow order:
  1. **Transport Error** (network down, timeout, DNS failure)
  2. **Status Code Error** (4xx / 5xx HTTP responses)
  3. **Decoding Error** (JSON doesn't match schema, required fields missing)
  4. **Auth Error** (401 / 403 / token expired)
  5. **Business Error** (server business rule rejection, e.g., "insufficient balance")
  6. **Display Error** (user-facing error text + actionable actions)
- Each error layer's ownership:
  - Transport Error: captured by APIClient / project's existing network abstraction layer (URLSession / custom NetworkManager / Alamofire etc.), converted to `ErrorModel.network`; do NOT expose `NSError` or underlying SDK error types upward.
  - Status Code Error: mapped by APIClient based on code (4xx → client error branch, 5xx → server error branch).
  - Decoding Error: thrown by Decoder layer, carrying schema mismatch details; do NOT fall back to display layer.
  - Auth Error: handled uniformly by `AuthInterceptor` (trigger refresh / jump to login / degrade to read-only).
  - Business Error: identified by Repository / UseCase layer via `code + message`; APIClient does NOT determine business semantics.
  - Display Error: ViewModel maps the first 5 error types to user-visible text and actions (retry / go back / contact support).
- UI-facing ErrorModel MUST be mappable to title, text, and action buttons; not directly display system error text.
- ErrorModel MUST state recoverability (retryable / degradable / terminal) and user actions.

## Mapping Rules
- DTO → Entity: happens at Repository or Mapper layer
- Entity → ViewState: happens at ViewModel layer
- Error → ErrorModel: happens at error mapping layer or ViewModel boundary

Requirements:
- Mapping logic is centralized, not scattered across View, Cell, Service.
- Each direction does only one layer of conversion; do NOT mix multiple semantic layers.

## Common Anti-Patterns
- Passing DTO directly to View
- Converting Entity to CellModel and then passing it back to business layer
- Using one `Model` to simultaneously hold DTO, Entity, ViewState responsibilities
- Using multiple booleans to compose complex page state

> The anti-pattern of directly displaying `localizedDescription` (with identification criteria / risks / fix) see [anti_patterns.md](anti_patterns.md) §4 "Error Passthrough to UI".
