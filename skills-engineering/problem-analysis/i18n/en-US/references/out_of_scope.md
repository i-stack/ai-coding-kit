<!-- last-verified: 2026-05 -->
# problem-analysis Out of Scope

> This is an English mirror of the authoritative Chinese `OUT-OF-SCOPE.md`.
> In case of discrepancies, the Chinese source takes precedence.

This skill is responsible for **problem pre-analysis** — testing problem logic and decomposing real requirements before answering. Not responsible for response content itself or conclusion verification.

## What Is Not Handled

- **Response content correctness**: Handled by corresponding domain skills.
- **External verification of conclusions**: Handled by `epistemic-integrity` (GR-011/012).
- **Response argumentation structure**: Handled by `logical-reasoning` (GR-010).
- **Engineering output structure**: Handled by `engineering-discipline` (GR-002/004).
- **Pure mechanical execution**: Tasks without judgment components like formatting code, direct translation do not need pre-analysis.

## Boundary Explanation

PA-001/002/003 are upfront gates:
- Problem logic testing completed **before** the response
- Output independent "Problem Analysis" block when deviation found
- Silent pass when problem is clear

Division of labor with GR-010:
- GR-010 constrains AI **own response**'s argumentation quality
- PA-001 tests **user question**'s logical validity
