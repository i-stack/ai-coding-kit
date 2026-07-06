---
layout: home
title: ai-coding-kit
hero:
  name: ai-coding-kit
  text: One Kit. All AI Coding Tools.
  tagline: Agent Skills management, MCP configuration sync, and iOS engineering rules — unified for 8+ AI coding platforms.
  image: false
  actions:
    - theme: brand
      text: Get Started
      link: /ios-engineer/
    - theme: alt
      text: View on GitHub
      link: https://github.com/i-stack/ai-coding-kit

features:
  - icon: 🧠
    title: Agent Skills Engineering
    details: Define skills once, sync to Claude Code, Codex CLI, Cursor, Gemini CLI, CodeBuddy, Continue, Cline, and Xcode Coding Assistant — with structured evolution governance.
  - icon: ⚙️
    title: MCP Config Sync
    details: Single source of truth for MCP servers, API keys, and model settings. Auto-render to each platform's native config format.
  - icon: 🍎
    title: iOS Engineering Rules
    details: Production-grade Swift / SwiftUI / UIKit rules with 40+ rule IDs, symptom routing, task triage, and auto-evolution — maintained by an Agent Skill system.
  - icon: 🔒
    title: Global Engineering Discipline
    details: Six global skills spanning security compliance, epistemic integrity, logical reasoning, cognitive expansion, and problem analysis — apply to any platform.
  - icon: 🚀
    title: Quick Start
    details: One clone, one secrets file, one sync command. Supports Homebrew and npm installation.
---

## Quick Start

```bash
# Clone & configure
git clone https://github.com/i-stack/ai-coding-kit.git
cd ai-coding-kit

# Edit your secrets (the only file you need to touch)
cp env/secrets.json.example env/secrets.json
$EDITOR env/secrets.json

# One command to sync everything
bash sync.sh
```

### Or install via package manager

```bash
# Homebrew
brew install i-stack/tap/ai-coding-kit

# npm
npm install -g @i-stack/ai-coding-kit
```

## Platform Support

| Tool | What Gets Synced |
|------|-----------------|
| **Cursor** | `.cursor/mcp.json` |
| **CodeBuddy** | `.codebuddy/mcp.json`, `models.json`, `skills/` |
| **Claude Code** | `.claude.json`, `settings.json`, `skills/` |
| **Codex CLI** | `.codex/config.toml`, `mcp.generated.toml` |
| **Gemini CLI** | Environment variables |
| **Continue** | `.continue/config.yaml` |
| **Cline** (VSCode) | MCP settings JSON, `skills/` |
| **Xcode Coding Assistant** | Codex + Claude Agent config paths |

## Modules

| Module | Description |
|--------|------------|
| **skills-engineering/** | Agent Skill content, multi-platform sync, governed evolution |
| **sync/** | MCP config sync engine — injects secrets, renders to native formats |
| **env/** | Config data source (secrets + MCP definitions + platform configs) |
| **hooks/** | Project hooks (xmcp init, etc.) |
| **.githooks/** | Git commit/push guards (pre-commit + pre-push) |
