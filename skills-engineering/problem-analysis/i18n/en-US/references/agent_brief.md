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

1. **[PA-001] Logic testing**: After receiving a problem, first review whether it contains logical errors, contradictory premises, circular assumptions, or false dichotomy. Reveal only substantial flaws; minor deviations stay silent.
2. **[PA-002] First principles**: For reasoning/trade-off questions, decompose from base requirements. If the user proposed no path, skip path evaluation. Fact-class questions are verified. A better path (means relation) is pointed out, then answered along the original path; if surface and base are substitutes, stop and confirm.
3. **[PA-003] Understanding gate**: Three mutually exclusive states — silent when clear / no path / fact-class; output `Problem Analysis` block then answer on substantial flaw or better path; if surface and base are substitutes, emit the block then only ask for confirmation (Path evaluation: "unconfirmed, do not proceed").

## When Not to Invoke

- Pure mechanical execution
- Information recitation without judgment components
- Pure translation/formatting tasks
