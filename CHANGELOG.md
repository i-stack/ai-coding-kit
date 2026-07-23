# Changelog

All notable changes to ai-coding-kit will be documented in this file.

---

## [3.0.3] — 2026-07-23

### Changed
- **多全局技能叠加口径协调 (D1-D5)**: `engineering-discipline` GR-002 前置确认被 `plan-grill` PG-000 盘问吸收、GR-006 战略性中断与 GR-002 同 anchor 合并；GR-004 与 `ios-engineer` 认知对手模式（CAM）详规对齐——不重复输出语义但保留 CAM 机械格式（`Step 0–6 + 置信度` 字段原样输出、不得省略或并入其它块）；跨块置信度归一到本轮唯一保留字段；新增多 SKILL 叠加分级读取与预算上限；CAM 激活时抑制 preamble 轻量校准段（Tier0/Tier2 互斥扩展到 preamble 层）。ios-engineer 走 `create_skill_proposal` 演进流程（提案 `20260723-173058-cam-fields-preserve-format`）
- **演进记录保留策略**: `ios-engineer/evolution/` 仅保留最近 10 份 proposal/validation/approval 记录，超出窗口的旧记录由 pre-commit 钩子自动淘汰

### Added
- **回归护栏**: 新增 `tests/test_en_us_mirror_sync.py`（zh 源 ↔ en-US 镜像双向锚点断言，防 en-US 静默滞后）与 `skills-engineering/scripts/validate-global-skills.sh`（只读验收入口，串起结构/行为/preamble dry-run/同步验证/integrity `--check-only`/全局协调回归测试）；`tests/test_codebuddy_sync.py` 新增 `GlobalSkillValidationScriptTests` 与多技能协调断言

### Fixed
- **en-US 镜像分发闭环**: `engineering-discipline` / `plan-grill` / `ios-engineer` / `cognitive-expansion` 的 en-US 镜像补齐 D1-D5 协同条款英文翻译，与 zh 源口径一致，可安全分发

---

## [3.0.2] — 2026-07-21

> 分析开源库 `NousResearch/hermes-agent` 后，按优先级补入与其「受控演进」定位契合、且不与其运行时能力冲突的能力。

### Added
- **P0-1 Skill 自我改进闭环**: 新增 `ios-engineer/scripts/suggest_skill_proposals.sh`，读取 `summarize_usage_ledger.sh --json` 的提案候选信号，自动生成 draft proposal（仅 draft，不自动晋升），并用 `evolution/.auto_proposal_registry.json` 去重。对齐 Hermes 学习循环，但落在既有受控演进闸门内（观测 → 建议 → 人工审批）
- **P0-2 agentskills.io 兼容打包/导入/校验**: 新增 `scripts/skill_bundles.sh`（`export` / `validate` / `import` / `list`），把任一 skill 打包成 agentskills.io 兼容产物（`SKILL.md` + `references/` + `bundle.json` 含 sha256），支持从社区 Skills Hub / Hermes 兼容 bundle 导入。导出产物落在 `skills-engineering/.bundles/`（已 gitignore）
- **P1-3 定时同步自动化**: 新增 `cron/`（launchd 默认、`--cron` 可选 crontab），`run-sync.sh` 复用 `sync.sh` + 技能同步 + preamble + 校验，日志滚动保留 30 份
- **P1-4 可选 MCP 服务器目录**: 新增 `env/optional-mcps/`（playwright 改名 `puppeteer` 避免与默认 `env/mcp/playwright.json` 冲突；另含 `filesystem-extra`、`wechat-bridge` 示例）与 `sync/scripts/optional_mcps.sh`（`enable` / `disable` / `list` / `sync`）。`disable` 带护栏：只移除由本工具启用的服务器，绝不删除仓库默认 `env/mcp/*.json`
- **P1-5 跨会话用户画像**: 新增仓库根 `USER.md.example` 与 `scripts/sync-user-profile.sh`，把用户画像同步到 `~/.ai-coding-kit/USER.md` 并注入各端 preamble 的 `user-profile` 托管块（与 agent-preamble 块标记独立、互不干扰）；个人 `USER.md` 已 gitignore。已接入 `sync-skill-full.sh` / `bootstrap.sh`（含 `SKIP_USER_PROFILE`）/ `cron/run-sync.sh`
- **P1-5b 跨会话事件记忆**: 新增 `scripts/sync-memory.sh`，落 `~/.ai-coding-kit/MEMORY.md`（仓库外、跨端共享），提供 `remember "..." [--tag]` / `recall [关键词]` 子命令；向各端 preamble 注入独立的 `user-memory` 托管块，并把脚本自复制到 `~/.ai-coding-kit/sync-memory.sh` 作为 Agent 稳定调用入口。补齐 Hermes 持久记忆中「从交互自动累积」的那一层（user-profile 为静态手维护，memory 为事件级累积，二者互补）。同样接入 `sync-skill-full.sh` / `bootstrap.sh`（`SKIP_MEMORY`）/ `cron/run-sync.sh`
- **P2-6 多平台模型路由抽象**: 新增 `sync/scripts/list_models.sh`（跨平台 model/provider 配置总览，密钥打码）与 `sync/model_routing.md`（统一 Provider 层设计说明）
- **P2-7 子代理并行同步**: `scripts/sync-skills.sh` 支持 `PARALLEL=1`（默认 `MAX_PARALLEL=4`），把 (skill × target) 同步以子代理式后台并行执行
- **P2-8 技能校验加固**: 新增 `scripts/validate-skill-integrity.sh`（sha256 基线比对，发现 ADDED/MODIFIED/REMOVED；`--verify-bundle` 校验 `skill_bundles` 产物 checksum），基线落在 `skills-engineering/.integrity/`（已 gitignore）

---

## [3.0.1] — 2026-07-10

### Added
- `scripts/validate-skill-behavior.sh`: 跨技能行为/一致性校验（companion 文件齐备、自有规则 ID 在 `references/` 有定义、`.agents/invocation.md` 触发矩阵覆盖全部技能、i18n 镜像覆盖与跨技能硬链提示）；接入 `pre-push` 作为结构校验后的硬闸门
  - 加固（后续 review 修复）：discovery 改以"含 SKILL.md 的顶层目录"为准，使缺 companion 的新 skill 也能被捕获；规则 ID 定义校验改为仅在本 skill 的 `references/*.md` 内用结构化锚点（标题 `## ID` / 括号 `[ID]` / 表格 `| ID |`）匹配，不再把 SKILL.md 或 ios-engineer 的 references 并入搜索空间（原本会让检查完全失效或误兜底）
  - `cognitive-expansion` 补 `CE-001~013` 自有规则 ID（`SKILL.md` 声明 + `references/rule_index.md` 表格定义 + `references/examples.md` before/after 形态样本与退化标本）；使其从"纯散文规范"升为可被 `validate-skill-behavior.sh` Check 2 校验的契约，对齐 ios-engineer 的 `rule_index.md` 模式
  - 复查修复：SKILL.md 入口链接 `examples.md`，消除结构门禁 `validate-skill-structure.sh` 的 orphan reference（原 examples.md 从入口不可达）；`validate-skill-behavior.sh` Check 2 增加反向校验（rule_index.md 中 active 表行须被 SKILL.md 声明），使"双向一致"契约成真，并排除 ios-engineer 的 retired / 镜像 ID 误报
  - 复查修复（续）：Check 2 前向定义集合此前经 `DEF_TABLE` 包含所有表行，使 `| ID | retired |` 这类退役行仍可作"有效定义"，与"退役 ID 不应再出现在 SKILL.md"的生命周期约定冲突，且注释自相矛盾。改为仅以 `DEF_ACTIVE`（active 表行）填充 `defined`，删除已无用的 `DEF_TABLE`；负向测试（把某 CE 行改 `retired`）现正确触发前向 FAIL
  - `cognitive-expansion` 收口（P1/P2 中的 C+B）：① Tier 3 `跨域类比` 加护栏（CE-008 细化）——须机制对齐、点名被映射机制，禁陈词/换词类比，附 1 good/1 bad 例（`cognitive_expansion.md` §Tier 3 + `examples.md` 示例 2 复用同一 good 例）；② `流程保障`（预测日志/双会话/每周深潜）由契约段移入`附录`并标注"可选习惯、非门控、不计入 `validate-skill-behavior.sh` 任何 Check"，避免稀释强制部分。三处 CE-008 措辞同步，`SKILL.md`/`rule_index.md`/`cognitive_expansion.md` 一致
- `scripts/verify-review-setup.sh`: 审查链前置自检（plan-reviews 构建产物、auto-code-review 配置、reviewer CLI 可用性）
- `.agents/composition.md`: 多全局技能同时命中时的块发射顺序与冲突裁决

### Changed
- `.agents/invocation.md`: 触发矩阵补齐缺失的 `plan-grill` 与 `cross-model-review`，并指向 `composition.md`
- `cognitive-expansion` / `logical-reasoning` 及 `cognitive_expansion.md`: 对 ios-engineer 的跨技能链接加"条件性"说明，消除非 iOS 环境死链风险
- `ios-engineer/SKILL.md`: en-US 镜像声明改为诚实的部分镜像说明（符合 GR-011）

---

## [3.0.0] — 2026-07-06

### Removed
- **rag-gateway**: 移除 Universal RAG Gateway 模块，由 skills-engineering/plan-reviews 中更轻量的嵌入式知识库方案替代

### Added
- **i18n 分层**: SKILL.md 英文元指令 + en-US 治理层镜像（rule_index / cognitive_adversary_mode / self_evolution），IR-001 从"强制中文"改为"语言匹配用户输入"
- **CI 自动验证**: `.github/workflows/validate.yml` 在每次 PR / push 时自动校验 Rule IDs、Scenario Specs、Ref 新鲜度、Usage Ledger、演进流水线，并扫查硬编码路径
- **CODEOWNERS**: ios-engineer 核心文件自动指定 reviewer
- **CONTRIBUTING.md**: 贡献指南（proposal 驱动演进、翻译贡献、平台支持新增）
- **端到端 recall 跨平台打通**: historical-recall 触发块扩展至 Cline（`~/.cline/rules/`）、CodeBuddy（`~/.codebuddy/CODEBUDDY.md`）、Qwen Code（`~/.qwen/QWEN.md`）与 Continue（`config.yaml` 的 `rules`），与 Claude Code 同构；通用平台只注入 recall 块，不连带 ios-engineer 审计
- **skills-engineering companion 文件**: 各 skill 目录新增 `AGENT-BRIEF.md`（Agent 快速决策参考）和 `OUT-OF-SCOPE.md`（范围外声明）
- **skills-engineering/docs/**: 每个 skill 的独立使用文档
- **skills-engineering/.agents/**: `invocation.md` 和 `writing-docs.md`
- **skills-engineering/.claude-plugin/plugin.json**: Claude Code 插件清单
- **skills-engineering/.out-of-scope/repository-scope.md**: 仓库级范围外声明
- **skills-engineering/scripts/list-skills.sh**: 列出所有已注册 skill 及描述
- **skills-engineering/scripts/templates/epistemic-integrity.mdc.tmpl**: 补齐 Cursor `.mdc` 生成链路

### Changed
- **IR-001 语义变更**: 从"始终使用简体中文"→"输出语言与用户输入语言一致"

### Fixed
- **Continue recall 合并破坏 YAML rules**: `_parse_rules` 的 block scalar 解析会吞掉同级 `- ` sibling 列表项，且 simple 列表项分支缺失 `i += 1` 导致死循环；改为按列表项缩进边界终止 block、保留内部相对缩进，并补 `tests/test_continue_recall.py` 回归测试
- **Continue recall=false 关闭契约未通过校验**: `recall` 已加入 `validate_env_schema.py` 与 `validate_platform_keys.py` 的 Continue 允许字段（engine-handled，不写入 config.yaml），用户配置 `recall: false` 不再被 validator 拦截
- **自定义安装路径未覆盖 recall preamble**: `sync-agent-preamble.sh` 现通过 `resolve_install_root` 读取 `env/secrets.json` 的 `paths` 覆盖（与 Python sync 引擎同源），Cline/CodeBuddy/Qwen 的 recall 目标、存在性判断与 skills 路径均跟随自定义 root
- **Continue recall 注入相对仓库路径**: recall 块改为注入绝对 `skills-engineering/historical-recall/` 与 `node <abs>/dist/cli.js` 路径，脱离 ai-coding-kit 工作目录仍可用；模板 `{{RECALL_CLI_PATH}}` 占位符同样让 cline/codebuddy/qwen 全局上下文使用绝对 CLI 路径
- **paths 覆盖崩溃（H-1）**: `_load_path_overrides` 的 `expanduser()` 在 try 之外，遇 `~不存在用户` 抛 `KeyError`/`RuntimeError` 拖垮整个 sync 引擎；改为 per-key try/except 跳过非法覆盖并告警，补 `test_bogus_tilde_user_does_not_crash`
- **Continue folded 标量被误转 literal（H-2）**: `_parse_rules` 把 `>`(folded) 与 `|`(literal) 都按 literal 存储，`_render_rules_yaml` 永远输出 `  - |`，丢失 folded 语义；现对 `>` 按空格折叠为单行内联值、对 `|` 保留换行块，补 folded/literal 区分与往返测试
- **Continue repo root 硬编码（M-1）**: `_sync_recall` 的 `parents[2]` 改为 `_repo_root()` 向上查找 `skills-engineering/` 标记目录，文件移动后不再静默指向错误路径
- **HR-003 shell 注入面（M-2）**: `historical_recall.md` 及 recall 指令块补充安全要求——query 须以数组/参数形式传递，严禁拼进 shell 字符串执行，避免反引号/`$()` 注入
- **scripts/verify-sync.sh**: 补齐 `epistemic-integrity` 和 `problem-analysis` 的 preamble 检查

---

## [2.0.0] — 2026-02-15

### Added
- skills-engineering 模块：Agent Skill 多平台统一同步（Claude Code / Codex CLI / Cursor / Gemini CLI / CodeBuddy / Continue / Cline / Xcode）
- ios-engineer skill：完整的 iOS 工程规则体系（Swift / SwiftUI / UIKit / 并发 / 测试 / 迁移），含 40+ 规则 ID 和自演进机制
- 5 个全局工程技能：工程纪律、认知拓展、真值接地、论证纪律、问题分析
- sync 模块：MCP 配置同步引擎，从单一数据源渲染到 8 个平台原生格式
- env 模块：统一配置数据源（secrets + MCP + 平台）
- rag-gateway：TypeScript / Fastify 通用 RAG 网关（OpenAI 兼容 API）
- Git hooks：pre-commit 规则变更治理 + pre-push 同步校验

---

## [1.0.0] — 2025-10-01

### Added
- 初始版本：MCP 配置同步核心引擎
- 基础平台支持（Cursor / Claude Code）
- env/ 配置分层（secrets.json + mcp/ + platforms/）
