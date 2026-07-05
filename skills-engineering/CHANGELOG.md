# skills-engineering Changelog

## [Unreleased]

### Added (2026-07-05)
- **AGENT-BRIEF.md**: 为 cognitive-expansion、engineering-discipline、epistemic-integrity、ios-engineer、logical-reasoning、problem-analysis 六个 skill 添加 Agent 快速决策参考
- **OUT-OF-SCOPE.md**: 为所有六个 skill 添加职责边界声明，明确不处理的内容
- **.claude-plugin/plugin.json**: Claude Code 插件清单，支持一键安装
- **.agents/**: Agent 调用规范与文档写作规范
- **.out-of-scope/**: 仓库级范围外声明
- **docs/**: 每个 skill 的独立使用文档
- **CONTEXT.md**: 仓库用途与快速上手指南
- **CHANGELOG.md**: 仓库变更日志（本文件）
- **COMPARISON-REPORT.md**: 与 mattpocock/skills 开源库的深度对比分析报告
- **list-skills.sh**: 列出所有已注册 skill 及描述

### Fixed
- `verify-sync.sh`: 补全 epistemic-integrity 和 problem-analysis 的 preamble 检查
- 创建缺失的 `epistemic-integrity.mdc.tmpl` 模板，补齐 Cursor 生成链路
