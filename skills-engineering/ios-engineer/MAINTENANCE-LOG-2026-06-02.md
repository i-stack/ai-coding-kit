# ios-engineer SKILL 维护日志 · 2026-06-02

> 一次性 SkillOps 维护记录。本文是后置审计报告，不是规则；不归入 references/ 也不进入 evolution/ 提案流。

## 背景

用户对 `skills-engineering/ios-engineer/references/` 全部 28 份 ref + `SKILL.md` 做一次横向审计，目标：
1. 识别真重复（同一规则在多文件被完整定义且无 single-source-of-truth 声明），删除冗余
2. 识别真错误（引用 deprecated/retired ID、机械锚点字符层失配等）
3. 识别冲突项与域适应性问题
4. 在执行修复时一并移除 deprecated 残留

## 分析阶段发现

### A. 真错误（必改）

| 编号 | 位置 | 问题 |
|---|---|---|
| E1 | `references/rule_index.md` L88 | OUT-002 摘要列写 "触发条件见 IR-004"，但 IR-004 在同文件 L24/L29/L123 已标 `deprecated → GR-004`。`validate_rule_ids.sh` 只校验 ID 集合，不捕获摘要列散文引用，会长期漂移 |
| E2 | `references/rule_index.md` L141 | `SIGNALS[“GR-010”]` 用 Unicode fancy quotes（U+201C/U+201D），同表其它行均为 ASCII `"`，且 `scripts/lint_hit_rules.sh` L85 实际写的是 ASCII。"段标题改名必须同步 lint_hit_rules.sh SIGNALS 表"这层 anchor 在字符层失配 |

### B. 真重复（建议收口）

| 编号 | 概念 | Owner（含识别条件） | 重复位置 |
|---|---|---|---|
| D1 | 万能 NetworkManager 反模式 | `anti_patterns.md` §1 | `architecture_and_network.md` "常见反模式"；`networking_patterns.md` "常见反模式" |
| D2 | 错误透传 UI / localizedDescription | `anti_patterns.md` §4 | `architecture_and_network.md` "常见反模式"；`domain_modeling.md` "常见反模式" |
| D3 | decision_records.md 触发条件 | — | L12-18 "必须记录的场景"（按业务场景列举）与 L86-90 "简化判断规则"（按结构变化列举）两节并存且无锁定关系 |

### C. 域适应性问题

| 编号 | 位置 | 问题 |
|---|---|---|
| S1 | `references/layout_and_ui.md` L80-148 "UITableView 发送消息置顶" | 整段是聊天 App 业务模板，代码直接引用 `MainContentViewCollection.pinMessageToTop` 等项目内符号；ios-engineer 是通用 iOS skill，业务模板嵌入会拖累通用 ref，且项目内类改名后这份模板无 owner 维护 |

### D. 假重复（已合理分工，无需改）

下列内容看似重复，但 `rule_index.md "跨文件共享概念索引"` L132-143 或 ref 文件内已显式声明 owner，分工正确：

- 残留风险声明（owner: GR-008，机械锚点冗余）
- 版本前提声明（owner: IR-006）
- 四段式输出（owner: GR-004）
- 请求链路骨架（owner: architecture_and_network.md "基础结构"）
- ErrorModel 6 层（owner: domain_modeling.md）
- 性能取证工具（owner: observability_logging.md）
- 散落 Task / DispatchQueue.main.async / @unchecked Sendable 反模式（owner: anti_patterns.md §2）
- 现象即根因 / 补丁式修复（owner: anti_patterns.md §6）
- 状态分层 vs 建模分层（互相引用，正交关系已澄清）
- 评估类 vs 实施类架构（互锁声明：architecture_analysis.md L12 vs architecture_and_network.md L12）

## 执行阶段变更

### P0：rule_index.md 直接错误修复

- L88: `IR-004` → `GR-004`
- L141: fancy quotes → ASCII（整行 4 处）

### P0+：deprecated 残留清理（用户在执行过程中追加的要求）

**rule_index.md**：
- 主表删除 7 条 `deprecated` IR 行（IR-002/003/004/005/007/008/010）
- 退役记录删除 7 条 `deprecated` 行（保留 2 条 `retired`：IR-009、ROUTE-019）
- L15 编号空洞示例 `IR-002 → IR-007` → `IR-001 → IR-006`
- L140 跨文件索引 `IR-002 落点` → `GR-002 落点`

**active 文档内 inline 引用统一改为 GR-XXX**：
- `SKILL.md` L13 `IR-004 / IR-006 / IR-008 / IR-010` → `GR-004 / IR-006 / GR-008 / GR-010`
- `references/examples.md` L19 `(履行 IR-008)` → `(履行 GR-008)`
- `references/code_templates.md` L9 同上
- `references/review_checklists.md` L103 `IR-008 在 findings-first 骨架里的落点` → `GR-008 ...`
- `references/validation_scenarios.md` L87 `(IR-008)` → `(GR-008)`；L167 示例 `IR-005` → `IR-006`
- `references/root_cause_enforcement.md` L52 `IR-002 落点` → `GR-002 落点`
- `references/usage_ledger.md` L18-19/L34/L50/L60-61/L82-83 6 处 IR-005 示例 → IR-006；L178 兼容描述 `IR-001 / IR-002 / IR-004 / IR-006 / IR-008` → `IR-001 / GR-002 / GR-004 / IR-006 / GR-008 / GR-010`

**scripts/lint_hit_rules.sh**：
- L12-13 帮助文本中 deprecated 兼容说明删除
- 删除 IR-002 / IR-004 / IR-008 / IR-010 四个委托 SIGNALS 条目

### P1：真重复收口

- **P1.1** `architecture_and_network.md` 与 `networking_patterns.md` 的 NetworkManager 反模式删除，改为 `> 见 anti_patterns.md §1 "万能 Manager"`
- **P1.2** `architecture_and_network.md` 与 `domain_modeling.md` 的 localizedDescription 反模式删除，改为 `> 见 anti_patterns.md §4 "错误透传到 UI"`
- **P1.3** `decision_records.md` "简化判断规则"节上方加锁定句：`本节是上文 "必须记录的场景" 的结构化判定版本：上文按业务场景列举，本节按结构变化判定；命中任一条即触发`

### P2：业务模板归属

第一轮决策：把 `layout_and_ui.md` 中 "UITableView 发送消息置顶" 抽离到独立 ref `chat_list_pin_to_top.md`（方案 A）。

第二轮决策（用户裁决）：业务模板不应保留在 ios-engineer 内：
- 删除 `references/chat_list_pin_to_top.md`
- `layout_and_ui.md` 中"UITableView 发送消息置顶"整节移除（含原 L80-148 业务模板 + 之前 P2 临时保留的引用桥），审查清单回归 5 条通用项

## 校验结果

所有结构校验通过：

```
[1/13] Validate YAML structure                          OK
[2/13] Validate SKILL.md size                           OK
[3/13] Validate referenced files exist                  OK
[4/13] Validate layering guardrails                     OK
[5/13] Validate internal markdown links                 OK
[6/13] Validate scenario specs                          OK (6 files, 6 slugs)
[7/13] Validate rule IDs                                OK (34 in SKILL.md, 41 in rule_index.md, 41 active)
[8/13] Validate usage ledger                            OK (39 entries, 41 active rule IDs)
[9/13] Validate no orphan references                    OK
[10/13] Validate unique ownership + retired words       OK
[11/13] Validate threshold doc/script sync              OK
[12/13] Validate snapshot consistency with v70          DRIFT (预期)
audit_ref_freshness.sh                                  FRESH=28 STALE=0 CRITICAL=0
```

## 未覆盖

- `evolution/` 历史归档（proposals / validations / approvals / history）含 deprecated IR 字符串 — 历史快照按设计**不应追溯改动**，保留
- `evolution/active_version.json` 的 `notes` 字段描述了迁移历史 — 是事实陈述，保留
- `evolution/usage/usage.jsonl` 历史 audit 数据中含 deprecated IR — 历史观测不改

## 残留风险

1. **快照漂移 v70**：当前 working tree 与 active 版本 v70 不一致，`validate_skill_evolution.sh [12/13]` 会一直报漂移。这是预期反馈，提示应走 [self_evolution.md "自进化闭环"](references/self_evolution.md) 完整流程：`create_skill_proposal.sh` → `validate_skill_proposal.sh` → `approve_skill_promotion.sh` → `promote_skill_evolution.sh`，归档为新版本（v71+）。
2. **失去 deprecated 历史护栏**：`rule_index.md` 删除 deprecated 行后，`validate_rule_ids.sh` L121 的 retired/deprecated 拦截集合从含 IR-002~008/010 缩到只剩 IR-009 / ROUTE-019。若将来又有规则被 deprecate 不及时清理，护栏不会触发警报。可考虑增设一条 lint 规则禁止 SKILL/ref 出现"已退役命名空间"的 IR 字符串，但属于扩张校验，不在本轮范围。
3. **业务模板归属丢失**：删除 `chat_list_pin_to_top.md` 后，原 "UITableView 发送消息置顶" 模板内容不再保存在本 skill 内。如有需要，应放回项目内的设计文档（如 `~/Desktop/iOS/<project>/docs/`）。本次维护不负责异地归档。

## 补丁记录 · 2026-06-02（用户回查后修正）

用户对前面维护结果做了第二轮审计，指出两个未被自检捕获的问题，已就地修复。

### 补丁 1：usage_ledger.md 语义迁移错误

**问题**：P0+ 阶段把 `usage_ledger.md` 中 4 处 `IR-005` 示例替换为 `IR-006`，但二者语义不同：
- IR-005（原）= "最小修复优先"，正确迁移目标是 `GR-005`
- IR-006（现）= "版本前提"，是完全不同的规则
- 同文件 L50 我自己写的 `GR-005 最小修复` 与 `evolution/scenarios/concurrency.json` 的 `rule_id: "GR-005"` 都证明正确目标是 GR-005

**根因**：当时只想"找一个 active ID 顶替"，没做语义对齐，把 IR-006 当成"任意可用 active ID"用了。

**修法**：把 4 处 `IR-006` → `GR-005`（最小修复，未追加 IR-006；如后续想表达"并发场景也命中版本前提"可独立追加）。
- L18-19 `expected_rules` / `hit_rules`
- L34 示例字面
- L60-61 CLI 示例
- L82-83 audit 块示例

### 补丁 2：12 份被改 ref 的 `last-verified` 未更新

**问题**：被实质修改的 12 份 ref 首行仍保留 `<!-- last-verified: 2026-05 -->`，违反 [self_evolution.md L153](references/self_evolution.md#L153) 协议"修改 ref 内容（除排版 / 链接修复外）后必须把 last-verified 更新为当前年月"。`audit_ref_freshness.sh` 通过只是因为 2026-05 还在 12 月阈值内，不能证明协议合规。

**根因**：执行 P0/P0+/P1/P2 时只关注内容修改本身，没顺手把元数据带上。这正是协议存在的理由——元数据不会自动跟随内容。

**修法**：批量更新 12 份 ref 首行为 `<!-- last-verified: 2026-06 -->`：
`rule_index.md` / `architecture_and_network.md` / `networking_patterns.md` / `domain_modeling.md` / `decision_records.md` / `examples.md` / `code_templates.md` / `review_checklists.md` / `validation_scenarios.md` / `root_cause_enforcement.md` / `usage_ledger.md` / `layout_and_ui.md`。

未被本次内容修改的 ref（anti_patterns / architecture_analysis / build_release_and_ci / cognitive_adversary_mode / execution_playbooks / ios_conventions / mcp_control / observability_logging / performance_optimization / self_evolution / swift_concurrency / team_collaboration / test_execution_and_repair / testing_strategy / ui_state_patterns）保留 `2026-05`，符合协议（"没有真正复核的情况下不批量推时间戳"）。

### 补丁后校验

```
validate_usage_ledger.sh   OK (39 entries, 41 active rule IDs)
audit_ref_freshness.sh     FRESH=28 STALE=0 CRITICAL=0 UNDATED=0 INVALID=0
validate_skill_evolution.sh:
  [1/13]–[11/13]  全部 OK（含 [9/13] No orphan references / [10/13] retired words OK）
  [12/13]         DRIFT v70（预期未走自进化晋升）
```

### 教训

- **语义保真 > 让校验通过**：用 active ID 顶替 deprecated ID 时，必须按 rule_index.md 的"替代 ID"列对齐，不能随便挑一个 active ID 让校验通过。
- **协议元数据是修改的一部分**：`last-verified` 不是文档装饰，是 self_evolution 流程的输入信号。修改 ref 内容后未同步元数据 = 修改未完成。
- **自检盲区**：本次两个问题都不会被现有校验脚本捕获（`validate_usage_ledger.sh` 只检查 ID 是否 active，不检查语义；`audit_ref_freshness.sh` 只看阈值，不对照 git diff）。这两个空白后续可考虑补 lint，但本轮不扩张范围。

## 文件变更清单

| 类型 | 路径 |
|---|---|
| 修改 | `SKILL.md` |
| 修改 | `references/rule_index.md` |
| 修改 | `references/architecture_and_network.md` |
| 修改 | `references/networking_patterns.md` |
| 修改 | `references/domain_modeling.md` |
| 修改 | `references/decision_records.md` |
| 修改 | `references/examples.md` |
| 修改 | `references/code_templates.md` |
| 修改 | `references/review_checklists.md` |
| 修改 | `references/validation_scenarios.md` |
| 修改 | `references/root_cause_enforcement.md` |
| 修改 | `references/usage_ledger.md` |
| 修改 | `references/layout_and_ui.md` |
| 修改 | `scripts/lint_hit_rules.sh` |
| 创建 → 删除 | `references/chat_list_pin_to_top.md`（P2 第一轮创建，第二轮按用户裁决删除） |
| 创建 | `MAINTENANCE-LOG-2026-06-02.md`（本文件） |
