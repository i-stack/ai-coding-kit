# Skill Evolution Proposal

## Metadata
- Proposal ID: 20260508-162159-align-playbook-headings-with-route-017
- Created At: 2026-05-08 16:21:59 +0800
- Active Version At Creation: v53

## 问题信号
- v52 收紧了 [ROUTE-017] 剧本入口词，把 5 个剧本名改为描述性更强的长短语（"反复偶现 Crash 系统排查 / 性能专项 / 并发架构迁移 / 大型重构落地"），意在强化"长周期剧本"语义。
- 但 execution_playbooks.md 的 5 个剧本章节标题仍用 v52 之前的"做一次 X"风格和旧词："排查偶现 Crash / 做一次性能优化 / 做一次并发迁移 / 做一次大型重构"。
- ROUTE-017 说"先选 execution_playbooks.md **对应剧本**"——用户被路由到该 ref 后预期能按 ROUTE-017 的入口词字面找到剧本节，但落差如下：
  | ROUTE-017 入口词 | exec_playbooks.md 章节 | 落差 |
  |---|---|---|
  | 接手遗留页 | 接手遗留页面 | 小（SKILL.md 侧少"面"）|
  | 反复偶现 Crash 系统排查 | 排查偶现 Crash | 大 |
  | 性能专项 | 做一次性能优化 | 大 |
  | 并发架构迁移 | 做一次并发迁移 | 小（少"架构"）|
  | 大型重构落地 | 做一次大型重构 | 大 |
- 用户在 exec_playbooks.md 里搜"反复偶现 Crash 系统排查"或"大型重构落地"会找不到——UX 断裂。自进化触发信号「某条规则持续带来误导 / 过度展开」命中（过度展开：用户找不到精确剧本，会退回读整份 ref）。

## 变更类型
- 修正表达（保留 ROUTE-017 与 execution_playbooks.md 5 个剧本的身份与内容不变；只对齐两侧的剧本**名称**；额外修 SKILL.md 里 "接手遗留页"少"面"的小 typo）

## 变更内容
- 修改文件：
  - `references/execution_playbooks.md`：
    - TOC（L14-18）5 行全部重写为 v52 ROUTE-017 的入口词拼写。
    - 5 个 `## <剧本名>` 章节标题逐个 rename：
      - `## 排查偶现 Crash` → `## 反复偶现 Crash 系统排查`（L39）
      - `## 做一次性能优化` → `## 性能专项`（L58）
      - `## 做一次并发迁移` → `## 并发架构迁移`（L78）
      - `## 做一次大型重构` → `## 大型重构落地`（L97）
      - `## 接手遗留页面`（L20）不动——保留更正确的"页面"拼写
    - 剧本正文（步骤、场景、步数）一律**不改**——本提案只改节标题。
  - `SKILL.md` 第 51 行 [ROUTE-017]："接手遗留页" → "接手遗留页面"（+1 字，消除与 exec_playbooks.md 的小落差）。
- 不修改：
  - rule_index.md 的 ROUTE-017 摘要仍是 "复杂任务剧本 → execution_playbooks.md"，不列剧本名，不需要同步。
  - 5 个剧本的 body 内容（步骤、场景、引用的其它 ref）全部不动。
  - 任何其它 ROUTE / IR / SYM / OUT。
- 替代或合并旧规则：无（ROUTE-017 ID 沿用）

## 预期收益
- ROUTE-017 入口词与 execution_playbooks.md 章节名全部字面一致；用户被路由后能直接搜到剧本。
- 剧本名风格由旧"做一次 X"改为 v52 引入的描述性长短语，和 ROUTE-017 入口条件"跨多日 / 跨多模块 / 长周期"的语义强度更一致。
- 不再引入 ROUTE-017 ↔ execution_playbooks.md 的潜在 naming drift。

## 验证
- 结构校验：
  - `bash scripts/validate_rule_ids.sh` 保持通过（本提案不动任何 ID）。
  - `SKIP_SNAPSHOT_CONSISTENCY=1 bash scripts/validate_skill_evolution.sh` 12 步全绿。其中 [3/12] `Validate referenced files exist` 不关心章节锚点；[5/12] `Validate internal markdown links` 只查 `.md` 路径，不查 `#章节` 锚点，所以章节 rename 不会把任何现有引用打挂。
  - 反向验证：故意留一个旧剧本名（如保留 `## 排查偶现 Crash`），不会触发任何校验失败——因为 validate 不做"剧本名与 ROUTE-017 对齐"的断言。这说明：**本提案的收益完全在用户 UX 层，不由脚本保护**。
- 跨文件引用检查（已手工执行）：
  - `grep -nE '做一次性能优化|做一次并发迁移|做一次大型重构' ios-engineer/references/*.md ios-engineer/SKILL.md` 返回空——旧剧本名在其它地方无引用。
  - `grep -nE '排查偶现 Crash' ios-engineer/references/*.md ios-engineer/SKILL.md` 返回空。
- 场景回放：
  - 6 个固定场景（layout / parameter-pass-through / concurrency / review / migration / mcp-control）都不是剧本场景，不涉及 execution_playbooks.md；预期全部 pass。
- 残留风险：
  - 剧本内容（步骤、场景）风格仍停留在 pre-v52 的描述视角——比如"大型重构落地"剧本节里的小节仍可能用"做一次"语调。本提案不动 body，后续如果要把整份剧本文调升级，再起独立提案。
  - 本次改的是 ref 内部章节锚点；若有历史外部文档（例如团队 wiki）链到 `execution_playbooks.md#排查偶现-crash`，那些外链会挂掉。repo 内没有这种外链，但 repo 外无法保证。影响面窄，可接受。

## 状态
- promoted
