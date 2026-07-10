#!/usr/bin/env bash
# Cross-skill BEHAVIORAL & CONSISTENCY validation for skills-engineering.
#
# Complements scripts/validate-skill-structure.sh (which only checks the
# machine-recognizable STRUCTURE of each SKILL.md: frontmatter, size, local
# links, orphan references). This script checks the things structure checks
# cannot: that each skill ships a complete companion set, that every rule ID a
# skill declares as its own is actually defined in its references, that the
# global trigger matrix in .agents/invocation.md covers every skill, i18n
# mirror coverage, and cross-skill hard links that may dead-end off iOS setups.
#
# FAIL  -> blocks (used as a pre-push gate, like validate-skill-structure.sh)
# WARN  -> reported, does not block (informational; e.g. partial en-US mirror)
#
# Usage:
#   scripts/validate-skill-behavior.sh            # all skills
#   scripts/validate-skill-behavior.sh plan-grill # one skill (behavior only)
#
# Exit code: 0 if no FAIL, 1 if any FAIL (WARNs never fail).

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

SKILL_ARG="${1:-}"

python3 - "$SE_DIR" "$SKILL_ARG" <<'PY'
import os, re, sys

SE_DIR, SKILL_ARG = sys.argv[1], sys.argv[2]

# --- discover real skill dirs (top-level dirs with a SKILL.md) ----------------
# We discover by the presence of SKILL.md alone, NOT by requiring AGENT-BRIEF.md
# up front. Otherwise a brand-new skill that ships only SKILL.md (and is missing
# its companion files) would be filtered out here and never reach the companion
# completeness check below — defeating the gate.
def discover_skills():
    out = []
    for name in sorted(os.listdir(SE_DIR)):
        d = os.path.join(SE_DIR, name)
        if not os.path.isdir(d):
            continue
        if name in ("scripts", "docs", ".agents", ".claude-plugin", ".out-of-scope"):
            continue
        if os.path.isfile(os.path.join(d, "SKILL.md")):
            out.append(d)
    return out

skills = discover_skills()
if SKILL_ARG:
    skills = [s for s in skills if os.path.basename(s.rstrip("/")) == SKILL_ARG]
    if not skills:
        print(f"No skill named '{SKILL_ARG}' found.", file=sys.stderr)
        sys.exit(1)

invocation_path = os.path.join(SE_DIR, ".agents", "invocation.md")
invocation_text = ""
if os.path.isfile(invocation_path):
    with open(invocation_path, encoding="utf-8") as f:
        invocation_text = f.read()

# Owned ids are declared as bullets `- [GR-001] ...` anywhere in SKILL.md, so
# MULTILINE is required: `^` must anchor each line, not just the file start
# (otherwise the frontmatter wins and owned_ids comes back empty, silently
# skipping the whole check).
RULE_BULLET = re.compile(r'^\s*-\s+\*?\[([A-Z]+-\d+)\]\*?', re.M)
# A rule id is "defined" only by a STRUCTURED anchor in THIS skill's own
# references/*.md — never by a bare substring, and never by ios-engineer's
# references (which must not backstop another skill's ids). Supported anchors:
#   - heading:        `## GR-001 安全合规防御`
#   - bracket pointer:`本文件是 ... **[GR-010]** 的细则真值`
#   - table registry:  `| IR-001 | active | ... |`  (ios-engineer/references/rule_index.md)
DEF_HEADING = re.compile(r'^#{1,6}\s+([A-Z]+-\d+)\b', re.M)
DEF_BRACKET = re.compile(r'\[([A-Z]+-\d+)\]')
# Active table rows only (status cell == 'active'): used for BOTH the forward
# definition set and the reverse check. A retired row (`| ID | retired |`) is
# NOT a valid definition — a retired id must not remain declared in SKILL.md
# (rule_index lifecycle), so it must keep failing the forward check. We read the
# full row to reach the status cell rather than stopping at the first `|`.
DEF_ACTIVE  = re.compile(r'^\s*\|[ \t]*([A-Z]+-\d+)[ \t]*\|[ \t]*active\b', re.M)
CROSS_LINK = re.compile(r'\.{1,2}/ios-engineer/references/')
LOAD_TOKENS = re.compile(r'触发|加载|调用|门控|enable|Enable')
SKIP_TOKENS = re.compile(r'不触发|跳过|不调用|SKIP|skip')

total_fail = 0

for skill_dir in skills:
    name = os.path.basename(skill_dir.rstrip("/"))
    fails = 0
    warns = 0
    print(f"=== {name} ===")

    skill_md = os.path.join(skill_dir, "SKILL.md")
    brief_md = os.path.join(skill_dir, "AGENT-BRIEF.md")
    oos_md   = os.path.join(skill_dir, "OUT-OF-SCOPE.md")
    refs_dir = os.path.join(skill_dir, "references")

    # --- Check 1: companion file completeness (FAIL) ---
    missing = [p for p in (skill_md, brief_md, oos_md) if not os.path.isfile(p)]
    ref_md_files = []
    if os.path.isdir(refs_dir):
        ref_md_files = sorted(os.path.join(refs_dir, f)
                              for f in os.listdir(refs_dir) if f.endswith(".md"))
    if not ref_md_files:
        missing.append(os.path.join(refs_dir, "<at least one .md>"))
    if missing:
        for m in missing:
            print(f"  FAIL: missing companion file: {os.path.relpath(m, SE_DIR)}")
            fails += 1
    else:
        print("  [ok] companion set: SKILL.md + AGENT-BRIEF.md + OUT-OF-SCOPE.md + references/")

    with open(skill_md, encoding="utf-8") as f:
        skill_text = f.read()

    # --- Check 2: owned rule IDs are DEFINED in THIS skill's references (FAIL) ---
    # The definition source is strictly this skill's own references/*.md, matched
    # by structured anchors (heading / bracket / table registry). We deliberately
    # do NOT search SKILL.md (the own-declaration bullet `- [ID] ...` would make
    # every id trivially "found" and void the gate) and do NOT fall back to
    # ios-engineer's references (which would let a non-iOS skill's id be silently
    # backstopped). Result: a skill that declares `[GR-999]` in SKILL.md but never
    # defines it in references/ now correctly FAILs.
    owned_ids = RULE_BULLET.findall(skill_text)
    if owned_ids:
        defined = set()               # structured anchors: heading / bracket / ACTIVE table row
        defined_active_table = set()  # active table rows (redundant with `defined`, kept for clarity)
        for rf in ref_md_files:
            with open(rf, encoding="utf-8") as f:
                txt = f.read()
            for m in DEF_HEADING.finditer(txt):
                defined.add(m.group(1))
            for m in DEF_BRACKET.finditer(txt):
                defined.add(m.group(1))
            for m in DEF_ACTIVE.finditer(txt):
                defined.add(m.group(1))
                defined_active_table.add(m.group(1))
        owned_set = set(owned_ids)

        # Forward (declared -> defined): a declared id must have a structured
        # anchor in THIS skill's references. Retired rows are excluded so a
        # retired id is never treated as a valid definition.
        undefined = sorted(owned_set - defined)
        if undefined:
            for i in undefined:
                print(f"  FAIL: owned rule id [{i}] declared in SKILL.md but not defined "
                      f"in {name}/references/ (heading '## {i}', bracket '[{i}]', or "
                      f"active table row '| {i} |')")
                fails += 1

        # Reverse (P2 fix): an ACTIVE table row whose prefix matches a declared
        # prefix must ALSO be declared in SKILL.md. Without this, a stale
        # `| CE-014 | active |` row would pass even if SKILL.md never declares it,
        # making the stated "bidirectional consistency" contract false. Scoped to
        # the skill's own prefixes so (a) mirrored IDs such as ios-engineer's
        # GR-* rows — which are owned by other global skills' SKILL.md — and
        # (b) retired rows are never falsely flagged.
        owned_prefixes = {i.rsplit("-", 1)[0] for i in owned_set}
        extra = sorted({d for d in defined_active_table
                        if d.rsplit("-", 1)[0] in owned_prefixes and d not in owned_set})
        if extra:
            for i in extra:
                print(f"  FAIL: rule id [{i}] defined as active in {name}/references/ "
                      f"but never declared in SKILL.md (rule_index.md row without a "
                      f"matching '- [{i}]' bullet)")
                fails += 1

        if not undefined and not extra:
            print(f"  [ok] {len(owned_set)} owned rule id(s) consistent with references/ "
                  f"(declared==defined, bidirectional)")

    # --- Check 3: load/skip gating present (WARN) ---
    has_load = bool(LOAD_TOKENS.search(skill_text))
    has_skip = bool(SKIP_TOKENS.search(skill_text))
    if not has_load or not has_skip:
        print("  WARN: SKILL.md lacks explicit load-or-skip gating language")
        warns += 1
    else:
        print("  [ok] load/skip gating present")

    # --- Check 4: cross-skill hard link dead-end risk (WARN, non-iOS only) ---
    if name != "ios-engineer":
        scanned = [skill_md] + ref_md_files
        hard_links = []
        for fp in scanned:
            with open(fp, encoding="utf-8") as f:
                for ln in f:
                    if CROSS_LINK.search(ln):
                        hard_links.append(os.path.relpath(fp, SE_DIR))
        if hard_links:
            print(f"  WARN: hard cross-skill link to ios-engineer in "
                  f"{sorted(set(hard_links))} — dead-ends if ios-engineer not synced to same parent")
            warns += 1

    # --- Check 5: i18n en-US mirror coverage (WARN) ---
    m = re.search(r'supported_locales:\s*(.+)', skill_text)
    if m and "en-US" in m.group(1):
        missing_mirrors = []
        en_dir = os.path.join(skill_dir, "i18n", "en-US", "references")
        for rf in ref_md_files:
            base = os.path.basename(rf)
            if not os.path.isfile(os.path.join(en_dir, base)):
                missing_mirrors.append(base)
        if missing_mirrors:
            print(f"  WARN: en-US declared but {len(missing_mirrors)}/{len(ref_md_files)} "
                  f"reference(s) lack i18n/en-US/references/ mirror (fallback to zh-CN)")
            warns += 1
        else:
            print(f"  [ok] en-US mirror complete ({len(ref_md_files)} reference(s))")

    # --- Check 6: covered by .agents/invocation.md trigger matrix (FAIL) ---
    if invocation_text and name not in invocation_text:
        print(f"  FAIL: '{name}' missing from .agents/invocation.md trigger matrix")
        fails += 1
    elif invocation_text:
        print("  [ok] present in invocation.md trigger matrix")

    tag = "PASS" if fails == 0 else f"FAIL ({fails})"
    suffix = f" ({warns} warn)" if warns else ""
    print(f"--- {name}: {tag}{suffix} ---")
    print("")
    total_fail += fails

print("=========================================")
if total_fail == 0:
    print("All skills PASSED behavioral/consistency validation.")
    sys.exit(0)
else:
    print(f"Behavioral/consistency FAILs: {total_fail}")
    sys.exit(1)
PY
