# Skill Evolution Proposal

## Metadata
- Proposal ID: 20260723-173058-cam-fields-preserve-format
- Created At: 2026-07-23 17:30:58 +0800
- Active Version At Creation: v73

## 问题信号
- `engineering-discipline` GR-004「多块合并」要求 CAM 激活时 `逻辑链`/`验证锚点` 字段并入 CAM 输出；但本 skill `cognitive_adversary_mode.md` 的「最终输出格式」与「执行要求」明确规定 Step 0–6 + `置信度` 字段不得合并或省略。
- 两者形成契约冲突（D4）：若不澄清，CAM 字段可能被「合并」掉，违反本 skill 的机械格式硬约束。需把 GR-004 的口径对齐为「不重复输出语义，但保留 CAM 机械格式」。

## 变更类型
- 修正表达（在 references/cognitive_adversary_mode.md 的「与工程技能的关系」段补一条协同条款，消除与 GR-004 的契约冲突）

## 变更内容
- 修改文件：`skills-engineering/ios-engineer/references/cognitive_adversary_mode.md`（仅「与工程技能的关系」段新增 1 行）。
- 新增内容：本模式的认知校准字段（Step 0–6 + `置信度`）已承载 `逻辑链`/`验证锚点` 的校准语义；CAM 激活时二者不另起独立块（见 engineering-discipline GR-004「多块合并」），但本模式字段仍须按「最终输出格式」原样输出、不得省略或并入其它块。
- 不替代或合并任何既有 GR 规则；`SKILL.md`、rule ID、usage ledger 均未变动。
- 该文变更是全局多 skill 协调修复（D1–D5）的一部分；同轮已同步 GR-004、plan-grill、cognitive-expansion 及各自的 en-US 镜像。

## 预期收益
- 消解 GR-004 与 CAM 详规的契约冲突，使「多块合并」与「CAM 机械格式」可共存。
- 明确 CAM 字段承载校准语义但不省略/不并入，避免后续实现把 CAM 字段错误合并掉。

## 验证
- 结构校验：`SKIP_SNAPSHOT_CONSISTENCY=1 bash scripts/validate_skill_proposal.sh evolution/proposals/20260723-173058-cam-fields-preserve-format.md` → 预期 status=validated（纯 references 文本澄清，不触碰 SKILL.md body 行为契约字面串）。
- 场景回放：不适用（无 body 规则字面串变更，无行为漂移风险）。
- 残留风险：无（仅补充协同说明，不改变任何字段输出要求，反而强化了 GR-004 要求的「不得省略」）。

## 状态
- ready_to_promote
