# 文档写作规范

## 文件命名

| 文件 | 命名规则 | 示例 |
|------|---------|------|
| Skill 入口 | `SKILL.md` | `ios-engineer/SKILL.md` |
| 参考细则 | `snake_case.md` | `references/swift_concurrency.md` |
| Agent 简报 | `AGENT-BRIEF.md` | `AGENT-BRIEF.md` |
| 范围外声明 | `OUT-OF-SCOPE.md` | `OUT-OF-SCOPE.md` |
| 规则索引 | `rule_index.md` | `references/rule_index.md` |

## 规则 ID 规范

| 前缀 | 含义 | 示例 |
|------|------|------|
| `IR-` | 核心铁律（Iron Rules） | IR-001, IR-006 |
| `GR-` | 全局规则（Global Rules） | GR-001, GR-010 |
| `ROUTE-` | 任务路由 | ROUTE-001 |
| `SYM-` | 症状映射 | SYM-001 |
| `OUT-` | 输出模板 | OUT-001 |
| `PA-` | 问题分析 | PA-001 |

ID 必须在 `rule_index.md` 中注册并保持 `status=active`。

## 文档卫生约束（doc-hygiene）

所有文档写作/更新任务须遵守 `doc-hygiene` 的 DH-* 规则：文档正文只陈述最终态事实，禁止写入过程叙事（迁移/owner 纠正/此前承载/待平移等），变更过程记入 CHANGELOG / evolution（见 DH-003 的去处约定）。详见 `doc-hygiene` skill。

> 依赖约定：本规范**建议**文档写作类任务在 frontmatter 中 `depends_on: [doc-hygiene]`，以在依赖闭包中显式表达卫生纪律（类比 `ios-engineer/cognitive-expansion/logical-reasoning` 对 `cognitive-calibration` 的 `depends_on`）。但当前实际落地路径是 `.agents/invocation.md` 的关键词触发行 + 本约定，CI 不强制校验「谁声明了依赖 doc-hygiene」。若某次改动未显式声明 `depends_on`，仍须遵守 DH-* 规则——声明是可选的信号增强，不是合规前提。

## 文档结构约定

### SKILL.md 结构
```markdown
---
name: <skill-name>
description: <一句话描述>
---

# <Skill 名称>

## 强制入口 / 核心铁律

## 任务分流 / 路由表

## 输出模板

## 何时加载 / 跳过条件
```

### References 结构
```markdown
# <主题>

## 规则声明
[规则ID] <规则描述>

## 细则
...
```

## 链接约定

- Skill 内引用 reference：相对路径 `references/<file>.md`
- 跨 skill 引用：`../<skill>/references/<file>.md`
- 规则 ID 引用：`[ID]` 格式内联

## 变更约定

对规则文件的任何变更必须通过受控演进流程：
1. 创建 proposal（`create_skill_proposal.sh`）
2. 运行基础校验（`validate_skill_evolution.sh`）
3. 记录验证与审批
4. 运行晋升（`promote_skill_evolution.sh`）
