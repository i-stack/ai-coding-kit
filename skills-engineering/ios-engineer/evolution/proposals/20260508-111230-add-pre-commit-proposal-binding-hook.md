# Skill Evolution Proposal

## Metadata
- Proposal ID: 20260508-111230-add-pre-commit-proposal-binding-hook
- Created At: 2026-05-08 11:12:30 +0800
- Active Version At Creation: v41

## 问题信号
- 架构体检 R1-B 长期建议：依赖 self_evolution.md 的"任何 SKILL.md / references 改动都必须走 proposal 全流程"约束目前是文档级纪律，没有自动守卫。一次靠自觉的绕过（commit dd07e2c）已经发生过；下一次只要有人忘记走流程，整个 evolution 体系的快照基线就会再次漂移。
- v36 的修复是事后补救（手动补 validation / approval / history / active_version）。要从根本上防止再次发生，必须在 commit 时机加机器拦截。
- 已有的 `validate_skill_evolution.sh` 是后置检查，仅在主动调用时运行，commit 路径上没有挂钩；需要在 git pre-commit 阶段引入对"SKILL.md 或 references/*.md 改动必须绑定 staged proposal 且具备 approval 记录"的硬拦截。

## 变更类型
- 新增能力：在仓库根新增 `.githooks/pre-commit`，以 git pre-commit 钩子形式拦截未绑定 proposal 的 SKILL.md / references 改动。
- 新增能力：在仓库根新增 `scripts/install-hooks.sh`，把 `core.hooksPath` 设为 `.githooks` 并把钩子置位为可执行。
- 新增能力：在仓库根 `README.md` 增补"提交前先运行 `bash scripts/install-hooks.sh`"的安装说明。

## 变更内容
- 修改文件：
  - `.githooks/pre-commit`（新增）
    - 入口：`#!/usr/bin/env bash`，`set -uo pipefail`。
    - 行为：
      - 若环境变量 `SKILL_BYPASS=1`，立即 exit 0（紧急绕过通道，使用必须显式声明，留痕审计靠 commit message + reflog）。
      - 用 `git diff --cached --name-only --diff-filter=ACMR` 拿 staged 的新增 / 复制 / 修改 / 重命名文件清单。
      - 过滤出 `^ios-engineer/(SKILL\.md|references/.+\.md)$` 的 guarded 改动；若为空，exit 0。
      - 若 guarded 非空，进一步过滤 staged 中是否存在 `^ios-engineer/evolution/proposals/[0-9]{8}-[0-9]{6}-[A-Za-z0-9_-]+\.md$` 的 proposal 文件；不存在则打印未绑定提示和 guarded 文件清单，exit 1。
      - 对每个 staged proposal，要求其对应的 `ios-engineer/evolution/approvals/<id>.json`：要么也在本次 staged，要么已在仓库历史中（`git ls-files --error-unmatch` 通过）。任何缺失都收集后报错 exit 1，并提示运行 `bash ios-engineer/scripts/approve_skill_promotion.sh`。
      - 不校验 `validations/` 与 `history/`，把它们留给已有的 `validate_skill_evolution.sh` 与 `check_snapshot_consistency.sh` 在主动校验路径上覆盖。
  - `scripts/install-hooks.sh`（新增）
    - 入口：`#!/usr/bin/env bash`，`set -euo pipefail`。
    - 行为：在仓库根运行 `git config core.hooksPath .githooks`；对 `.githooks/*` 执行 `chmod +x`；最后打印当前生效的 `core.hooksPath` 并提示开发者验证。
  - `README.md`
    - 在已有的 "## 快速开始" 段或紧随其后追加一节 "## 提交守卫"：说明所有协作者克隆后须运行 `bash scripts/install-hooks.sh`；解释钩子拦截范围（`ios-engineer/SKILL.md` 与 `ios-engineer/references/*.md`）；标明绕过开关 `SKILL_BYPASS=1` 仅限紧急情况，并提示绕过应在 commit message 中显式说明原因。
- 替代或合并旧规则：
  - 不替代任何旧规则；本提案是把 self_evolution.md 已有的纪律层从"文档约束"升级为"机器拦截"的新增层。

## 预期收益
- 任何后续对 SKILL.md / references 的改动都必须在同一 commit 中包含对应 proposal + 已有 approval；丢失任一都被 git 直接拦下。
- "悄悄改 SKILL.md 后再补 evolution 元数据"的反例无法再次发生；snapshot consistency 在仓库 commit 路径上有了真守卫。
- 紧急路径仍然存在（`SKILL_BYPASS=1`），但需要协作者显式声明、可审计；不再依赖纯靠纪律。

## 验证
- 结构校验：
  - `bash scripts/install-hooks.sh` 后，`git config --get core.hooksPath` 输出 `.githooks`；`ls -la .githooks/pre-commit` 显示带 `+x`。
  - `bash ios-engineer/scripts/validate_skill_evolution.sh` 9/9 base + 5/5 behavior 全绿（本提案不动 SKILL.md / references/*.md）。
  - `bash ios-engineer/scripts/test_proposal_scripts.sh` 保持 Passed=39 Failed=0。
- 场景回放：
  - 场景 `hook-rejects-unbound-skill-change`：临时 `git add ios-engineer/SKILL.md`（仅修改一个无关字符）后 `git commit -m test`，必须被钩子拦截并打印 "skill-evolution pre-commit: SKILL.md or references/ changed without a staged evolution proposal."；随后 `git reset` 还原，验证流不进入 commit。
  - 场景 `hook-rejects-proposal-without-approval`：临时构造 SKILL.md 无关改动 + 一个新 proposal（无 approval）一起 staged，必须被钩子打印 "staged proposals lack approval records." 并拦截。
  - 场景 `hook-bypass-with-explicit-flag`：临时构造同上不合规改动，但显式 `SKILL_BYPASS=1 git commit ...`，必须放行；事后 reset 干净。
  - 场景 `hook-allows-unrelated-changes`：仅修改 `ios-engineer/scripts/*.sh` 或 `ios-engineer/evolution/**` 而不动 SKILL.md / references 时，钩子不触发拒绝。
- 残留风险：
  - 钩子只能拦截本机 git commit；GitHub 端 PR 合并不在钩子作用域。后续如需仓库级守卫，需配合 GitHub Actions 添加同等检查（属 v43+ 范围）。
  - 钩子检查的是 staged 内容，不读取提案的 `## 状态` 字段；理论上有人可以 staged 一个 status=draft 的 proposal + 一个 approval JSON（但 approval JSON 由 `approve_skill_promotion.sh` 生成且要求 `validate_skill_proposal.sh` 已 validated），上游脚本约束已基本封死该路径。深度校验（要求 proposal status==promoted/approved）属 v43+ 增量。
  - `git config core.hooksPath` 是 per-clone 配置；新协作者克隆后必须主动运行 `scripts/install-hooks.sh`。README 增补的目的就是让安装步骤显式可见。

## 状态
- promoted
