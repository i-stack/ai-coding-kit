# ai-coding-kit

[![Skill](https://img.shields.io/badge/skill-ios--engineer-0A84FF)](skills-engineering/ios-engineer/SKILL.md)
[![Skills sync](https://img.shields.io/badge/skills_sync-Codex%20%7C%20Claude%20%7C%20Cursor-5856D6)](skills-engineering/README.md)
[![MCP sync](https://img.shields.io/badge/MCP_sync-Cursor%20%7C%20Codex%20%7C%20Claude%20%7C%20Xcode-663399)](sync/README.md)
[![Skills platform](https://img.shields.io/badge/skills-macOS-0A84FF?style=flat-square)](skills-engineering/README.md)
[![MCP platform](https://img.shields.io/badge/MCP-macOS%20%7C%20Linux-555555?style=flat-square)](sync/README.md)

本仓库聚合两套互相关联的本地工程化能力：**Agent Skill 的维护与多端同步**，以及 **MCP / Codex 配置的单源多端同步**。二者可独立使用；一起使用时，可在 Codex、Claude Code、Cursor 与 Xcode 相关路径上保持技能与 MCP 配置同源、少漂移。

| 目录 | 说明 |
|------|------|
| [skills-engineering](skills-engineering/README.md) | 维护、同步与演进工程化 Skill（当前主技能 `ios-engineer`）；含 `SKILL.md`、references、演进提案与校验、同步到各 Agent skills 目录与 preamble。详见该目录 [README](skills-engineering/README.md)。 |
| [env](env/) | 唯一配置源目录：`env/config.json`（gitignored，本机密钥与平台配置）与 `env/config.json.example`（可提交模板）。 |
| [sync](sync/README.md) | 把 `env/config.json` 渲染并同步到 Cursor、Codex、Claude Code 与 Xcode Coding Assistant 等路径。详见该目录 [README](sync/README.md)。 |
| [docs](docs/) | 仓库文档与架构设计。 |
| ↳ [universal-rag-gateway.md](docs/universal-rag-gateway.md) | 通用型自学习 RAG Gateway 架构草案：多端协议适配、混合检索、声明式工具、自学习慢循环，含 MVP 范围与验收条件。[目录](docs/universal-rag-gateway.md#目录) |

## 认知拓展

独立 skill `cognitive-expansion`，与 `ios-engineer` 同级：**单源** `SKILL.md` + `references/cognitive_expansion.md`，经 `sync-skills.sh` 同步 **全文** 到 Codex / Claude / Cursor / Xcode 的 `~/.*/skills/cognitive-expansion/`；Cursor 项目内另生成 `.cursor/rules/cognitive-expansion.mdc`（由详规自动生成，勿手改）。

| 入口 | 路径 |
|------|------|
| Skill 源（唯一维护处） | [skills-engineering/cognitive-expansion/](skills-engineering/cognitive-expansion/) |
| 详规正文 | [skills-engineering/cognitive-expansion/references/cognitive_expansion.md](skills-engineering/cognitive-expansion/references/cognitive_expansion.md) |
| 认知对手（Tier 2） | [skills-engineering/ios-engineer/references/cognitive_adversary_mode.md](skills-engineering/ios-engineer/references/cognitive_adversary_mode.md) |

**同步**：`cd skills-engineering && ./scripts/sync-skill-full.sh`（先 `sync-skills.sh` 全文，再 `sync-agent-preamble.sh` 写入 preamble 加载指令与 Cursor `.mdc`）。新增 skill 时在 `agent-preamble.md.tmpl` 的 `sync-manifest` 加 `skill:<name>`。详见 [skills-engineering/README.md](skills-engineering/README.md)。

**触发层级**：
- **Tier 0（门控）**：默认不触发；仅当本次回答含判断/取舍/归因/设计选择且能产出可证伪盲区时才追加，否则静默
- **Tier 3（加深）**：`【深潜】` / `【拓展】`
- **Tier 2（认知对手）**：`【认知对手模式】` / `【不要迎合】` / `【red team】` — 走 ios-engineer 认知对手全文

## 快速开始

- **技能与 preamble**：在 `skills-engineering` 下按 [skills-engineering/README.md](skills-engineering/README.md) 的「快速开始」执行 `./scripts/sync-skills.sh` 等。
- **MCP / Codex / Claude / Gateway 共享**：复制并编辑 `env/config.json`，然后执行 `bash sync/sync_all.sh`。详见 [sync/README.md](sync/README.md)。

**忽略规则**：敏感文件与本机配置由仓库根目录 [`.gitignore`](.gitignore) 统一管理（例如 `env/config.json`、`skills-engineering/scripts/config.local.sh`）。

## Git 钩子

仓库根级统一管理 `pre-commit` 与 `pre-push`，安装一次同时启用两个 subtree 的守卫：

```bash
bash install-hooks.sh
```

会把 `core.hooksPath` 指向 `.githooks/`：

- [`.githooks/pre-commit`](.githooks/pre-commit)：拦截 `skills-engineering/ios-engineer/SKILL.md` 与 `references/*.md` 的未治理变更（必须同 commit 绑定 evolution proposal + approval）。
- [`.githooks/pre-push`](.githooks/pre-push)：推送前依次跑 skills-engineering 同步链（`sync-skills.sh` → `sync-agent-preamble.sh` → `verify-sync.sh`），再跑 [`sync/sync_all.sh`](sync/sync_all.sh)；默认任一失败中止 push（例外：`env/config.json` 缺失时，`sync_all.sh` 会跳过并退出 `0`，不阻断 push）。

紧急绕过：

```bash
SKILL_BYPASS=1 git commit ...        # 跳过 skill 治理 + skill-sync 链（仍跑 sync/sync_all.sh）
git push --no-verify                 # 跳过整个 pre-push
```

详细行为见各 subtree README 的「Git 钩子」章节。

## 平台说明

技能同步与脚本当前以 **macOS** 下的 Codex、Claude Code、Cursor 为主；MCP 同步支持 macOS 与 Linux。细节以各子目录 README 为准。
