# skills-engineering

[![Skill](https://img.shields.io/badge/skill-ios--engineer-0A84FF)](ios-engineer/SKILL.md)
![Agent](https://img.shields.io/badge/agent-skill--engineering-34C759)
![Sync](https://img.shields.io/badge/sync-Codex%20%7C%20Claude%20%7C%20Cursor%20%7C%20Gemini-5856D6)

用于维护、同步与演进工程化 Agent Skill 的仓库。

## 当前技能

| 技能 | 类型 | 描述 |
|------|------|------|
| `ios-engineer` | 平台技能 | iOS / Swift / SwiftUI / UIKit / Xcode 工程全生命周期 |
| `cognitive-reasoning` | 全局技能 | 认知与论证纪律：认知对手模式 CAM（Tier 2）+ 论证质量 GR-010 + 真值接地 GR-011~013 + 认知拓展 CE-001~013（合并自 cognitive-calibration / cognitive-expansion / logical-reasoning / epistemic-integrity） |
| `engineering-discipline` | 全局技能 | 工程纪律：安全合规、前置确认、四段式输出 |
| `problem-analysis` | 全局技能 | 问题前置分析：逻辑检验、第一性原理拆解（PA-001/002/003） |
| `classics-reading` | 全局技能 | 克制型古典文献解读：版本先行、标注出处、并列争议、三层分层（字面义/注疏义/个人推演），把「无定论/无出处」设为合法输出 |
| `historical-recall` | 全局技能 | 每个用户任务动手前 best-effort 召回 `.plan-reviews/` 历史线索，作待验证上下文；`plan-grill` PG-006 与 `auto-code-review` ACR-006 委托于此 |
| `doc-hygiene` | 全局技能 | 文档卫生纪律：`.md` 正文只陈述最终态事实，禁写过程叙事 |
| `plan-grill` | 工作流技能 | 需求对齐/盘问锁定计划，产出 PLAN.md（Act 1，基于 grill-me） |
| `cross-model-review` | 工作流技能 | 跨模型对抗审查 PLAN.md，自动发现 CLI（Act 2，基于 grill-me-codex） |
| `auto-code-review` | 工作流技能 | 用户显式启动的跨模型代码审查（Act 3）；默认只读，可显式授权修复 |

本仓库同时提供三类能力：

- Skill 内容源：`ios-engineer/SKILL.md` 与 `ios-engineer/references/` 是技能规则和参考文档的来源。
- 多端同步：把技能同步到 Codex、Claude Code、Cursor、Gemini 的本地 skills 目录，并把托管 preamble 写入对应 Agent 配置。
- 受控演进：用 proposal、validation、approval、history、usage ledger 管理技能变更，避免直接修改规则后失去验证链路。

当前同步实现面向 macOS，并覆盖 Codex、Claude Code、Cursor、Gemini、Cline、Continue、CodeBuddy、Qwen Code 与 Xcode CodingAssistant。统一配置同步入口为仓库根 `sync.sh` 或 `python3 sync/cli/main.py`；本目录的 `scripts/sync-*.sh` 负责技能内容与 preamble。

## 当前状态

- 主技能：`ios-engineer`
- Active 版本：见 `ios-engineer/evolution/active_version.json`
- 技能入口：`ios-engineer/SKILL.md`
- 认知对手模式（platform-agnostic）：真值 owner 为 `cognitive-reasoning`，详规 `cognitive-reasoning/references/cognitive_adversary_mode.md`；`ios-engineer` 经 `depends_on: [cognitive-reasoning]` 引用并维护镜像 `ios-engineer/references/cognitive_adversary_mode.md`
- 认知拓展（打破茧房）：`cognitive-reasoning/` skill（合并自 cognitive-calibration / cognitive-expansion / logical-reasoning / epistemic-integrity，Tier 0/3 形态与 CAM 同一真值 owner）；`sync-skills.sh` 同步全文到各端；preamble 仅声明加载路径，Cursor `.mdc` 由详规自动生成
- 规则索引：`ios-engineer/references/rule_index.md`
- 使用观测：`ios-engineer/references/usage_ledger.md` 与 `ios-engineer/evolution/usage/usage.jsonl`
- 回归场景：`ios-engineer/evolution/scenarios/*.json`
- Skill 真值清单：`source-truth.json`；`validate-source-freshness.py` 校验 Skill 集合、canonical `SKILL.md` 入口和所有 canonical reference 的 `last-verified` 时效。
- 跨 Agent 行为评测：`behavior-evals/scenarios.json`、`run.py`、`evaluate.py`；CLI 基础设施失败与模型行为失败分别统计。

## 目录结构

```text
.
├── README.md
├── ios-engineer/              # iOS 工程主技能
│   ├── SKILL.md               # 技能主入口
│   ├── AGENT-BRIEF.md         # Agent 快速决策参考
│   ├── OUT-OF-SCOPE.md        # 范围外声明
│   ├── references/            # 28+ 参考细则文件
│   ├── scripts/               # 演进治理脚本
│   └── evolution/             # 变更历史与提案
├── cognitive-reasoning/       # 认知与论证纪律技能（合并自 cognitive-calibration / cognitive-expansion / logical-reasoning / epistemic-integrity）
│   ├── SKILL.md
│   ├── AGENT-BRIEF.md
│   ├── OUT-OF-SCOPE.md
│   └── references/
├── engineering-discipline/    # 工程纪律技能（同构）
├── problem-analysis/          # 问题分析技能（同构）
├── classics-reading/          # 克制型经典解读技能（同构）
├── plan-grill/                # 需求盘问锁定计划（Act 1）
├── cross-model-review/        # 跨模型对抗审查 PLAN.md（Act 2）
├── auto-code-review/          # 用户显式启动的代码审查（Act 3）
├── scripts/                   # 仓库级脚本
│   ├── bootstrap.sh
│   ├── sync-skills.sh
│   ├── sync-agent-preamble.sh
│   ├── sync-user-profile.sh      # 跨会话用户画像（env/user-profile.md → ~/.ai-coding-kit/USER.md → preamble 托管块）
│   ├── sync-memory.sh            # 跨会话事件级记忆（MEMORY.md + remember/recall + preamble 托管块）
│   ├── verify-sync.sh
│   ├── list-skills.sh
│   └── templates/
├── docs/                      # 各 skill 使用文档（供人类阅读）
├── .agents/                   # Agent 调用规范与文档写作规范
├── .claude-plugin/            # Claude Code 插件清单（一键安装）
└── .out-of-scope/             # 仓库级范围外声明
```

关键目录：

- `ios-engineer/references/`：按主题拆分的技能规则与参考材料，例如认知对手模式、并发、布局、网络、性能、审查、迁移、测试、可观测性和自进化治理。
- `ios-engineer/scripts/`：技能演进、校验、提案、验证、晋升、回滚、usage ledger 写入与汇总脚本。
- `ios-engineer/evolution/`：技能演进数据，包括 `proposals/`、`validations/`、`approvals/`、`history/`、`scenarios/`、`usage/`。
- `scripts/`：仓库级脚本，负责同步技能、同步 Agent preamble 与同步结果校验；本机专属路径配置统一放在仓库根 `env/secrets.json`。
- `docs/`：各 skill 的独立使用文档，供人类阅读，不参与 Agent 运行时加载。
- `.agents/`：`invocation.md`（多 skill 并行加载规范）、`composition.md`（多技能同时命中时的块发射顺序与冲突裁决）和 `writing-docs.md`（文档写作规范）。
- `.claude-plugin/plugin.json`：Claude Code 插件清单，支持一键安装为 Claude 插件。
- `.out-of-scope/repository-scope.md`：仓库级范围外声明（安全合规等跨 skill 通用约束）。
- 提交/推送守卫：合并入 `ai-coding-kit` 后由仓库根的 [../.githooks/](../.githooks/) 统一管理，详见外层根 README 的「Git 钩子」章节。

## 快速开始

### 1. 同步技能到本地 Agent 目录

推荐同步矩阵：

- `Codex`：需要 `~/.codex/skills/ios-engineer` + `~/.codex/AGENTS.md`。前者提供 `SKILL.md + references/`，后者负责把技能路径接入 system prompt。
- `Claude`：需要 `~/.claude/skills/ios-engineer` + `~/.claude/CLAUDE.md`。只同步 skill 目录不足以保证自动加载。
- `Cursor`：每个 skill 需要 `~/.cursor/skills/<skill>` + 项目内 `.cursor/rules/<skill>.mdc`。全局纪律使用 `alwaysApply: true`；需要用户授权的工作流可提供专用模板并设为 `alwaysApply: false`（如 `auto-code-review`）。
- `Gemini`：需要 `~/.gemini/skills/ios-engineer` + `~/.gemini/GEMINI.md`。前者提供 `SKILL.md + references/`，后者负责作为全局上下文在对话中每次自动加载。
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
- `~/.gemini/skills/ios-engineer`
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
- `GEMINI_DEST_BASE`：默认 `~/.gemini/skills`
- `XCODE_CODEX_DEST_BASE`：默认 `~/Library/Developer/Xcode/CodingAssistant/codex/skills`
- `XCODE_CLAUDE_DEST_BASE`：默认 `~/Library/Developer/Xcode/CodingAssistant/ClaudeAgentConfig/skills`

同步目标门控（各端独立；值：`1 / true / yes / on` 强制开启，`0 / false / no / off` 强制关闭，留空 = 按目标根目录是否存在自动探测）：

- `SYNC_CLAUDE`
- `SYNC_CODEX`
- `SYNC_CURSOR`
- `SYNC_GEMINI`
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

`sync-skills.sh` 默认同步 `skills-engineering/` 下所有含 `SKILL.md` 的目录（含 `cognitive-reasoning`）。`sync-agent-preamble.sh` 的 `sync-manifest` 中 `skill:<name>` 行用于从 skill 详规生成 Cursor `.mdc`；preamble 托管块要求 Agent **读取 skills 目录中的全文**，不得仅用摘要。

默认写入：

- `~/.claude/CLAUDE.md`
- `~/.codex/AGENTS.md`
- `~/Library/Developer/Xcode/CodingAssistant/codex/AGENTS.md`
- `~/Library/Developer/Xcode/CodingAssistant/ClaudeAgentConfig/CLAUDE.md`

同步到 `~/.claude/CLAUDE.md` 时，脚本会清理历史遗留的 Claude router 托管块。
`agents: true` 仅表示 Claude 端允许同步 agent/preamble 能力，不再默认写入自动模型分流规则，
也不再生成旧的分流 agent 文件。

如需同步 Cursor 项目规则，传入冒号分隔的项目根目录：

```bash
CURSOR_PROJECT_ROOTS="/path/to/appA:/path/to/appB" ./scripts/sync-agent-preamble.sh
```

也可以把外部 Cursor 项目根写进 `env/config.json` 的 `paths.cursor_project_roots`。命令行传入的 `CURSOR_PROJECT_ROOTS` 仍然优先，适合一次性覆盖。

Claude / Codex 两端同样遵循 `SYNC_CLAUDE` / `SYNC_CODEX` 门控语义（`1 / 0 / 留空自动探测`）；Cursor 项目规则由 `env/config.json` 的 `paths.cursor_project_roots` 或临时 `CURSOR_PROJECT_ROOTS` 决定，不复用 `SYNC_CURSOR`。
Xcode Codex / Claude 侧分别遵循 `SYNC_XCODE_CODEX` / `SYNC_XCODE_CLAUDE` 门控语义（`1 / 0 / 留空自动探测`），默认写入 `codex/AGENTS.md` 与 `ClaudeAgentConfig/CLAUDE.md`。

脚本只重写 `<!-- managed-block:agent-preamble:begin ... :end -->` 托管块（并兼容迁移旧的 `ios-engineer` 托管块标记），保留文件中的其他内容。

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
- `SKIP_USER_PROFILE=true`：跳过 `sync-user-profile.sh`（跨会话用户画像）
- `SKIP_MEMORY=true`：跳过 `sync-memory.sh`（跨会话事件记忆）
- `CURSOR_PROJECT_ROOTS`：临时覆盖 `env/config.json` 的 `paths.cursor_project_roots`，透传给 `sync-agent-preamble.sh`

### 5. 跨会话记忆（用户画像 + 事件记忆）

对标 Hermes Agent 的持久记忆系统，提供两层互补的长期记忆，均跨会话、跨端共享：

**L0 — 用户画像（`sync-user-profile.sh`）**：用户从 `env/user-profile.md.example` 复制出 `env/user-profile.md`（已 gitignore）手动维护稳定偏好 / 角色 / 约束；`env/user-profile.json` 提供 `auto/on/off` 开关与画像路径配置。脚本把画像同步到 `~/.ai-coding-kit/USER.md`，并在各端 preamble 注入独立的 `user-profile` 托管块（与 agent-preamble 块互不干扰）。

**L1 — 事件级记忆（`sync-memory.sh`）**：交互中累积的纠正、项目约定与决策理由，落在本机 `~/.ai-coding-kit/MEMORY.md`（仓库外，无需 gitignore）。脚本向各端 preamble 注入独立的 `user-memory` 托管块，并把自身复制到 `~/.ai-coding-kit/sync-memory.sh` 作为 Agent 的稳定调用入口：

```bash
# 注入托管块 + 自复制（幂等，已接入 sync-skill-full.sh / bootstrap.sh / cron/run-sync.sh）
bash scripts/sync-memory.sh

# 会话中让 Agent 累积一条记忆（可选 --tag 分类）
~/.ai-coding-kit/sync-memory.sh remember "用户偏好用中文回答，先给结论" --tag 沟通

# 检索记忆（按关键词过滤，或打印全部）
~/.ai-coding-kit/sync-memory.sh recall 中文

# 关闭记忆注入（保留 MEMORY.md 数据）
bash scripts/sync-memory.sh --remove
```

两层记忆与 `user-profile`、`agent-preamble` 托管块标记各自独立，`sync-agent-preamble.sh` 重写 agent-preamble 块时不会破坏它们；`verify-sync.sh` 校验 agent-preamble 块的标记与关键路径，不受新增块影响。

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

## 跨技能协调与 i18n 治理

多个全局技能会在同一轮命中（如 `engineering-discipline` + `plan-grill` + `cognitive-reasoning` 认知对手模式（CAM））。为避免块堆叠、口径打架与读取预算爆炸，约定如下协调契约（详见各 skill 的 `references/`；块发射顺序与冲突裁决另见 `.agents/composition.md`）：

### 多技能叠加口径（D1-D5）

- **前置确认被盘问吸收（GR-002 ↔ PG-000）**：任务描述不清时，`engineering-discipline` GR-002 的「前置确认」不另起独立块；若 `plan-grill` PG-000 已进入盘问，该确认问题被吸收为盘问首问，按「一次只问一个」推进。
- **战略性中断同 anchor 合并（GR-006 ↔ GR-002）**：`GR-006` 战略性中断若在盘问/排查期间触发，其「前置确认」块与 GR-002 同 anchor 合并，≥2 战略分支吸收 GR-002 提问，不重复输出。
- **CAM 机械格式保留（GR-004 ↔ cognitive-reasoning CAM）**：CAM 激活时，其 `Step 0–6 + 置信度` 字段已承载 `逻辑链` / `验证锚点` 的校准语义，二者不另起独立块；但 CAM 字段须按「最终输出格式」原样输出，不得省略或并入其它块。CAM 真值 owner 为 `cognitive-reasoning` skill（platform-agnostic，合并自 cognitive-calibration 等四技能），`ios-engineer` 经 `depends_on: [cognitive-reasoning]` 引用，不再依赖相对路径硬链接。
- **跨块置信度归一**：同一回复内所有置信 / 强度信号（逻辑链结论强度、验证锚点置信度、CAM 置信度、认知校准不确定）必须同源、写同一值，归一到本轮唯一保留的字段。
- **分级读取与预算上限**：各 skill「须先读 references 全文」仅在该 skill 详规确被命中时执行；多技能同轮触发时按 `问题分析(输入) → 工程纪律 / 论证 / 真值接地(论证与交付) → 计划盘问(计划锁定) → 平台 specifics` 分配读取与输出预算，避免叠加爆炸触发 GR-006 中断。

### i18n 镜像治理

- **zh 源 + en-US 镜像**：`SKILL.md` / `references/*.md` 的 zh-CN 为唯一真源；`i18n/en-US/` 是 zh 源的分发镜像（翻译改写产物，`sync-skills.sh` 同步全文到各端）。
- **支持等级政策**：
  - 在 `SKILL.md` frontmatter 正式声明 `supported_locales: [..., en-US]` 的 skill，**必须**提供结构完整的镜像（硬门：源版本 + 规则 ID + 标题/机械锚点 + 源文件 hash）；缺失则 `validate-skill-behavior.sh` WARN 并回退 zh-CN。
  - `experimental_locales: [en-US]` 表示镜像是实验性翻译产物，不构成运行时支持承诺；校验器检查目录与声明一致。
  - 不以「语义完全一致」作为自动硬门（翻译等价难可靠机械判断）；采用**结构硬门 + 人工审核**（见 `tests/test_en_us_mirror_sync.py` 的锚点/同步断言）。
- **同步纪律**：改动任一协调条款的 zh 源，必须同步更新对应 en-US 镜像，否则 `tests/test_en_us_mirror_sync.py` 会 FAIL（zh 源 ↔ en-US 镜像双向锚点断言）。
- **覆盖校验**：`validate-skill-behavior.sh` 在 pre-push 阶段按上述政策支持等级检查 i18n 镜像覆盖与跨技能依赖闭包（`depends_on`）。

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

### 全局协调与 i18n 回归测试

除 `ios-engineer` 自有的演进校验外，仓库级 Python 测试守护「多技能协调条款」与「en-US 镜像」不漂移：

```bash
python3 tests/test_en_us_mirror_sync.py      # zh 源 ↔ en-US 镜像双向锚点断言
python3 tests/test_codebuddy_sync.py         # 含多技能协调断言与全局验收入口校验
```

- `test_en_us_mirror_sync.py`：锁定 `engineering-discipline` / `plan-grill` / `ios-engineer` / `cognitive-reasoning` 的协同条款在 zh 源与 en-US 镜像中成对存在，任一侧漏翻即 FAIL。
- `test_codebuddy_sync.py`：含 `MultiSkillCoordinationTests`（多技能叠加口径）与 `GlobalSkillValidationScriptTests`（校验 `validate-global-skills.sh` 为只读且覆盖完整验收步骤）。
- 一键只读验收：`bash skills-engineering/scripts/validate-global-skills.sh`（见下方「pre-push」）。

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

若只想本地一键跑完整验收闭环，可执行：

```bash
bash skills-engineering/scripts/validate-global-skills.sh
```

该脚本串起结构校验、行为一致性、preamble dry-run、同步验证、integrity `--check-only` 与全局协调回归测试；它是只读验收入口，不会刷新 integrity baseline。

[`.githooks/pre-push`](../.githooks/pre-push) 在推送前顺序执行（默认任一失败即中止 push）：

0. `skills-engineering/scripts/validate-skill-structure.sh` —— 推送前校验全部 `SKILL.md` 的机器可识别结构（frontmatter 必填键、行数上限、本地 `references/` 引用存在性、内部链接可解析、无孤儿 reference）；任一技能结构回归即中止 push。
0b. `skills-engineering/scripts/validate-skill-behavior.sh` —— 推送前跨技能行为/一致性校验（companion 文件齐备、各技能自有规则 ID 在 `references/` 中有定义、`.agents/invocation.md` 触发矩阵覆盖全部技能、i18n 镜像覆盖与跨技能硬链提示）；任一 FAIL 即中止 push。独立运行：`bash skills-engineering/scripts/validate-skill-behavior.sh [<skill>]`。
1. `skills-engineering/scripts/sync-skills.sh` —— 把 `ios-engineer/` 同步到 `~/.claude`、`~/.codex`、`~/.cursor`，以及可选的 `~/Library/Developer/Xcode/CodingAssistant/codex` 和 `~/Library/Developer/Xcode/CodingAssistant/ClaudeAgentConfig` skill 缓存（按 `SYNC_*` 门控与排除规则）。
2. `skills-engineering/scripts/sync-agent-preamble.sh` —— 重写各端 preamble 托管块，并按 `sync-manifest` 的 `skill:*` 生成 `.cursor/rules/*.mdc`。
3. `skills-engineering/scripts/verify-sync.sh` —— 断言各已启用缓存只有 `SKILL.md + references/`、preamble 托管块已 tilde 化。
4. `sync/scripts/sync_all.sh` —— 把 MCP / Codex 共享配置同步到 Cursor / Codex / Claude / Xcode（来自 `sync/` subtree，与本守卫并存）。

任何一步失败都会 `exit 1` 并阻止 `git push`，保证远端指向的版本与本地 Agent 正在加载的版本一致。  
例外：若仅缺少本地 `env/secrets.json`，`sync/scripts/sync_all.sh` 会按"未配置本地密钥文件"处理并退出 `0`，即跳过本次 MCP 同步但不阻断 push。

### 紧急绕过

```bash
SKILL_BYPASS=1 git commit ...        # 跳过 pre-commit + pre-push 中的 skill-sync 段（仍会跑 sync/scripts/sync_all.sh）
SKILL_BYPASS=1 git push ...
git push --no-verify                 # 跳过整个 pre-push（含 sync/scripts/sync_all.sh）
```

绕过只应用于无法走完整流程的紧急修复，并应在 commit message / PR 里说明原因。

## 开发建议

- 修改技能前先读 `ios-engineer/SKILL.md` 和目标 `references/*.md`，避免把规则重复写到多个 owner 文件。
- 新增或修改规则 ID 时，先更新 `ios-engineer/references/rule_index.md`，再同步 `SKILL.md` 中的 inline ID。
- 跨文件共享概念变更前先全量搜索相关术语，proposal 中明确覆盖范围。
- 修改任一技能的 zh 源（`SKILL.md` / `references/*.md`）时，若涉及 en-US 镜像覆盖的协调条款，必须同步更新 `i18n/en-US/`，否则 `tests/test_en_us_mirror_sync.py` 会 FAIL；该测试是 en-US 分发闭环的回归护栏。
- 提交前运行 `./scripts/sync-skills.sh --dry-run` 和 `bash ios-engineer/scripts/validate_skill_evolution.sh`。
- 修改托管 preamble 时只改 `scripts/templates/agent-preamble.md.tmpl`，再运行 `./scripts/sync-agent-preamble.sh --dry-run` 检查输出。
- 推送前（或 `SKILL_BYPASS=1` 推送后）手动跑 `./scripts/verify-sync.sh` 确认各已启用缓存与 preamble 状态一致，避免 Agent 侧加载漂移版本。
- 本机专属配置（如外部 Cursor 项目根）写进仓库根 `env/secrets.json`；该文件已由仓库根 `.gitignore` 排除，切勿提交进仓库。

## 变更记录

所有修改 / 新增 / 删除类变更统一记录在仓库根的 [`CHANGELOG.md`](../CHANGELOG.md)；各 skill 内部规则变化通过 `ios-engineer/evolution/` 治理（proposal 驱动）。本说明文档只描述结构与使用方式，不含版本变更明细。
