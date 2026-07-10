#!/usr/bin/env bash
# Validate the machine-recognizable STRUCTURE of a skill (or all skills),
# independent of ios-engineer-specific governance (usage ledger, scenarios,
# snapshot consistency, slug sync). These checks are safe to run on every
# skill/ directory that contains a SKILL.md.
#
# Checks:
#   1. SKILL.md exists
#   2. YAML frontmatter present and required keys (name/description/locale/
#      supported_locales) non-empty
#   3. SKILL.md size <= 500 lines
#   4. local references/*.md files exist (resolved path inside this skill's
#      references/ dir; cross-skill ../ios-engineer/... links are excluded)
#   5. other internal markdown links resolve (SKILL.md + references/*.md)
#   6. no orphan references/ files (unreachable from the SKILL.md entry point
#      via transitive local reference links)
#
# Usage:
#   scripts/validate-skill-structure.sh            # all skills
#   scripts/validate-skill-structure.sh plan-grill # one skill
#
# Exit code: 0 if all pass, 1 if any FAIL.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

SKILL_ARG="${1:-}"

SKILLS=()
if [[ -n "$SKILL_ARG" ]]; then
  SKILLS=("$SE_DIR/$SKILL_ARG")
else
  for d in "$SE_DIR"/*/; do
    [[ -f "$d/SKILL.md" ]] && SKILLS+=("$d")
  done
fi

if [[ ${#SKILLS[@]} -eq 0 ]]; then
  echo "No skill directories found." >&2
  exit 1
fi

# Python3 does the real work (link resolution, frontmatter parse).
check_one() {
  local skill_dir="$1"
  python3 - "$skill_dir" <<'PY'
import os, re, sys

skill_dir = sys.argv[1]
skill_name = os.path.basename(skill_dir.rstrip("/"))
skill_md = os.path.join(skill_dir, "SKILL.md")

fails = 0
def fail(msg):
    global fails
    fails += 1
    print(f"  FAIL: {msg}")

# 1. SKILL.md exists
if not os.path.isfile(skill_md):
    print(f"=== {skill_name} ===")
    fail(f"SKILL.md not found in {skill_dir}")
    sys.exit(1)

print(f"=== {skill_name} ===")

with open(skill_md, encoding="utf-8") as f:
    raw = f.read()

# 2. Frontmatter parse + required keys.
# Frontmatter MUST be a YAML block delimited by '---' on the FIRST line and a
# closing '---' later. Anything else is not valid frontmatter.
lines = raw.splitlines()
fm = {}
if not lines or lines[0].strip() != "---":
    fail("frontmatter missing: first line is not '---'")
elif len(lines) < 2:
    fail("frontmatter missing: no closing '---' delimiter")
else:
    end = None
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            end = idx
            break
    if end is None:
        fail("frontmatter missing: no closing '---' delimiter")
    else:
        block_lines = lines[1:end]
        block_key = None
        for ln in block_lines:
            m = re.match(r'^([A-Za-z_][\w-]*):\s?(.*)$', ln)
            if m and not ln.startswith(" "):
                key, val = m.group(1), m.group(2)
                block_key = key if val.strip() in (">", ">-", "|", "|-") else None
                fm[key] = val.strip()
            elif block_key and (ln.startswith(" ") or ln.strip() == ""):
                if ln.strip():
                    fm[block_key] = (fm.get(block_key, "") + " " + ln.strip()).strip()
            else:
                block_key = None

for req in ("name", "description", "locale", "supported_locales"):
    if req not in fm or not fm[req].strip():
        fail(f"frontmatter missing/empty required key: {req}")
    else:
        print(f"  [ok] frontmatter.{req} = {fm[req][:48]}{'...' if len(fm[req])>48 else ''}")

# 3. SKILL.md size <= 500 lines
nlines = len(lines)
if nlines > 500:
    fail(f"SKILL.md too long: {nlines} lines (>500)")
else:
    print(f"  [ok] SKILL.md size = {nlines} lines")

# 4 + 5 + 6. Unified link/reference resolution + reachability-based orphan check.
# A path is a LOCAL reference (must live inside this skill's references/ dir) ONLY
# when its resolved absolute path falls within <skill>/references/. This correctly:
#   - excludes cross-skill links like ../ios-engineer/references/x.md
#   - includes bare-filename sibling links like [x.md](x.md)
refs_dir = os.path.join(skill_dir, "references")
ref_files = []
if os.path.isdir(refs_dir):
    ref_files = sorted(os.path.join(refs_dir, f) for f in os.listdir(refs_dir) if f.endswith(".md"))
files_to_scan = [skill_md] + ref_files

link_re = re.compile(r'\[([^\]]*)\]\(([^)]+)\)')
broken = 0
local_missing = 0
# adjacency for orphan reachability: basename(file) -> set(basename local ref targets)
local_targets = {}
for fp in files_to_scan:
    fn = os.path.basename(fp)
    local_targets[fn] = set()
    with open(fp, encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            for _text, link in link_re.findall(line):
                if re.match(r'^(https?|mailto):', link, re.I):
                    continue
                path = link.split('#', 1)[0].strip()
                if not path:
                    continue
                full = os.path.normpath(os.path.join(os.path.dirname(fp), path))
                is_local_ref = bool(refs_dir) and full.startswith(refs_dir + os.sep) and full.endswith(".md")
                if is_local_ref:
                    tgt = os.path.basename(full)
                    local_targets[fn].add(tgt)
                    if not os.path.isfile(full):
                        local_missing += 1
                        rel = os.path.relpath(fp, skill_dir)
                        print(f"  FAIL: missing local reference in {rel}:{i} -> {link}")
                elif not os.path.exists(full):
                    broken += 1
                    rel = os.path.relpath(fp, skill_dir)
                    print(f"  FAIL: broken link in {rel}:{i} -> {link}")

if local_missing == 0:
    print(f"  [ok] local references exist")
else:
    fails += 1

if broken == 0:
    print(f"  [ok] other internal links resolve ({len(files_to_scan)} file(s) scanned)")
else:
    fails += 1

# Orphan references: present in references/ but NOT reachable from the SKILL.md
# entry point via local reference links (transitive). A cluster of references
# that only links to each other (or to nothing) and is never pulled in by
# SKILL.md is dead weight the agent will never load -> flagged as orphan.
all_ref_names = {os.path.basename(p) for p in ref_files}
skill_fn = os.path.basename(skill_md)
reachable = set(local_targets.get(skill_fn, set()))
queue = list(reachable)
while queue:
    cur = queue.pop()
    for nxt in local_targets.get(cur, set()):
        if nxt not in reachable:
            reachable.add(nxt)
            queue.append(nxt)
orphans = sorted(all_ref_names - reachable)
if orphans:
    for o in orphans:
        fail(f"orphan reference (unreachable from SKILL.md): references/{o}")
else:
    if all_ref_names:
        print(f"  [ok] no orphan references ({len(all_ref_names)} reference file(s), all reachable from SKILL.md)")
    else:
        print("  [skip] no references/ directory to check")

print(f"--- {skill_name}: {'PASS' if fails == 0 else 'FAIL ('+str(fails)+')'} ---")
sys.exit(1 if fails else 0)
PY
  return $?
}

TOTAL_FAIL=0
for d in "${SKILLS[@]}"; do
  if ! check_one "$d"; then
    TOTAL_FAIL=$((TOTAL_FAIL + 1))
  fi
  echo ""
done

echo "========================================="
if [[ $TOTAL_FAIL -eq 0 ]]; then
  echo "ALL SKILLS PASSED structure validation."
  exit 0
else
  echo "FAILED skill(s): $TOTAL_FAIL"
  exit 1
fi
