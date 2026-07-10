<!-- last-verified: 2026-06 -->
# epistemic-integrity Out of Scope

> This is an English mirror of the authoritative Chinese `OUT-OF-SCOPE.md`.
> In case of discrepancies, the Chinese source takes precedence.

This skill is responsible for **epistemic grounding** — ensuring conclusions can be externally verified, confidence matches correctness. Not responsible for the technical correctness of the response content itself.

## What Is Not Handled

- **Technical content correctness**: This skill defines verification methodology, but does not replace specific domain knowledge. iOS-specific technical correctness is handled by `ios-engineer`.
- **Internal argument consistency**: GR-010 (logic chain internal consistency) is handled by `logical-reasoning` skill; this skill focuses on conclusion grounding with the **external real world**.
- **Pre-analysis of questions**: Logical validity testing of questions is handled by `problem-analysis` skill.

## Division of Labor Boundaries

| Skill | Direction | Responsibility |
|-------|-----------|----------------|
| `epistemic-integrity` (this skill) | outward | Whether conclusions match the world, how to verify |
| `logical-reasoning` (GR-010) | inward | Whether the response itself is self-consistent, layered, uncertainty marked clearly |
| `problem-analysis` (PA-001/002) | upfront | Problem validity itself, first principles decomposition |
