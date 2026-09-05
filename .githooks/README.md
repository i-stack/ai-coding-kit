# .githooks

Git 钩子目录，通过 `install-hooks.sh` 注册为仓库的 `core.hooksPath`。

## 安装

```bash
bash install-hooks.sh
```

会将 `core.hooksPath` 指向此目录，启用以下守卫。

## pre-commit — 技能变更分级守卫

对所有 `skills-engineering/` 下的技能变更实施分级守卫：

1. **结构门（所有技能）**：任何 `SKILL.md` / `AGENT-BRIEF.md` / `OUT-OF-SCOPE.md` /
   `references/*.md` 变更必须通过 `validate-skill-structure.sh`（frontmatter、行数、
   链接、孤儿引用、rule_index 元数据）。
2. **DH-002 卫生门（所有技能）**：变更的运行期入口文档须通过
   `validate-doc-hygiene.sh` 禁用词扫描。
3. **治理门（含 `evolution/` 目录的技能，当前为 ios-engineer）**：
   `SKILL.md` / `references/*.md` 变更必须与 staged proposal 绑定，且
   proposal 的 approval 记录必须已 stage 或已提交。
4. **跨技能协调门**：`.agents/*.md`（invocation/composition 矩阵）或
   `source-truth.json` 变更须通过 `validate-skill-behavior.sh` 一致性校验。

`MINOR_CHANGE=1` 可跳过治理门（仅治理技能生效），`SKILL_BYPASS=1` 跳过全部。

**删除与部分暂存同样受守卫**：删除状态（`git diff --cached --diff-filter=D`）
同样触发门禁（删除 `SKILL.md` FAIL 结构门；删除 `references/*.md` 仍须满足
治理门）；守卫文件禁止部分暂存（staged 版本必须与工作树一致）。

## pre-push — 推送前强制同步并校验

推送前顺序执行：
1. `sync-skills.sh` — 同步 skill 到各 Agent 目录
2. `sync-agent-preamble.sh` — 重写 preamble 托管块
3. `verify-sync.sh` — 校验同步结果
4. `sync/scripts/sync_all.sh` — 同步 MCP 配置到所有平台

任一步骤失败则阻止推送。

## 紧急绕过

```bash
SKILL_BYPASS=1 git commit -m "..."   # 跳过 skill 治理检查
SKILL_BYPASS=1 git push              # 跳过 skill-sync 段
git push --no-verify                 # 跳过所有 hooks
```

绕过仅限紧急修复，需在 commit message 中说明原因。
