<!-- last-verified: 2026-06 -->
# engineering-discipline Out of Scope

> This is an English mirror of the authoritative Chinese `OUT-OF-SCOPE.md`.
> In case of discrepancies, the Chinese source takes precedence.

This skill provides **global engineering discipline**, which is a **universal constraint layer** for all engineering tasks. It is not responsible for specific platform/framework-specific problems.

## What Is Not Handled

- **Platform-specific technical issues**: Implementation details for specific platforms like iOS, Android, Web are handled by corresponding platform skills. This skill only constrains the structure and discipline of engineering responses, not replacing domain knowledge.
- **Purely creative/non-engineering tasks**: Writing literary content, artistic creation, pure translation, and other non-code tasks are out of scope. But if these tasks involve technical engineering (such as generating frontend code), this skill's discipline still applies.
- **Strategic/business decisions**: Non-engineering decisions such as product roadmaps, business strategies, and marketing are out of scope.

## Boundary Explanation

Rules GR-001 through GR-008 in this skill are an **orthogonal layer** — they define "how to output", not "what to output":
- `ios-engineer` defines iOS engineering domain knowledge
- `engineering-discipline` defines the structural discipline that engineering output must follow

When both are triggered, they execute in parallel without conflict.
