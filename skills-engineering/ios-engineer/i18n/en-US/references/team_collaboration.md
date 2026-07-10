<!-- last-verified: 2026-05 -->
# Team Collaboration Specification

> This is an English mirror of the authoritative Chinese `references/team_collaboration.md`.
> In case of discrepancies, the Chinese source takes precedence.

## Table of Contents
- Usage Rules
- Change Scope
- Module Ownership
- PR Rules
- Review Responsibility
- Technical Debt Handling
- Communication & Decision Sync
- Common Anti-Patterns

## Usage Rules
- This file MUST be used when involving multi-person collaboration, cross-module changes, long-term refactoring, or shared component governance.
- Technical proposals MUST simultaneously consider code correctness, team collaboration cost, and ongoing maintenance responsibility.
- Do NOT make locally optimal decisions based solely on "can the current requirement be done".
- If the current task has no clear multi-person collaboration, shared modules, release process, or PR context, this file degrades to a risk reminder; full ownership, PR splitting, or team sync processes are not强制 output.

## Change Scope
- Every change MUST clearly define: what changes, what doesn't change, who is affected, who verifies.
- A single PR MUST maintain a single theme; do NOT mix feature changes, refactoring, style adjustments, and incidental fixes.
- If cross-module changes are truly needed, first document impact scope and dependency order.

## Module Ownership
- Every Feature, Core module, and shared component MUST have clear ownership.
- When non-owners modify shared modules, they MUST explain the reason, impact scope, and verification method.
- Shared module changes MUST simultaneously consider compatibility and downstream impact.

## PR Rules
- PR title MUST state the change objective; vague titles are NOT allowed.
- PR description MUST cover: background, change scope, risks, verification method, uncovered risks.
- Large changes MUST be split into multiple independently reviewable PRs.
- Architecture refactoring PRs MUST include a decision record or phased plan.

## Review Responsibility
- Review is not just about code style; MUST check correctness, boundaries, regression risk, tests, and maintainability.
- Reviewers MUST pay attention to shared modules, state boundaries, concurrency boundaries, and side effect propagation.
- If changes affect other teams or modules, Reviewers MUST request supplementary impact documentation.

## Technical Debt Handling
- Technical debt MUST be explicitly recorded; no verbal leftovers.
- If technical debt is not addressed now, MUST explain the reason, risk, and conditions for future handling.
- Do NOT disguise temporary workarounds as long-term architecture.

## Communication & Decision Sync
- Architecture decisions, migration plans, and compatibility strategies MUST be reproducible by the team.
- Key conclusions MUST be documented, not just exist in chat logs.
- For high-risk changes involving cross-person collaboration, MUST sync rollback conditions and failure contingencies.

## Common Anti-Patterns
- A single PR doing features, refactoring, performance optimization, and style adjustments simultaneously
- Modifying shared modules without explaining impact
- Reviewer only looking at naming and formatting, not risks
- Technical debt not recorded, just "we'll get to it later"
- Temporary workarounds persisting long-term
