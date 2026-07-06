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

### Changed
- **IR-001 语义变更**: 从"始终使用简体中文"→"输出语言与用户输入语言一致"

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
