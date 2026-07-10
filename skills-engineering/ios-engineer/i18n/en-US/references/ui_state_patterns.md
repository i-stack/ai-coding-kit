<!-- last-verified: 2026-05 -->
# UI State Patterns

> This is an English mirror of the authoritative Chinese `references/ui_state_patterns.md`.
> In case of discrepancies, the Chinese source takes precedence.

## Table of Contents
- Usage Rules
- State Layering
- Page State Machine
- List State Pattern
- Form State Pattern
- Async Writeback Rules
- Empty State & Error State
- Common Anti-Patterns

## Usage Rules
- When dealing with page state, list state, form state, loading state, or error state, first define the state model.
- Do NOT use multiple booleans to compose complex page state.
- Do NOT let View, ViewModel, and Service simultaneously maintain a copy of the page state.

## State Layering
Fixed split into three layers:
- Domain State: whether business logic holds, whether data is valid
- Page State: whether the page is in loading, success, failure, empty, refresh, or pagination state
- Component State: dialogs, button disabled, input focus, local loading

Requirements:
- Page state is produced uniformly by the ViewModel.
- Component state MUST NOT reversely pollute domain state.
- List item local state MUST NOT override the entire page state.

> This file's "State Layering" is a **runtime semantic** layering (domain / page / component), defining which semantic layer a state belongs to;
> [domain_modeling.md](domain_modeling.md) "Modeling Layering" (DTO / Entity / ViewState / ErrorModel) is a **data type structure** layering, defining the type ownership of data at the code level.
> The two are orthogonal: e.g., "loading" is both a page state semantically and expressed as a ViewState type.

## Page State Machine
Recommended skeleton:

```swift
enum PageState: Equatable {
    case idle
    case loading
    case loaded(ContentState)
    case empty(EmptyState)
    case failed(ViewError)
}
```

Requirements:
- `idle`, `loading`, `loaded`, `empty`, `failed` five states MUST be distinct.
- Do NOT mix empty state into failure state.
- Do NOT mis-model mid-refresh success state as full-screen loading.

## List State Pattern
List state MUST be split into at least:
- Initial load state
- Pull-to-refresh state
- Pagination load state
- Empty list state
- Last page state
- Partial error prompt state

Requirements:
- Initial load failure and pagination failure are modeled separately.
- Pull-to-refresh MUST NOT clear already displayed data.
- Pagination failure MUST NOT overwrite existing list content.
- New refresh results MUST NOT be overwritten by old pagination results.

Recommended skeleton:

```swift
struct ListViewState<Item: Equatable>: Equatable {
    var items: [Item]
    var phase: Phase
    var pagination: PaginationState

    enum Phase: Equatable {
        case idle
        case loading
        case loaded
        case empty
        case failed(ViewError)
    }

    enum PaginationState: Equatable {
        case idle
        case loadingNextPage
        case noMoreData
        case failed(ViewError)
    }
}
```

## Form State Pattern
Form state MUST be split into at least:
- Input values
- Validation state
- Submission state
- Submission error
- Interactability state

Requirements:
- Validation errors and submission errors are modeled separately.
- Local validation failure MUST NOT be disguised as server failure.
- Submitting state MUST prevent duplicate submission.
- Form draft state MUST define reset and refill rules.

## Async Writeback Rules
- Before any async result writeback, MUST confirm the task is not cancelled, state is not stale, and the page is still valid.
- After page navigation, list reuse, or search keyword change, old results MUST NOT overwrite new state.
- Stale results MUST be discarded; do NOT do "best-effort writeback".

## Empty State & Error State
- Empty state means "successfully returned but no data".
- Error state means "request failed, parsing failed, business failure, or critical condition not met".
- Empty state MUST have empty state semantics; do NOT use "no data" to cover all failure scenarios.
- Error state MUST provide user actions: retry, go back, contact support, check network.

## Common Anti-Patterns
- `isLoading`, `hasError`, `isEmpty`, `hasData` four booleans coexisting
- Clearing the list directly during refresh causing flash
- Switching entire page to failure state on pagination error
- Allowing repeated button taps during submission
- Old request results overwriting new results after search keyword change
