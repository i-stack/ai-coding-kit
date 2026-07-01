# ai-coding-kit

[![Agent Skills](https://img.shields.io/badge/Agent%20Skills-8%2B%20AI%20Coding%20Tools-5856D6)](skills-engineering/README.md)
[![iOS Engineer Skill](https://img.shields.io/badge/iOS%20Engineer-Swift%20%7C%20SwiftUI%20%7C%20UIKit-0A84FF)](skills-engineering/ios-engineer/SKILL.md)
[![MCP Config Sync](https://img.shields.io/badge/MCP%20Config-8%20Platforms-663399)](sync/README.md)
[![Universal RAG Gateway](https://img.shields.io/badge/Universal%20RAG%20Gateway-TypeScript%20%7C%20Fastify-34C759)](docs/universal-rag-gateway.md)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **One kit. All your AI coding tools.** Agent Skills management, MCP configuration sync, iOS engineering rules, and a Universal RAG Gateway — unified for Cursor, CodeBuddy, Codex, Claude Code, Gemini CLI, Continue, Cline, and Xcode Coding Assistant.

**ai-coding-kit** is a local-first AI coding workflow toolkit for developers who use multiple AI coding tools and need a single source of truth for Agent Skills (AI coding skills / coding agent skills / prompt engineering rules), MCP server configuration (Model Context Protocol config), platform settings, and RAG Gateway routing. It replaces scattered config files with one maintainable `env/config.json` and auto-syncs to every AI coding host you use.

中文定位：这是一个面向 AI Coding / Agentic Coding / MCP（模型上下文协议）/ RAG Gateway 的本地工程化工具包。为同时使用多个 AI 编码工具（Cursor、CodeBuddy、Codex、Claude Code、Gemini CLI、Continue、Cline、Xcode Coding Assistant）的开发者提供统一的 Agent Skill 维护、MCP 配置同步、iOS 工程规则和智能网关路由。

## Why ai-coding-kit?

Managing MCP servers, API keys, and Agent Skills across multiple AI coding assistants is a hassle — each tool stores its config in a different format and location. Update one, forget the rest. **ai-coding-kit** solves this:

- **One config file** → auto-generates Cursor mcp.json, Codex TOML, Claude JSON, CodeBuddy models, Continue YAML, and more.
- **One sync command** → `bash sync.sh` updates every tool in seconds.
- **Git-ignored secrets** → `env/config.json` stays local; only the sanitized example is committed.

## Features

> **Agent Skills & Prompt Engineering**
>
> Ready-to-use AI coding skills for engineering discipline, iOS / Swift / SwiftUI / UIKit development, problem analysis, logical reasoning, and cognitive expansion. Version-controlled, syncable, and auditable.

> **MCP Config Sync (Model Context Protocol)**
>
> Define MCP servers once in `env/config.json` and auto-render to Cursor (mcp.json), CodeBuddy (mcp.json + models.json), Codex (config.toml), Claude Code (.claude.json + settings.json), Gemini CLI, Continue (config.yaml), and Cline — with per-server platform filtering.

> **iOS Engineering Rules**
>
> Production-grade rules for Swift, SwiftUI, UIKit, Xcode, concurrency (async/await, actors), networking, performance, testing, code review, migration, and release-risk control — designed for AI coding assistants to produce reliable iOS code.

> **Universal RAG Gateway**
>
> TypeScript / Fastify gateway with OpenAI-compatible API, provider routing, semantic memory, transcript storage, declarative tools, GraphRAG, and telemetry. A local alternative to cloud RAG services.

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

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/i-stack/ai-coding-kit.git
cd ai-coding-kit

# 2. Configure your MCP servers, API keys, and platform settings
#    First run auto-copies from the example template
vim env/config.json

# 3. One-command sync to all your AI coding tools
bash sync.sh
```

`sync.sh` automatically syncs your MCP server config and platform settings to **Cursor, CodeBuddy, Codex, Claude Code, Xcode, Cline, Gemini CLI, and Continue** in one shot.

| Next Steps | Documentation |
|------|---------------|
| Learn Agent Skills in depth | [skills-engineering/README.md](skills-engineering/README.md) |
| Understand MCP config sync | [sync/README.md](sync/README.md) |
| See the config template | [env/config.json.example](env/config.json.example) |
| Explore the iOS engineer skill | [skills-engineering/ios-engineer/SKILL.md](skills-engineering/ios-engineer/SKILL.md) |
| Study the RAG Gateway | [docs/universal-rag-gateway.md](docs/universal-rag-gateway.md) |
| Set up Git hooks | [install-hooks.sh](install-hooks.sh) |

## What is MCP? (Model Context Protocol)

[Model Context Protocol (MCP)](https://modelcontextprotocol.io/) is an open protocol that lets AI coding tools connect to external services — GitHub, Playwright, databases, APIs, design tools — through a standardized interface. **ai-coding-kit** gives you one place to define all your MCP servers and syncs them to every tool that supports MCP.

## Documentation

| Topic | Link |
|------|------|
| Agent Skill engineering | [skills-engineering/README.md](skills-engineering/README.md) |
| iOS engineer skill | [skills-engineering/ios-engineer/SKILL.md](skills-engineering/ios-engineer/SKILL.md) |
| iOS skill rule index | [skills-engineering/ios-engineer/references/rule_index.md](skills-engineering/ios-engineer/references/rule_index.md) |
| Cognitive expansion skill | [skills-engineering/cognitive-expansion/SKILL.md](skills-engineering/cognitive-expansion/SKILL.md) |
| Engineering discipline skill | [skills-engineering/engineering-discipline/SKILL.md](skills-engineering/engineering-discipline/SKILL.md) |
| Logical reasoning skill | [skills-engineering/logical-reasoning/SKILL.md](skills-engineering/logical-reasoning/SKILL.md) |
| Epistemic integrity skill | [skills-engineering/epistemic-integrity/SKILL.md](skills-engineering/epistemic-integrity/SKILL.md) |
| Problem analysis skill | [skills-engineering/problem-analysis/SKILL.md](skills-engineering/problem-analysis/SKILL.md) |
| MCP and platform config sync | [sync/README.md](sync/README.md) |
| Universal RAG Gateway | [docs/universal-rag-gateway.md](docs/universal-rag-gateway.md) |
| Token comparison notes | [docs/token-comparison-results-v2.md](docs/token-comparison-results-v2.md) |

## Repository Layout

| Path | Role |
|------|------|
| [skills-engineering/](skills-engineering/) | Agent Skill sources, references, sync scripts, validation data, and skill evolution workflow. |
| [sync/](sync/) | Renderers and orchestration for local MCP / platform config sync. |
| [env/](env/) | Local configuration template; the real `env/config.json` is intentionally gitignored. |
| [rag-gateway/](rag-gateway/) | Universal RAG Gateway source, tests, providers, retrieval, memory, telemetry, and declarative tool runtime. |
| [docs/](docs/) | Architecture notes, Gateway status, and token comparison reports. |
| [.githooks/](.githooks/) | Repository-managed commit and push guards. |

## Who This Is For

- **Developers using multiple AI coding tools** who want one config to rule them all — define MCP servers and Agent Skills once, sync everywhere.
- **iOS / Swift engineers** who want production-grade AI coding rules for Swift, SwiftUI, UIKit, Xcode, concurrency, testing, code review, and app migration.
- **AI infrastructure builders** experimenting with local memory, semantic retrieval, declarative tools, provider routing, and OpenAI-compatible RAG gateway patterns.
- **Team maintainers** who need a single source of truth for MCP configuration, API keys, and model settings across Cursor, CodeBuddy, Claude Code, Codex, Gemini, Continue, Cline, and Xcode.

## License

[MIT](LICENSE)

