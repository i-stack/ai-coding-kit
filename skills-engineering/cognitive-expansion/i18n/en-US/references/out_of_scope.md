<!-- last-verified: 2026-07 -->
# cognitive-expansion Out of Scope

> This is an English mirror of the authoritative Chinese `OUT-OF-SCOPE.md`.
> In case of discrepancies, the Chinese source takes precedence.

This skill is responsible for **post-response cognitive expansion** (breaking knowledge filter bubbles), not for the response content itself.

## What Is Not Handled

- **Main response content**: This skill appends cognitive footnotes after the main response is complete; it does not participate in generating the main response.
- **Cognitive Adversary Mode**: Anti-sycophancy/challenge in technical decisions/architecture trade-offs is owned by `cognitive-calibration/references/cognitive_adversary_mode.md` (Tier 2); ios-engineer only maintains a mirror/dependency. This skill manages Tier 0 (footnotes) and Tier 3 (deep dive/expansion).
- **Pure factual recitation**: Pure information queries without judgment/trade-offs/attribution/design choices do not require cognitive expansion.

## Trigger Gate

Tier 0 cognitive footnotes **do not trigger by default**. They are only appended when the response contains real judgment/trade-offs/attribution/design choices, **AND** can produce at least 1 falsifiable blind spot. Otherwise silently skipped.
