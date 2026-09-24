<!-- last-verified: 2026-09 -->
# problem-analysis Agent Invocation Guide

> This is an English mirror of the authoritative Chinese `AGENT-BRIEF.md`.
> In case of discrepancies, the Chinese source takes precedence.

## One-line Description

Problem pre-analysis — logic testing, first principles decomposition, respond only after sufficient understanding (PA-001/002/003). Default-load on judgment, solution discussion, implementation requests, or architecture trade-offs.

## When to Invoke

- **Default**: Any technical question containing judgment, solution discussion, implementation request, or architecture trade-off. Does not depend on the user saying "first principles / deeper need / problem deviation".
- **Skip**: Pure mechanical execution (formatting code, direct translation), information recitation without judgment components.

## Key Behaviors

1. **[PA-001] Logic testing**: After receiving a problem, first review whether it contains logical errors, contradictory premises, circular assumptions, or false dichotomy. If found, must reveal first; must not answer directly on flawed premises.
2. **[PA-002] First principles**: For reasoning/trade-off questions, decompose from base requirements. Fact-class questions are verified, not derived from first principles. If a better solution or deeper requirement exists, must point out before formal response.
3. **[PA-003] Understanding gate**: Three states — silent when clear; output `Problem Analysis` block then answer on substantial deviation; confirm real intent when base requirement does not match surface request.

## When Not to Invoke

- Pure mechanical execution
- Information recitation without judgment components
- Pure translation/formatting tasks
