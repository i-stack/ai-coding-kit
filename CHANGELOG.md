# Changelog

## 2026-09-02

- **plan-reviews CLI 调用统一为 preamble 注入的绝对路径（RECALL_CLI_PATH）**: `historical-recall`（SKILL.md HR-003、AGENT-BRIEF、references/rule_index.md、references/historical_recall.md）、`auto-code-review`（references/auto_code_review.md zh 与 en-US 镜像）及 `docs/plan-grill.md`、`docs/auto-code-review.md` 中所有 cwd 相对命令 `node skills-engineering/plan-reviews/dist/cli.js recall|sync|merge` 改为「以本机 preamble 的 historical-recall 段注入的绝对 CLI 路径执行」：CLI 位于 ai-coding-kit 仓库 `skills-engineering/plan-reviews/dist/cli.js`，不在 `~/.codebuddy/` 下，仓库根相对路径仅在 cwd=仓库根时可用。修复 cwd 漂移（如 `~/.codebuddy`）下 node 解析出 `~/.codebuddy/skills-engineering/...` 导致的 `MODULE_NOT_FOUND` 噪音；仓库真值与 `~/.codebuddy/skills/` 已安装副本同步更新。

## 2026-08-14

- **新增 `classics-reading` 全局技能**: 克制型中国古典文献解读（版本先行、标注出处、并列争议、字面义/注疏义/个人推演三层分层），把「无定论/无出处」设为合法输出。含权威版本注疏谱系与可直接粘贴提示词模板两份 reference；已登记 `source-truth.json`、触发矩阵与技能表，并新增 `docs/classics-reading.md`。
- **移除自动配置备份**: 同步前不再备份 Git 已管理的 `env/mcp/` 与 `env/platforms/`；删除备份脚本、配置模板及文档，避免 pre-push 因用户目录备份写入失败而中断。
- **CodeBuddy models 同步改为 marker 机制 (`_managed_by`)**: `sync/platforms/codebuddy.py` 的模型合并逻辑不再依赖外部 sidecar，改为把 `"_managed_by": "ai-coding-kit"` 持久写入 `~/.codebuddy/models.json` 的每个同步模型项。按 `id` 的合并规则：带 marker 的同 id 项由配置整条覆盖（所有字段正确同步）；无 marker 的同 id 项视为用户自有、绝不覆盖；带 marker 但 id 不在配置中的项在下次同步时精确删除；无 marker 且不在配置的项原样保留。已实测验证：codebuddy IDE 能正常识别并回写保留 `_managed_by` 字段（重启 VSCodeX 后模型列表正常）。同步契约文档 `docs/platform-sync-contract.md` 的 CodeBuddy Reference 同步更新。
- **CodeBuddy availableModels 修正为真正整表覆盖**: 文档原声明"整表覆盖"但实现实为"配置优先+保留用户 ID"，二者相反。按用户"保持整列表覆盖"的意图，`_merge_available_models` 改为每次同步直接用配置列表整体替换，用户/UI 添加的 ID 在下次同步时移除。同步契约文档描述与实现现已一致。
- **CodeBuddy 升级认领（legacy claim）**: 旧版本（pre-marker）同步的条目没有 `_managed_by`，升级后会被误判为用户项而失去更新/删除能力。新增 `_claim_legacy_entries`：无 marker 且与配置解析值一致的条目被认领并打上 marker，恢复管理；用户改动过值的条目不认领、原样保留。已知边界：升级前就已在配置中删除的 legacy 条目无法被认领（无配置可匹配），安全侧保留，需手动删除一次。
- **修复 legacy claim 误认领（高优先级发现）**: 认领条件从「仅比较 `url`/`apiKey`」收紧为「与配置解析值精确一致」——键集完全一致（无多余/缺失字段）、所有字段值相等、且配置至少有一个非 `None` 可比对字段。修复两类误认领：与配置共享凭据但自定义其他字段的用户条目、除 `id` 外无任何可比对字段（如双方仅 `id`，`None == None`）的用户条目——此前会被错误认领并在本次合并中被配置整条覆盖，违反「无 marker 同 ID 用户项绝不覆盖」的核心保护。注意：仅缺少凭据不会阻止认领，双方无 `url`/`apiKey` 但其余字段精确一致（如 name/vendor 相同）的条目仍按精确副本认领。配套补齐测试：共享凭据不认领、无可比对字段不认领、无凭据但其余字段一致仍认领、真实的 claim-then-prune 两轮同步流程（sync 1 认领 → config 删除模型后 sync 2 自动剪除）、孤儿保留；文档测试清单与实际覆盖一致。
- **marker 机制推广到其他平台（`_managed_by`）**: CodeBuddy 的 marker 合并引擎泛化到 `sync/core/common.py`（`merge_managed_entries` 处理列表容器、`merge_managed_dict` 处理 name→cfg 字典容器，含 legacy 认领与精确匹配判断），行为与 CodeBuddy `models` 完全一致：配置条目写入时带 `_managed_by`；同键无 marker 目标条目视为用户自有、绝不覆盖；带 marker 但不在配置的条目剪除；无 marker 条目保留。空配置对 dict 容器同样剪除带 marker 条目。Qwen 配置中消失的 provider 类型仍走空列表 merge。CodeBuddy models 改为调用共享引擎，删除本地副本。`merge_managed_dict` 以字典键为身份、不再借用 payload 的 `name` 字段，并原样保留无法打 marker 的非字典用户值。接入范围：MCP servers（`sync_json_mcp` 公共层 + Claude `~/.claude.json`、Cursor `~/.cursor/mcp.json`、Cline `cline_mcp_settings.json`、Gemini `~/.gemini/settings.json`，按 `name` 合并）与 Qwen `modelProviders.*`（按 `id` 合并，同 id 无 marker 用户条目保留、cleanup 只删带 marker 条目）。不再适用并已文档说明：Codex `config.toml`（管理块整体替换已提供块级所有权）与 Continue `config.yaml`（YAML 列表整块替换）。配套测试：`test_common_sync_json_mcp` 覆盖 same-name 用户项、legacy 认领、空配置 prune、非字典用户值保留、payload `name` 字段保留；`test_codebuddy_sync` 的 MCP 断言改为 marker 语义（用户 server 保留、stale 剪除）；`test_qwen_sync` 新增同 id 用户条目保留、带 marker 条目覆盖/剪除、vanished provider-type prune、marker-aware cleanup；Claude/Gemini 平台测试断言 `_managed_by`；文档新增 "Marker Sync Across Platforms" 小节并同步各平台契约。
- 明确 Skill 的正式与实验 locale 契约，并消除英文镜像状态歧义。
- 增加跨 Agent 黄金场景、只读 CLI runner、独立成功评分与基础设施失败分类。
- MCP 定义增加权限、副作用、敏感度、并行、降级和验证 capability 契约。
- 增加仓库级 Skill 真值 manifest 与 reference freshness 门禁。
- Usage Ledger 增加 task/session 关联键与覆盖率，并按证据等级分层统计结果。
- plan-reviews 索引增加逐版本 migration、provenance/trust、prompt-injection signals 及完整同步事务锁。

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
- **P1-4 可选 MCP 服务器目录**: 新增 `env/optional_mcps/`（playwright 改名 `puppeteer` 避免与默认 `env/mcp/playwright.json` 冲突；另含 `filesystem-extra`、`wechat-bridge` 示例）与 `sync/scripts/optional_mcps.sh`（`enable` / `disable` / `list` / `sync`）。`disable` 带护栏：只移除由本工具启用的服务器，绝不删除仓库默认 `env/mcp/*.json`
- **P1-5 跨会话用户画像**: 新增仓库根 `USER.md.example` 与 `scripts/sync-user-profile.sh`，把用户画像同步到 `~/.ai-coding-kit/USER.md` 并注入各端 preamble 的 `user-profile` 托管块（与 agent-preamble 块标记独立、互不干扰）；个人 `USER.md` 已 gitignore。已接入 `sync-skill-full.sh` / `bootstrap.sh`（含 `SKIP_USER_PROFILE`）/ `cron/run-sync.sh`
- **用户画像配置迁移**: `USER.md.example` 迁移并统一命名为 `env/user-profile.md.example`，新增 `env/user-profile.json.example` 管理 `auto/on/off` 开关与画像路径；`sync.sh` 现在会通过 `sync_all.sh` 执行可选用户画像同步。
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
