# Skill Evolution Proposal

## Metadata
- Proposal ID: 20260905-095415-rollback-integrity-baseline-refresh
- Created At: 2026-09-05 09:54:15 +0800
- Active Version At Creation: v74

## 问题信号
- `rollback` 与 `promote` 在完整性基线上行为不对称：`promote` 只写 `evolution/` 快照，而完整性基线采集范围明确排除 `evolution/`（其变化由治理流程登记、由专门校验器守护），因此 promote 不会漂移；`rollback` 则把快照内容恢复进工作副本，真实改动了 `SKILL.md` / `references/` / `agents/` 等契约文件，基线若不同步刷新，随后的 commit 会在 CI 的 `--check-only` 上因 MODIFIED 漂移而失败。
- 基线为「内容登记制」：变更必须显式登记（运行 `validate-skill-integrity.sh` 不带 `--check-only`）。此前 rollback 缺少这一步，需人工记得补跑，属于易遗漏的隐性步骤。

## 变更类型
- 新增能力（治理链路补强：回滚后自动登记基线）。

## 变更内容
- 修改文件：`ios-engineer/scripts/rollback-skill-evolution.sh` —— 在主流程成功后新增第 8 步：调用 `../scripts/validate-skill-integrity.sh ios-engineer` 刷新完整性基线（不带 `--check-only`，即写入新基线）。
  - 守卫式调用：仅当脚本存在时执行；以 `|| true` 兜底，基线刷新失败只告警不中断 rollback 主流程，避免治理附属动作反向阻断用户的回滚操作。
  - 脚本缺失时打印手动刷新提示（`⚠ integrity script not found; refresh the baseline manually:`），给出可直接复制的命令。
- 关联文件（本次不改，已入库，仅被引用）：`skills-engineering/scripts/validate-skill-integrity.sh`、基线产物 `skills-engineering/.integrity/ios-engineer.sha256`。
- 不替代或合并任何既有 GR 规则；`SKILL.md`、rule ID、行为契约、演化流程均未变动。
- 历史快照（`evolution/history/`）与治理记录（proposals/approvals/validations）为固化事实，不做改动。

## 预期收益
- `rollback` 后直接 commit 不再触发 CI 的完整性漂移失败，消除一次隐性人工步骤。
- 与 `promote` 的「不漂移」行为形成对称：写工作副本契约内容的动作（rollback）自动登记，只写快照的动作（promote）不登记。
- 失败不阻断，治理动作不增加回滚操作的风险。

## 验证
- 结构校验：`validate-skill-evolution.sh` 步骤 1-14 全部通过（引用完整性、rule ID、usage ledger、threshold 同步、slug 同步），在 `SKIP_SNAPSHOT_CONSISTENCY=1` 下通过（快照一致性待 promote v75 后由新快照满足）。
- 场景回放：`run-behavior-validation.sh` 步骤 2（proposal 脚本拒绝路径）39 项、步骤 4（gc 不变式）7 项全部通过。
- drift 范围：工作区相对活动快照 v74 的差异经全量逐字节比对，仅 `scripts/rollback-skill-evolution.sh` 1 个文件，无夹带改动。
- 引用一致性：活动区（排除历史快照与治理记录）已无 snake_case 脚本引用残留；29 个脚本引用全部命中存在的文件，无悬空引用。
- 残留风险：本机 Xcode-beta 缺 `sys/cdefs.h`，Repository 模板 Swift 编译无法运行，本轮以 `SKIP_SWIFT_TYPECHECK=1` 跳过（CI 完整 Xcode 不受影响）；完整性脚本以守卫式调用，在其缺失环境下 rollback 仍可正常完成。

## 状态
- promoted
