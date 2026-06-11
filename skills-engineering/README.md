# skills-engineering

[![Skill](https://img.shields.io/badge/skill-ios--engineer-0A84FF)](ios-engineer/SKILL.md)
![Agent](https://img.shields.io/badge/agent-skill--engineering-34C759)
![Sync](https://img.shields.io/badge/sync-Codex%20%7C%20Claude%20%7C%20Cursor-5856D6)

用于维护、同步与演进工程化 Agent Skill 的仓库。当前主技能为 `ios-engineer`，覆盖 iOS / Swift / SwiftUI / UIKit / Xcode 工程任务中的架构、并发、网络、UI、性能、测试、审查、迁移和发布风险控制。

本仓库同时提供三类能力：

- Skill 内容源：`ios-engineer/SKILL.md` 与 `ios-engineer/references/` 是技能规则和参考文档的来源。
- 多端同步：把技能同步到 Codex、Claude Code、Cursor 的本地 skills 目录，并把托管 preamble 写入对应 Agent 配置。
- 受控演进：用 proposal、validation、approval、history、usage ledger 管理技能变更，避免直接修改规则后失去验证链路。

当前仅适配 macOS 下的 Codex、Claude Code 和 Cursor；欢迎提交 PR 补充 Windows 同步脚本，或补充其他需要同步的 AI 工具。

## 当前状态

- 主技能：`ios-engineer`
- Active 版本：见 `ios-engineer/evolution/active_version.json`
- 技能入口：`ios-engineer/SKILL.md`
- 认知对手模式：`ios-engineer/SKILL.md` 顶部全局强制；详规 `ios-engineer/references/cognitive_adversary_mode.md`
- 认知拓展（打破茧房）：`cognitive-expansion/` skill（与 `ios-engineer` 同构）；`sync-skills.sh` 同步全文到各端；preamble 仅声明加载路径，Cursor `.mdc` 由详规自动生成
- 规则索引：`ios-engineer/references/rule_index.md`
- 使用观测：`ios-engineer/references/usage_ledger.md` 与 `ios-engineer/evolution/usage/usage.jsonl`
- 回归场景：`ios-engineer/evolution/scenarios/*.json`

## 目录结构

```text
.
├── README.md
├── cognitive-expansion/
│   ├── SKILL.md
│   └── references/
├── scripts/
│   ├── bootstrap.sh
│   ├── sync-agent-preamble.sh
│   ├── sync-skills.sh
│   ├── verify-sync.sh
│   ├── config.local.sh.example
│   └── templates/
└── ios-engineer/
    ├── SKILL.md
    ├── agents/
    ├── references/
    ├── scripts/
    └── evolution/
```

关键目录：

- `ios-engineer/references/`：按主题拆分的技能规则与参考材料，例如认知对手模式、并发、布局、网络、性能、审查、迁移、测试、可观测性和自进化治理。
- `ios-engineer/scripts/`：技能演进、校验、提案、验证、晋升、回滚、usage ledger 写入与汇总脚本。
- `ios-engineer/evolution/`：技能演进数据，包括 `proposals/`、`validations/`、`approvals/`、`history/`、`scenarios/`、`usage/`。
- `scripts/`：仓库级脚本，负责同步技能、同步 Agent preamble 与同步结果校验；本地机器专属配置放在 `scripts/config.local.sh`（模板为 `scripts/config.local.sh.example`），路径由仓库根 `.gitignore` 排除，会被 sync 脚本自动 source。
- 提交/推送守卫：合并入 `ai-coding-kit` 后由仓库根的 [../.githooks/](../.githooks/) 统一管理，详见外层根 README 的「Git 钩子」章节。

## 快速开始

### 1. 同步技能到本地 Agent 目录

推荐同步矩阵：

- `Codex`：需要 `~/.codex/skills/ios-engineer` + `~/.codex/AGENTS.md`。前者提供 `SKILL.md + references/`，后者负责把技能路径接入 system prompt。
- `Claude`：需要 `~/.claude/skills/ios-engineer` + `~/.claude/CLAUDE.md`。只同步 skill 目录不足以保证自动加载。
- `Cursor`：每个 skill 需要 `~/.cursor/skills/<skill>` + 项目内 `.cursor/rules/<skill>.mdc`（`cognitive-expansion.mdc` 由 `sync-agent-preamble.sh` 从 skill 详规生成）。`alwaysApply: true` 的 `.mdc` 负责项目内自动加载。
- `Xcode Codex`：需要 `~/Library/Developer/Xcode/CodingAssistant/codex/skills/ios-engineer` + `~/Library/Developer/Xcode/CodingAssistant/codex/AGENTS.md`。
- `Xcode Claude`：需要 `~/Library/Developer/Xcode/CodingAssistant/ClaudeAgentConfig/skills/ios-engineer` + `~/Library/Developer/Xcode/CodingAssistant/ClaudeAgentConfig/CLAUDE.md`。

推荐执行顺序：

1. 修改数据源：只改 `ios-engineer/SKILL.md` 与 `ios-engineer/references/`。
2. 完整同步并校验：运行 `./scripts/sync-skill-full.sh`。

常见场景建议：

- 日常改规则后：直接运行 `./scripts/sync-skill-full.sh`。
- 新机器初始化：直接跑 `bootstrap.sh`，它会先同步 skill，再同步 preamble。
- 只验证某一端是否能自动读取：至少确认该端的 `skills/ios-engineer` 和对应的 `AGENTS.md` / `CLAUDE.md` / `.mdc` 同时存在且是最新。

如需拆开执行，`sync-skill-full.sh` 等价于依次运行：

```bash
./scripts/sync-skills.sh
./scripts/sync-agent-preamble.sh
./scripts/verify-sync.sh
```

默认同步 `ios-engineer` 到本地已启用的 skills 目录：

```bash
./scripts/sync-skills.sh
```

同步目标：

- `~/.codex/skills/ios-engineer`
- `~/.claude/skills/ios-engineer`
- `~/.cursor/skills/ios-engineer`
- `~/Library/Developer/Xcode/CodingAssistant/codex/skills/ios-engineer`
- `~/Library/Developer/Xcode/CodingAssistant/ClaudeAgentConfig/skills/ios-engineer`

同步内容只包含技能运行期真正需要的规则和参考：`SKILL.md` + `references/`。`evolution/`、`scripts/`、`agents/`、`proposals/`、`validations/`、`approvals/`、`history/`、`usage/`、`scenarios/` 等目录一律 rsync 排除，并通过 `--delete-excluded` 从目标端清除历史残留，保证 Agent 侧只加载运行期必要文件。

常用参数：

```bash
./scripts/sync-skills.sh --dry-run   # 仅预览 rsync 变更
./scripts/sync-skills.sh --watch     # 监听技能目录并自动同步
```

可选环境变量：

- `SKILL_NAME`：默认 `ios-engineer`
- `SOURCE_DIR`：默认 `<repo>/<SKILL_NAME>`
- `CODEX_DEST_BASE`：默认 `~/.codex/skills`
- `CLAUDE_DEST_BASE`：默认 `~/.claude/skills`
- `CURSOR_DEST_BASE`：默认 `~/.cursor/skills`
- `XCODE_CODEX_DEST_BASE`：默认 `~/Library/Developer/Xcode/CodingAssistant/codex/skills`
- `XCODE_CLAUDE_DEST_BASE`：默认 `~/Library/Developer/Xcode/CodingAssistant/ClaudeAgentConfig/skills`

同步目标门控（各端独立；值：`1 / true / yes / on` 强制开启，`0 / false / no / off` 强制关闭，留空 = 按目标根目录是否存在自动探测）：

- `SYNC_CLAUDE`
- `SYNC_CODEX`
- `SYNC_CURSOR`
- `SYNC_XCODE_CODEX`
- `SYNC_XCODE_CLAUDE`

例如只对 Cursor 做一次同步：

```bash
SYNC_CLAUDE=0 SYNC_CODEX=0 SYNC_CURSOR=1 ./scripts/sync-skills.sh
```

例如强制同步到 Xcode 内建 Codex：

```bash
SYNC_XCODE_CODEX=1 ./scripts/sync-skills.sh
```

例如只同步 Xcode 内建 Claude：

```bash
SYNC_CLAUDE=0 SYNC_CODEX=0 SYNC_CURSOR=0 SYNC_XCODE_CODEX=0 SYNC_XCODE_CLAUDE=1 ./scripts/sync-skills.sh
```

### 2. 同步 Agent preamble

将 `scripts/templates/agent-preamble.md.tmpl` 渲染为各工具的托管规则块：

```bash
./scripts/sync-agent-preamble.sh
```

托管块包含两段全局认知规则：（1）**认知校准**——技术决策、根因归因、review 最终判断、用户强烈确信时，优先接近真实（最强反驳、隐藏假设、可证伪条件等）；（2）**认知拓展**——每次主答后默认追加简短「认知尾注」（重框 / 盲区 / 邻域 / 带走），打破知识茧房。iOS 工程任务会在此基础上加载完整 `ios-engineer` skill 规则。

`sync-skills.sh` 默认同步 `skills-engineering/` 下所有含 `SKILL.md` 的目录（含 `cognitive-expansion`）。`sync-agent-preamble.sh` 的 `sync-manifest` 中 `skill:<name>` 行用于从 skill 详规生成 Cursor `.mdc`；preamble 托管块要求 Agent **读取 skills 目录中的全文**，不得仅用摘要。

默认写入：

- `~/.claude/CLAUDE.md`
- `~/.codex/AGENTS.md`
- `~/Library/Developer/Xcode/CodingAssistant/codex/AGENTS.md`
- `~/Library/Developer/Xcode/CodingAssistant/ClaudeAgentConfig/CLAUDE.md`

如需同步 Cursor 项目规则，传入冒号分隔的项目根目录：

```bash
CURSOR_PROJECT_ROOTS="/path/to/appA:/path/to/appB" ./scripts/sync-agent-preamble.sh
```

也可以把 `CURSOR_PROJECT_ROOTS` 写进 `scripts/config.local.sh`（从 `scripts/config.local.sh.example` 复制得到；该文件已由仓库根 `.gitignore` 按路径 `skills-engineering/scripts/config.local.sh` 排除），脚本启动时会自动 source，CLI / shell 变量仍然优先。

Claude / Codex 两端同样遵循 `SYNC_CLAUDE` / `SYNC_CODEX` 门控语义（`1 / 0 / 留空自动探测`）；Cursor 侧由 `CURSOR_PROJECT_ROOTS` 是否设置来决定，不复用 `SYNC_CURSOR`。
Xcode Codex / Claude 侧分别遵循 `SYNC_XCODE_CODEX` / `SYNC_XCODE_CLAUDE` 门控语义（`1 / 0 / 留空自动探测`），默认写入 `codex/AGENTS.md` 与 `ClaudeAgentConfig/CLAUDE.md`。

脚本只重写 `<!-- managed-block:ios-engineer:begin ... :end -->` 托管块，保留文件中的其他内容。

### 3. 校验同步结果

在本地跑完 `sync-skills.sh` 和 `sync-agent-preamble.sh` 之后，用 `verify-sync.sh` 确认各已启用 skill 缓存干净、preamble 托管块正确：

```bash
./scripts/verify-sync.sh
```

该脚本做的事：

- 各已启用 skill 目录里只能有 `SKILL.md` + `references/`；一旦检测到残留的 `evolution/`、`proposals/`、`history/`、`scripts/`、`agents/`、`validations/`、`scenarios/`、`approvals/`、`usage/` 等目录，立即 `FAIL`（这些目录应被 `sync-skills.sh` 的 `--delete-excluded` 清除）。
- `~/.claude/CLAUDE.md`、`~/.codex/AGENTS.md`、`~/Library/Developer/Xcode/CodingAssistant/codex/AGENTS.md` 和 `~/Library/Developer/Xcode/CodingAssistant/ClaudeAgentConfig/CLAUDE.md` 的托管块必须以 `` SKILL 规则位于 `~ `` 开头（tilde 化），避免绝对路径泄露到多机环境。
- 同样支持 `SYNC_CLAUDE / SYNC_CODEX / SYNC_CURSOR / SYNC_XCODE_CODEX / SYNC_XCODE_CLAUDE` 门控，未启用的目标不参与校验。

任何一项失败都会 `exit 1` 并给出 `FAIL: ...` 明细；`pre-push` 会用这一脚本做最后一道闸门（见下文）。

### 4. 新机器一键安装

可用 bootstrap 脚本克隆仓库并执行技能同步与 preamble 同步：

```bash
curl -fsSL https://raw.githubusercontent.com/i-stack/ai-coding-kit/main/skills-engineering/scripts/bootstrap.sh | bash
```

常用环境变量：

- `CLONE_TARGET`：仓库克隆位置，默认 `~/Desktop/github/ai-coding-kit`
- `REF`：要检出的分支、tag 或 commit，默认 `main`
- `SKIP_SKILLS=true`：跳过 `sync-skills.sh`
- `SKIP_PREAMBLE=true`：跳过 `sync-agent-preamble.sh`
- `CURSOR_PROJECT_ROOTS`：透传给 `sync-agent-preamble.sh`

## ios-engineer 技能概览

`ios-engineer/SKILL.md` 是技能主入口，定义：

- 核心铁律：语言、澄清策略、根因优先、最小修复、版本前提声明（IR-006：独立"版本前提"块，给出工程真值或显式假设）、格式化边界、残留风险声明（IR-008：独立"残留风险声明"块，固定已覆盖 / 未覆盖 / 残留风险三字段）。两个声明块均需作为独立段落字面存在，字段存在性由回归场景机械校验。
- 症状导航：Crash、UI 错位、状态错乱、网络异常、性能问题、命名结构问题、遗留架构问题等入口。
- 任务分流：按 ROUTE 加载 2 到 4 份相关 reference，控制上下文规模。
- 输出模板：正式方案、代码审查、代码骨架、测试策略、架构裁决、测试执行与修复等。

常用 reference：

- `root_cause_enforcement.md`：排障和根因纪律
- `swift_concurrency.md`：Swift 并发、取消链路、Sendable、actor
- `layout_and_ui.md`：SwiftUI / UIKit 布局稳定性与无障碍
- `ui_state_patterns.md`：状态建模、异步回写和列表状态
- `networking_patterns.md`：网络、分页、缓存、重试、鉴权
- `review_checklists.md`：代码审查与方案审查
- `migration_strategy.md`：重构、灰度、回滚和迁移
- `self_evolution.md`：技能自进化治理

## 演进工作流

对 `ios-engineer/SKILL.md` 或 `ios-engineer/references/*.md` 做规则变更时，默认走受控演进流程：

1. 创建 proposal：

```bash
bash ios-engineer/scripts/create_skill_proposal.sh <slug>
```

脚本会输出 `evolution/proposals/<proposal-id>.md`。后续命令里的 `<proposal-file>` 使用这个相对路径。

2. 修改技能文件，并在 proposal 中说明问题信号、变更类型、变更内容、预期收益和验证计划。

3. 运行基础校验：

```bash
bash ios-engineer/scripts/validate_skill_evolution.sh
```

4. 写入 proposal 验证记录：

```bash
bash ios-engineer/scripts/validate_skill_proposal.sh <proposal-file> [scenario-slug ...]
```

5. 必要时记录场景验证：

```bash
bash ios-engineer/scripts/record_validation_scenario.sh \
  <proposal-file> \
  <scenario> \
  <pass|partial|fail> \
  "命中点1;命中点2" \
  "偏差点1;偏差点2" \
  "改进建议1;改进建议2"
```

6. 满足晋升条件后，记录审批并晋升：

```bash
bash ios-engineer/scripts/approve_skill_promotion.sh <proposal-file> <approved-by>
bash ios-engineer/scripts/promote_skill_evolution.sh <new-version> proposal:<proposal-id> <proposal-file>
```

7. 如新版本带来回归，使用回滚脚本恢复历史快照：

```bash
bash ios-engineer/scripts/rollback_skill_evolution.sh <version>
```

演进约束详见 `ios-engineer/references/self_evolution.md`。

## 校验与观测

### 基础校验

技能演进的伞形校验入口：

```bash
bash ios-engineer/scripts/validate_skill_evolution.sh
```

该脚本会执行 12 类检查，包括 YAML 结构、SKILL 大小、引用文件存在性、内部链接、场景规格、规则 ID、usage ledger、孤儿 reference、唯一 owner、退役术语、active snapshot 一致性和行为回归场景。

如只需检查特定维度，可直接运行对应脚本，例如：

```bash
bash ios-engineer/scripts/validate_rule_ids.sh
bash ios-engineer/scripts/validate_scenario_specs.sh
bash ios-engineer/scripts/validate_usage_ledger.sh
```

### Usage ledger

真实 iOS 工程任务完成后，Agent 可输出 `<usage-audit>` 块，再由脚本灌入 ledger；也可以直接用 CLI 追加：

```bash
bash ios-engineer/scripts/append_usage_entry.sh \
  --tool codex \
  --task-type concurrency \
  --prompt-summary "异步搜索结果串线" \
  --expected-rules "IR-005,ROUTE-007,SYM-003" \
  --hit-rules "IR-005,ROUTE-007" \
  --outcome partial
```

批量抽取 audit 块：

```bash
bash ios-engineer/scripts/extract_usage_audit.sh path/to/transcript.txt
```

查看汇总信号：

```bash
bash ios-engineer/scripts/summarize_usage_ledger.sh
```

Ledger schema、脱敏要求和 self-grading 偏差说明见 `ios-engineer/references/usage_ledger.md`。

## 提交与推送守卫

钩子由仓库根目录统一管理（合并入 `ai-coding-kit` 后，整个仓库共享一个 `core.hooksPath`）。在 `ai-coding-kit/` 根执行：

```bash
bash install-hooks.sh
```

会把 `core.hooksPath` 指向 `<repo-root>/.githooks/`，一次启用 `pre-commit` 与 `pre-push` 两条守卫。

### pre-commit：规则变更必须绑定治理记录

[`.githooks/pre-commit`](../.githooks/pre-commit) 拦截以下文件的未治理变更：

- `skills-engineering/ios-engineer/SKILL.md`
- `skills-engineering/ios-engineer/references/*.md`

如果这些文件有 staged 改动，同一个 commit 必须包含：

- `skills-engineering/ios-engineer/evolution/proposals/<id>.md`
- `skills-engineering/ios-engineer/evolution/approvals/<id>.json`，或该 approval 已经在历史中存在

### pre-push：推送前强制同步并校验

[`.githooks/pre-push`](../.githooks/pre-push) 在推送前顺序执行（默认任一失败即中止 push）：

1. `skills-engineering/scripts/sync-skills.sh` —— 把 `ios-engineer/` 同步到 `~/.claude`、`~/.codex`、`~/.cursor`，以及可选的 `~/Library/Developer/Xcode/CodingAssistant/codex` 和 `~/Library/Developer/Xcode/CodingAssistant/ClaudeAgentConfig` skill 缓存（按 `SYNC_*` 门控与排除规则）。
2. `skills-engineering/scripts/sync-agent-preamble.sh` —— 重写各端 preamble 托管块，并按 `sync-manifest` 的 `skill:*` 生成 `.cursor/rules/*.mdc`。
3. `skills-engineering/scripts/verify-sync.sh` —— 断言各已启用缓存只有 `SKILL.md + references/`、preamble 托管块已 tilde 化。
4. `sync/sync_all.sh` —— 把 MCP / Codex 共享配置同步到 Cursor / Codex / Claude / Xcode（来自 `sync/` subtree，与本守卫并存）。

任何一步失败都会 `exit 1` 并阻止 `git push`，保证远端指向的版本与本地 Agent 正在加载的版本一致。  
例外：若仅缺少本地 `mcp/servers.json`，`sync/sync_all.sh` 会按“未配置本地密钥文件”处理并退出 `0`，即跳过本次 MCP 同步但不阻断 push。

### 紧急绕过

```bash
SKILL_BYPASS=1 git commit ...        # 跳过 pre-commit + pre-push 中的 skill-sync 段（仍会跑 sync/sync_all.sh）
SKILL_BYPASS=1 git push ...
git push --no-verify                 # 跳过整个 pre-push（含 sync/sync_all.sh）
```

绕过只应用于无法走完整流程的紧急修复，并应在 commit message / PR 里说明原因。

## 开发建议

- 修改技能前先读 `ios-engineer/SKILL.md` 和目标 `references/*.md`，避免把规则重复写到多个 owner 文件。
- 新增或修改规则 ID 时，先更新 `ios-engineer/references/rule_index.md`，再同步 `SKILL.md` 中的 inline ID。
- 跨文件共享概念变更前先全量搜索相关术语，proposal 中明确覆盖范围。
- 提交前运行 `./scripts/sync-skills.sh --dry-run` 和 `bash ios-engineer/scripts/validate_skill_evolution.sh`。
- 修改托管 preamble 时只改 `scripts/templates/agent-preamble.md.tmpl`，再运行 `./scripts/sync-agent-preamble.sh --dry-run` 检查输出。
- 推送前（或 `SKILL_BYPASS=1` 推送后）手动跑 `./scripts/verify-sync.sh` 确认各已启用缓存与 preamble 状态一致，避免 Agent 侧加载漂移版本。
- 本机专属配置（如 `CURSOR_PROJECT_ROOTS`）写进 `scripts/config.local.sh`（由 `scripts/config.local.sh.example` 复制）；该路径在仓库根 `.gitignore` 中已排除，切勿提交进仓库。
