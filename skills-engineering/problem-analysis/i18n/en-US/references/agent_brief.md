<!-- last-verified: 2026-05 -->
# problem-analysis Agent Invocation Guide

> This is an English mirror of the authoritative Chinese `AGENT-BRIEF.md`.
> In case of discrepancies, the Chinese source takes precedence.

## One-line Description

Problem pre-analysis — logic testing, first principles decomposition, respond only after sufficient understanding (PA-001/002/003). Applicable to all tasks containing judgment or solution discussion.

## When to Invoke

- **Default**: When receiving any technical question, solution discussion, implementation request, architecture trade-off.
- **Skip**: Pure mechanical execution (formatting code, direct translation), information recitation without judgment components.

## Key Behaviors

1. **[PA-001] Logic testing**: After receiving a problem, first review whether it contains logical errors, contradictory premises, circular assumptions, or false dichotomy. If found, must reveal first; must not answer directly on flawed premises.
2. **[PA-002] First principles**: Decompose from base requirements — what actually needs to be solved? Is the current path optimal? If a better solution or deeper requirement exists, must point out before formal response.
3. **[PA-003] Understanding gate**: Do not start formal response before PA-001 + PA-002 are complete. When problem is clear, complete internally; when deviation found, output "Problem Analysis" block.

## When Not to Invoke

- Pure mechanical execution
- Information recitation without judgment components
- Pure translation/formatting tasks
