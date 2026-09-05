#!/usr/bin/env bash
# =============================================================================
# skill-bundles.sh — agentskills.io 兼容的技能打包 / 导入 / 校验
#
# 对齐 Hermes Agent 的 skill_bundles.py：让本仓库技能可以「走出去」——
#   1) export  把任一 skill 打包成 agentskills.io 兼容产物（SKILL.md + references/）
#   2) validate 校验某 skill 是否满足 agentskills.io frontmatter 契约
#   3) import  从社区 Skills Hub / Hermes 兼容 bundle 导入技能到本仓库
#
# agentskills.io 契约（Anthropic 开放标准）：
#   - 目录含 SKILL.md
#   - SKILL.md 顶部 YAML frontmatter 须含 `name`（kebab-case，与目录名一致）
#     与 `description`（非空字符串）
#   - 允许附带 references/ 等额外文件
#
# 用法:
#   bash scripts/skill-bundles.sh export <skill> [--out DIR] [--tar]
#   bash scripts/skill-bundles.sh validate <skill>
#   bash scripts/skill-bundles.sh import <bundle.tar.gz|bundle-dir> [--target DIR] [--name NAME] [--force]
#   bash scripts/skill-bundles.sh list
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
BUNDLES_DIR="${SE_DIR}/.bundles"

usage() {
  grep '^#' "$0" | sed 's/^# \{0,1\}//'
  exit "${1:-0}"
}

# ---- 通用 frontmatter 解析（python3，与 sync subtree 一致） ----
parse_frontmatter() {
  # $1 = skill dir; prints JSON {name,description,locale,supported_locales,raw_lines}
  python3 - "$1" <<'PY'
import os, re, sys, json
skill_dir = sys.argv[1]
skill_md = os.path.join(skill_dir, "SKILL.md")
out = {"ok": False, "name": "", "description": "", "locale": "", "supported_locales": "", "lines": 0}
if not os.path.isfile(skill_md):
    print(json.dumps(out)); sys.exit(0)
with open(skill_md, encoding="utf-8") as f:
    raw = f.read()
lines = raw.splitlines()
out["lines"] = len(lines)
if not lines or lines[0].strip() != "---":
    print(json.dumps(out)); sys.exit(0)
end = None
for i in range(1, len(lines)):
    if lines[i].strip() == "---":
        end = i; break
if end is None:
    print(json.dumps(out)); sys.exit(0)
fm = {}
block_key = None
for ln in lines[1:end]:
    m = re.match(r'^([A-Za-z_][\w-]*):\s?(.*)$', ln)
    if m and not ln.startswith(" "):
        k, v = m.group(1), m.group(2)
        block_key = k if v.strip() in (">", ">-", "|", "|-") else None
        fm[k] = v.strip()
    elif block_key and (ln.startswith(" ") or ln.strip() == ""):
        if ln.strip():
            fm[block_key] = (fm.get(block_key, "") + " " + ln.strip()).strip()
    else:
        block_key = None
out["ok"] = True
out["name"] = fm.get("name", "")
out["description"] = fm.get("description", "")
out["locale"] = fm.get("locale", "")
out["supported_locales"] = fm.get("supported_locales", "")
print(json.dumps(out))
PY
}

cmd="${1:-}"; shift || true
case "$cmd" in
  export)
    [ $# -ge 1 ] || usage 1
    SKILL="$1"; shift
    OUT_DIR="$BUNDLES_DIR"
    MAKE_TAR=0
    while [ $# -gt 0 ]; do
      case "$1" in
        --out) OUT_DIR="$2"; shift 2 ;;
        --tar) MAKE_TAR=1; shift ;;
        *) echo "Unknown arg: $1" >&2; usage 1 ;;
      esac
    done
    SRC="${SE_DIR}/${SKILL}"
    [ -d "$SRC" ] || { echo "Skill not found: $SRC"; exit 1; }
    FM="$(parse_frontmatter "$SRC")"
    if ! python3 -c "import sys,json; d=json.load(sys.stdin); sys.exit(0 if d['ok'] else 1)" <<<"$FM"; then
      echo "SKILL.md missing or no frontmatter in $SRC"; exit 1
    fi
    NAME="$(python3 -c "import sys,json;print(json.loads(sys.argv[1])['name'])" "$FM")"
    DESC="$(python3 -c "import sys,json;print(json.loads(sys.argv[1])['description'])" "$FM")"
    # 版本：ios-engineer 取 active_version，否则 local
    VERSION="local"
    if [ -f "${SRC}/evolution/active_version.json" ]; then
      VERSION="$(python3 -c "import json;print(json.load(open('${SRC}/evolution/active_version.json')).get('active_version','local'))" 2>/dev/null || echo local)"
    fi
    DEST="${OUT_DIR}/${SKILL}"
    rm -rf "$DEST"; mkdir -p "$DEST"
    # agentskills.io 布局：SKILL.md + 随技能分发的支持目录（references/ scripts/
    # templates/ examples/ assets/）+ 允许的 companion 文件。scripts/ 等目录被
    # references/*.md 以 ../scripts/... 形式引用，必须随包分发，否则导出的技能不完整。
    cp "${SRC}/SKILL.md" "$DEST/SKILL.md"
    # 随技能分发的支持目录（被 references/ 与 scripts/ 引用，必须随包分发）。
    # 注意：这是「允许随包分发」的白名单——新增需要在 bundle 中可用的目录时，
    # 需在此处登记；若某 skill 不含该目录则自动跳过（不影响通用性）。
    for subdir in references scripts templates examples assets agents; do
      [ -d "${SRC}/${subdir}" ] && cp -R "${SRC}/${subdir}" "$DEST/${subdir}"
    done
    # 自校验（scripts/validate.sh --quick / --scenarios）依赖的演进工具链最小必要子集。
    # 不复制整个 evolution/（含 490+ history 文件，会使 bundle 臃肿且含仓库内部演进历史），
    # 仅复制运行校验所需的：active_version.json、scenarios/，并保留空的演进工作目录结构。
    if [ -d "${SRC}/evolution" ]; then
      mkdir -p "${DEST}/evolution"
      [ -f "${SRC}/evolution/active_version.json" ] && cp "${SRC}/evolution/active_version.json" "${DEST}/evolution/active_version.json"
      [ -d "${SRC}/evolution/scenarios" ] && cp -R "${SRC}/evolution/scenarios" "${DEST}/evolution/scenarios"
      # 演进工作目录：保留空结构，避免校验/工具因目录缺失而失败。
      # usage.jsonl 是运行时生成的用量账本，bundle 内创建空文件以满足
      # references 中的 ../evolution/usage/usage.jsonl 链接（避免自校验断链）。
      for wd in proposals validations approvals; do
        mkdir -p "${DEST}/evolution/${wd}"
      done
      mkdir -p "${DEST}/evolution/usage"
      : > "${DEST}/evolution/usage/usage.jsonl"
    fi
    for extra in AGENT-BRIEF.md OUT-OF-SCOPE.md; do
      [ -f "${SRC}/${extra}" ] && cp "${SRC}/${extra}" "$DEST/${extra}"
    done
    # 生成 manifest + 校验和
    python3 - "$DEST" "$NAME" "$DESC" "$VERSION" "$SKILL" <<'PY'
import os, sys, json, hashlib, datetime
dest, name, desc, version, skill = sys.argv[1:6]
files = []
checksums = {}
for root, _, fnames in os.walk(dest):
    for fn in sorted(fnames):
        if fn == "bundle.json":
            continue
        fp = os.path.join(root, fn)
        rel = os.path.relpath(fp, dest)
        files.append(rel)
        h = hashlib.sha256()
        with open(fp, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        checksums[rel] = h.hexdigest()
manifest = {
    "format": "agentskills.io",
    "agentskills_compatible": True,
    "name": name,
    "description": desc,
    "version": version,
    "source_skill": skill,
    "source_repo": "ai-coding-kit/skills-engineering",
    "exported_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S%z"),
    "files": files,
    "checksums_sha256": checksums,
}
with open(os.path.join(dest, "bundle.json"), "w", encoding="utf-8") as f:
    json.dump(manifest, f, indent=2, ensure_ascii=False)
    f.write("\n")
print(f"Exported '{skill}' -> {dest}")
print(f"  name={name}  version={version}  files={len(files)}")
PY
    if [ "$MAKE_TAR" -eq 1 ]; then
      TAR="${OUT_DIR}/${SKILL}-${VERSION}.tar.gz"
      tar -czf "$TAR" -C "$OUT_DIR" "$SKILL"
      echo "Bundled tarball: $TAR"
    fi
    ;;

  validate)
    [ $# -ge 1 ] || usage 1
    SKILL="$1"
    SRC="${SE_DIR}/${SKILL}"
    [ -d "$SRC" ] || { echo "Skill not found: $SRC"; exit 1; }
    FM="$(parse_frontmatter "$SRC")"
    python3 - "$FM" "$SRC" <<'PY'
import os, sys, json, re
fm_raw, src = sys.argv[1:3]
fm = json.loads(fm_raw)
fails = 0
def fail(m):
    global fails; fails += 1; print(f"  FAIL: {m}")
def ok(m):
    print(f"  [ok] {m}")
if not fm["ok"]:
    fail("SKILL.md missing or no YAML frontmatter"); print(f"--- {os.path.basename(src)}: FAIL ---"); sys.exit(1)
name = fm["name"]; desc = fm["description"]
if not name:
    fail("frontmatter.name missing/empty (agentskills.io requires 'name')")
else:
    ok(f"name = {name}")
    if not re.match(r'^[a-z0-9]+(-[a-z0-9]+)*$', name):
        fail(f"name '{name}' is not kebab-case (agentskills.io recommends kebab-case)")
if not desc:
    fail("frontmatter.description missing/empty (agentskills.io requires 'description')")
else:
    ok(f"description present ({len(desc)} chars)")
if fm["lines"] > 500:
    fail(f"SKILL.md too long: {fm['lines']} lines (>500)")
else:
    ok(f"SKILL.md size = {fm['lines']} lines")
# 本地引用解析：扫描 SKILL.md + 所有 references/*.md，校验全部本地相对链接
# （含 ../scripts/... 等非 .md 目标），链接相对「所在文件目录」解析，限定在 skill 根内。
link_re = re.compile(r'\[([^\]]*)\]\(([^)]+)\)')
src_root = os.path.normpath(src)

md_files = []
skill_md = os.path.join(src, "SKILL.md")
if os.path.isfile(skill_md):
    md_files.append(skill_md)
refs_dir = os.path.join(src, "references")
if os.path.isdir(refs_dir):
    for rf in sorted(os.listdir(refs_dir)):
        if rf.endswith(".md"):
            md_files.append(os.path.join(refs_dir, rf))

missing = 0
for md in md_files:
    base_dir = os.path.dirname(md)
    rel_label = os.path.relpath(md, src)
    with open(md, encoding="utf-8") as f:
        for line in f:
            for _, link in link_re.findall(line):
                if re.match(r'^(https?|mailto|tel):', link): continue
                path = link.split('#', 1)[0].strip()
                if not path: continue          # 纯锚点（#section）跳过
                if path.startswith("//"): continue
                full = os.path.normpath(os.path.join(base_dir, path))
                # 只校验解析后仍落在 skill 根目录内的本地链接
                if full != src_root and not full.startswith(src_root + os.sep):
                    continue
                exists = os.path.isdir(full) if link.rstrip().endswith("/") else (os.path.isfile(full) or os.path.isdir(full))
                if not exists:
                    missing += 1
                    fail(f"missing local reference in {rel_label}: {link}")
if missing == 0:
    ok("local references resolve")
print(f"--- {os.path.basename(src)}: {'PASS' if fails==0 else 'FAIL ('+str(fails)+')'} (agentskills.io compatible: {fails==0}) ---")
sys.exit(1 if fails else 0)
PY
    ;;

  import)
    [ $# -ge 1 ] || usage 1
    BUNDLE="$1"; shift
    TARGET_DIR="$SE_DIR"
    FORCE=0
    NAME_OVERRIDE=""
    while [ $# -gt 0 ]; do
      case "$1" in
        --target) TARGET_DIR="$2"; shift 2 ;;
        --name) NAME_OVERRIDE="$2"; shift 2 ;;
        --force) FORCE=1; shift ;;
        *) echo "Unknown arg: $1" >&2; usage 1 ;;
      esac
    done
    [ -e "$BUNDLE" ] || { echo "Bundle not found: $BUNDLE"; exit 1; }
    TMP="$(mktemp -d)"
    trap 'rm -rf "$TMP"' EXIT
    if [ -f "$BUNDLE" ]; then
      tar -xzf "$BUNDLE" -C "$TMP" 2>/dev/null || { echo "Failed to extract $BUNDLE (expected .tar.gz)"; exit 1; }
    else
      cp -R "$BUNDLE/." "$TMP/"
    fi
    # 定位含 SKILL.md 的目录（tar 可能多包一层）
    SKILL_SRC=""
    for d in "$TMP" "$TMP"/*; do
      [ -f "$d/SKILL.md" ] && { SKILL_SRC="$d"; break; }
    done
    [ -n "$SKILL_SRC" ] || { echo "No SKILL.md found in bundle"; exit 1; }
    FM="$(parse_frontmatter "$SKILL_SRC")"
    BNAME="$(python3 -c "import sys,json,os;print(json.load(sys.stdin)['name'] or os.path.basename(sys.argv[1]))" "$SKILL_SRC" <<<"$FM")"
    NAME="${NAME_OVERRIDE:-$BNAME}"
    DEST="${TARGET_DIR}/${NAME}"
    if [ -e "$DEST" ] && [ "$FORCE" -ne 1 ]; then
      echo "Target already exists: $DEST (use --force to overwrite)"; exit 1
    fi
    # 若 bundle 自带 bundle.json，先校验 checksums_sha256，防止导入被篡改/损坏的产物
    if [ -f "$SKILL_SRC/bundle.json" ]; then
      echo "Verifying bundle integrity..."
      if ! bash "${SCRIPT_DIR}/validate-skill-integrity.sh" --verify-bundle "$SKILL_SRC/bundle.json"; then
        echo "Bundle checksum verification FAILED. Aborting import." >&2
        exit 1
      fi
    fi
    mkdir -p "$(dirname "$DEST")"
    rm -rf "$DEST"; cp -R "$SKILL_SRC" "$DEST"
    echo "Imported bundle -> $DEST"
    # 用现有结构校验兜底
    if [ -x "${SCRIPT_DIR}/validate-skill-structure.sh" ]; then
      echo "Running structure validation..."
      bash "${SCRIPT_DIR}/validate-skill-structure.sh" "$NAME" || echo "  [warn] structure validation reported issues — please review."
    fi
    ;;

  list)
    for d in "$SE_DIR"/*/; do
      [ -f "${d}SKILL.md" ] && echo "$(basename "${d}")"
    done
    ;;

  ""|-h|--help) usage 0 ;;
  *) echo "Unknown command: $cmd" >&2; usage 1 ;;
esac
