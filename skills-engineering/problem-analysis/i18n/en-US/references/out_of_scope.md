<!-- last-verified: 2026-09 -->
# problem-analysis Out of Scope

> This is an English mirror of the authoritative Chinese `OUT-OF-SCOPE.md`.
> In case of discrepancies, the Chinese source takes precedence.

This skill is responsible for **problem pre-analysis** — testing problem logic and decomposing real requirements before answering. Not responsible for response content itself or conclusion verification.

## What Is Not Handled

- **Response content correctness**: Handled by corresponding domain skills.
- **External verification of conclusions**: Handled by `cognitive-reasoning` (GR-011~013).
- **Response argumentation structure**: Handled by `cognitive-reasoning` (GR-010).
- **Adversarial challenge of user conclusions**: Handled by `cognitive-reasoning` (CAM-001~005).
- **Implementation decision-tree grilling**: Handled by `plan-grill` (PG-000) after this skill completes.
- **Engineering output structure**: Handled by `engineering-discipline` (GR-002/004).
- **Pure mechanical execution**: Tasks without judgment components like formatting code, direct translation do not need pre-analysis.
- **Deriving empirical facts from first principles**: Fact-class questions are verified (GR-013); this skill does not grow a requirements tree from APIs/numbers/events.

## Boundary Explanation

PA-001/002/003 are upfront gates:
- Problem logic testing completed **before** the response
- Output independent "Problem Analysis" block when substantial deviation found (fields: Logic test / Real requirement / Path evaluation)
- Silent pass when problem is clear
- Confirm first when base requirement does not match surface request; do not advance the solution before confirmation

Division of labor with GR-010:
- GR-010 constrains AI **own response**'s argumentation quality
- PA-001 tests **user question**'s logical validity
