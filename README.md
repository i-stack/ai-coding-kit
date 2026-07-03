# ai-coding-kit

[![Agent Skills](https://img.shields.io/badge/Agent%20Skills-8%2B%20AI%20Coding%20Tools-5856D6)](skills-engineering/README.md)
[![iOS Engineer Skill](https://img.shields.io/badge/iOS%20Engineer-Swift%20%7C%20SwiftUI%20%7C%20UIKit-0A84FF)](skills-engineering/ios-engineer/SKILL.md)
[![MCP Config Sync](https://img.shields.io/badge/MCP%20Config-8%20Platforms-663399)](sync/README.md)
[![Universal RAG Gateway](https://img.shields.io/badge/Universal%20RAG%20Gateway-TypeScript%20%7C%20Fastify-34C759)](rag-gateway/README.md)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **One kit. All your AI coding tools.** Agent Skills management, MCP configuration sync, iOS engineering rules, and a Universal RAG Gateway — unified for Cursor, CodeBuddy, Codex, Claude Code, Gemini CLI, Continue, Cline, and Xcode Coding Assistant.

**ai-coding-kit** is a local-first AI coding workflow toolkit. Define your MCP servers, API keys, Agent Skills, and platform settings once — auto-sync to every AI coding host you use.

面向 AI Coding / Agentic Coding / MCP（模型上下文协议）的多工具本地工程化工具包。为同时使用多个 AI 编码工具的开发者提供统一的 Agent Skill 维护、MCP 配置同步、iOS 工程规则和智能网关路由。

## Quick Start

```bash
git clone https://github.com/i-stack/ai-coding-kit.git
cd ai-coding-kit

# 唯一需要编辑的文件
cp env/secrets.json.example env/secrets.json
$EDITOR env/secrets.json

# 一键同步
bash sync.sh
```

## 平台支持

当前主要开发和测试环境为 **macOS**。部分平台模块（如 Codex 同步中的 Xcode 集成、`.zshrc` 导出）在 macOS 外不可用。

欢迎 Windows 用户在 Windows 上验证并提交 PR。核心同步逻辑已尽量保持跨平台，适配改动预计较小。

## 模块

各模块有独立的 README，按需深入：

| 模块 | 说明 | 文档 |
|------|------|------|
| **skills-engineering/** | Agent Skill 内容源、多端同步、受控演进 | [README](skills-engineering/README.md) |
| **sync/** | MCP 配置同步引擎，注入 secrets 渲染到各平台原生格式 | [README](sync/README.md) |
| **env/** | 配置数据源（secrets + MCP 定义 + 平台配置） | [README](env/README.md) |
| **rag-gateway/** | TypeScript / Fastify 通用 RAG 网关（OpenAI 兼容 API） | [README](rag-gateway/README.md) |
| **hooks/** | 项目钩子脚本（xmcp 初始化等） | [README](hooks/README.md) |
| **.githooks/** | Git 提交/推送守卫（pre-commit + pre-push） | [README](.githooks/README.md) |

## Supported AI Coding Tools

| Tool | Synced Config |
|------|--------------|
| **Cursor** | `.cursor/mcp.json` |
| **CodeBuddy** | `.codebuddy/mcp.json`, `models.json`, `skills/` |
| **Claude Code** | `.claude.json`, `settings.json`, `skills/` |
| **Codex CLI** | `.codex/config.toml`, `mcp.generated.toml` |
| **Gemini CLI** | Environment variables |
| **Continue** | `.continue/config.yaml` |
| **Cline** (VSCode) | MCP settings JSON, `skills/` |
| **Xcode Coding Assistant** | Codex + Claude Agent config paths |

## 安装 Git 钩子

```bash
bash install-hooks.sh
```

启用 pre-commit（规则变更治理）和 pre-push（推送前强制同步校验）。详见 [.githooks/README.md](.githooks/README.md)。

## What is MCP?

[Model Context Protocol (MCP)](https://modelcontextprotocol.io/) is an open protocol that lets AI coding tools connect to external services — GitHub, Playwright, databases, APIs, design tools — through a standardized interface. **ai-coding-kit** gives you one place to define all your MCP servers and syncs them to every tool that supports MCP.

## Who This Is For

- **Developers using multiple AI coding tools** — define MCP servers and Agent Skills once, sync everywhere.
- **iOS / Swift engineers** — production-grade AI coding rules for Swift, SwiftUI, UIKit, concurrency, testing, and migration.
- **AI infrastructure builders** — local memory, semantic retrieval, declarative tools, and OpenAI-compatible RAG gateway patterns.
- **Team maintainers** — single source of truth for MCP configuration, API keys, and model settings.

## License

[MIT](LICENSE)

