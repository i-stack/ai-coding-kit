# iOS Engineer

<Badge type="tip" text="v3.0.0" />

iOS / Swift / SwiftUI / UIKit / Xcode / CocoaPods / SPM engineering — architecture, concurrency, networking, performance, crash debugging, code review, refactoring, migration, testing.

This is the primary Agent Skill in ai-coding-kit, providing **production-grade AI coding rules** for iOS development.

::: info Supported Locales
English (en-US) · 简体中文 (zh-CN). The skill auto-matches your language.
:::

## Architecture

The skill is organized as a layered system:

```
ios-engineer/
├── SKILL.md              # Entry point: routing, triggers, output templates
├── references/           # 34 domain reference files (zh-CN)
│   ├── rule_index.md     # Canonical Rule ID registry
│   ├── self_evolution.md # Auto-evolution governance
│   └── ...               # 31 domain-specific references
├── i18n/en-US/           # English governance-layer mirrors
│   └── references/
├── scripts/              # 27 validation & evolution scripts
├── evolution/            # Proposal-driven evolution pipeline
│   ├── proposals/        # Active/in-review proposals
│   ├── archive/          # Archived/implemented proposals
│   └── hooks/            # Evolution guard scripts
└── snapshots/            # Evolution snapshots for consistency checks
```

## Rule System

The skill enforces **40+ rule IDs** across 5 categories:

| Category | Prefix | Count | Scope |
|----------|--------|-------|-------|
| Iron Rules | `IR-NNN` | 3 | Always enforced |
| Global Rules | `GR-NNN` | 9 | Cross-platform (epistemic, logic, discipline) |
| Symptom Routing | `SYM-NNN` | 7 | Auto-route symptoms → references |
| Task Routing | `ROUTE-NNN` | 10 | Auto-route task types → references |
| Output Templates | `OUT-NNN` | 6 | Structured output formats |

See the [Rule Index](./rule-index) for the complete registry.

## Key Rules

### IR-001 — Language Anchoring
Output language matches the user's input language. No forced Chinese output.

### IR-006 — Version Context Block
All concurrency / availability / SwiftUI behavior / network cancellation answers require a version context block before conclusions.

### IR-011 — Cognitive Adversary Mode
When triggered: output restatement, strongest counter-argument, hidden assumptions, failure conditions, falsifiable conditions, position flip, conformity self-check, confidence level, conclusion.

## Evolution Governance

The skill evolves through a **proposal-driven pipeline**:

1. **Propose** — Create a proposal in `evolution/proposals/`
2. **Validate** — Run `scripts/validate-skill-evolution.sh` (14-step check)
3. **Implement** — Add/modify references; update `rule_index.md`
4. **Promote** — Archive proposal; snapshot the skill state

All changes to `SKILL.md` or `references/` are gated by the pre-commit hook, which requires a staged evolution proposal in the same commit.
