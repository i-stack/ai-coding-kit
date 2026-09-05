#!/usr/bin/env bash
# =============================================================================
# suggest-skill-proposals.sh — Skill 自我改进闭环 (观测 → 建议 → 人工审批)
#
# 对齐 Hermes Agent 的「学习循环」思路，但落地为本仓库既有的「受控演进」闸门：
#   1. 读取 summarize-usage-ledger.sh --json 产出的 proposal_signals
#   2. 对每个超过阈值的信号，自动生成一份 DRAFT proposal（仅 draft，不自动晋升）
#   3. 用注册表去重，避免对同一信号反复建草稿
#   4. 打印一份「建议清单」供人工 review / 审批
#
# 设计原则：
#   - 只产出 draft，绝不自动 approve / promote（受控演进不被绕过）
#   - 幂等：同一信号重复运行不会新建重复草稿
#   - 只读 ledger，不改变 active 版本；仅落盘 draft proposal 与去重 registry
#
# 用法:
#   bash scripts/suggest-skill-proposals.sh            # 生成草稿并打印建议
#   bash scripts/suggest-skill-proposals.sh --dry-run  # 只打印会生成什么，不落盘
#   bash scripts/suggest-skill-proposals.sh --json     # 机器可读输出
# =============================================================================
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

DRY_RUN=0
EMIT_JSON=0
while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run) DRY_RUN=1 ;;
    --json) EMIT_JSON=1 ;;
    -h|--help)
      grep '^#' "$0" | sed 's/^# \{0,1\}//'
      exit 0
      ;;
    *) echo "Unknown arg: $1" >&2; exit 1 ;;
  esac
  shift
done

SUMMARIZE="scripts/summarize-usage-ledger.sh"
PROPOSALS_DIR="evolution/proposals"
REGISTRY="evolution/.auto_proposal_registry.json"
mkdir -p "$PROPOSALS_DIR"

# 读取信号
if [ ! -f "$SUMMARIZE" ]; then
  echo "summarizer not found: $SUMMARIZE" >&2
  exit 1
fi

SIGNALS_JSON="$(bash "$SUMMARIZE" --json 2>/dev/null || true)"
if [ -z "$SIGNALS_JSON" ]; then
  echo "No ledger summary produced (ledger empty or missing)."
  exit 0
fi

# 用 python3 解析信号并生成草稿（python3 与 sync subtree 一致，JSON 处理更稳）
python3 - "$SIGNALS_JSON" "$PROPOSALS_DIR" "$REGISTRY" "$DRY_RUN" "$EMIT_JSON" <<'PY'
import json, sys, os, re, datetime

signals_raw, proposals_dir, registry_path, dry_run_s, emit_json_s = sys.argv[1:6]
dry_run = dry_run_s == "1"
emit_json = emit_json_s == "1"

try:
    payload = json.loads(signals_raw)
except Exception:
    # summarizer may emit a plain-text "no entries" message when the ledger is
    # empty (not valid JSON) — treat that as "no signals" rather than failing.
    msg = "No proposal signals (ledger empty or summarizer produced no JSON)."
    print(msg if not emit_json else json.dumps({"generated": [], "skipped": [], "message": msg}, indent=2, ensure_ascii=False))
    sys.exit(0)

signals = payload.get("proposal_signals", []) or []
if not signals:
    msg = "No proposal signals above threshold — skill is currently healthy."
    print(msg if not emit_json else json.dumps({"generated": [], "skipped": [], "message": msg}, indent=2, ensure_ascii=False))
    sys.exit(0)

# 加载注册表（signal_key -> {proposal_id, status}）
registry = {}
if os.path.isfile(registry_path):
    try:
        with open(registry_path, encoding="utf-8") as f:
            registry = json.load(f)
    except Exception:
        registry = {}

def signal_key(s):
    kind = s.get("kind", "unknown")
    if kind == "missed_rule":
        return f"missed_rule:{s.get('rule_id','')}"
    if kind == "task_type_other":
        return "task_type_other"
    if kind == "deviation":
        return f"deviation:{s.get('text','')[:60]}"
    if kind == "tool_divergence":
        return f"tool_divergence:{s.get('rule_id','')}"
    return f"{kind}:{s.get('rule_id', s.get('text', ''))}"

def slugify(s):
    kind = s.get("kind", "x")
    key = signal_key(s)
    tail = re.sub(r'[^A-Za-z0-9]+', '-', key.split(':',1)[-1])[:40].strip('-')
    return f"auto-{kind}-{tail}"

def change_type_for(s):
    kind = s.get("kind")
    if kind == "task_type_other":
        return "新增能力"
    if kind == "tool_divergence":
        return "修正表达 / 一致性"
    return "修正表达"

generated = []
skipped = []

for s in signals:
    key = signal_key(s)
    # 去重：已注册且目标草稿仍存在且未 rejected
    if key in registry:
        pid = registry[key].get("proposal_id")
        pstat = registry[key].get("status")
        if pid and os.path.isfile(os.path.join(proposals_dir, pid + ".md")) and pstat != "rejected":
            skipped.append({"signal_key": key, "reason": f"already drafted as {pid} (status={pstat})"})
            continue
    if dry_run:
        generated.append({"signal_key": key, "slug": slugify(s), "note": s.get("note",""), "dry_run": True})
        continue

    # 生成草稿
    now = datetime.datetime.now(datetime.timezone.utc)
    ts = now.strftime("%Y%m%d-%H%M%S")
    slug = slugify(s)
    pid = f"{ts}-{slug}"
    note = s.get("note", "").strip()
    ctype = change_type_for(s)

    # 针对 missed_rule / tool_divergence 给出更具体的变更内容
    if s.get("kind") == "missed_rule":
        rid = s.get("rule_id", "")
        change = (f"1. 复查 `{rid}` 在 `references/rule_index.md` 的 active 定义与对应 ref 文件。\n"
                  f"2. 提升该规则的表达清晰度或路由触发条件，使 Agent 在相关任务更易命中。\n"
                  f"3. 若规则已过时，考虑按「退役规则」流程处理。")
        benefit = f"降低 `{rid}` 的 missed 次数（当前累计 {s.get('miss_count','?')} 次），提升规则命中率。"
    elif s.get("kind") == "tool_divergence":
        d = s.get("data", {}) or {}
        rid = s.get("rule_id", "")
        change = (f"1. 对比 `{rid}` 在 {d.get('high_tool','?')}（{d.get('high_rate','?')}%）与 "
                  f"{d.get('low_tool','?')}（{d.get('low_rate','?')}%）两端的命中差异。\n"
                  f"2. 检查两端 preamble / 注入语境是否一致，统一触发表述。")
        benefit = f"收敛 `{rid}` 的工具间命中率差异（当前差 {d.get('diff_pct','?')}%）。"
    elif s.get("kind") == "task_type_other":
        change = ("1. 在 `evolution/scenarios/` 与 validation_scenarios 中增补 task_type=other 的高频模式。\n"
                  "2. 若形成稳定类别，考虑在 SKILL.md 症状导航中新增入口。")
        benefit = "覆盖当前 12 选 1 之外的高频任务类型，减少 audit 落入 other。"
    else:  # deviation
        change = (f"1. 针对稳定失败模式「{s.get('text','')}」在相关 ref 增加更明确的检查项。\n"
                  "2. 必要时补充回归场景固化该检查。")
        benefit = f"消除「{s.get('text','')}」这类稳定失败模式（累计 {s.get('count','?')} 次）。"

    proposal = f"""# 自动生成的演进提案（观测驱动）

## Metadata
- **Proposal ID**: {pid}
- **Title**: 观测驱动 — {s.get('kind','')} 信号
- **Author**: skill-self-improvement-loop (auto)
- **Date**: {now.strftime('%Y-%m-%d %H:%M:%S %z')}
- **Active Version At Creation**: (待填充 — 运行 create-skill-proposal.sh 风格元数据)
- **Status**: draft
- **Auto-generated**: true
- **Signal key**: {key}

## 问题信号
- 来源：usage ledger 汇总信号（summarize-usage-ledger.sh）。
- {note}

## 变更类型
- {ctype}

## 变更内容
{change}

## 预期收益
- {benefit}

## 验证
- 结构校验：`bash ios-engineer/scripts/validate-skill-evolution.sh`
- 场景回放：必要时 `bash ios-engineer/scripts/validate-skill-proposal.sh evolution/proposals/{pid}.md`
- 残留风险：本提案为自动草稿，需人工 review 后走 approve → promote 流程，未审批前不生效。

## 状态
- draft
"""
    ppath = os.path.join(proposals_dir, pid + ".md")
    with open(ppath, "w", encoding="utf-8") as f:
        f.write(proposal)
    registry[key] = {"proposal_id": pid, "status": "draft", "created_at": now.isoformat()}
    generated.append({"signal_key": key, "proposal_id": pid, "note": note})

# 写回注册表
if not dry_run and generated:
    with open(registry_path, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)
        f.write("\n")

if emit_json:
    print(json.dumps({"generated": generated, "skipped": skipped}, indent=2, ensure_ascii=False))
    sys.exit(0)

if dry_run:
    print("== [dry-run] 以下信号将生成草稿（未落盘） ==")
else:
    print("== 已生成草稿提案（仅 draft，需人工审批） ==")
for g in generated:
    if dry_run:
        print(f"  • {g['signal_key']}  ->  slug={g['slug']}")
        print(f"      {g['note']}")
    else:
        print(f"  • {g['proposal_id']}")
        print(f"      {g['note']}")
if skipped:
    print("")
    print("== 已跳过（去重：已有未驳回草稿） ==")
    for k in skipped:
        print(f"  • {k['signal_key']}  ({k['reason']})")
print("")
print(f"共生成 {len(generated)} 份草稿，跳过 {len(skipped)} 份。运行 create-skill-proposal.sh / approve 流程前请先 review。")
PY
