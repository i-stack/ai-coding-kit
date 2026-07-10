<!-- last-verified: 2026-05 -->
# Performance Optimization

> This is an English mirror of the authoritative Chinese `references/performance_optimization.md`.
> In case of discrepancies, the Chinese source takes precedence.

## Applicable Scenarios
For analyzing and optimizing:
- Slow launch, slow first screen, slow page transitions
- List stutter, frame drops, unstable scrolling
- SwiftUI excessive refresh, UIKit high rendering cost
- Memory growth, object leaks, frequent peaks
- High battery drain, background task out of control, excessive image and network overhead

## General Principles
- Quantify first, optimize second; no metrics, no guesswork optimization.
- Handle by priority: main thread single call > 16ms (frame drop) or > 100ms (stall) → repeated computation > 20% of total time → SwiftUI `body` recalculation > 60Hz or UIKit `cellForItem` with synchronous I/O → resource waste (uncached images, unreused objects).
- Optimization MUST have before/after comparison data and confirm no behavioral regression.

## Performance Diagnostic Order
1. **Gather evidence first**: use metrics + tool selection from [observability_logging.md](observability_logging.md) "Performance Observation" to collect data; clarify current metric value + trigger path.
2. **Compare against thresholds**: use the thresholds above (> 16ms frame drop / > 100ms stall / repeated computation > 20% / body recalculation > 60Hz) to determine if optimization is warranted.
3. **Select root cause**: identify one main cause (main thread blocking / excessive refresh / repeated computation / resource waste / memory hotspot), then do targeted optimization per the specialized sections below (SwiftUI / UIKit / Launch / Memory).
4. **Before/after comparison**: re-collect with the same metrics; confirm metric improvement with no behavioral regression.

## SwiftUI Optimization Key Points
### Refresh Scope
- First check what triggers `body` recalculation, rather than blindly splitting Views.
- Reduce state radiation scope; avoid root node holding oversized mutable objects.
- Consider `Equatable` or more stable value semantic models for comparable inputs.

### Lists & Large Data
- Use lazy containers for large data.
- Ensure stable `id` to avoid diff failure causing rebuilds.
- Image loading, pagination, prefetching, and placeholder strategies MUST be evaluated together.

## UIKit Optimization Key Points
### Scrolling & Rendering
- Reduce view hierarchy and constraint complexity.
- Check off-screen rendering, transparency blending, shadows, corner radius, and mask combination costs.
- Avoid repeatedly creating formatters, rich text parsers, and heavyweight objects in Cells.

### Task Scheduling
- Main thread only does what MUST be on main thread.
- Move data shaping, precomputation, image decoding, and log organization off main thread.
- Async is not a panacea; the key is avoiding main thread waits and switch-back jitter.

## Launch Optimization
- Cold start: first compress synchronous I/O, synchronous network, and heavyweight singleton initialization on the launch path.
- First screen: load only first-screen-essential data; defer non-critical capabilities.
- Avoid excessive global registration in `AppDelegate` / `SceneDelegate` / root page initialization.

## Memory Governance
- Focus on whether caches are controlled, images are too large, and lists hold too many intermediate objects.
- Investigate closure retain cycles, Task lifecycles, unreleased notifications, and unremoved observers.
- Optimize both peak and steady state, not just instantaneous allocations.

## Tool Selection
Performance evidence tools (Instruments / Time Profiler / Core Animation / Allocations / Leaks / Memory Graph / Points of Interest / OSLog / MetricKit) usage and collection methods see [observability_logging.md](observability_logging.md) "Performance Observation". This file does not maintain a separate tool list.

## Common Anti-Patterns
- Blindly "optimizing" code style without metrics.
- Scattering state and caches everywhere to avoid one computation.
- SwiftUI page state change causing full-page redraw.
- UIKit lists doing decoding, layout, image processing, and height calculation on main thread.
- Only optimizing in the lab environment, not verifying on real devices and weak networks.

## Verification Checklist
- [ ] Are reproducible paths and performance metrics provided?
- [ ] Is there quantified before/after comparison?
- [ ] Is main thread hotspot, refresh scope, or memory hotspot confirmed to have decreased?
- [ ] Are low-end devices, long lists, weak networks, background-to-foreground scenarios verified?
- [ ] Is maintainability and correctness preserved (not sacrificed for performance)?
