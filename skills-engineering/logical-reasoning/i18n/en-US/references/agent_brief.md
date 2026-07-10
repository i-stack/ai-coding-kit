<!-- last-verified: 2026-05 -->
# logical-reasoning Agent Invocation Guide

> This is an English mirror of the authoritative Chinese `AGENT-BRIEF.md`.
> In case of discrepancies, the Chinese source takes precedence.

## One-line Description

Global argumentation discipline — traceable logic chain, layered, causal discipline, logic chain output block (GR-010). Applies to all engineering tasks, platform-independent.

## When to Invoke

- **Default**: All tasks containing judgment components.
- **Must output logic chain block**: Technical decisions, architecture trade-offs, root cause attribution, performance attribution, review final judgments, user strong conviction or explicitly requests challenging viewpoints.
- **Skip**: Pure mechanical execution, tasks without any judgment components.

## Key Behaviors

1. **[GR-010]** Responses must have a traceable logic chain.
2. Distinguish "facts / inferences / recommendations / speculations"; must not write unverified inferences as established conclusions.
3. Prohibited: unjustified causal jumps, circular reasoning, self-contradiction within the same response.
4. Non-obvious judgments must mark at least one "because...therefore..." step.
5. When evidence is insufficient, mark uncertainty; must not use fluent wording to disguise certainty.
6. High-risk judgments output independent "Logic Chain" block (facts/evidence, inference, conclusion strength, falsifiable/gaps).

## When Not to Invoke

- Pure mechanical execution
- Without any judgment components (pure information recitation)
- Pure subjective preference/creation
