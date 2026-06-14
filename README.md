# ai-coding-kit

[![Agent Skills](https://img.shields.io/badge/Agent%20Skills-Codex%20%7C%20Claude%20%7C%20Cursor-5856D6)](skills-engineering/README.md)
[![iOS Engineer Skill](https://img.shields.io/badge/iOS%20Engineer-Swift%20%7C%20SwiftUI%20%7C%20UIKit-0A84FF)](skills-engineering/ios-engineer/SKILL.md)
[![MCP Config Sync](https://img.shields.io/badge/MCP%20Config-Cursor%20%7C%20Codex%20%7C%20Claude%20%7C%20Xcode-663399)](sync/README.md)
[![Universal RAG Gateway](https://img.shields.io/badge/Universal%20RAG%20Gateway-TypeScript%20%7C%20Fastify-34C759)](docs/universal-rag-gateway.md)

**ai-coding-kit** is a local AI coding workflow kit for maintaining Agent Skills, syncing MCP configuration, and experimenting with a Universal RAG Gateway. It is built for Codex, Claude Code, Cursor, Xcode Coding Assistant, and OpenAI-compatible clients that need shared engineering rules, tool configuration, memory, retrieval, and provider routing.

中文定位：这是一个面向 AI Coding / Agentic Coding / iOS Engineering / MCP / RAG Gateway 的本地工程化工具包，用于维护 Agent Skill、同步多端 MCP 配置，并沉淀可审计的工程规则与网关架构。

## Overview

This repository has three connected parts:

| Area | Purpose | Start Here |
|------|---------|------------|
| Agent Skill engineering | Maintain, sync, and evolve reusable AI coding skills for Codex, Claude Code, Cursor, and Xcode-related paths. | [skills-engineering/README.md](skills-engineering/README.md) |
| MCP and platform config sync | Render one local configuration source into Cursor, Codex, Claude Code, and Xcode host formats. | [sync/README.md](sync/README.md) |
| Universal RAG Gateway | Explore an OpenAI-compatible gateway with provider routing, transcript storage, semantic memory, declarative tools, telemetry, and budget planning. | [docs/universal-rag-gateway.md](docs/universal-rag-gateway.md) |

## Core Capabilities

- **Agent Skills**: source-managed skills for engineering discipline, iOS / Swift / SwiftUI / UIKit work, problem analysis, logical reasoning, epistemic integrity, and cognitive expansion.
- **Multi-host sync**: one local config template for MCP servers, shared environment values, and platform-specific settings across AI coding tools.
- **iOS engineering rules**: an auditable `ios-engineer` skill for architecture, concurrency, networking, UI, performance, testing, review, migration, and release-risk control.
- **Gateway architecture**: a TypeScript / Fastify Universal RAG Gateway with OpenAI-compatible routing, provider adapters, memory, tool execution, GraphRAG direction, and observability.

## Quick Start

| Task | Documentation |
|------|---------------|
| Set up or sync Agent Skills | [skills-engineering/README.md](skills-engineering/README.md) |
| Configure MCP and platform settings | [sync/README.md](sync/README.md) |
| Create local config from the template | [env/config.json.example](env/config.json.example) |
| Inspect the iOS engineer skill | [skills-engineering/ios-engineer/SKILL.md](skills-engineering/ios-engineer/SKILL.md) |
| Study the Gateway design and current implementation status | [docs/universal-rag-gateway.md](docs/universal-rag-gateway.md) |
| Install repository-managed Git hooks | [install-hooks.sh](install-hooks.sh) |

## Documentation

| Topic | Link |
|------|------|
| Agent Skill engineering | [skills-engineering/README.md](skills-engineering/README.md) |
| iOS engineer skill source | [skills-engineering/ios-engineer/SKILL.md](skills-engineering/ios-engineer/SKILL.md) |
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

- Developers who want reusable Agent Skills for Codex, Claude Code, Cursor, or Xcode workflows.
- iOS / Swift engineers who want explicit AI coding rules for Swift, SwiftUI, UIKit, Xcode, testing, review, migration, and release work.
- AI infrastructure builders experimenting with local memory, retrieval, declarative tools, provider routing, and OpenAI-compatible gateway patterns.
- Maintainers who want one source of truth for MCP configuration across multiple AI coding hosts.

