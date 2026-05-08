# Skill Evolution Proposal

## Metadata
- Proposal ID: 20260508-113308-bootstrap-scenario-specs
- Created At: 2026-05-08 11:33:08 +0800
- Active Version At Creation: v42

## 问题信号
- SkillOps 闭环的后半段（提案 → 验证 → 晋升）已成型，但前半段「真实任务命中观测」缺失。
- `references/validation_scenarios.md` 6 个固定场景目前只有散文形式，无机器可读规格——人工评分时各自解读，新场景定义易漂移、跨提案验证记录不可比。
- 后续 rule-ID / usage ledger / 自动评分器都需要一份稳定的回归基线，而当前没有。

## 变更类型
- 新增能力（不替代任何旧规则；散文版 `validation_scenarios.md` 仍作为人读权威）

## 变更内容
- 修改文件：
  - 新增目录 `evolution/scenarios/` 与 6 份 JSON：`layout.json`、`parameter-pass-through.json`、`concurrency.json`、`review.json`、`migration.json`、`mcp-control.json`
  - 新增 `scripts/validate_scenario_specs.sh`（结构校验：JSON 合法、必填字段、id 与文件名一致、id 落在 6 个固定 slug 内、`primary_refs` 路径存在、`expected_hits` 与 `failure_signals` 的 `key` 在文件内唯一、6 个 slug 全部覆盖）
  - `scripts/validate_skill_evolution.sh` 插入新步骤 `[6/10] Validate scenario specs`，原 [6-9] 顺延为 [7-10]
  - `references/validation_scenarios.md` 顶部加指针段，说明结构化定义沉淀在 `evolution/scenarios/*.json`，新增/调整场景须先改 JSON 后同步本文
  - `references/self_evolution.md` 第 4 节追加一句，明确 `record_validation_scenario.sh` 的 `scenario` 字段必须落在规格 id 集合内
- 替代或合并旧规则：无；本提案不动任何业务规则、不改 `record_validation_scenario.sh` 契约

## 预期收益
- 让每次 skill 改动都能照同一把尺子量：`expected_hits` / `failure_signals` 字段化后，跨提案的验证记录第一次具备可比性
- 为后续可选的自动评分器提供机器可读输入；为 rule-ID 与 usage ledger 步骤提供受控回归基线
- 防止 6 个场景定义随时间漂移：伞形校验会断言 6 个固定 slug 全部存在、每个字段齐全

## 验证
- 结构校验：`bash scripts/validate_scenario_specs.sh` 6 份 JSON 全过；`bash scripts/validate_skill_evolution.sh` 10 步全绿
- 场景回放：6 个场景人工自评分，按现有 `scripts/record_validation_scenario.sh` 写入；预期全 pass
- 残留风险：
  - 本步未在 `record_validation_scenario.sh` 加运行时 id 校验（避免改既有脚本契约）；后续 grader 落地时统一加
  - JSON 中 `expected_hits` / `failure_signals` 由人翻译散文得出，存在主观误差；用人工反向验证（uniqueness 校验）保护结构正确性，但语义层准确性要靠后续真实回放检验

## 状态
- promoted
