# Skill Evolution Proposal

## Metadata
- Proposal ID: 20260710-154300-sync-gr-ids-to-templates-ledger
- Created At: 2026-07-10 15:43:00 +0800
- Active Version At Creation: v73

## 问题信号
- `engineering-discipline` 的真值源（`SKILL.md` + `references/engineering_discipline.md`）已在提案 `20260629-174233-complete-global-rules` 中升级为覆盖 `GR-001~008`（补齐 `GR-001` 安全防御、`GR-006` 预算拦截）。但由模板渲染的产物并未同步：
  - `agent-preamble.md.tmpl` 的 engineering-discipline 摘要仍只列 `GR-002/003/004/005/007/008`，静默漏掉 `GR-001` 与 `GR-006`；
  - `engineering-discipline.mdc.tmpl` 的 description 同样停留在旧列表。
- 更关键：`agent-preamble.md.tmpl` 此前明文 instruct 模型 "`GR-NNN` 等全局纪律 ID 不在此词表内、校验会拒收，不要写"——主动禁止模型在 `<usage-audit>` 块中记录全局规则命中，尽管 `GR-NNN` 已是 active 且属于 engineering-discipline。这导致 usage ledger 系统性低估全局纪律遵守度。
- `usage_ledger.md` 的可复制 Codex / Cursor audit 提示的 `expected-rules / hit-rules` 家族也只列 `IR/SYM/ROUTE/OUT`，漏列 `GR-XXX`，用户粘贴提示后无法登记全局规则命中。

## 变更类型
- 修正表达 / 补齐同步（将真值源已完整的 `GR-001~008` 回灌到生成模板与审计台账提示）

## 变更内容
- 修改文件：
  - `skills-engineering/scripts/templates/agent-preamble.md.tmpl`
    - engineering-discipline 摘要由 `GR-002/003/004/005/007/008` 改为 `GR-001/002/003/004/005/006/007/008`，补全 `GR-001`/`GR-006` 并补述语义（保护敏感信息、触发预算阈值时主动中断）。
    - Rule ID 词表由 `（IR-NNN / SYM-NNN / ROUTE-NNN / OUT-NNN）` 且"GR-NNN 不在此词表内、校验会拒收"改为 `（IR-NNN / SYM-NNN / ROUTE-NNN / OUT-NNN / GR-NNN）`，移除对 `GR` 的拒收声明。
  - `skills-engineering/scripts/templates/engineering-discipline.mdc.tmpl`
    - description 由 `（GR-002/003/004/005/007/008）` 升级为 `（GR-001~008）` 并补全语义词（安全防御、预算拦截、防 Diff 噪声、残留风险声明）。
  - `skills-engineering/ios-engineer/references/usage_ledger.md`
    - §5.1 Codex 与 §5.3 Cursor 可复制 audit 提示中，`expected-rules / hit-rules` 家族由 `IR-XXX / SYM-XXX / ROUTE-XXX / OUT-XXX` 扩展为追加 `/ GR-XXX`。
    - （§5.2 Claude Code 提示未改：它指向 `rule_index.md` 的 `status=active` 集合，`GR-XXX` 已是 active，隐式已覆盖——属设计自洽，非遗漏。）
  - `tests/test_ios_engineer_scripts.py`
    - 新增 3 个回归测试，固化上述契约：
      - `test_agent_preamble_rule_id_families_match_active_index`：断言 preamble 的 audit 契约允许 `rule_index.md` 中每一个 `active` 家族（IR/SYM/ROUTE/OUT/GR）。
      - `test_agent_preamble_summarizes_all_engineering_discipline_rules`：断言 preamble 的 engineering-discipline 摘要覆盖 `GR-001~008` 全部编号。
      - `test_usage_ledger_prompts_allow_global_rule_ids`：断言 usage_ledger 的 codex/cursor 提示含 `GR-XXX`、claude 提示含 `status=active 的 ID`。
- 替代或合并旧规则：
  - 无新规则；本次仅把已存在于真值源（`GR-001`/`GR-006`）的覆盖回灌到生成模板与台账提示，消除"真值源已全、渲染产物缺半"的漂移。
  - 移除了 `agent-preamble.md.tmpl` 中"`GR-NNN` 不在此词表内、校验会拒收"的过时拒收声明。

## 预期收益
- 生成的 agent preamble 与 Cursor `.mdc` 不再漏述 `GR-001`/`GR-006`，与 engineering-discipline 真值源完全一致。
- 模型在 `<usage-audit>` 块中可正确记录 `GR-XXX` 命中，usage ledger 能统计全局纪律遵守情况，不再系统性低估。
- 新增测试把"模板/台账必须与 `rule_index` active 集合一致"固化为可回归契约，防止再次漂移。

## 验证
- 单元校验（已通过）：`python -m pytest tests/test_ios_engineer_scripts.py -k "rule_id_families or engineering_discipline_rules or usage_ledger_prompts"` → **3 passed**。3 个新增回归测试全部通过，固化了"模板/台账必须与 `rule_index` active 集合一致"的契约。
- 结构校验（14 步，`validate_skill_evolution.sh`）：
  - [1/14]–[11/14] 全过：YAML、SKILL.md 体积、引用文件、分层护栏、内部链接、scenario specs、rule IDs（52 active）、usage ledger、orphan references、unique ownership + retired words、threshold doc/script sync 均 OK。
  - [12/14] 快照一致性：与 v73 快照存在 drift（`check_snapshot_consistency` 报 FAILED）。但 drift 列表含 `app_extensions/notifications/persistence/privacy_permissions/storekit_iap` 等大量分支新增 ref 与多个 script，**非本提案引入**；本提案仅改动 `usage_ledger.md`（drift 列表之一）。属 `feature_3.0.0` 分支整体相对 v73 演进的**既有漂移**，需经版本提升（promote a new version）流程消除，不在本提案 scope。
  - [13/14] behavior validation：behavior 4/5「Code review output contract」失败，报错 `SKILL.md no longer routes code review to findings-first review_checklists.md`。该断言针对 `ios-engineer/SKILL.md` 的 code-review 路由，而**本提案未改动 SKILL.md 该部分**，属分支既有状态导致的**既有失败**，非本提案引入；[14/14] 因此未执行。建议另立提案修复该 behavior 契约或更新对应 scenario。
  - 结论：脚本整体退出码非 0，但失败项均为**分支级既有问题**；本提案实际改动（4 文件 + 3 测试）在 [1]–[11] 与单测层面全部通过，提案本身成立。
- 残留风险：模板渲染产物 `.cursor/rules/*.mdc` 等副本由 `sync-agent-preamble.sh` / `sync-skills.sh` 从模板再生成，属 git 忽略本地产物；本提案不手动改这些副本，验证以模板与 `tests/` 契约为准（CI/sync 时自动传播）。

## 状态
- approved
