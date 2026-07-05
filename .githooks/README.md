# .githooks

Git 钩子目录，通过 `install-hooks.sh` 注册为仓库的 `core.hooksPath`。

## 安装

```bash
bash install-hooks.sh
```

会将 `core.hooksPath` 指向此目录，启用以下守卫。

## pre-commit — 规则变更必须绑定治理记录

拦截对以下文件的未治理变更：
- `skills-engineering/ios-engineer/SKILL.md`
- `skills-engineering/ios-engineer/references/*.md`

如果这些文件被 staged，同一个 commit 必须包含对应的 proposal 和 approval 记录。

## pre-push — 推送前强制同步并校验

推送前顺序执行：
1. `sync-skills.sh` — 同步 skill 到各 Agent 目录
2. `sync-agent-preamble.sh` — 重写 preamble 托管块
3. `verify-sync.sh` — 校验同步结果
4. `sync_all.sh` — 同步 MCP 配置到所有平台

任一步骤失败则阻止推送。

## 紧急绕过

```bash
SKILL_BYPASS=1 git commit -m "..."   # 跳过 skill 治理检查
SKILL_BYPASS=1 git push              # 跳过 skill-sync 段
git push --no-verify                 # 跳过所有 hooks
```

绕过仅限紧急修复，需在 commit message 中说明原因。
