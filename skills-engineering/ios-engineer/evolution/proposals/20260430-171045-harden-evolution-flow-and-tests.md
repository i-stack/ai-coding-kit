# Skill Evolution Proposal

## Metadata
- Proposal ID: 20260430-171045-harden-evolution-flow-and-tests
- Created At: 2026-04-30 17:10:45 +0800
- Active Version At Creation: v32

## 问题信号
- v31 漂移事件暴露三类流程空洞：
  1. 工作区可以被直接改动而无人察觉，`active_version` 指向的 snapshot 与现网文件不再一致，`rollback` 语义失效。
  2. 六个 proposal 脚本的入参白名单规则是上一轮人工统一的；缺乏自动回归手段，下次重构即可能静默退化。
  3. `references/code_templates.md` 使用 `Feature*` / `*Protocol` 作为占位名，缺一句显式声明，复制后不可编译的问题会被当成"模板缺陷"而非"使用者未替换"。
- 另外本轮本地测试触发一个真实 bug：`approve_skill_promotion.sh` / `validate_skill_proposal.sh` 的校验顺序（先 `-f` 后 regex）与其他四个脚本相反，格式非法且不存在的路径会收到 "Missing proposal file" 而非 "Invalid proposal_file format"，错误面向用户不一致。

## 变更类型
- 新增能力（快照一致性校验、proposal 脚本测试）
- 修正表达（code_templates 占位声明、approve/validate 校验顺序）

## 变更内容
- 修改文件：
  - 新增 `scripts/check_snapshot_consistency.sh`：读取 `evolution/active_version.json`，对 `evolution/history/<active>/snapshot/{SKILL.md,agents,references,scripts}` 与当前工作区四目录逐项 `diff`，任意漂移即退出非零并打印漂移位置。
  - 修改 `scripts/validate_skill_evolution.sh`：新增步骤 `[8/8] Validate snapshot consistency with active version`，调用上述新脚本；识别环境变量 `SKIP_SNAPSHOT_CONSISTENCY=1` 以允许晋升/验证链路的内部调用绕过（避免自噬）。1–7 步对应编号同步调整。
  - 修改 `scripts/validate_skill_proposal.sh`：调用 `validate_skill_evolution.sh` 时设置 `SKIP_SNAPSHOT_CONSISTENCY=1`；把 regex 白名单提前到 `-f` 存在性检查之前，与其他脚本语义一致。
  - 修改 `scripts/promote_skill_evolution.sh`：调用 `validate_skill_evolution.sh` 时设置 `SKIP_SNAPSHOT_CONSISTENCY=1`。
  - 修改 `scripts/approve_skill_promotion.sh`：把 regex 白名单提前到 `-f` 存在性检查之前。
  - 新增 `scripts/test_proposal_scripts.sh`：覆盖非法 slug 7 例、非法 proposal_file 5 × 6 脚本 = 30 例，以及 `validate_skill_evolution.sh --SKIP` 烟雾测试 1 例，共 38 例；任意失败退出非零。
  - 修改 `references/code_templates.md`：在"使用规则"小节增加一行，明确声明 `Feature*` 及占位协议名均为需业务替换/定义的占位，模板直接复制不保证可编译。
- 替代或合并旧规则：无

## 预期收益
- 快照漂移在日常 `validate_skill_evolution.sh` 运行时即被捕获，v31 那类"active 与现网不一致"无法再静默存在；而晋升流程本身通过 `SKIP` 不被自噬。
- Proposal 脚本入参校验的一致性具备自动回归保障；未来任何脚本修改只要破坏了六脚本同构就会被 `test_proposal_scripts.sh` 当场命中。
- `code_templates.md` 的占位声明让使用者第一眼就知道哪些类型必须替换，减少"复制即崩"与"误判模板有 bug"两类噪声。
- approve / validate 与其他四个脚本的错误文案、顺序完全统一。

## 验证
- 结构校验：`bash scripts/validate_skill_evolution.sh` 在工作区与 v32 不一致时应失败（步骤 8 报漂移）；设置 `SKIP_SNAPSHOT_CONSISTENCY=1` 后 8/8 通过；v33 晋升后再跑一次，应 8/8 且"Snapshot consistency OK"。
- 场景回放：
  - `snapshot-drift-detection`：人为引入 drift（本轮改动即构成 drift）→ step [8/8] 必须失败并列出漂移文件；`SKIP=1` 时必须打印 "Skipped (SKIP_SNAPSHOT_CONSISTENCY=1)" 并让整体校验通过。
  - `proposal-script-rejection-tests`：`test_proposal_scripts.sh` 全部 38 例 pass。
  - `template-placeholder-clarity`：`code_templates.md` "使用规则"末尾存在占位声明条目，措辞覆盖 `Feature*` 与协议占位两类。
- 残留风险：
  - 晋升流程内部通过 `SKIP` 绕过一致性检查，若人为在 promote 前手改 `evolution/history/<current>/snapshot/` 制造"假一致"，外部 `check_snapshot_consistency.sh` 也会被骗过——这是单向前提，不在本 proposal 范围内解决。
  - `test_proposal_scripts.sh` 覆盖拒绝路径与单烟雾测试，未覆盖合法路径的 happy path；后者需要更复杂的临时工作区隔离，留待真实回归出现时再补。
  - `LoggerProtocol` 等占位协议目前在 skill 内无集中定义位置；本次仅做声明，后续如有多个模板都需要 logger 可考虑抽 `references/logging_contract.md`。

## 状态
- promoted
