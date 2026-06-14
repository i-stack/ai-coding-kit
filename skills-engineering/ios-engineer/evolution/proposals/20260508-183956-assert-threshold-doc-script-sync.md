# Skill Evolution Proposal

## Metadata
- Proposal ID: 20260508-183956-assert-threshold-doc-script-sync
- Created At: 2026-05-08 18:39:56 +0800
- Active Version At Creation: v59

## 问题信号
- 提案 D（v58）把 summarize 阈值显式写入 usage_ledger.md 第 8 节表格，但缺自动化断言：若有人改 scripts/summarize_usage_ledger.sh L69-L72 的常量却忘改文档，summarize 输出与文档解释会静默漂移。
- 提案 D 残留风险段已留作后续提案，本提案兑现。

## 变更类型
- 新增能力（在 validate_skill_evolution.sh 加新断言步骤；不动 ID 集合，不改文档表格内容）

## 变更内容
- 修改文件：scripts/validate_skill_evolution.sh
- 在原 [10/12] 后插入新一步「Validate threshold doc/script sync」（步骤号顺延，[11→12]，[12→13]，总步数从 12 改为 13）：
  - 解析 scripts/summarize_usage_ledger.sh 中的 4 个 `*_THRESHOLD = <value>` 常量
  - 解析 references/usage_ledger.md 第 8 节表格中的 4 个对应行 `| <CONST_NAME> | <value> |`
  - 双向比对 4 对（常量名 / 数值都必须一致）
  - 任一对不一致 → 非零退出，打印漂移位置
- 修改文件：references/rule_index.md
- 在「跨文件共享概念索引」表追加新行：`提案候选信号阈值 | scripts/summarize_usage_ledger.sh L69-L72 | usage_ledger.md 第 8 节 + scripts/validate_skill_evolution.sh `[11/13]` 步 | 改任一侧必须同步另一侧；validate_skill_evolution.sh 会自动断言不一致`。
- 替代或合并旧规则：无；本提案是提案 D 的"自动化断言"补丁。

## 预期收益
- 阈值文档与脚本常量永不漂移。
- cross-ref 索引表多一条受自动化保护的"跨文件共享概念"，落实"先建索引，再加自动化"的演进节奏。

## 验证
- 结构校验：scripts/validate_skill_evolution.sh + scripts/validate_rule_ids.sh + scripts/validate_scenario_specs.sh。
- 场景回放：6 场景结构校验；本提案不改 SKILL 输出行为。
- 残留风险：若 summarize 脚本未来扩展第 5 个阈值，本断言不会自动覆盖；建议在脚本顶部加注释 "新增阈值常量需同步 usage_ledger.md 第 8 节 + validate_skill_evolution.sh 解析正则"。

## 状态
- promoted
