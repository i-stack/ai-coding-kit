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
- 规则索引：`ios-engineer/references/rule_index.md`
- 使用观测：`ios-engineer/references/usage_ledger.md` 与 `ios-engineer/evolution/usage/usage.jsonl`
- 回归场景：`ios-engineer/evolution/scenarios/*.json`

## 目录结构

```text
.
├── README.md
├── scripts/
│   ├── bootstrap.sh
│   ├── install-hooks.sh
│   ├── sync-agent-preamble.sh
│   ├── sync-skills.sh
│   └── templates/
├── .githooks/
│   └── pre-commit
└── ios-engineer/
    ├── SKILL.md
    ├── agents/
    ├── references/
    ├── scripts/
    └── evolution/
```

关键目录：

- `ios-engineer/references/`：按主题拆分的技能规则与参考材料，例如并发、布局、网络、性能、审查、迁移、测试、可观测性和自进化治理。
- `ios-engineer/scripts/`：技能演进、校验、提案、验证、晋升、回滚、usage ledger 写入与汇总脚本。
- `ios-engineer/evolution/`：技能演进数据，包括 `proposals/`、`validations/`、`approvals/`、`history/`、`scenarios/`、`usage/`。
- `scripts/`：仓库级脚本，负责安装、同步技能和同步 Agent preamble。
- `.githooks/`：提交守卫，约束技能规则变更必须绑定演进提案和审批记录。

## 快速开始

### 1. 同步技能到本地 Agent 目录

默认同步 `ios-engineer` 到三端 skills 目录：

```bash
./scripts/sync-skills.sh
```

同步目标：

- `~/.codex/skills/ios-engineer`
- `~/.claude/skills/ios-engineer`
- `~/.cursor/skills/ios-engineer`

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

### 2. 同步 Agent preamble

将 `scripts/templates/agent-preamble.md.tmpl` 渲染为各工具的托管规则块：

```bash
./scripts/sync-agent-preamble.sh
```

默认写入：

- `~/.claude/CLAUDE.md`
- `~/.codex/AGENTS.md`

如需同步 Cursor 项目规则，传入冒号分隔的项目根目录：

```bash
CURSOR_PROJECT_ROOTS="/path/to/appA:/path/to/appB" ./scripts/sync-agent-preamble.sh
```

脚本只重写 `<!-- managed-block:ios-engineer:begin ... :end -->` 托管块，保留文件中的其他内容。

### 3. 新机器一键安装

可用 bootstrap 脚本克隆仓库并执行技能同步与 preamble 同步：

```bash
curl -fsSL https://raw.githubusercontent.com/i-stack/skills-engineering/main/scripts/bootstrap.sh | bash
```

常用环境变量：

- `CLONE_TARGET`：仓库克隆位置，默认 `~/Desktop/github/skills-engineering`
- `REF`：要检出的分支、tag 或 commit，默认 `main`
- `SKIP_SKILLS=true`：跳过 `sync-skills.sh`
- `SKIP_PREAMBLE=true`：跳过 `sync-agent-preamble.sh`
- `CURSOR_PROJECT_ROOTS`：透传给 `sync-agent-preamble.sh`

## ios-engineer 技能概览

`ios-engineer/SKILL.md` 是技能主入口，定义：

- 核心铁律：语言、澄清策略、根因优先、最小修复、版本基线读取、格式化边界、覆盖与风险声明。
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

## 提交守卫

安装仓库级 Git hooks：

```bash
bash scripts/install-hooks.sh
```

`.githooks/pre-commit` 会拦截以下规则文件的未治理变更：

- `ios-engineer/SKILL.md`
- `ios-engineer/references/*.md`

如果这些文件有 staged 改动，同一个 commit 必须包含：

- `ios-engineer/evolution/proposals/<id>.md`
- `ios-engineer/evolution/approvals/<id>.json`，或该 approval 已经在历史中存在

紧急绕过：

```bash
SKILL_BYPASS=1 git commit ...
```

绕过只应用于无法走完整演进流程的紧急修复，并应在 commit message 中说明原因。

## 开发建议

- 修改技能前先读 `ios-engineer/SKILL.md` 和目标 `references/*.md`，避免把规则重复写到多个 owner 文件。
- 新增或修改规则 ID 时，先更新 `ios-engineer/references/rule_index.md`，再同步 `SKILL.md` 中的 inline ID。
- 跨文件共享概念变更前先全量搜索相关术语，proposal 中明确覆盖范围。
- 提交前运行 `./scripts/sync-skills.sh --dry-run` 和 `bash ios-engineer/scripts/validate_skill_evolution.sh`。
- 修改托管 preamble 时只改 `scripts/templates/agent-preamble.md.tmpl`，再运行 `./scripts/sync-agent-preamble.sh --dry-run` 检查输出。
