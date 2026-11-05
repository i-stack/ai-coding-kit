# iOS Engineer

<Badge type="tip" text="v3.0.0" />

iOS / Swift / SwiftUI / UIKit / Xcode / CocoaPods / SPM engineering — architecture, concurrency, networking, performance, crash debugging, code review, refactoring, migration, testing.

This is the primary Agent Skill in ai-coding-kit, providing **production-grade AI coding rules** for iOS development.

::: info Supported Locales
English (en-US) · 简体中文 (zh-CN). The skill auto-matches your language.
:::

## Architecture

The skill is a single entry document plus lazily-loaded domain references:

```
ios-engineer/
├── SKILL.md              # Entry point: routing, triggers, output templates
├── AGENT-BRIEF.md        # Companion brief for agent hosts
├── OUT-OF-SCOPE.md       # Explicit non-goals
├── references/           # 30 domain reference files (zh-CN)
├── i18n/en-US/           # English mirrors of the governance layer
│   └── references/
├── scripts/              # Reference freshness audit + iOS test runner
└── agents/               # Host-specific agent metadata
```

## Rule System

The skill declares **42 rule IDs** across 4 local categories, plus mirrored global rules:

| Category | Prefix | Count | Scope |
|----------|--------|-------|-------|
| Iron Rules | `IR-NNN` | 3 | Always enforced |
| Symptom Routing | `SYM-NNN` | 7 | Auto-route symptoms → references |
| Task Routing | `ROUTE-NNN` | 23 | Auto-route task types → references |
| Output Templates | `OUT-NNN` | 6 | Structured output formats |
| Global Rules (mirrored) | `GR-NNN` | 3 | Owned by global skills, cited here |

Rule IDs are declared inline in `SKILL.md`; their authoritative text lives in the reference file each bullet points to.

## Key Rules

### IR-001 — Language Anchoring
Output language matches the user's input language. No forced Chinese output.

### IR-006 — Version Context Block
All concurrency / availability / SwiftUI behavior / network cancellation answers require a version context block before conclusions.

### IR-011 — Cognitive Adversary Mode
When triggered: output restatement, strongest counter-argument, hidden assumptions, failure conditions, falsifiable conditions, position flip, conformity self-check, confidence level, conclusion.

## Validation

Changes to `SKILL.md` or `references/` are guarded mechanically:

- **Structure gate** — `skills-engineering/scripts/validate-skill-structure.sh` (frontmatter, size, reference links, orphan references).
- **Doc hygiene** — `skills-engineering/scripts/validate-doc-hygiene.sh` (banned-phrase scan on runnable entry docs).
- **Integrity baseline** — `skills-engineering/scripts/validate-skill-integrity.sh` registers content hashes; CI compares with `--check-only`.
- **Reference freshness** — `scripts/audit-ref-freshness.sh` flags stale `last-verified` dates.
