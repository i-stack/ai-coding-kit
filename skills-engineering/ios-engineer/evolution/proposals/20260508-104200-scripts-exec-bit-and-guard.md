# Skill Evolution Proposal

## Metadata
- Proposal ID: 20260508-104200-scripts-exec-bit-and-guard
- Created At: 2026-05-08 10:42:00 +0800
- Active Version At Creation: v36

## 问题信号
- `ios-engineer/scripts/` 下 13 个 `.sh`，在 v35 及之前有 10 个缺 `+x` 位（仅 `check_snapshot_consistency.sh` / `test_proposal_scripts.sh` / `validate_skill_evolution.sh` 带执行位）。evolution 工作流与 `demo_skill_evolution_flow.sh` 隐含用 `./scripts/xxx.sh` 直接调用，但实际必须加 `bash` 前缀才能运行，造成新人与 CI 首次接入即失败。
- 本仓库缺少针对脚本权限位的回归守护。一旦未来有人重新生成脚本（如通过 `cp` / 模板）丢失 `+x`，不会被任何现有验证发现，会再次回到晋升前的坏态。
- v36 晋升过程已经伴随 `chmod +x scripts/*.sh`，当前工作树与 v36 快照中的脚本已全部带 `+x`；但该权限修正不属于 v36 提案的范围（v36 专注于 test_system_prompt 合并），需要在本提案里把"脚本权限位 + 守护断言"正式立项并归档。

## 变更类型
- 工具链修正：追认并归档 `chmod +x scripts/*.sh` 的权限位修复。
- 新增能力：在 `scripts/test_proposal_scripts.sh` 中增加一条断言，要求 `scripts/*.sh` 全部带 `+x`。

## 变更内容
- 修改文件：
  - `scripts/test_proposal_scripts.sh`
    - 在脚本末尾、汇总打印之前，新增一段"所有 `scripts/*.sh` 必须带执行位"的断言逻辑：遍历目录下 `.sh`，对任何不带 `+x` 的文件直接调用 `fail` 计数并打印具体路径。
  - `scripts/*.sh`
    - 文件权限统一为 `-rwxr-xr-x`（通过 git index 记录 `+x` 位）。
- 替代或合并旧规则：
  - 无规则替代；本提案是工具链纪律的增量。

## 预期收益
- evolution 工作流即时可用，`bash scripts/...` 前缀不再是可用性唯一路径，`./scripts/...` 也可正常执行。
- 为将来的脚本维护提供权限位回归防线：任何使 `+x` 丢失的改动都会在 `test_proposal_scripts.sh` 中被立即拦截。
- 把"晋升 v36 时顺带发生的 chmod"显式归档为提案可追溯动作，维持 self_evolution.md 要求的"改动必须有 proposal 闭环"纪律。

## 验证
- 结构校验：
  - 已确认当前工作树下 `ls -la ios-engineer/scripts/*.sh` 全部带 `-rwxr-xr-x`。
  - 已确认 `test_proposal_scripts.sh` 的新增断言会在存在任一缺 `+x` 脚本时 fail，否则不增加 fail 计数。
- 场景回放：
  - 场景 `scripts-all-executable`：期望 `bash scripts/test_proposal_scripts.sh` 打印 `Passed: N` 且 `Failed: 0`，且在日志中出现"所有脚本均带执行位"的断言通过提示。
  - 场景 `missing-exec-bit-regression`：人为把一个脚本 `chmod -x`，再次运行 `test_proposal_scripts.sh`，期望 fail 计数增加且具体路径出现在输出里。
- 残留风险：
  - Git 对文件 mode 变更的追踪依赖仓库的 `core.filemode` 配置；若有开发者本地 `core.filemode=false`，commit 的权限位不生效。本提案不处理该场景，仅保证提交时 index 侧权限位正确。
  - `chmod +x` 仅对 `scripts/*.sh` 生效；后续若新增其他可执行文件类型（如 `.rb` / `.py` worker），需要在断言里显式扩展文件匹配。

## 状态
- promoted
