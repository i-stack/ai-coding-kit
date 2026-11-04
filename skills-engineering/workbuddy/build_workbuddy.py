#!/usr/bin/env python3
# =============================================================================
# build_workbuddy.py — WorkBuddy 开放平台技能上架包构建 / 校验
#
# 规范来源：https://open.workbuddy.cn/docs/skill
#   zip 内顶层必须是技能目录，SKILL.md 在技能根下一级直接可见：
#     {skill-name}/SKILL.md  +  references/  scripts/  templates/
#   SKILL.md = YAML frontmatter + Markdown 正文
#   frontmatter 必填：name / display_name / display_name_en / description /
#                    description_zh / description_en / version / author
#   frontmatter 选填：allowed-tools / examples_zh / examples_en
#
# 设计约束（与本仓库治理不冲突）：
#   1. 仓库内 SKILL.md 保持单一真源，WorkBuddy 专属字段不回写源 SKILL.md，
#      而是由 workbuddy/catalog.json 提供，并在打包时注入，避免破坏
#      validate-skill-structure.sh 的必填键门与 pre-commit 治理门。
#   2. description 直接取源 SKILL.md 的 description（触发语义单一真源），
#      catalog.json 只维护市场展示面字段（展示名 / 中英简介 / 示例 / 定价建议）。
#   3. 市场侧没有 depends_on 机制，用户只装一个技能；因此 catalog 声明的
#      deps 必须在打包时内联为 references/deps/<dep>/，并把跨技能链接改写。
#
# 用法:
#   python3 workbuddy/build_workbuddy.py list
#   python3 workbuddy/build_workbuddy.py build <skill|--all> [--out DIR] [--no-validate]
#   python3 workbuddy/build_workbuddy.py validate [<skill|--all>]
#   python3 workbuddy/build_workbuddy.py sheet
#   python3 workbuddy/build_workbuddy.py clean
# =============================================================================
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SE_DIR = HERE.parent
CATALOG_PATH = HERE / "catalog.json"
DIST_DIR = SE_DIR / "dist" / "workbuddy"

SPEC_SUBDIRS = ("references", "scripts", "templates")
REQUIRED_FM_KEYS = (
    "name",
    "display_name",
    "display_name_en",
    "description",
    "description_zh",
    "description_en",
    "version",
    "author",
)
MAX_PACKAGE_BYTES = 5 * 1024 * 1024
LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")
SECRET_NAME_RE = re.compile(r"(secrets?\.json$|\.pem$|\.p12$|\.key$|id_rsa)")
ABS_USER_PATH_RE = re.compile(r"/Users/[A-Za-z0-9._-]+/")


# --------------------------------------------------------------------------
# catalog
# --------------------------------------------------------------------------
def load_catalog() -> dict:
    if not CATALOG_PATH.is_file():
        sys.exit(f"catalog not found: {CATALOG_PATH}")
    with open(CATALOG_PATH, encoding="utf-8") as f:
        return json.load(f)


def entry_for(cat: dict, skill: str) -> dict:
    d = cat.get("defaults", {})
    e = cat.get("skills", {}).get(skill)
    if e is None:
        sys.exit(f"skill '{skill}' not present in {CATALOG_PATH}")
    merged = {**d, **e}
    merged.setdefault("map_dirs", {})
    merged.setdefault("deps", [])
    merged.setdefault("include", ["references"])
    return merged


def available_skills(cat: dict) -> list[str]:
    return sorted(cat.get("skills", {}).keys())


def skill_version(entry: dict) -> str:
    """市场版本号一律来自 catalog；仓库内部演进号（active_version）不上架。"""
    return str(entry.get("version", "1.0.0"))


# --------------------------------------------------------------------------
# frontmatter
# --------------------------------------------------------------------------
def parse_frontmatter(path: Path) -> tuple[dict, list[str]]:
    """返回 (frontmatter 字段, 正文行)。支持 >- / | 块标量与行内列表。"""
    if not path.is_file():
        return {}, []
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, lines
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return {}, lines
    fm: dict = {}
    key = None
    block = False
    nested = False
    for ln in lines[1:end]:
        m = re.match(r"^([A-Za-z_][\w-]*):\s?(.*)$", ln)
        if m and not ln.startswith((" ", "\t")):
            key, val = m.group(1), unquote(m.group(2).strip())
            if val in (">", ">-", "|", "|-"):
                fm[key] = ""
                block, nested = True, False
            elif val == "":
                # 嵌套映射（专家 Agent 定义的 displayName / profession）
                fm[key] = {}
                block, nested = False, True
            else:
                fm[key] = val
                block, nested = False, False
        elif key and ln.startswith((" ", "\t")) and ln.strip():
            if nested and isinstance(fm.get(key), dict):
                m2 = re.match(r"^\s*([A-Za-z_][\w-]*):\s?(.*)$", ln)
                if m2:
                    fm[key][m2.group(1)] = unquote(m2.group(2).strip())
            elif block:
                fm[key] = (fm[key] + " " + ln.strip()).strip()
            elif fm.get(key, "").startswith("["):
                fm[key] = (fm[key] + " " + ln.strip()).strip()
    return fm, lines[end + 1 :]


def y(v) -> str:
    """用 JSON 双引号标量发射，等价于合法 YAML 字符串，免去 PyYAML 依赖。"""
    return json.dumps(v, ensure_ascii=False)


def unquote(s: str) -> str:
    if len(s) >= 2 and s[0] == s[-1] and s[0] in ("'", '"'):
        return s[1:-1]
    return s


def collapse(s: str) -> str:
    return " ".join((s or "").split())


def render_frontmatter(skill: str, entry: dict, src_fm: dict, author: str, version: str) -> list[str]:
    out = ["---"]
    out.append(f"name: {y(skill)}")
    out.append(f"display_name: {y(entry['display_name'])}")
    out.append(f"display_name_en: {y(entry['display_name_en'])}")
    out.append(f"description: {y(collapse(src_fm.get('description', '')))}")
    out.append(f"description_zh: {y(collapse(entry['description_zh']))}")
    out.append(f"description_en: {y(collapse(entry['description_en']))}")
    for key in ("examples_zh", "examples_en"):
        items = [collapse(i) for i in entry.get(key, []) if collapse(i)]
        if items:
            out.append(f"{key}:")
            out.extend(f"  - {y(i)}" for i in items)
    out.append(f"version: {y(version)}")
    out.append(f"author: {y(author)}")
    tools = entry.get("allowed-tools") or entry.get("allowed_tools")
    if tools:
        out.append(f"allowed-tools: {y(tools)}")
    out.append("---")
    return out


# --------------------------------------------------------------------------
# 链接改写：市场包是独立个体，跨技能 / 跨目录链接必须重定位或降级
# --------------------------------------------------------------------------
def _dep_root(stage: Path, dep: str) -> Path:
    return stage / "references" / "deps" / dep


def _within(stage: Path, p: Path) -> bool:
    try:
        p.resolve().relative_to(stage.resolve())
        return True
    except ValueError:
        return False


def _resolve(
    base_dir: Path,
    stage: Path,
    path: str,
    deps: list[str],
    boundary: Path,
    fallback_dir: Path,
) -> Path | None:
    # 1) 边界内可解析（技能包边界 = 技能根；专家包边界 = skills/ 根，允许跨技能引用）
    cand = (base_dir / path).resolve()
    if cand.exists() and _within(boundary, cand):
        return cand
    parts = os.path.normpath(os.path.join(base_dir, path)).split(os.sep)
    base = str(stage.resolve())
    # dep 作用域：文件本身位于 references/deps/<dep>/ 下时，优先同域查找
    own_dep = None
    rel = os.path.relpath(str(base_dir.resolve()), base)
    rel_parts = rel.split(os.sep)
    if len(rel_parts) >= 3 and rel_parts[0] == "references" and rel_parts[1] == "deps":
        own_dep = rel_parts[2]
    if own_dep:
        sibling = _dep_root(stage, own_dep) / os.path.basename(path)
        if sibling.exists():
            return sibling.resolve()
    # 2) 跨技能链接 → 内联依赖目录
    for dep in deps:
        if dep in parts:
            idx = len(parts) - 1 - parts[::-1].index(dep)
            rest = parts[idx + 1 :]
            if rest and rest[0] == "references":
                rest = rest[1:]
            target = _dep_root(stage, dep).joinpath(*rest)
            if target.exists():
                return target.resolve()
    # 3) 边界外但包内存在的同名文件（companion 文件等）→ 落到 fallback 目录
    if fallback_dir:
        fallback = fallback_dir / os.path.basename(path)
        if fallback.exists():
            return fallback.resolve()
    return None


def fix_links(
    stage: Path,
    deps: list[str],
    boundary: Path | None = None,
    fallback_dir: Path | None = None,
    degrade: bool = True,
) -> int:
    """重写包内 .md 的相对链接；无法解析且越界的链接降级为纯文本。返回降级数。"""
    boundary = boundary or stage
    fallback_dir = fallback_dir or (stage / "references")
    degraded = 0
    for md in sorted(stage.rglob("*.md")):
        text = md.read_text(encoding="utf-8")
        stats = {"n": 0}

        def repl(m: re.Match) -> str:
            label, target = m.group(1), m.group(2)
            if re.match(r"^(https?|mailto|tel):", target) or target.startswith("//"):
                return m.group(0)
            path = target.split("#", 1)[0].strip()
            if not path:
                return m.group(0)
            anchor = target[len(path) :]
            resolved = _resolve(md.parent, stage, path, deps, boundary, fallback_dir)
            if resolved is None:
                stats["n"] += 1
                return f"`{label}`" if degrade and label else (m.group(0) if not degrade else "")
            new = os.path.relpath(str(resolved), str(md.parent))
            return f"[{label}]({new}{anchor})"

        new_text = LINK_RE.sub(repl, text)
        if new_text != text:
            md.write_text(new_text, encoding="utf-8")
        degraded += stats["n"]
    return degraded


# --------------------------------------------------------------------------
# build
# --------------------------------------------------------------------------
def stage_skill(
    skill: str,
    entry: dict,
    author: str,
    dest: Path | None = None,
    boundary: Path | None = None,
    companion_in_refs: bool = True,
    inline_deps: bool = True,
    fix_links_now: bool = True,
) -> tuple[Path, dict]:
    """把单个技能落到 dest（默认 DIST_DIR/<skill>）。

    boundary        : 链接允许落到的根；技能包 = 技能根，专家包 = skills/ 根。
    companion_in_refs: True 时 AGENT-BRIEF/OUT-OF-SCOPE 放到 references/（市场包根级白名单要求），
                       False 时留在技能根（专家包内，保留原有相对链接）。
    inline_deps     : 专家包内 13 个技能同在 skills/ 下，无需内联。
    """
    src = SE_DIR / skill
    if not src.is_dir():
        sys.exit(f"source skill not found: {src}")
    stage = dest or (DIST_DIR / skill)
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir(parents=True)
    boundary = boundary or stage

    src_fm, body = parse_frontmatter(src / "SKILL.md")
    if not src_fm.get("name"):
        sys.exit(f"{skill}/SKILL.md missing frontmatter name")
    version = skill_version(entry)

    head = render_frontmatter(skill, entry, src_fm, author, version)
    deps = list(entry.get("deps") or []) if inline_deps else []
    out_body = list(body)
    if deps:
        out_body += [
            "",
            "## 依赖说明（上架包已内联）",
            "",
            "本技能在原仓库通过 `depends_on` 复用以下技能，市场侧不提供依赖安装，"
            "相关细则已内联到包内，无需另外安装：",
            "",
        ]
        out_body += [f"- `{d}` → `references/deps/{d}/`" for d in deps]
        out_body.append("")
    elif entry.get("deps"):
        # 专家包模式：依赖技能与本技能同在 skills/ 下，直接按兄弟目录读取
        out_body += [
            "",
            "## 依赖技能（同包内）",
            "",
            "本技能复用以下兄弟技能的细则，它们与本技能同在 `skills/` 下，"
            "按相对路径直接读取即可，不需要内联：",
            "",
        ]
        out_body += [f"- `{d}` → `../{d}/`" for d in entry["deps"]]
        out_body.append("")
    (stage / "SKILL.md").write_text("\n".join(head + [""] + out_body).rstrip() + "\n", encoding="utf-8")

    # 子资源目录（白名单：官方仅识别 references / scripts / templates）
    for sub in entry.get("include", ["references"]):
        if sub not in SPEC_SUBDIRS and sub not in (entry.get("map_dirs") or {}):
            continue
        sdir = src / sub
        if sdir.is_dir() and any(sdir.iterdir()):
            shutil.copytree(sdir, stage / sub)
    for src_name, dst_name in (entry.get("map_dirs") or {}).items():
        sdir = src / src_name
        if sdir.is_dir() and any(sdir.iterdir()):
            dst = stage / dst_name
            if dst.exists():
                for f in sdir.iterdir():
                    shutil.copy2(f, dst / f.name)
            else:
                shutil.copytree(sdir, dst)

    # companion 文件：市场技能包根级只认 SKILL.md + 三个子目录，故下沉到 references/
    companion_dir = (stage / "references") if companion_in_refs else stage
    companion_dir.mkdir(parents=True, exist_ok=True)
    for fname in entry.get("include_files") or []:
        fsrc = src / fname
        if fsrc.is_file():
            shutil.copy2(fsrc, companion_dir / fname)

    # 依赖内联
    for dep in deps:
        dsrc = SE_DIR / dep
        if not dsrc.is_dir():
            sys.exit(f"declared dep '{dep}' not found for '{skill}'")
        ddst = _dep_root(stage, dep)
        ddst.mkdir(parents=True, exist_ok=True)
        if (dsrc / "SKILL.md").is_file():
            shutil.copy2(dsrc / "SKILL.md", ddst / "SKILL.md")
        drefs = dsrc / "references"
        if drefs.is_dir():
            for f in sorted(drefs.glob("*.md")):
                shutil.copy2(f, ddst / f.name)

    degraded = (
        fix_links(
            stage,
            deps,
            boundary=boundary,
            fallback_dir=(stage / "references") if companion_in_refs else stage,
            degrade=True,
        )
        if fix_links_now
        else 0
    )
    meta = {"skill": skill, "version": version, "deps": deps, "degraded_links": degraded}
    return stage, meta


def zip_package(skill: str, version: str, layout: str = "flat") -> Path:
    """打包技能 zip。

    flat   : zip 根目录直接是技能内容（SKILL.md 在根）—— 平台报错
             「所选文件夹中未找到 SKILL.md」时用它。
    nested : zip 根目录是 <skill>/ 目录，SKILL.md 在下一级 —— 对应官方文档
             技能基础结构 {skill-name}/SKILL.md 的另一种解读。
    compat : 根目录有 SKILL.md，同时镜像一份 <skill>/SKILL.md，两种解析器都能找到。
    """
    suffix = "" if layout == "flat" else f"-{layout}"
    out = DIST_DIR / f"{skill}-v{version}{suffix}.zip"
    if out.exists():
        out.unlink()
    stage = DIST_DIR / skill
    if layout == "flat":
        subprocess.run(["zip", "-qrX", str(out), "."], cwd=str(stage), check=True)
    elif layout == "nested":
        subprocess.run(["zip", "-qrX", out.name, skill], cwd=str(DIST_DIR), check=True)
    else:  # compat: 根目录内容 + <skill>/ 完整副本
        tmp = DIST_DIR / f".compat-{skill}"
        if tmp.exists():
            shutil.rmtree(tmp)
        tmp.mkdir(parents=True)
        shutil.copytree(stage, tmp / skill)
        for item in stage.iterdir():
            dst = tmp / item.name
            if item.is_dir():
                shutil.copytree(item, dst)
            else:
                shutil.copy2(item, dst)
        subprocess.run(["zip", "-qrX", str(out), "."], cwd=str(tmp), check=True)
        shutil.rmtree(tmp)
    return out


# --------------------------------------------------------------------------
# validate
# --------------------------------------------------------------------------
def validate_stage(
    skill: str,
    entry: dict,
    stage: Path,
    boundary: Path | None = None,
    allow_root_files: tuple[str, ...] = (),
    check_size: bool = True,
) -> tuple[list[str], list[str]]:
    fails: list[str] = []
    warns: list[str] = []
    boundary = boundary or stage

    def fail(m: str) -> None:
        fails.append(m)

    def warn(m: str) -> None:
        warns.append(m)

    skill_md = stage / "SKILL.md"
    if not skill_md.is_file():
        fail("SKILL.md missing at package root")
        return fails, warns
    fm, _ = parse_frontmatter(skill_md)
    for k in REQUIRED_FM_KEYS:
        if not collapse(fm.get(k, "")):
            fail(f"frontmatter missing/empty required key: {k}")
    name = collapse(fm.get("name", ""))
    if name != skill:
        fail(f"frontmatter name '{name}' != package dir '{skill}'")
    if not re.match(r"^[a-z0-9]+(-[a-z0-9]+)*$", name):
        fail(f"name '{name}' is not kebab-case")
    desc = collapse(fm.get("description", ""))
    if len(desc) < 20:
        fail(f"description too short ({len(desc)} chars): must state purpose + trigger words")
    ex_zh = entry.get("examples_zh") or []
    ex_en = entry.get("examples_en") or []
    if not ex_zh or not ex_en:
        warn(f"examples_zh/examples_en incomplete (zh={len(ex_zh)}, en={len(ex_en)}), 详情页【试试这样用】会缺项")
    if len(ex_zh) > 3 or len(ex_en) > 3:
        warn("examples 超过 3 条，建议精简到 3 条以内")

    # 根目录白名单
    for child in sorted(stage.iterdir()):
        if child.name == "SKILL.md":
            continue
        if child.is_dir() and child.name in SPEC_SUBDIRS:
            continue
        if child.is_file() and child.name in allow_root_files:
            continue
        fail(f"unexpected entry at package root: {child.name} (only SKILL.md + {list(SPEC_SUBDIRS)})")

    # 依赖内联完整性（专家包内技能同级存在，不内联，跳过）
    if (stage / "references" / "deps").is_dir():
        for dep in entry.get("deps") or []:
            d = _dep_root(stage, dep)
            if not d.is_dir() or not any(d.iterdir()):
                fail(f"declared dep '{dep}' not inlined under references/deps/{dep}/")

    # 安全扫描
    for root, _, files in os.walk(stage):
        for fn in files:
            if SECRET_NAME_RE.search(fn):
                fail(f"secret-like file in package: {os.path.relpath(os.path.join(root, fn), stage)}")
    home = str(Path.home())
    for md in sorted(stage.rglob("*.md")):
        txt = md.read_text(encoding="utf-8")
        for hit in ABS_USER_PATH_RE.finditer(txt):
            p = hit.group(0)
            if p.startswith(home):
                fail(f"本机绝对路径泄露 in {md.relative_to(stage)}: {p}")
            else:
                warn(f"疑似占位绝对路径，请人工确认 {md.relative_to(stage)}: {p}")
        for m in LINK_RE.finditer(txt):
            t = m.group(2)
            if re.match(r"^(https?|mailto|tel):", t) or t.startswith("//"):
                continue
            p = t.split("#", 1)[0].strip()
            if not p:
                continue
            target = (md.parent / p).resolve()
            if not target.exists() or not _within(boundary, target):
                fail(f"local link escapes package in {md.relative_to(stage)}: {t}")

    if check_size:
        size = sum(f.stat().st_size for f in stage.rglob("*") if f.is_file())
        if size > MAX_PACKAGE_BYTES:
            fail(f"package too large: {size/1024/1024:.2f} MB (> 5 MB)")
        elif size > 2 * 1024 * 1024:
            warn(f"package size {size/1024/1024:.2f} MB — 超过 2MB 时加载体验会下降")

    return fails, warns


def validate_zip(zip_path: Path, skill: str, layout: str = "flat") -> list[str]:
    fails: list[str] = []
    out = subprocess.run(["unzip", "-Z1", str(zip_path)], capture_output=True, text=True)
    names = [n for n in out.stdout.splitlines() if n.strip()]
    if layout == "flat":
        if "SKILL.md" not in names:
            fails.append("zip 根目录缺少 SKILL.md（平台按「所选文件夹根目录」找 SKILL.md）")
        if any(n.startswith(f"{skill}/") for n in names):
            fails.append(f"flat 布局不应包含外层目录 '{skill}/'")
    elif layout == "compat":
        if "SKILL.md" not in names:
            fails.append("compat 布局根目录缺少 SKILL.md")
        if f"{skill}/SKILL.md" not in names:
            fails.append(f"compat 布局缺少镜像副本 '{skill}/SKILL.md'")
    else:
        if f"{skill}/SKILL.md" not in names:
            fails.append(f"zip top-level must contain '{skill}/SKILL.md'")
    if any(n.startswith("__MACOSX") for n in names):
        fails.append("zip contains __MACOSX junk")
    return fails


# --------------------------------------------------------------------------
# expert package（专家 / 专家团：一个 zip 带多个技能）
# 规范：https://open.workbuddy.cn/docs/expert
# --------------------------------------------------------------------------
EXPERT_DIST = SE_DIR / "dist" / "workbuddy-expert"
EXPERT_PATH = HERE / "expert.json"
AGENT_TMPL = HERE / "templates" / "expert-agent.md.tmpl"
AVATAR_SIZE = 512
MAX_AVATAR_BYTES = 500 * 1024
CATEGORY_IDS = {
    "01-ProductDesign", "02-Engineering", "03-GameSpatial", "04-DataAI",
    "05-MarketingGrowth", "06-ContentCreative", "07-SalesCommerce",
    "08-FinanceInvestment", "09-OperationsHR", "10-ProjectQuality",
    "11-SecurityCompliance", "12-IndustryConsultant", "13-TencentZone",
    "14-WorldWise", "15-Education",
}
PLACEHOLDER_RE = re.compile(r"(changeme|example\.com|your[_-]?name|placeholder)", re.I)
CJK_RE = re.compile(r"[一-鿿]")


def load_expert() -> dict:
    if not EXPERT_PATH.is_file():
        sys.exit(f"expert config not found: {EXPERT_PATH}")
    with open(EXPERT_PATH, encoding="utf-8") as f:
        return json.load(f)


def _png_bytes(size: int) -> bytes:
    """纯 stdlib 生成 512×512 占位头像（渐变纯色，无外部依赖）。"""
    import struct
    import zlib

    raw = bytearray()
    for y in range(size):
        raw.append(0)  # filter type 0
        t = y / max(size - 1, 1)
        px = bytes((int(0x0A + 0x14 * t), int(0x51 + 0x2E * t), int(0xC4 + 0x3B * t)))
        raw += px * size

    def chunk(tag: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + tag
            + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        )

    ihdr = struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        + chunk(b"IEND", b"")
    )


def render_agent_doc(expert: dict, cat: dict, skills: list[str]) -> str:
    tmpl = AGENT_TMPL.read_text(encoding="utf-8") if AGENT_TMPL.is_file() else (
        "---\nname: {{agent_name}}\ndescription: {{agent_desc}}\n"
        "displayName:\n  en: {{display_name_en}}\n  zh: {{display_name_zh}}\n"
        "profession:\n  en: {{profession_en}}\n  zh: {{profession_zh}}\n"
        "maxTurns: {{max_turns}}\n---\n\n# {{display_name_zh}}\n\n{{skills_table}}\n"
    )
    rows = ["| 技能 | 触发场景 | 入口 |", "|---|---|---|"]
    for s in skills:
        e = entry_for(cat, s)
        desc = collapse(e.get("route_hint", "")) or collapse(e.get("description_zh", ""))
        short = desc[:30] + ("…" if len(desc) > 30 else "")
        rows.append(f"| `{s}` | {short} | skills/{s}/SKILL.md |")
    agent = expert.get("agent", {})
    dn = expert.get("display_name", {})
    pf = expert.get("profession", {})
    rep = {
        "{{agent_name}}": agent.get("name", expert.get("name", "")),
        "{{agent_desc}}": collapse(agent.get("description", "")),
        "{{display_name_en}}": dn.get("en", ""),
        "{{display_name_zh}}": dn.get("zh", ""),
        "{{profession_en}}": pf.get("en", ""),
        "{{profession_zh}}": pf.get("zh", ""),
        "{{max_turns}}": str(agent.get("max_turns", 50)),
        "{{skills_table}}": "\n".join(rows),
        "{{skill_count}}": str(len(skills)),
    }
    out = tmpl
    for k, v in rep.items():
        out = out.replace(k, v)
    return out


def build_expert(
    cat: dict, allow_placeholder: bool = False, layout: str = "nested"
) -> tuple[Path | None, dict]:
    expert = load_expert()
    name = expert.get("name", "")
    if not name:
        sys.exit("expert.json missing 'name'")
    version = str(expert.get("version", "1.0.0"))
    skills = list(expert.get("skills") or [])
    pkg = EXPERT_DIST / name
    if pkg.exists():
        shutil.rmtree(pkg)
    (pkg / ".codebuddy-plugin").mkdir(parents=True)
    (pkg / "agents").mkdir()
    (pkg / "avatars").mkdir()

    # 技能树：同处 skills/ 下，不做内联，跨技能链接天然可解析
    skills_root = pkg / "skills"
    skills_root.mkdir()
    author = expert.get("author", {}).get("name") or cat.get("author", "")
    staged = []
    for s in skills:
        e = entry_for(cat, s)
        if not e.get("enabled", True):
            continue
        dest = skills_root / s
        meta = stage_skill(
            s, e, author, dest=dest, boundary=skills_root,
            companion_in_refs=False, inline_deps=False, fix_links_now=False,
        )[1]
        staged.append(meta)

    # 链接修复必须等全部技能落盘后再统一做：跨技能引用（../../<skill>/references/x.md）
    # 依赖兄弟技能目录已存在，逐个落盘时会被误判为越界而降级。
    degraded = fix_links(skills_root, [], boundary=skills_root, fallback_dir=skills_root)

    # plugin.json
    agent = expert.get("agent", {})
    agent_file = f"agents/{agent.get('name', name)}.md"
    (pkg / "agents" / f"{agent.get('name', name)}.md").write_text(
        render_agent_doc(expert, cat, [m["skill"] for m in staged]), encoding="utf-8"
    )
    plugin = {
        "name": name,
        "version": version,
        "description": collapse(expert.get("description", "")),
        "author": {"name": author, "email": expert.get("author", {}).get("email", "")},
        "agents": [f"./{agent_file}"],
        "expertType": expert.get("expert_type", "agent"),
        "agentName": agent.get("name", name),
        "displayName": expert.get("display_name", {}),
        "profession": expert.get("profession", {}),
        "displayDescription": expert.get("display_description", {}),
        "avatar": expert.get("avatar", "avatars/expert.png"),
        "categoryId": expert.get("category_id", "02-Engineering"),
        "defaultInitPrompt": expert.get("default_init_prompt", {}),
        "plugin": name,
        "tags": expert.get("tags", []),
        "quickPrompts": expert.get("quick_prompts", []),
        "skills": [f"./skills/{m['skill']}" for m in staged],
    }
    if plugin["expertType"] == "team":
        plugin["teamInfo"] = expert.get("team_info", {})
    with open(pkg / ".codebuddy-plugin" / "plugin.json", "w", encoding="utf-8") as f:
        json.dump(plugin, f, indent=2, ensure_ascii=False)
        f.write("\n")

    # 头像：优先用仓库内源图 workbuddy/avatars/expert.png；缺失时用占位图补齐
    avatar_rel = expert.get("avatar", "avatars/expert.png")
    avatar_path = pkg / avatar_rel
    avatar_path.parent.mkdir(parents=True, exist_ok=True)
    src_avatar = HERE / avatar_rel
    if src_avatar.is_file():
        shutil.copy2(src_avatar, avatar_path)
        generated = False
    else:
        avatar_path.write_bytes(_png_bytes(AVATAR_SIZE))
        generated = True

    # README（专家包规范要求）
    lines = [
        f"# {expert.get('display_name', {}).get('zh', name)}",
        "",
        collapse(expert.get("display_description", {}).get("zh", "")),
        "",
        "## 内置技能",
        "",
    ]
    for m in staged:
        e = entry_for(cat, m["skill"])
        lines.append(f"- **{m['skill']}** —— {collapse(e.get('description_zh', ''))}")
    lines += ["", "## 使用方式", "", "召唤本专家后直接描述任务，专家按场景路由到对应技能并加载其细则全文。", ""]
    (pkg / "README.md").write_text("\n".join(lines), encoding="utf-8")

    fails, warns = validate_expert_pkg(expert, cat, pkg, allow_placeholder)
    if generated:
        warns.append(f"头像 {avatar_rel} 为自动生成的占位图，上架前必须替换为 512×512 PNG/JPG（≤500KB）")
    for w in warns:
        print(f"  [warn] {name}: {w}")
    for f in fails:
        print(f"  [FAIL] {name}: {f}")
    if fails:
        print(f"--- expert {name}: FAIL ---")
        return None, {"skills": staged}
    suffix = "" if layout == "nested" else f"-{layout}"
    zp = EXPERT_DIST / f"{name}-v{version}{suffix}.zip"
    if zp.exists():
        zp.unlink()
    if layout == "nested":
        subprocess.run(["zip", "-qrX", zp.name, name], cwd=str(EXPERT_DIST), check=True)
    else:
        subprocess.run(["zip", "-qrX", str(zp), "."], cwd=str(pkg), check=True)
    zf = validate_expert_zip(zp, name, [m["skill"] for m in staged], layout)
    for f in zf:
        print(f"  [FAIL] {name}: {f}")
    if zf:
        print(f"--- expert {name}: FAIL ---")
        return None, {"skills": staged}
    print(
        f"[ok] expert {name} v{version} -> {zp} "
        f"({zp.stat().st_size/1024:.0f} KB, {len(staged)} 个技能, 降级链接 {degraded} 处)"
    )
    return zp, {
        "skills": staged,
        "version": version,
        "avatar_generated": generated,
        "degraded_links": degraded,
    }


def validate_expert_pkg(expert: dict, cat: dict, pkg: Path, allow_placeholder: bool) -> tuple[list[str], list[str]]:
    fails: list[str] = []
    warns: list[str] = []

    def fail(m: str) -> None:
        fails.append(m)

    def warn(m: str) -> None:
        warns.append(m)

    pj = pkg / ".codebuddy-plugin" / "plugin.json"
    if not pj.is_file():
        fail("missing .codebuddy-plugin/plugin.json")
        return fails, warns
    with open(pj, encoding="utf-8") as f:
        p = json.load(f)
    name = p.get("name", "")
    if not name:
        fail("plugin.json missing 'name'")
    if name != pkg.name:
        fail(f"plugin name '{name}' != package dir '{pkg.name}'")
    if not re.match(r"^[a-z0-9]+(-[a-z0-9]+)*$", name):
        fail(f"plugin name '{name}' 必须是小写字母 + 连字符")
    if p.get("plugin") != name:
        fail("plugin.json 'plugin' 必须与 'name' 一致")
    if not re.match(r"^\d+\.\d+\.\d+$", str(p.get("version", ""))):
        fail(f"version '{p.get('version')}' 不是语义化版本（x.y.z）")
    if p.get("expertType") not in ("agent", "team"):
        fail(f"expertType '{p.get('expertType')}' 非法（只能是 agent / team）")
    for k in ("description", "categoryId", "avatar"):
        if not p.get(k):
            fail(f"plugin.json missing required field: {k}")
    if p.get("categoryId") not in CATEGORY_IDS:
        fail(f"categoryId '{p.get('categoryId')}' 不在官方行业分类表中")

    author = p.get("author") or {}
    if not author.get("name"):
        fail("plugin.json author.name missing")
    email = str(author.get("email", ""))
    if not email or PLACEHOLDER_RE.search(email):
        msg = "plugin.json author.email 未填写或仍是占位值（平台必填）"
        (warn if allow_placeholder else fail)(msg)

    for k in ("displayName", "profession", "displayDescription", "defaultInitPrompt"):
        v = p.get(k) or {}
        if not v.get("zh") or not v.get("en"):
            fail(f"plugin.json {k} 必须含 zh + en 双语")
    zh_desc = (p.get("displayDescription") or {}).get("zh", "")
    n_cjk = len(CJK_RE.findall(zh_desc))
    if not 40 <= n_cjk <= 50:
        fail(f"displayDescription.zh 中文字数 {n_cjk} 字，规范要求 40-50 字")

    tags = p.get("tags") or []
    if len(tags) != 3:
        fail(f"tags 必须固定 3 个，当前 {len(tags)} 个")
    for t in tags:
        if not t.get("zh") or not t.get("en"):
            fail("tags 每项必须含 zh + en")
    qp = p.get("quickPrompts") or []
    if len(qp) != 3:
        fail(f"quickPrompts 必须固定 3 个，当前 {len(qp)} 个")
    for q in qp:
        if not q.get("zh") or not q.get("en"):
            fail("quickPrompts 每项必须含 zh + en")
    if qp and p.get("defaultInitPrompt") != qp[0]:
        fail("defaultInitPrompt 必须与 quickPrompts 第一条一致")

    # avatar
    av = pkg / p.get("avatar", "avatars/expert.png")
    if not av.is_file():
        fail(f"avatar missing: {p.get('avatar')}")
    else:
        if av.stat().st_size > MAX_AVATAR_BYTES:
            fail(f"avatar too large: {av.stat().st_size/1024:.0f} KB (> 500 KB)")
        with open(av, "rb") as f:
            head = f.read(24)
        if head[:8] != b"\x89PNG\r\n\x1a\n":
            warn(f"avatar 非 PNG（{p.get('avatar')}），官方推荐 PNG/JPG 512×512")
        else:
            import struct

            w, h = struct.unpack(">II", head[16:24])
            if (w, h) != (AVATAR_SIZE, AVATAR_SIZE):
                fail(f"avatar 尺寸 {w}×{h}，规范要求 512×512")

    # agents
    agent_name = p.get("agentName", "")
    if not agent_name:
        fail("plugin.json missing 'agentName'")
    for rel in p.get("agents") or []:
        if not (pkg / rel).is_file():
            fail(f"agents 路径不存在: {rel}")
    af = pkg / "agents" / f"{agent_name}.md"
    if not af.is_file():
        fail(f"agents/{agent_name}.md 不存在（agentName 必须对应 agents/ 下的文件名）")
    else:
        fm, _ = parse_frontmatter(af)
        for k in ("name", "description"):
            if not collapse(fm.get(k, "")):
                fail(f"agent 定义 frontmatter missing: {k}")
        if collapse(fm.get("name", "")) != agent_name:
            fail(f"agent frontmatter name '{fm.get('name')}' != 文件名 '{agent_name}'")
        for k in ("displayName", "profession"):
            v = fm.get(k) or {}
            if not v.get("zh") or not v.get("en"):
                fail(f"agent frontmatter {k} 必须含 zh + en 双语")

    if p.get("expertType") == "team":
        ti = p.get("teamInfo") or {}
        if not ti.get("leadAgent"):
            fail("expertType=team 时 teamInfo.leadAgent 必填")
        members = ti.get("memberAgents") or []
        if not members:
            fail("expertType=team 时 teamInfo.memberAgents 必填")
        for m in [ti.get("leadAgent")] + list(members):
            if m and not (pkg / "agents" / f"{m}.md").is_file():
                fail(f"team 成员缺少 agents/{m}.md")

    # skills
    skills_root = pkg / "skills"
    declared = []
    for rel in p.get("skills") or []:
        sd = (pkg / rel).resolve()
        if not sd.is_dir():
            fail(f"skills 路径不存在: {rel}")
            continue
        declared.append(sd.name)
        s_fails, s_warns = validate_stage(
            sd.name,
            entry_for(cat, sd.name),
            sd,
            boundary=skills_root,
            allow_root_files=("AGENT-BRIEF.md", "OUT-OF-SCOPE.md"),
            check_size=False,
        )
        for w in s_warns:
            warns.append(f"{sd.name}: {w}")
        for f in s_fails:
            fails.append(f"{sd.name}: {f}")
    if not declared:
        fail("plugin.json skills 为空：专家包至少要带一个技能目录")

    total = sum(f.stat().st_size for f in pkg.rglob("*") if f.is_file())
    if total > MAX_PACKAGE_BYTES:
        fail(f"expert package too large: {total/1024/1024:.2f} MB (> 5 MB)")
    return fails, warns


def validate_expert_zip(zip_path: Path, name: str, skills: list[str], layout: str = "nested") -> list[str]:
    fails: list[str] = []
    out = subprocess.run(["unzip", "-Z1", str(zip_path)], capture_output=True, text=True)
    names = [n for n in out.stdout.splitlines() if n.strip()]
    pre = f"{name}/" if layout == "nested" else ""
    need = [
        f"{pre}.codebuddy-plugin/plugin.json",
        f"{pre}avatars/expert.png",
        f"{pre}README.md",
    ] + [f"{pre}skills/{s}/SKILL.md" for s in skills]
    for n in need:
        if n not in names:
            fails.append(f"zip missing: {n}")
    if any(n.startswith("__MACOSX") for n in names):
        fails.append("zip contains __MACOSX junk")
    return fails


# --------------------------------------------------------------------------
# commands
# --------------------------------------------------------------------------
def cmd_list(cat: dict) -> int:
    print(f"{'skill':32s} {'ver':10s} {'pricing':22s} deps")
    for s in available_skills(cat):
        e = entry_for(cat, s)
        p = e.get("pricing", {})
        pricing = f"{p.get('mode','free')} ¥{p.get('cny', 0)}"
        flag = "" if e.get("enabled", True) else " (disabled)"
        print(f"{s:32s} {skill_version(e):10s} {pricing:22s} {','.join(e.get('deps') or []) or '-'}{flag}")
    return 0


def cmd_build(
    cat: dict,
    targets: list[str],
    out_dir: Path | None,
    do_validate: bool,
    layout: str = "both",
) -> int:
    global DIST_DIR
    if out_dir:
        DIST_DIR = out_dir
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    layouts = ("flat", "nested") if layout == "both" else (layout,)
    author = cat.get("author", "")
    skills = available_skills(cat) if targets == ["--all"] else targets
    built: list[dict] = []
    rc = 0
    for s in skills:
        e = entry_for(cat, s)
        if not e.get("enabled", True):
            print(f"[skip] {s}: disabled in catalog")
            continue
        stage, meta = stage_skill(s, e, author)
        version = meta["version"]
        fails, warns = validate_stage(s, e, stage)
        for w in warns:
            print(f"  [warn] {s}: {w}")
        for f in fails:
            print(f"  [FAIL] {s}: {f}")
        if fails:
            rc = 1
            print(f"--- {s}: FAIL ---")
            continue
        zips: list[str] = []
        zok = True
        for lay in layouts:
            zp = zip_package(s, version, lay)
            zfails = validate_zip(zp, s, lay)
            for f in zfails:
                print(f"  [FAIL] {s}: {f}")
            if zfails:
                rc = 1
                zok = False
                continue
            zips.append(str(zp))
        if not zok:
            print(f"--- {s}: FAIL ---")
            continue
        size = Path(zips[0]).stat().st_size
        print(
            f"[ok] {s} v{version} -> {', '.join(Path(p).name for p in zips)} "
            f"({size/1024:.0f} KB, 降级链接 {meta['degraded_links']} 处)"
        )
        built.append({**meta, "zips": zips, "size": size})
    if built:
        sheet = DIST_DIR / "build-manifest.json"
        with open(sheet, "w", encoding="utf-8") as f:
            json.dump(built, f, indent=2, ensure_ascii=False)
            f.write("\n")
        print(f"\nmanifest: {sheet}")
    return rc


def cmd_validate(cat: dict, targets: list[str]) -> int:
    global DIST_DIR
    skills = available_skills(cat) if not targets or targets == ["--all"] else targets
    rc = 0
    for s in skills:
        e = entry_for(cat, s)
        stage = DIST_DIR / s
        if not stage.is_dir():
            print(f"[info] {s}: no build found, staging a temporary copy for preflight")
            tmp = Path(os.environ.get("TMPDIR", "/tmp")) / f"wb-{s}"
            keep = DIST_DIR
            DIST_DIR = tmp
            try:
                stage, _ = stage_skill(s, e, cat.get("author", ""))
            finally:
                DIST_DIR = keep
        fails, warns = validate_stage(s, e, stage)
        for w in warns:
            print(f"  [warn] {s}: {w}")
        for f in fails:
            print(f"  [FAIL] {s}: {f}")
        print(f"--- {s}: {'PASS' if not fails else 'FAIL (' + str(len(fails)) + ')'} ---")
        rc = rc or (1 if fails else 0)
    return rc


def cmd_sheet(cat: dict) -> int:
    """生成上架填表清单：平台后台需要逐项填写的展示名 / 简介 / 示例 / 定价建议。"""
    lines = ["# WorkBuddy 上架填表清单", "", "由 `workbuddy/catalog.json` 生成，请勿手改；定价在开放平台「收入变现」后台选择。", ""]
    for s in available_skills(cat):
        e = entry_for(cat, s)
        if not e.get("enabled", True):
            continue
        p = e.get("pricing", {})
        lines += [
            f"## {s}（v{skill_version(e)}）",
            "",
            f"- 展示名称：{e['display_name']}",
            f"- 英文展示名：{e['display_name_en']}",
            f"- 中文简介：{collapse(e['description_zh'])}",
            f"- 英文简介：{collapse(e['description_en'])}",
            "- 试试这样用（中）：",
        ]
        lines += [f"  {i}. {x}" for i, x in enumerate(e.get("examples_zh") or [], 1)]
        lines += ["- 试试这样用（英）："]
        lines += [f"  {i}. {x}" for i, x in enumerate(e.get("examples_en") or [], 1)]
        lines += [
            f"- 定价建议：{p.get('mode','free')} ¥{p.get('cny', 0)} — {p.get('note','')}",
            f"- 依赖内联：{', '.join(e.get('deps') or []) or '无'}",
            "",
        ]
    out = DIST_DIR / "upload-sheet.md"
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(f"sheet: {out}")
    return 0


def cmd_clean() -> int:
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
        print(f"cleaned: {DIST_DIR}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="WorkBuddy 上架包构建 / 校验")
    ap.add_argument("cmd", choices=["list", "build", "validate", "sheet", "expert", "clean"])
    ap.add_argument("targets", nargs="*", help="skill 名；配合 --all 处理全部")
    ap.add_argument("--all", action="store_true", help="对 catalog 中全部 skill 生效")
    ap.add_argument("--out", help="产物输出目录，默认 skills-engineering/dist/workbuddy")
    ap.add_argument("--no-validate", action="store_true")
    ap.add_argument(
        "--allow-placeholder",
        action="store_true",
        help="expert 自检用：允许 author.email / 头像留占位值",
    )
    ap.add_argument(
        "--layout",
        choices=["flat", "nested", "compat", "both"],
        default="both",
        help="技能 zip 层级：flat=根目录即 SKILL.md，nested=外层为 <skill>/，compat=两种都有，both=flat+nested",
    )
    args = ap.parse_args()

    targets = ["--all"] if args.all else args.targets
    cat = load_catalog()
    if args.cmd == "list":
        return cmd_list(cat)
    if args.cmd == "expert":
        zp, meta = build_expert(
            cat, args.allow_placeholder, "nested" if args.layout == "both" else args.layout
        )
        if zp is None:
            return 1
        with open(EXPERT_DIST / "expert-manifest.json", "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)
            f.write("\n")
        return 0
    if args.cmd == "build":
        if not targets:
            sys.exit("build requires <skill|--all>")
        return cmd_build(
            cat, targets, Path(args.out) if args.out else None, not args.no_validate, args.layout
        )
    if args.cmd == "validate":
        return cmd_validate(cat, targets)
    if args.cmd == "sheet":
        return cmd_sheet(cat)
    return cmd_clean()


if __name__ == "__main__":
    sys.exit(main())
