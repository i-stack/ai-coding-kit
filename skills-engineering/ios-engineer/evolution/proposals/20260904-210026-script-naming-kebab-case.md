# Skill Evolution Proposal

## Metadata
- Proposal ID: 20260904-210026-script-naming-kebab-case
- Created At: 2026-09-04 21:00:26 +0800
- Active Version At Creation: v73

## 问题信号
- 脚本命名风格分裂：`skills-engineering/scripts/` 采用 kebab-case（`sync-skills.sh`、`validate-global-skills.sh`），而 `ios-engineer/scripts/` 采用 snake_case（`validate_skill_evolution.sh`、`append_usage_entry.sh`），另有全局 `detect_project_type.sh`、`skill_bundles.sh` 两个蛇形异常。命名风格不统一增加心智负担与检索成本。

## 变更类型
- 修正表达（脚本命名统一为 kebab-case，属可维护性治理的一部分）。

## 变更内容
- 统一脚本命名：将 `ios-engineer/scripts/` 下 28 个 snake_case 脚本与全局 `scripts/` 下 2 个蛇形异常（`detect_project_type.sh`、`skill_bundles.sh`）重命名为 kebab-case。
  - 例：`validate_skill_evolution.sh` → `validate-skill-evolution.sh`、`append_usage_entry.sh` → `append-usage-entry.sh`、`skill_bundles.sh` → `skill-bundles.sh`。
- 为每个改名脚本保留旧名 shim（转发到新名），保证既有调用方与文档链接不中断。
- 同步更新全部现役引用：`references/*.md` 及 en-US 镜像、`.githooks/pre-commit`、`.githooks/post-commit`、`.github/workflows/validate.yml`、`.agents/writing-docs.md`、`scripts/sync-agent-preamble.sh`、`tests/test_ios_engineer_scripts.py`、脚本内部互调引用。
- 不替代或合并任何既有 GR 规则；`SKILL.md`、rule ID、行为契约均未变动。
- 历史快照（`evolution/history/`）与治理记录（proposals/approvals/validations）为固化事实，不做改动。

## 预期收益
- 全局脚本命名统一为 kebab-case，消除风格分裂。
- shim 保证向后兼容，降低迁移冲击。

## 验证
- 结构校验：`validate_skill_evolution.sh`（步骤 1-14，含引用完整性、threshold 同步、usage ledger、rule ID）在 `SKIP_SNAPSHOT_CONSISTENCY=1` 下全部通过（快照一致性待 promote v74 后由新快照满足）。
- 场景回放：`run_behavior_validation.sh` 步骤 2（proposal 脚本拒绝路径）与步骤 4（gc 不变式）通过；Swift 模板编译在本机因 Xcode-beta SDK 缺 `sys/cdefs.h` 无法运行（CI 完整 Xcode 不受影响）。
- 测试套件：`tests/test_ios_engineer_scripts.py`、`test_en_us_mirror_sync.py`、`test_ios_engineer_duplication.py` 共 90 项全部通过。
- 残留风险：改名后旧名以 shim 形式保留，新旧名并存一段时间；快照一致性在本轮 promote v74 后恢复。

## 状态
- promoted
