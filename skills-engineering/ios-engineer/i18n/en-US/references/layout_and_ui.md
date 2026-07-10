<!-- last-verified: 2026-06 -->
# Layout & HIG Specification

> This is an English mirror of the authoritative Chinese `references/layout_and_ui.md`.
> In case of discrepancies, the Chinese source takes precedence.

## Applicable Scenarios
For the following issues:
- Auto Layout conflicts, page misalignment, abnormal list heights
- SwiftUI view flickering, jumping, excessive refreshes, navigation state corruption
- Dark Mode, Dynamic Type, accessibility support gaps
- High-fidelity restoration, complex forms, complex lists, mixed layouts

## UIKit Layout Diagnostic Order
Diagnostic order is fixed:
1. Is the view hierarchy reasonable
2. Are constraints complete and conflict-free
3. Are `contentHugging` / `compressionResistance` correct
4. Is there incorrect reliance on fixed dimensions
5. Is it affected by reuse, async writeback, or hidden logic

Requirements:
- Layout diagnostics converge in the above order; do NOT list multiple broad candidate directions in parallel.
- When outputting, first point out the most likely break point, then supplement secondary possibilities.

### UIKit Constraint Rules
- Do NOT use `999` near-required priority to mask design issues unless constraint intent is clearly explained and standard constraint approaches don't apply.
- Constraints first express relative relationships and content-driven chains; do NOT rely on hardcoded dimensions, magic spacing, or patch-style sizing.
- When constraint conflicts appear, first fix the view hierarchy and constraint design; do NOT first try to work around by tuning priorities.
- Express layout through complete constraint relationships; do NOT force with `layoutIfNeeded()`.
- Complex Cells MUST define content boundaries, spacing sources, and self-sizing height chains.
- Self-sizing height MUST clearly explain what stretches the content, how constraints close, and where the chain might break due to hiding or reuse.
- Do NOT repeatedly create, activate, or rebuild constraints in `layoutSubviews`, `updateConstraints`, or similar high-frequency lifecycle methods.
- When using Auto Layout, MUST clarify `translatesAutoresizingMaskIntoConstraints` on/off semantics to avoid mixing system and manual constraints.
- `UIStackView` is suitable for linear layouts, NOT for complex, highly conditional page skeletons.

### Content-Adaptive Sizing
- Rely on `intrinsicContentSize` and constraint chains for adaptation.
- Text, localization,超长 text, and extreme font sizes MUST be included in verification.
- List height calculation must account for async images, rich text, expand/collapse, and reuse writeback.

## SwiftUI View Design Rules
### State Management
- Keep state granularity low; avoid root View holding oversized mutable state.
- Do NOT write network requests, analytics, or navigation side effects directly in `body`'s temporary closures.
- MUST ensure stable `id` to avoid list flickering, scroll position loss, and view state misalignment.

### Layout Stability
- MUST understand `frame`, `fixedSize`, `layoutPriority`, `alignment` semantics; stacking modifiers by trial-and-error is prohibited.
- Avoid unnecessary `GeometryReader` propagation.
- For complex scroll pages, evaluate `LazyVStack`, segmented loading, and subview decomposition.

## Lists & Reuse
- UIKit lists: focus on reuse identifiers, async task cancellation, image writeback misalignment, state residue.
- SwiftUI lists: focus on identity stability, minimal refresh scope, and data source diff quality.
- Any list issue MUST check all four dimensions: "data source, reuse chain, async writeback, layout constraints".

## Auto Layout Supplementary Checks
- Multi-line text, self-sizing height, long text, localization, and extreme font sizes are default verification items, not optional add-ons.
- After hiding, folding, expanding, placeholder switching, and async content writeback, MUST re-check that constraint chains still close.
- For nested scrolling, complex forms, and dynamic list pages, first determine if it's a hierarchy design problem, then if it's a single constraint issue.
- When SwiftUI has jumping, flickering, or misalignment, simultaneously check `id` stability, state granularity, and refresh boundaries; do NOT attribute all symptoms to layout.

## Apple HIG & Accessibility
### Basic Requirements
- Use semantic colors, dynamic fonts, and system interaction feedback.
- Interaction areas, hierarchy, back paths, and empty states should follow iOS user expectations.
- Do NOT break platform interaction consistency for "design mock fidelity".

### Accessibility Requirements
- Key controls provide accurate `accessibilityLabel`, `accessibilityHint`, `accessibilityTraits`.
- Focus order, VoiceOver content, and tappable areas MUST be functional.
- Images and icons MUST distinguish decorative assets from semantic assets.

## Common Anti-Patterns
- Fixing layout issues with hardcoded dimensions, extra spacer Views, or疯狂 priority adjustments.
- Forgetting to reset state and cancel async tasks in Cell/Item reuse scenarios.
- Repeatedly rebuilding constraints in `layoutSubviews` or constraint update callbacks, causing jitter, conflicts, or performance degradation.
- Reducing Auto Layout problems to "just tweak priorities until it works".
- Stuffing multiple business states into one large object in SwiftUI, causing full-page refreshes.
- Skipping Dark Mode, Dynamic Type, VoiceOver to rush deadlines.

## Review Checklist
- [ ] Is layout driven by explicit constraints or clear SwiftUI layout semantics?
- [ ] Is it compatible with long text, localization, extreme font sizes, and dark mode?
- [ ] Do lists/forms account for reuse, writeback, focus, and scroll stability?
- [ ] Is there unstable identity, excessive refresh, or incorrect state ownership?
- [ ] Are accessibility and platform consistency requirements covered?
