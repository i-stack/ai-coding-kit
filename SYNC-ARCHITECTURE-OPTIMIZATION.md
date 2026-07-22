# Sync Architecture Optimization Plan

## Goal

Reduce the maintenance cost of syncing ai-coding-kit to multiple agent
platforms by moving from scattered script-specific target knowledge to one
shared, verifiable target registry.

The current pain is not that there are too many scripts. The deeper issue is
that each sync surface knows a slightly different version of the platform map:

- `sync/sync_config.py` knows config renderers and platform config targets.
- `sync/platforms/paths.py` knows install roots and derived paths.
- `skills-engineering/scripts/sync-skills.sh` knows skill cache targets.
- `skills-engineering/scripts/sync-agent-preamble.sh` knows preamble targets.
- `skills-engineering/scripts/verify-sync.sh` still verifies a hardcoded subset.
- `sync/platforms/continue.py` and `sync/platforms/recall.py` own YAML recall
  behavior that is related to, but not fully orchestrated by, the Bash preamble
  sync path.

As more platforms are added, this creates a multiplication problem:

```text
platforms x config sync x skills sync x preamble sync x verify x docs/tests
```

The target state is:

```text
one target registry -> config sync / skills sync / preamble sync / verify / docs
```

## Current Architecture

### 1. Config and MCP Sync

Entry points:

- `sync.sh`
- `sync/scripts/sync_all.sh`
- `sync/sync_config.py`

Current behavior:

- Reads `env/mcp/*.json`.
- Reads `env/platforms/*.json`.
- Uses explicit Python renderers for complex platforms.
- Auto-discovers simple JSON-MCP targets via `mcp_target`.
- Skips native targets when the platform install root is missing.

Strengths:

- Platform config is already mostly data-driven.
- Renderer logic is isolated per platform.
- Install-root override logic is centralized in `sync/platforms/paths.py`.

Weaknesses:

- Renderer registration still lives in Python code.
- The platform JSON mixes native platform config with ai-coding-kit orchestration
  metadata such as `enabled`, `preamble`, and `export_env_to_zshrc`.
- The config sync command does not cover the full "sync everything to every
  endpoint" story.

### 2. Skill Payload Sync

Entry point:

- `skills-engineering/scripts/sync-skills.sh`

Current behavior:

- Discovers all skill directories by scanning for `SKILL.md`.
- Syncs only the runtime payload:
  - `SKILL.md`
  - `AGENT-BRIEF.md`
  - `OUT-OF-SCOPE.md`
  - `references/`
  - `i18n/`
- Excludes repo-only governance material such as `scripts/`, `evolution/`,
  `agents/`, `history/`, `usage/`, and validation artifacts.
- Auto-discovers most skill targets from `env/platforms/*.json`.
- Keeps Xcode Codex and Xcode Claude as explicit special cases.

Strengths:

- Runtime payload boundary is clear.
- `--delete-excluded` prevents stale installed skill copies.
- Skill discovery is automatic.

Weaknesses:

- Bash still owns orchestration and file operations.
- Target discovery depends on calling Python from Bash to reuse path logic.
- Xcode targets are still modeled outside the same platform registry.

### 3. Preamble and Recall Sync

Entry points:

- `skills-engineering/scripts/sync-agent-preamble.sh`
- `sync/platforms/continue.py`
- `sync/platforms/recall.py`

Current behavior:

- Renders managed blocks from
  `skills-engineering/scripts/templates/agent-preamble.md.tmpl`.
- Reads `env/platforms/<platform>.json` `preamble` declarations for many
  platforms.
- Supports `mode=full` and `mode=recall`.
- Continue is special because recall is injected into YAML `rules`.
- Cursor project `.mdc` generation is manifest-driven but still handled in the
  Bash script.

Strengths:

- Preamble target declaration is already moving toward data-driven sync.
- Shared recall rendering exists in Python.
- Full preamble vs recall-only is an explicit mode.

Weaknesses:

- Markdown block merge exists in Bash, while recall/YAML merge exists in Python.
- Claude router and agent generation are embedded in the Bash preamble script.
- Cursor project rules remain an external root list rather than a first-class
  target type.

### 4. Verification

Entry point:

- `skills-engineering/scripts/verify-sync.sh`

Current behavior:

- Checks installed skill payload shape.
- Checks preamble tilde-ification and expected full-text-load instructions.
- Hardcodes Claude, Codex, Gemini, Cursor, Xcode Codex, and Xcode Claude.

Strengths:

- Catches stale payload directories.
- Catches some preamble drift.

Weaknesses:

- Not driven by the same platform declarations as sync.
- New platforms can receive preamble or skills without matching verification.
- Verify does not naturally know per-platform capabilities like recall-only,
  full preamble, YAML recall, or no skills target.

## Architecture Direction

Introduce a shared target registry and make all sync surfaces consume it.

The registry should answer these questions for each target:

- Is this target installed?
- Which env flag controls it?
- Does it receive native config?
- Does it receive skill payloads?
- Does it receive a preamble?
- Is the preamble full, recall-only, YAML, or generated project rules?
- What should verification assert?
- What renderer owns platform-specific behavior?

Conceptual model:

```python
@dataclass
class PreambleSpec:
    target: Path | None  # None when the preamble is injected by a renderer (e.g.
                         # Continue YAML recall, which has no standalone target file)
    mode: Literal["full", "recall", "none"]
    format: Literal["markdown", "yaml", "cursor-mdc"]
    tool: str
    router: bool = False
    agents: bool = False

@dataclass
class VerifySpec:
    skills: bool
    full_preamble: bool = False
    recall_preamble: bool = False
    yaml_recall: bool = False
    # Note: yaml_recall with target=None (e.g. Continue) skips the file-exists
    # check; verifying YAML recall requires reading the platform's config file,
    # which is handled by a platform-specific check rather than this generic spec.
```

This can initially be implemented in `sync/registry.py`, backed by the existing
`env/platforms/*.json` files and `sync/platforms/paths.py`.

## Recommended Implementation Phases

### P0: Make Verification Consume the Same Target Data

This is the highest leverage first step.

Actions:

- Add `sync/registry.py` with read-only target discovery.
- Keep existing path helpers in `sync/platforms/paths.py`.
- Add a Python verifier, for example `sync/verify.py`.
- Make `skills-engineering/scripts/verify-sync.sh` a thin wrapper around
  `python3 sync/verify.py`.
- Verify all targets declared with skills or preamble support, not just the
  current hardcoded subset.

Validation:

- Unit test registry discovery with temporary `HOME` and temporary
  `env/platforms`.
- Unit test that every target with `preamble.mode=full` gets full preamble
  checks.
- Unit test that every target with `preamble.mode=recall` gets recall checks.
- Unit test that disabled or missing install roots are skipped consistently.

Expected benefit:

- Stops the most dangerous drift: write path and verify path disagreeing.
- Low behavior risk because write logic can remain unchanged.

### P1: Introduce One Python CLI for Sync Operations

Add a single orchestration CLI while preserving old commands as wrappers.

**Wrapper lifecycle:** P1 wrappers are intentionally temporary. Each wrapper
script must carry a `# TODO(P2): remove after sync/cli.py is proven stable`
comment. Once P2 file-mutation logic is tested and stable, delete the wrappers
and have callers invoke `sync/cli.py` directly. Do not allow the wrapper layer
to accumulate logic — any conditional or transform in a wrapper is a sign it
should move into the Python CLI instead.

Proposed command surface:

```bash
python3 sync/cli.py config --target all
python3 sync/cli.py skills --target all
python3 sync/cli.py preamble --target all
python3 sync/cli.py verify --target all
python3 sync/cli.py all --verify
```

Compatibility wrappers:

- `sync.sh` calls `python3 sync/cli.py config --target all`.
- `skills-engineering/scripts/sync-skills.sh` calls
  `python3 sync/cli.py skills --target all`.
- `skills-engineering/scripts/sync-agent-preamble.sh` calls
  `python3 sync/cli.py preamble --target all`.
- `skills-engineering/scripts/sync-skill-full.sh` calls
  `python3 sync/cli.py skills preamble verify`, or `all --skills --preamble`.

Expected benefit:

- Users get one mental model.
- Existing install/bootstrap/npm paths do not break immediately.
- New behavior can be tested in Python without rewriting every shell script at
  once.

### P2: Move Skill and Preamble Writes into Python

Port the actual file mutation logic after P1 is stable.

Actions:

- Implement `sync/skills.py`.
- Implement `sync/preamble.py`.
- Reuse a shared managed-block merge helper for markdown files.
- Keep Continue YAML recall merge in its renderer, but feed it from the same
  registry and shared recall renderer.
- Move Claude router/agent generation out of Bash into a renderer or template
  module.
- Keep `rsync` optional. For portability, Python can copy the whitelisted
  payload and delete excluded stale directories directly.

Expected benefit:

- Removes Bash/Python split-brain orchestration.
- Enables better unit tests without writing to real home directories.
- Makes dry-run output consistent across config, skills, preamble, and verify.

### P3: Separate Native Platform Config from Sync Metadata

Current `env/platforms/*.json` files mix platform-native fields with
ai-coding-kit orchestration fields. That is workable now, but it becomes harder
as the platform count grows.

Two possible routes:

#### Option A: `_sync` namespace inside each platform file

Example:

```json
{
  "model": "gpt-5.5",
  "sandbox_mode": "workspace-write",
  "_sync": {
    "enabled": true,
    "skills": true,
    "preamble": {
      "target": "AGENTS.md",
      "mode": "full",
      "tool": "codex"
    },
    "verify": {
      "skills": true,
      "full_preamble": true
    }
  }
}
```

Pros:

- One file per platform remains.
- Smaller migration.

Cons:

- Native config and orchestration metadata are still colocated.

#### Option B: Separate target metadata files

Example:

```text
env/platforms/codex.json
sync/targets/codex.json
```

Pros:

- Cleanest boundary.
- Platform renderer reads platform config; orchestrator reads target config.

Cons:

- More files.
- Requires stronger docs and tests so users know where to edit.

Recommendation:

- Use Option A first.
- Move to Option B only if `_sync` grows too large or if external users start
  confusing native platform config with ai-coding-kit metadata.

### P4: Model Xcode as First-Class Targets

Replace Xcode special branches with registry entries:

- `xcode-codex`
- `xcode-claude`
- `xcode-gemini`

Each entry can share the same parent install root but define separate outputs:

- native config path
- skills path
- preamble path
- verification expectations

Expected benefit:

- Removes repeated Xcode conditionals.
- Makes future Xcode agent additions cheaper.

### P5: Generate Docs and Test Matrices from the Registry

Once the registry is stable, use it to generate or validate:

- supported target table in docs
- command help text
- `SYNC_*` flag list
- verify coverage matrix
- install-root override key list

Expected benefit:

- Documentation stops becoming a second source of truth.
- New platforms fail tests when docs/help/verify are incomplete.

## Proposed Target Registry Fields

Minimum viable fields:

```json
{
  "name": "codex",
  "installRootKey": "codex",
  "enabledFlag": "SYNC_CODEX",
  "config": {
    "renderer": "codex"
  },
  "skills": {
    "enabled": true,
    "path": "skills"
  },
  "preamble": {
    "enabled": true,
    "target": "AGENTS.md",
    "mode": "full",
    "format": "markdown",
    "tool": "codex"
  },
  "verify": {
    "skills": true,
    "fullPreamble": true
  }
}
```

Rules:

- Relative paths resolve under the install root.
- `enabledFlag` owns force-on, force-off, and auto-detect behavior.
- Missing install root skips by default.
- Force-on may create target directories only when the operation explicitly
  writes that surface.
- Continue can declare `skills.enabled=false` because it loads skills from the
  repo.
- Recall-only targets should not trigger ios-engineer audit verification.

## Migration Safety Rules

- Preserve existing public commands until the Python CLI is proven stable.
- Do not change installed payload shape during registry migration.
- Do not change platform-native output semantics while moving orchestration.
- Keep `env/*.json` valid JSON.
- Every phase must have a temporary-HOME test path.
- Any real-home sync remains opt-in or explicitly invoked by the user.

## Validation Plan

Local verification after each phase:

```bash
python3 -m unittest discover -s tests
bash skills-engineering/scripts/validate-skill-structure.sh
bash skills-engineering/scripts/validate-skill-behavior.sh
bash skills-engineering/scripts/sync-skills.sh --dry-run
bash skills-engineering/scripts/sync-agent-preamble.sh --dry-run
bash skills-engineering/scripts/verify-sync.sh
git diff --check
```

**Rollback criteria:** If the Python CLI dry-run output diverges from the
legacy Bash dry-run output for any enabled target, the phase is not stable.
Before promoting a phase as complete, diff the two outputs:

```bash
# Legacy dry-run output
bash skills-engineering/scripts/sync-skills.sh --dry-run 2>&1 > /tmp/legacy.txt

# New CLI dry-run output
python3 sync/cli.py skills --target all --dry-run 2>&1 > /tmp/new.txt

diff /tmp/legacy.txt /tmp/new.txt
```

Any real-home diff not explained by cosmetic formatting differences is a
rollback trigger. Keep the old wrapper commands live until this diff is clean.

For phases that touch real sync behavior, add a temp-HOME harness:

```bash
HOME=/tmp/ai-coding-kit-sync-home python3 sync/cli.py all --verify
```

The temp-HOME harness should create only explicitly enabled test roots and
should assert skipped roots are not created accidentally.

## Non-Goals

- Do not merge all scripts into `sync/` by filename alone.
- Do not remove existing wrapper commands in the first pass.
- Do not rewrite every platform renderer at once.
- Do not change secrets resolution semantics.
- Do not broaden installed skill payloads to include repo-only scripts.

## Open Questions

- ~~Should the registry live entirely in Python, or should it be represented as
  JSON and loaded by Python?~~

  **Decision: JSON backed by Python loader.** Bash scripts must be able to
  introspect the registry via `jq` without spawning a Python subprocess. Pure
  Python dataclasses would deepen the existing `heredoc-Python-from-Bash`
  pattern that is already a pain point in `sync-skills.sh:23-30` and
  `sync-agent-preamble.sh:21-32`. A JSON registry is also easier to audit
  and diff in CI.

- Should `_sync` metadata remain inside `env/platforms/*.json`, or move to
  `sync/targets/*.json` after the first migration?
- Should `sync.sh` eventually become "sync everything" instead of only config
  sync?
- Should Cursor project roots become registry entries, or remain a local
  per-machine setting in `skills-engineering/scripts/config.local.sh`?

## Recommended Next Step

Implement P0 only:

1. Add `sync/registry.py`.
2. Add `sync/verify.py`.
3. Convert `verify-sync.sh` into a wrapper.
4. Add tests proving verify coverage is generated from the same target registry
   used by skill and preamble sync.

This keeps the first change small and directly targets the current highest-risk
failure mode: sync writes to one platform surface while verification still
checks an older hardcoded target list.
