# Proposal: 合并组 A 四个认知/论证技能为 `cognitive-reasoning`

- 提案日期：2026-08-14
- 提案人：song（经 AI 助手执行）
- 状态：待审批

## 背景

组 A（论证/认知质量类）包含四个全局技能，职责同属"认知与论证质量"域，但物理分散为 4 个目录：

- `cognitive-calibration`（Tier 2 认知对手模式，CAM-001~005，平台无关真值 owner）
- `cognitive-expansion`（Tier 0/3 认知拓展，CE-001~013）
- `logical-reasoning`（单回复内论证质量，GR-010）
- `epistemic-integrity`（回复与外部世界接地，GR-011~013）

四个技能已通过 `depends_on`、preamble 托管块、`.agents/composition.md` 做了运行时协调与分层，但目录分散带来维护面与加载复杂度。

## 目标

将四个技能合并为单一技能 **`cognitive-reasoning`**（认知与论证纪律），保留全部规则 ID 不变（CAM-*/CE-*/GR-010/GR-011~013），不破坏任何回归校验（规则 ID 唯一性由 `validate-skill-behavior.sh` Check 2 校验，依赖 ID 而非目录名）。

## 影响面（需同步修改）

1. 新建 `cognitive-reasoning/`：
   - `SKILL.md`（统一入口：4 类纪律 + 强制入口 + 触发场景 + 规则索引）
   - `AGENT-BRIEF.md` / `OUT-OF-SCOPE.md`
   - `references/`：`cognitive_adversary_mode.md`（原 calibration）、`logical_reasoning.md`、`epistemic_integrity.md`、`cognitive_expansion.md`、`examples.md`、`rule_index.md`（合并全部 ID 元数据）
   - `i18n/en-US/references/`：上述 zh 文件的 en-US 镜像，**每个 zh reference 带 `<!-- sha256:... -->` 锚点**以满足 i18n 硬门
2. 删除旧目录：`cognitive-calibration` / `cognitive-expansion` / `logical-reasoning` / `epistemic-integrity`
3. `ios-engineer/SKILL.md`：`depends_on: [cognitive-calibration]` → `[cognitive-reasoning]`；镜像 `references/cognitive_adversary_mode.md` 指向新路径
4. `.agents/invocation.md` / `.agents/composition.md`：触发矩阵 / 层级表改指向 `cognitive-reasoning` 与规则 ID
5. `scripts/templates/agent-preamble.md.tmpl`：4 个 global 段合并为 1 个 `cognitive-reasoning` 段；`sync-manifest` 改为新 skill 名
6. `scripts/templates/`：删除 `logical-reasoning.mdc.tmpl` / `epistemic-integrity.mdc.tmpl` / `cognitive-expansion.mdc.tmpl`，新增 `cognitive-reasoning.mdc.tmpl`
7. `scripts/sync-agent-preamble.sh`：`sibling_skill_dir` 列表改为 `cognitive-reasoning`
8. `tests/test_en_us_mirror_sync.py`：路径断言改为 `cognitive-reasoning`
9. `README.md` 技能表：4 行合并为 1 行
10. `source-truth.json`：4 条合并为 1 条

## 校验

- `bash skills-engineering/scripts/validate-skill-behavior.sh`
- `python3 tests/test_en_us_mirror_sync.py`
- `bash skills-engineering/scripts/sync-agent-preamble.sh`（dry-run 校验）

## 风险与缓解

- **i18n 硬门**：合并后 `cognitive-reasoning` 保留 `supported_locales: [zh-CN, en-US]`，每个 zh reference 须带 `<!-- sha256:... -->` 锚点；en-US 镜像须逐文件存在。
- **ios-engineer 依赖闭包**：保留 `cam` 真实所有权在 `cognitive-reasoning/references/cognitive_adversary_mode.md`，`ios-engineer` 仅改 `depends_on` 与镜像 `mirror-of` 路径。
- **规则 ID 全球唯一**：合并后 rule_index.md 含 CAM/CE/GR-010/GR-011~013 全部 ID，无新增前缀，不与其他技能冲突。
