<!-- last-verified: 2026-07 -->
# Rule ID Index

> This is an English mirror of the authoritative Chinese `references/rule_index.md`.
> In case of discrepancies, the Chinese source takes precedence.

## Usage Rules
- This file is the canonical index for rule IDs used in [SKILL.md](../SKILL.md). **Add/modify/retire IDs here first, then sync SKILL.md**.
- The [scripts/validate-rule-ids.sh](../scripts/validate-rule-ids.sh) automated check asserts bidirectional set equality between both sides; mismatch → nonzero exit.
- ID format: `^[A-Z]+-\d{3}$`. Five prefix categories:
  - `IR-NNN` — Iron Rule, globally enforced
  - `SYM-NNN` — Symptom navigation table row
  - `ROUTE-NNN` — Task routing bullet
  - `OUT-NNN` — Output template entry
  - `GR-NNN` — Global Rule, cross-platform; owned by independent global skills; ios-engineer tasks may reference them; this file serves as a mirror registration point
- IDs are never reused once published: retired entries stay in the "Retirement Records" section, marked `retired`, with a replacement ID noted (or `retired-no-replacement` if none). Retired IDs **must not appear** in SKILL.md — the validator will flag them.
- IDs carry no semantic suffix (no `ROUTE-LAYOUT-001`); semantics are communicated via this table's "Summary" column to avoid meaning drift during rename/split.
- Numbering may have gaps (e.g., IR-001 jumps to IR-006); no continuity is enforced. New entries prefer `max(existing number) + 1` within the prefix.

## Iron Rules IR-NNN

| ID | Status | Summary | SKILL.md Anchor |
|----|--------|---------|-----------------|
| IR-001 | active | Response language anchored to user input language; code comments/API names/compiler errors/crash stacks/command output/log literals may remain in original language; natural-language content (conversation, analysis, diagnosis, rule output) must match user language | `## Core Iron Rules` |
| IR-006 | active | Concurrency / availability API / SwiftUI behavior / network cancellation semantics output must include a standalone "Version Baseline" block before "Conclusion" (real values or explicit assumptions); field presence must be mechanically verifiable | ibid. |
| IR-011 | active | When Cognitive Adversary Mode is triggered, output must include: Restatement, Strongest Counter-argument, Hidden Assumptions, Failure Conditions, Falsifiable Conditions, Position Reversal, Sycophancy Self-check, Confidence, Conclusion | ibid. |

## Global Rules GR-NNN

GR-NNN rules are owned by independent global skills and are cross-platform (not iOS-specific). ios-engineer tasks may reference them; this file serves as a mirror registration point.

| ID | Status | Summary | Skill Location |
|----|--------|---------|----------------|
| GR-001 | active | Security & compliance defense (never expose .env credentials, restrict high-sensitivity shells, prevent API/network leaks) | [engineering-discipline/references/engineering_discipline.md](../../engineering-discipline/references/engineering_discipline.md) |
| GR-002 | active | Pre-confirmation block (literalized trigger when info is insufficient; section title serves as mechanical verification anchor) | ibid. |
| GR-003 | active | Single root cause lock (1 primary path + at most 1 alternative) | ibid. |
| GR-004 | active | Four-section output (root cause → why → fix → verification); review exceptions defined by platform skill | ibid. |
| GR-005 | active | Minimum fix priority | ibid. |
| GR-006 | active | Tool call budget interception & proactive abort mechanism (3 failures on same path or 15 turns → hard stop) | ibid. |
| GR-007 | active | No code formatting (prevent diff noise, limit beautification scope, eliminate blank lines) | ibid. |
| GR-008 | active | Change coverage declaration (covered / not covered / residual risk — three fields; section title as mechanical verification anchor) | ibid. |
| GR-010 | active | Traceable logical chain; high-risk scenarios output independent "Logical Chain" block (facts/evidence, inference, conclusion strength, falsifiable/gaps) | [cognitive-reasoning/references/logical_reasoning.md](../../cognitive-reasoning/references/logical_reasoning.md) |

## Symptom Navigation SYM-NNN

| ID | Status | Summary | SKILL.md Anchor |
|----|--------|---------|-----------------|
| SYM-001 | active | Crash / assertion / force-unwrap / wild pointer / EXC_BAD_ACCESS → root_cause_enforcement.md | `### Symptom Navigation` |
| SYM-002 | active | UI misalignment / constraint conflicts / list jitter / accessibility → layout_and_ui.md | ibid. |
| SYM-003 | active | State corruption / async write-back / stale request overwrites → ui_state_patterns.md | ibid. |
| SYM-004 | active | Request failure / auth refresh / pagination or cache issues → networking_patterns.md | ibid. |
| SYM-005 | active | Lag / slow launch / memory growth / energy drain → performance_optimization.md | ibid. |
| SYM-006 | active | Naming chaos / force-unwrap / access control → ios_conventions.md | ibid. |
| SYM-007 | active | Legacy project degradation / afraid to touch code / unfamiliar project no entry point → architecture_analysis.md | ibid. |

## Task Routing ROUTE-NNN

Each ROUTE entry's TRIGGER/SKIP anchor pair is defined in SKILL.md under the corresponding bullet; this table's "Summary" column retains only the primary keyword set to avoid dual-maintenance of TRIGGER/SKIP.

| ID | Status | Summary | SKILL.md Anchor |
|----|--------|---------|-----------------|
| ROUTE-001 | active | Debugging / Bug / Intermittent issues / Crash → root_cause_enforcement.md | `## Task Routing` |
| ROUTE-002 | active | Architecture design / Module decomposition / State ownership / Parameter pass-through → architecture_and_network.md | ibid. |
| ROUTE-003 | active | Architecture analysis / Project health / Refactoring roadmap → architecture_analysis.md | ibid. |
| ROUTE-004 | active | Data modeling / DTO / Entity / ViewState / ErrorModel → domain_modeling.md | ibid. |
| ROUTE-005 | active | UI state / Lists / Forms / Async write-back → ui_state_patterns.md | ibid. |
| ROUTE-006 | active | UI layout / SwiftUI stability / Auto Layout / Accessibility → layout_and_ui.md | ibid. |
| ROUTE-007 | active | Concurrency / Cancellation chains / actor / Sendable → swift_concurrency.md | ibid. |
| ROUTE-008 | active | Networking patterns / Pagination / Cache / Retry / Auth → networking_patterns.md | ibid. |
| ROUTE-009 | active | Logging / Observability / Required fields / Debug forensics → observability_logging.md | ibid. |
| ROUTE-010 | active | Performance / Launch / List lag / Memory / Energy → performance_optimization.md | ibid. |
| ROUTE-011 | active | Code review / PR Review / Design Review → review_checklists.md | ibid. |
| ROUTE-012 | active | Refactoring implementation / Migration / Canary / Rollback → migration_strategy.md | ibid. |
| ROUTE-013 | active | Build / CI / Release observability → build_release_and_ci.md | ibid. |
| ROUTE-014 | active | Coding conventions / Terminology / Naming / Access control → ios_conventions.md | ibid. |
| ROUTE-015 | active | Cross-module collaboration / Ownership / PR decomposition / Tech debt → team_collaboration.md | ibid. |
| ROUTE-016 | active | Tool budget / Sub-agent routing / Multi-round investigation / Search control / MCP priority mapping → mcp_control.md | ibid. |
| ROUTE-017 | active | Complex task playbooks (escalation criteria: see SKILL.md `### Routing Priority`) → execution_playbooks.md | ibid. |
| ROUTE-018 | active | Skill self-evolution / Rule gaps-conflicts-retirements / Skill validation scenarios → self_evolution.md | ibid. |
| ROUTE-020 | active | Git workflow / pbxproj & storyboard conflicts / Lock file commits / Branching & hotfix → git_workflow.md | ibid. |
| ROUTE-021 | active | Push Notifications / Remote push / Local notifications / Notification Service Extension / Rich media notifications / Notification permissions → notifications.md | ibid. |
| ROUTE-022 | active | Privacy permissions / Location / Camera / Photo Library / Microphone / Contacts / HealthKit / ATT tracking / Permission requests → privacy_permissions.md | ibid. |
| ROUTE-023 | active | SwiftData / Core Data / Persistence / Data migration / Model Schema / Lightweight migration / Heavyweight migration → persistence.md | ibid. |
| ROUTE-024 | active | StoreKit / In-App Purchase / Subscriptions / IAP / Receipt validation / Restore purchases / Promotional offers → storekit_iap.md | ibid. |
| ROUTE-025 | active | App Extensions / Widget / Share Extension / Watch App / Siri Intent / Action Extension / Notification Content Extension → app_extensions.md | ibid. |

## Output Templates OUT-NNN

| ID | Status | Summary | SKILL.md Anchor |
|----|--------|---------|-----------------|
| OUT-001 | active | Formal proposals / Debugging conclusions / Migration roadmaps / Performance analysis: four-section field template → examples.md | `## Output Templates` |
| OUT-002 | active | Code review / PR Review: findings-first skeleton (trigger conditions: see GR-004) → review_checklists.md §8 | ibid. |
| OUT-003 | active | Production code skeleton → code_templates.md | ibid. |
| OUT-004 | active | Testing strategy / Verification scope → testing_strategy.md | ibid. |
| OUT-005 | active | Architecture decision records → decision_records.md | ibid. |
| OUT-006 | active | iOS test system construction / Execute tests and repair failures → test_execution_and_repair.md + testing_strategy.md | ibid. |

## OUT Sub-unit Mapping

`OUT-NNN` IDs map to ref files that often contain multiple independent sub-units (template sections, playbook chapters, dual-file responsibilities). This table aids reverse lookup and does not replace OUT-NNN ID governance. Sync this table when adding new templates/playbooks.

| OUT-ID | Sub-unit Name | File Anchor | Applicable Scenario |
|--------|---------------|-------------|---------------------|
| OUT-003 | ViewModel Template | [code_templates.md](code_templates.md) "## ViewModel 模板" | UIKit MVVM / SwiftUI state-driven pages / list-form-detail page state orchestration |
| OUT-003 | UseCase Template | [code_templates.md](code_templates.md) "## UseCase 模板" | Business rule aggregation / multi-data-source orchestration / domain layer I/O modeling |
| OUT-003 | Repository Template | [code_templates.md](code_templates.md) "## Repository 模板" | Remote + local cache aggregation / decouple Service from business layer |
| OUT-003 | APIClient Template | [code_templates.md](code_templates.md) "## APIClient 模板" | URLSession + async/await / strongly-typed error modeling |
| OUT-003 | Coordinator Template | [code_templates.md](code_templates.md) "## Coordinator 模板" | UIKit navigation orchestration / Feature routing decoupling |
| OUT-003 | Actor Template | [code_templates.md](code_templates.md) "## Actor 模板" | Shared mutable state isolation / Token refresh / In-memory cache / Request dedup |
| OUT-003 | SwiftUI Property Wrapper Selection | [code_templates.md](code_templates.md) "## SwiftUI propertyWrapper 选型" | State ownership decisions / @State / @Binding / @StateObject / @Observable / @Environment selection |
| OUT-003 | Dependency Injection Triad | [code_templates.md](code_templates.md) "## 依赖注入三选一" | Constructor injection vs property injection vs container decisions |
| OUT-003 | Concurrency Model Selection | [code_templates.md](code_templates.md) "## 并发模型选型" | async/await / AsyncSequence / Combine / callback / GCD selection |
| OUT-006 | Test Planning (layering & coverage strategy) | [testing_strategy.md](testing_strategy.md) | Design tests: choose stubs per layer / decide coverage scope |
| OUT-006 | Test Execution & Failure Repair | [test_execution_and_repair.md](test_execution_and_repair.md) | Run tests / analyze failures / decide fix vs supplement |
| ROUTE-017 | Legacy Page Handover | [execution_playbooks.md](execution_playbooks.md) "## 接手遗留页面" | Massive ViewController / scattered state / UIKit + SwiftUI hybrid legacy pages |
| ROUTE-017 | Systematic Intermittent Crash Investigation | [execution_playbooks.md](execution_playbooks.md) "## 反复偶现 Crash 系统排查" | Hard-to-reproduce crashes / online sporadic exceptions / random state corruption |
| ROUTE-017 | Performance Deep-Dive | [execution_playbooks.md](execution_playbooks.md) "## 性能专项" | Slow launch / list lag / heavy page refresh / abnormal memory growth |
| ROUTE-017 | Concurrency Architecture Migration | [execution_playbooks.md](execution_playbooks.md) "## 并发架构迁移" | callback → async/await migration / GCD → structured concurrency / serial queue → actor |
| ROUTE-017 | Large-Scale Refactoring Implementation | [execution_playbooks.md](execution_playbooks.md) "## 大型重构落地" | Module decomposition / navigation rebuild / state model rebuild / network layer refactor |

## Retirement Records

| ID | Status | Reason | Replacement | Proposal |
|----|--------|--------|-------------|----------|
| ROUTE-019 | retired | True duplicate of ROUTE-018: ROUTE-019 routed "Skill validation scenarios" to validation_scenarios.md, while ROUTE-018 already declared "need validation scenarios → append validation_scenarios.md". Post-retirement, "Skill validation scenarios" keyword merged into ROUTE-018 primary keyword set. | ROUTE-018 | 20260508-154338-retire-route-019-merge-into-018 |
| IR-009 | retired | The only meta-IR among 9 IRs (delegated execution to ios_conventions.md), at a different layer from the other 8 concrete behavioral directives; its function is already covered by ROUTE-014 ("coding conventions → ios_conventions.md"). Post-retirement, IR layer retains only concrete behavioral directives with consistent expression. | ROUTE-014 | 20260508-155152-retire-ir-009-meta-ir |

## Cross-File Shared Concept Index

Implements the execution rules from [self_evolution.md](self_evolution.md) "Candidate Constraints" requiring full grep coverage of all reference locations for proposals involving cross-file shared concepts. When modifying the owner location, all reference locations must be synchronized; modifying reference locations without touching the owner is considered a local clarification and does not enter the cross-file proposal scope.

| Concept | Owner Location | Reference Locations | Modification Protocol |
|---------|---------------|---------------------|-----------------------|
| Four-section output (root cause → why → fix → verification) | [engineering-discipline/SKILL.md](../../engineering-discipline/SKILL.md) GR-004 | [examples.md](examples.md) §1/§2/§4/§5/§6; [decision_records.md](decision_records.md) L5; [test_execution_and_repair.md](test_execution_and_repair.md) L82; [validation_scenarios.md](validation_scenarios.md) L26/L88; [migration_strategy.md](migration_strategy.md) (playbook artifact layer) | Changing owner must sync all references; any reference phrasing deviating from owner is drift |
| findings-first skeleton (review output) | [review_checklists.md](review_checklists.md) §8 | [SKILL.md](../SKILL.md) OUT-002; [examples.md](examples.md) §3; [migration_strategy.md](migration_strategy.md) L114 | Changing owner skeleton fields must sync SKILL.md OUT-002 description and examples.md §3 reference phrasing |
| Parameter pass-through & data sources | [architecture_and_network.md](architecture_and_network.md) "参数透传与数据来源" section | [SKILL.md](../SKILL.md) ROUTE-002; [review_checklists.md](review_checklists.md) §1/§2; [validation_scenarios.md](validation_scenarios.md) Scenario 2 | Changing owner section title must sync literal references in review_checklists.md; changing concept definition must sync SKILL.md ROUTE-002 keywords |
| Task routing primary keyword sets | [SKILL.md](../SKILL.md) ROUTE table | This file's ROUTE-NNN Summary column; [mcp_control.md](mcp_control.md) (by tool budget routing) | Changing SKILL.md ROUTE keywords must sync this file's Summary column; new ROUTE must sync [scripts/validate-rule-ids.sh](../scripts/validate-rule-ids.sh) bidirectional assertion |
| Residual risk declaration (covered / not covered / residual risk — 3 fields) | [engineering-discipline/SKILL.md](../../engineering-discipline/SKILL.md) GR-008 | [examples.md](examples.md) usage rules + §1/§2/§4/§5/§6 template tails; [review_checklists.md](review_checklists.md) §8 skeleton tail; [code_templates.md](code_templates.md) usage rules; [scripts/lint-hit-rules.sh](../scripts/lint-hit-rules.sh) SIGNALS["GR-008"] | Changing owner field names or field count must sync all 3 reference files |
| Version baseline declaration (iOS / Swift actual or explicit assumption) | [SKILL.md](../SKILL.md) IR-006 | [examples.md](examples.md) usage rules + §1/§2/§4/§5/§6 template heads; [review_checklists.md](review_checklists.md) §8 skeleton head; [validation_scenarios.md](validation_scenarios.md) Scenario 3 pass criteria; [scripts/lint-hit-rules.sh](../scripts/lint-hit-rules.sh) SIGNALS["IR-006"] | Changing owner wording must sync all references |
| Pre-confirmation block (GR-002 literalized trigger when info insufficient) | [engineering-discipline/SKILL.md](../../engineering-discipline/SKILL.md) GR-002 | [root_cause_enforcement.md](root_cause_enforcement.md) §2 forensics strategy "前置确认问题维度" subsection; [scripts/lint-hit-rules.sh](../scripts/lint-hit-rules.sh) SIGNALS["GR-002"] | Changing owner wording must sync root_cause_enforcement.md dimension examples |
| Logical reasoning (traceable argumentation / four-tier distinction / visible inference) | [cognitive-reasoning/SKILL.md](../../cognitive-reasoning/SKILL.md) GR-010 | [cognitive-reasoning/references/logical_reasoning.md](../../cognitive-reasoning/references/logical_reasoning.md); [scripts/lint-hit-rules.sh](../scripts/lint-hit-rules.sh) SIGNALS["GR-010"] | Updating general rule in cognitive-reasoning skill; mechanical anchor is independent "Logic Chain" block + 4 fields |
| Cognitive Adversary Mode (anti-sycophancy / strongest counter-argument / falsifiable / sycophancy self-check) | [SKILL.md](../SKILL.md) IR-011 | [cognitive_adversary_mode.md](cognitive_adversary_mode.md); [scripts/lint-hit-rules.sh](../scripts/lint-hit-rules.sh) SIGNALS["IR-011"] | Changing owner wording must sync cognitive_adversary_mode.md final output format |
| Proposal candidate signal thresholds | [scripts/summarize-usage-ledger.sh](../scripts/summarize-usage-ledger.sh) L69-L72 (4 `*_THRESHOLD` constants) | [usage_ledger.md](usage_ledger.md) §8 threshold table; [scripts/validate-skill-evolution.sh](../scripts/validate-skill-evolution.sh) `[11/13]` step | Changing either side must sync the other; validate-skill-evolution.sh `[11/13]` step auto-asserts consistency |
