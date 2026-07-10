# SKILL 文档审查与修复记录

> 审查对象：`skills-engineering/` 下 9 个 SKILL 的 `SKILL.md` / `AGENT-BRIEF.md` / `OUT-OF-SCOPE.md` 三层文档
> 审查时间：2026-07-10
> 修复时间：2026-07-10
> 配套文档：[../README.md](../README.md)

## 1. 修复概览

| # | 优先级 | 问题 | 修复动作 | 状态 |
|---|--------|------|----------|------|
| F1 | P1 | `docs/` 缺 `plan-grill.md` 与 `cross-model-review.md` | 新建两份人类可读使用文档 | ✅ |
| F2 | P1 | `plan-grill` 的 `plan-reviews recall` 来源不明 | SKILL.md 澄清为 `plan-reviews` 工具 CLI，并补 build 步骤 | ✅ |
| F3 | P2 | `rule_index.md` 的 GR 命名空间漏登 GR-011/012/013 | 在 GR 表补 3 行 + GR-009 空缺说明 | ✅ |
| F4 | P2 | 跨 skill 相对链接（cognitive-expansion / logical-reasoning → ios-engineer）独立同步会断 | 两处加同步依赖声明 | ✅ |
| F5 | P3 | `auto-code-review` 入口未说明配置来源 | SKILL.md 补配置来源与"不随 sync 分发"提示 | ✅ |
| F6 | P3 | `cross-model-review` / `plan-grill` 的 `examples/` 未被 SKILL.md 引用 | 两处 SKILL.md 补 `examples/` 引用 | ✅ |
| F7 | P3 | `ROUTE-019` 退役注释 | 核实已记录在 `rule_index.md` 退役表，**无需新增** | ✅（已具备） |
| F8 | P3 | frontmatter 字段不统一（仅 ios 有 locale） | 为其余 8 个单语 skill 补齐 `locale` / `supported_locales`，统一为四字段 frontmatter | ✅ |

## 2. 逐项修复详情

### F1 — 补齐 `docs/` 缺失文档

- 新建 `docs/plan-grill.md`：概述、与 problem-analysis / cross-model-review 衔接、触发条件、PG-000~006 规则、工作流程、运行前置依赖（`plan-reviews` 工具 build/recall）、PLAN.md 模板、跳过条件、示例链接、常见问题。
- 新建 `docs/cross-model-review.md`：概述、前置、触发/跳过、CMR-001~005 规则、工作流程、三 adapter 只读命令表、安全规则、与 auto-code-review 区别、示例链接、常见问题。
- 对齐现有 `docs/auto-code-review.md` / `docs/ios-engineer.md` 的「概述 / 何时触发 / 工作流程 / 常见问题」结构。

### F2 — 澄清 `plan-reviews recall` 来源

文件：`plan-grill/SKILL.md`（PG-006）

```diff
- 自动或显式进入盘问后，在第一个问题前 best-effort 调用 `plan-reviews recall`
+ 自动或显式进入盘问后，在第一个问题前 best-effort 调用 `plan-reviews recall`
+ （即 `node skills-engineering/plan-reviews/dist/cli.js recall`，
+   需先在 `plan-reviews/` 执行 `npm run build` 生成 `dist/`）
```

详规 `plan-grill/references/plan_grill.md` 本已展开该命令，此改动让「强制入口」SKILL.md 自身也自洽，避免只读入口的人误以为存在独立 `plan-reviews` 命令。

### F3 — 补全 GR 命名空间登记

文件：`ios-engineer/references/rule_index.md`（GR-NNN 表）

在 `GR-010` 后新增：

| ID | Status | 摘要 | Skill 位置 |
|----|--------|------|------------|
| GR-011 | active | 反幻觉接地 | epistemic-integrity/references/epistemic_integrity.md |
| GR-012 | active | 验证方法论 | 同上 |
| GR-013 | active | 求真方法边界 | 同上 |

并加注：`GR-009` 故意未分配（编号可有空洞）；`GR-001~008` 由 engineering-discipline 承载，`GR-010` 由 logical-reasoning 承载，`GR-011~013` 由 epistemic-integrity 承载。新增全局规则须在此表登记并同步各 global skill 的 SKILL.md，避免跨 skill ID 冲突。

> 说明：`validate_rule_ids.sh` 当前只断言 ios-engineer 内部 ID 双向一致；GR 跨 skill 登记目前靠人工约定。本次把 GR-011/012/013 显式登记，堵住"命名空间分散在 3 个 skill、易撞号"的隐患。

### F4 — 跨 skill 相对链接同步依赖声明

- `cognitive-expansion/SKILL.md` 强制入口新增：本 skill 通过 `../ios-engineer/references/cognitive_adversary_mode.md` 引用 ios；同步到各端时需确保 `ios-engineer` 也同步到同层 skills 目录，否则链接失效。
- `logical-reasoning/SKILL.md` 强制入口新增相同声明。

> 背景：`sync-skills.sh` 默认同步所有含 SKILL.md 的目录，同根下可解析；但若用户只同步单 skill（如仅 SYNC 单端 + 只装 cognitive-expansion），链接即断。声明把该隐性依赖显性化。

### F5 — `auto-code-review` 配置来源提示

文件：`auto-code-review/SKILL.md` 强制入口新增：运行前置依赖（不随 skill 同步包分发，需宿主环境另行提供）为 `env/review.json`（模板 `env/review.json.example`）、项目内 `.auto-review-config.json`、`AUTO_REVIEW_*` 环境变量，并指向 `AGENT-BRIEF.md` 与 `docs/auto-code-review.md`。

### F6 — `examples/` 目录引用

- `cross-model-review/SKILL.md`：补「登录限流场景完整运行样例见 `examples/regression-login-rate-limit.md`」。
- `plan-grill/SKILL.md`：补「计划示例见 `examples/plan-example-login-rate-limit.md`」。

### F7 — `ROUTE-019` 退役注释（核实已具备）

复查发现 `rule_index.md` 退役表已记录：`ROUTE-019` retired，原因"与 ROUTE-018 真重复"，替代 `ROUTE-018`，提案 `20260508-154338-retire-route-019-merge-into-018`。治理已到位，**未重复添加**。

### F8 — frontmatter 统一（已统一）

将 9 个 skill 的 frontmatter 统一为相同的四字段结构：`name` / `description` / `locale` / `supported_locales`。

- `ios-engineer`（唯一多语言 skill，含 `i18n/en-US/references/` 镜像）：`locale: auto` + `supported_locales: [zh-CN, en-US]`（保持原值）。
- 其余 8 个单语 skill：`locale: zh-CN` + `supported_locales: [zh-CN]`（本次新补齐）。
- 语义：多语言 skill 用 `auto` 表示可跟随用户切换镜像；单语 skill 固定 `zh-CN`。`supported_locales` 显式声明该 skill 实际维护的语言集，便于加载器 / 机械校验识别「单语 vs 多语」，也消除了原先只有 ios 有该字段、其余无的不一致。
- 涉及文件（8 个，各新增 2 行）：`cognitive-expansion`、`auto-code-review`、`cross-model-review`、`engineering-discipline`、`epistemic-integrity`、`logical-reasoning`、`plan-grill`、`problem-analysis` 的 `SKILL.md` frontmatter。

## 3. 未改动但已确认无问题的项

- **所有 SKILL.md 引用的 `references/*.md` 均真实存在**：已逐一验证 `cognitive_expansion.md`、`auto_code_review.md`、`cross_model_review.md`、`engineering_discipline.md`、`epistemic_integrity.md`、`logical_reasoning.md`、`plan_grill.md`、`problem_analysis.md`、`cognitive_adversary_mode.md` 均存在，无断链。
- **外部脚本/模板真实存在**：`scripts/detect-review-clis.sh`、`env/review.json.example` 均核实存在。
- **OUT-OF-SCOPE 边界清晰**：9 个 skill 的 OUT-OF-SCOPE 均用 upfront / inward / outward / Tier 分层划清与相邻 skill 的边界，未发现职责重叠漏洞。
- **强制入口一致性**：所有 skill 均规定"完整阅读 references 全文，不以 preamble / Cursor 摘要代替"，规则漂移防护到位。

## 4. 验证建议

修复后建议执行以下校验（不强制，供提交前确认）：

```bash
# 1. ios-engineer 规则 ID 双向一致性（含新增 GR-011/012/013 登记）
bash ios-engineer/scripts/validate_rule_ids.sh

# 2. 全量演进基础校验（12 类）
bash ios-engineer/scripts/validate_skill_evolution.sh

# 3. 同步 dry-run，确认新增 docs/examples 引用不影响同步包
./scripts/sync-skills.sh --dry-run

# 4. 同步结果校验（确认各端缓存只有 SKILL.md + references/）
./scripts/verify-sync.sh

# 5. frontmatter 四字段一致性（9 个 SKILL.md 均含 name/description/locale/supported_locales）
for f in $(find . -name SKILL.md -maxdepth 2); do
  grep -q '^supported_locales:' "$f" || echo "MISSING supported_locales: $f"
done
```

> 注意：`docs/` 不参与 Agent 运行时加载（README 明确定义），新增两份 doc 不会进入 `~/.claude/skills/` 等同步包；它们的受众是阅读源码的人类维护者。

## 5. 后续可选项（非本次修复范围）

- 若希望 GR 跨 skill 编号冲突能被机械校验，可扩展 `validate_rule_ids.sh` 增加对 `engineering-discipline` / `logical-reasoning` / `epistemic-integrity` 三处 GR 登记的双向一致性断言。
- `plan-grill` / `cross-model-review` 的 `examples/` 目前各 1 个示例，后续可按需补充更多场景样本。
