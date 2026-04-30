# skills-engineering

用于维护与演进工程化 Agent Skill 的仓库，当前主技能为 `ios-engineer`。

## 目录结构

- `ios-engineer/`：iOS 工程技能本体（`SKILL.md` + `references/` + `scripts/` + `evolution/`）。
- `scripts/`：仓库级工具脚本（当前包含 `sync-skills.sh`）。

## 快速开始

### 1) 同步技能到本地 Agent 目录

仓库提供统一同步脚本，会把技能内容同步到以下目录：

- `~/.codex/skills/<skill-name>`
- `~/.claude/skills/<skill-name>`
- `~/.cursor/skills/<skill-name>`

默认同步 `ios-engineer`：

```bash
./scripts/sync-skills.sh
```

常用参数：

```bash
./scripts/sync-skills.sh --dry-run   # 仅预览变更
./scripts/sync-skills.sh --watch     # 持续监听并自动同步
```

可选环境变量：

- `SKILL_NAME`（默认：`ios-engineer`）
- `SOURCE_DIR`
- `CODEX_DEST_BASE`
- `CLAUDE_DEST_BASE`
- `CURSOR_DEST_BASE`

示例：

```bash
SKILL_NAME=ios-engineer ./scripts/sync-skills.sh --dry-run
```

### 2) 查看技能主入口

从这里开始阅读技能规则与分流策略：

- `ios-engineer/SKILL.md`

常用参考文档位于：

- `ios-engineer/references/`

## evolution 目录说明

`ios-engineer/evolution/` 用于技能演进闭环管理，主要包含：

- `proposals/`：演进提案
- `approvals/`：审批记录
- `validations/`：验证记录
- `history/`：版本历史快照

配套自动化脚本位于：

- `ios-engineer/scripts/`

## 开发建议

- 提交前优先执行 `./scripts/sync-skills.sh --dry-run` 检查同步结果。
- 变更 `ios-engineer/references/` 时，建议补充对应的 proposal / validation 记录，保证演进链路可追踪。
