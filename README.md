# ai-coding-kit

[![Skill](https://img.shields.io/badge/skill-ios--engineer-0A84FF)](skills-engineering/ios-engineer/SKILL.md)
[![Skills sync](https://img.shields.io/badge/skills_sync-Codex%20%7C%20Claude%20%7C%20Cursor-5856D6)](skills-engineering/README.md)
[![MCP sync](https://img.shields.io/badge/MCP_sync-Cursor%20%7C%20Codex%20%7C%20Claude%20%7C%20Xcode-663399)](mcp-sync/README.md)
[![Skills platform](https://img.shields.io/badge/skills-macOS-0A84FF?style=flat-square)](skills-engineering/README.md)
[![MCP platform](https://img.shields.io/badge/MCP-macOS%20%7C%20Linux-555555?style=flat-square)](mcp-sync/README.md)

本仓库聚合两套互相关联的本地工程化能力：**Agent Skill 的维护与多端同步**，以及 **MCP 服务清单的单源多端同步**。二者可独立使用；一起使用时，可在 Codex、Claude Code、Cursor 与 Xcode 相关路径上保持技能与 MCP 配置同源、少漂移。

| 目录 | 说明 |
|------|------|
| [skills-engineering](skills-engineering/README.md) | 维护、同步与演进工程化 Skill（当前主技能 `ios-engineer`）；含 `SKILL.md`、references、演进提案与校验、同步到各 Agent skills 目录与 preamble。详见该目录 [README](skills-engineering/README.md)。 |
| [mcp-sync](mcp-sync/README.md) | 以单份 `mcp-servers.json` 同步 MCP 到 Cursor、Codex、Claude Code 与 Xcode Coding Assistant 等路径。详见该目录 [README](mcp-sync/README.md)。 |

## 认知拓展

独立 skill `cognitive-expansion`，与 `ios-engineer` 同级：**单源** `SKILL.md` + `references/cognitive_expansion.md`，经 `sync-skills.sh` 同步 **全文** 到 Codex / Claude / Cursor / Xcode 的 `~/.*/skills/cognitive-expansion/`；Cursor 项目内另生成 `.cursor/rules/cognitive-expansion.mdc`（由详规自动生成，勿手改）。

| 入口 | 路径 |
|------|------|
| Skill 源（唯一维护处） | [skills-engineering/cognitive-expansion/](skills-engineering/cognitive-expansion/) |
| 详规正文 | [skills-engineering/cognitive-expansion/references/cognitive_expansion.md](skills-engineering/cognitive-expansion/references/cognitive_expansion.md) |
| 认知对手（Tier 2） | [skills-engineering/ios-engineer/references/cognitive_adversary_mode.md](skills-engineering/ios-engineer/references/cognitive_adversary_mode.md) |

**同步**：`cd skills-engineering && ./scripts/sync-skill-full.sh`（先 `sync-skills.sh` 全文，再 `sync-agent-preamble.sh` 写入 preamble 加载指令与 Cursor `.mdc`）。新增 skill 时在 `agent-preamble.md.tmpl` 的 `sync-manifest` 加 `skill:<name>`。详见 [skills-engineering/README.md](skills-engineering/README.md)。

**触发语**：默认 Tier 0 尾注；`【深潜】` / `【拓展】`；`【认知对手模式】` 等走 ios-engineer 认知对手全文。

## 快速开始

- **技能与 preamble**：在 `skills-engineering` 下按 [skills-engineering/README.md](skills-engineering/README.md) 的「快速开始」执行 `./scripts/sync-skills.sh` 等。
- **MCP**：在 `mcp-sync` 下按 [mcp-sync/README.md](mcp-sync/README.md) 配置并执行 `sync_all.sh` 等。

**忽略规则**：敏感文件与本机配置由仓库根目录 [`.gitignore`](.gitignore) 统一管理（例如 `mcp-sync/mcp-servers.json`、`skills-engineering/scripts/config.local.sh`，以及 `mcp-sync/lanhu-mcp/` 下的 Python 虚拟环境、缓存与本地密钥路径）。

## Git 钩子

仓库根级统一管理 `pre-commit` 与 `pre-push`，安装一次同时启用两个 subtree 的守卫：

```bash
bash install-hooks.sh
```

会把 `core.hooksPath` 指向 `.githooks/`：

- [`.githooks/pre-commit`](.githooks/pre-commit)：拦截 `skills-engineering/ios-engineer/SKILL.md` 与 `references/*.md` 的未治理变更（必须同 commit 绑定 evolution proposal + approval）。
- [`.githooks/pre-push`](.githooks/pre-push)：推送前依次跑 skills-engineering 同步链（`sync-skills.sh` → `sync-agent-preamble.sh` → `verify-sync.sh`），再跑 [`mcp-sync/sync_all.sh`](mcp-sync/sync_all.sh)；默认任一失败中止 push（例外：`mcp-sync/mcp-servers.json` 缺失时，`sync_all.sh` 会跳过并退出 `0`，不阻断 push）。

紧急绕过：

```bash
SKILL_BYPASS=1 git commit ...        # 跳过 skill 治理 + skill-sync 链（仍跑 mcp-sync）
git push --no-verify                 # 跳过整个 pre-push
```

详细行为见各 subtree README 的「Git 钩子」章节。

## 平台说明

技能同步与脚本当前以 **macOS** 下的 Codex、Claude Code、Cursor 为主；MCP 同步支持 macOS 与 Linux。细节以各子目录 README 为准。
