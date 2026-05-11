# Skill Evolution Proposal

## Metadata
- Proposal ID: 20260430-171802-add-behavior-validation-layer
- Created At: 2026-04-30 17:18:02 +0800
- Active Version At Creation: v33

## 问题信号
- 现有 `validate_skill_evolution.sh` 已覆盖结构质量，但对行为质量的覆盖不足：只能证明文档引用、唯一归属、退役词和 active snapshot 一致，不能证明关键脚本拒绝路径、模板可用性和场景回放可重复执行。
- v31 曾出现 active snapshot 漂移；v33 已补 snapshot 一致性检查，但行为回放仍散落在人工记录和 `test_proposal_scripts.sh` 中，未形成统一门禁。
- Repository 模板曾出现 `logger.error(...)` 未注入 `logger` 的不可用样例，说明模板需要自动可用性检查，不能只靠人工审查。

## 变更类型
- 新增能力：增加行为验证层。
- 修正表达：将 `validate_skill_evolution.sh` 从 8 步扩展到 9 步，明确行为验证是基础门禁的一部分。

## 变更内容
- 修改文件：
  - `scripts/run_behavior_validation.sh`：新增行为回放入口。
  - `scripts/validate_skill_evolution.sh`：新增 `[9/9] Run behavior validation scenarios`，通过 `SKIP_BEHAVIOR_VALIDATION=1` 防止递归。
  - `scripts/test_proposal_scripts.sh`：内部调用主校验时增加 `SKIP_BEHAVIOR_VALIDATION=1`，避免 proposal 脚本测试触发递归校验。
- 行为验证覆盖：
  - active snapshot 一致性：默认调用 `scripts/check_snapshot_consistency.sh`；候选验证阶段可通过 `SKIP_SNAPSHOT_CONSISTENCY=1` 跳过，晋升后必须完整通过。
  - proposal 脚本拒绝路径：复用 `scripts/test_proposal_scripts.sh`，覆盖非法 slug、非法 proposal path 和主校验加载路径。
  - Repository 模板可用性：检查 logger 字段、init 参数、赋值、读写失败日志闭环；拒绝 `try? cache.read/write` 回归；若本机存在 `swiftc`，使用 `/tmp` module cache 对抽取出的模板做 `swiftc -typecheck`。
- 替代或合并旧规则：不替代旧规则；把原本人工或散落脚本的行为验证合并为统一入口。

## 预期收益
- 每次候选改动都能自动回放关键行为，不再只证明 Markdown 结构正确。
- active snapshot 漂移、proposal 脚本边界回归、Repository 模板不可用这三类已发生问题被纳入固定门禁。
- 后续可继续在 `run_behavior_validation.sh` 中追加 Crash、并发、网络缓存、UI 复用、代码审查等真实任务回放，不需要扩写 `SKILL.md`。

## 验证
- 结构校验：
  - `SKIP_SNAPSHOT_CONSISTENCY=1 bash scripts/validate_skill_evolution.sh` 通过 9 步校验。
- 场景回放：
  - `behavior-snapshot`：晋升前默认检查能发现 active snapshot 漂移；候选验证阶段通过 `SKIP_SNAPSHOT_CONSISTENCY=1` 跳过。
  - `behavior-proposal-scripts`：非法 slug / 非法 proposal path 被统一拒绝。
  - `behavior-template-usability`：Repository 模板具备 logger 注入闭环、无 `try? cache.*` 回归，并通过 `swiftc -typecheck`。
- 残留风险：
  - 当前行为验证仍偏工程门禁，尚未覆盖真实 iOS 任务输出质量；后续可在本脚本继续加入固定 prompt 回放与预期输出断言。
  - `swiftc` 不存在时会降级为文本检查；在本机已执行到 typecheck 路径。

## 状态
- promoted
