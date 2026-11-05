# References

The iOS Engineer skill includes **30 domain reference files** covering the full iOS / Swift engineering lifecycle.

::: tip How references are used
References are loaded by the AI agent at runtime based on symptom routing (SYM-*) or task routing (ROUTE-*) rules. They provide detailed domain knowledge for specific scenarios.
:::

## Governance Layer

| Reference | Description |
|-----------|-------------|
| [cognitive_adversary_mode.md](https://github.com/i-stack/ai-coding-kit/blob/feature_3.0.0/skills-engineering/ios-engineer/references/cognitive_adversary_mode.md) | Cognitive adversary mode specification |

## Domain References

| Reference | Domain |
|-----------|--------|
| [architecture_analysis.md](https://github.com/i-stack/ai-coding-kit/blob/feature_3.0.0/skills-engineering/ios-engineer/references/architecture_analysis.md) | Architecture analysis |
| [architecture_and_network.md](https://github.com/i-stack/ai-coding-kit/blob/feature_3.0.0/skills-engineering/ios-engineer/references/architecture_and_network.md) | Architecture & networking |
| [anti_patterns.md](https://github.com/i-stack/ai-coding-kit/blob/feature_3.0.0/skills-engineering/ios-engineer/references/anti_patterns.md) | Anti-patterns |
| [app_extensions.md](https://github.com/i-stack/ai-coding-kit/blob/feature_3.0.0/skills-engineering/ios-engineer/references/app_extensions.md) | App extensions |
| [build_release_and_ci.md](https://github.com/i-stack/ai-coding-kit/blob/feature_3.0.0/skills-engineering/ios-engineer/references/build_release_and_ci.md) | Build, release & CI |
| [code_templates.md](https://github.com/i-stack/ai-coding-kit/blob/feature_3.0.0/skills-engineering/ios-engineer/references/code_templates.md) | Code templates |
| [decision_records.md](https://github.com/i-stack/ai-coding-kit/blob/feature_3.0.0/skills-engineering/ios-engineer/references/decision_records.md) | Decision records |
| [domain_modeling.md](https://github.com/i-stack/ai-coding-kit/blob/feature_3.0.0/skills-engineering/ios-engineer/references/domain_modeling.md) | Domain modeling |
| [examples.md](https://github.com/i-stack/ai-coding-kit/blob/feature_3.0.0/skills-engineering/ios-engineer/references/examples.md) | Examples |

See the [full reference directory](https://github.com/i-stack/ai-coding-kit/tree/feature_3.0.0/skills-engineering/ios-engineer/references) on GitHub for all 30 files.

## Scripts

The skill ships with two auxiliary scripts in `scripts/`:

| Script | Purpose |
|--------|---------|
| `audit-ref-freshness.sh` | Audits `last-verified` dates in reference files |
| `run-ios-tests.sh` | Runs the skill's example-project tests |
