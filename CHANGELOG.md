# Changelog

All notable changes to ai-coding-kit will be documented in this file.

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
