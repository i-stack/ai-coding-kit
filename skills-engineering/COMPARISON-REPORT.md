# skills-engineering vs mattpocock/skills 深度对比分析报告

> 分析日期：2026-07-05

---

## 一、mattpocock/skills 开源库功能分析

该仓库由 TypeScript 专家 Matt Pocock 维护，是一个面向 AI Agent（尤其是 Claude Code）的 **Skill 集合和发布工具链**。核心特点：

| 维度 | 描述 |
|------|------|
| **Skill 结构** | `SKILL.md`（主文件）+ `AGENT-BRIEF.md`（Agent 速览）+ `OUT-OF-SCOPE.md`（范围外） |
| **分类体系** | `engineering/`、`productivity/`、`misc/`、`personal/`、`in-progress/`、`deprecated/` |
| **插件发布** | `.claude-plugin/plugin.json` — 可作为 Claude Code 插件一键安装 |
| **文档深度** | 每个 skill 有独立的 `docs/<skill>.md` |
| **Agent 治理** | `.agents/` 目录包含调用规范和文档写作规范 |
| **仓库范围** | `.out-of-scope/` 声明跨 skill 通用约束 |
| **工程化** | `package.json` + npm 发布 + changeset 版本管理 |
| **工具脚本** | `list-skills.sh`、`link-skills.sh` |

### Skill 清单

#### engineering/ (工程类)
- `triage` — 快速分诊 bug 报告，不做深入修复
- `code-review` — 代码审查，严格检查清单
- `implement` — 从 spec → implementation 全程
- `tdd` — 测试驱动开发
- `diagnosing-bugs` — 系统化 bug 定位
- `research` — 技术调研与方案对比
- `domain-modeling` — 领域建模
- `improve-codebase-architecture` — 架构改进
- `resolving-merge-conflicts` — 合并冲突解决
- `to-prd` — 需求转 PRD

#### productivity/ (生产力类)
- `handoff` — 工作交接记录，确保上下文不丢失
- `grill-me` / `grilling` — 追问-反驳式审查
- `teach` — 以教代学的解释模式
- `writing-great-skills` — Skill 写作方法论（元 Skill）

#### misc/ (杂项)
- `git-guardrails-claude-code` — Git 安全护栏

---

## 二、skills-engineering 的独特优势（mattpocock 没有的）

skills-engineering 在以下方面**远超** mattpocock/skills：

1. **受控演进流水线**（mattpocock 只用 changeset，无 governance）
2. **规则 ID 体系**（IR/SYM/ROUTE/OUT/GR/PA）及 `rule_index.md` 索引
3. **多端自动同步**（Codex/Claude/Cursor/Gemini/Xcode 一键同步）
4. **Pre-commit/Pre-push 守卫**（规则变更必须绑定治理记录）
5. **Usage Ledger**（使用观测与效果评估）
6. **认知对手模式**（Step 0–6 全链条反迎合机制）
7. **ROUTE 精确定向**（症状 → 路由 → 仅加载 2–4 份 reference）
8. **12 类校验**（`validate_skill_evolution.sh` 伞形入口）

---

## 三、发现的问题与修复

### 🐛 问题 1：`verify-sync.sh` preamble 检查不完整

`check_preamble_tilde()` 函数只检查了 cognitive-expansion、logical-reasoning、engineering-discipline 三个 skill 的 preamble 引用，漏掉了 epistemic-integrity 和 problem-analysis。

**修复**：已在 `verify-sync.sh` 第 89–94 行补全。

### 🐛 问题 2：`epistemic-integrity.mdc.tmpl` 模板缺失

sync-manifest 中注册了 `skill:epistemic-integrity`，但 `scripts/templates/` 下没有对应的 `.mdc.tmpl`。

**修复**：已创建该模板，补齐了 Cursor `.mdc` 生成链路。

---

## 四、从 mattpocock/skills 补全的新增功能

| 新增内容 | 说明 |
|---------|------|
| **各 skill 的 `AGENT-BRIEF.md`**（6 个） | Agent 快速决策参考：触发条件、关键行为、不调用情况 |
| **各 skill 的 `OUT-OF-SCOPE.md`**（6 个） | 明确声明 skill 不处理的内容，防止误触发 |
| **`.claude-plugin/plugin.json`** | Claude Code 插件清单，支持一键安装为 Claude 插件 |
| **`.agents/invocation.md`** | Agent 调用规范与多 skill 并行加载流程 |
| **`.agents/writing-docs.md`** | 文档写作规范（命名、ID 格式、结构约定） |
| **`.out-of-scope/repository-scope.md`** | 仓库级范围外声明（安全合规、问题数量限制等） |
| **`docs/*.md`**（6 个） | 每个 skill 的独立使用文档 |
| **`CONTEXT.md`** | 仓库用途与快速上手指南（给人类读） |
| **`CHANGELOG.md`** | 仓库变更日志（与 skill 内部的 evolution 历史互补） |
| **`list-skills.sh`** | 列出所有已注册 skill 及描述 |

---

## 五、功能对比总览

| 功能 | mattpocock/skills | skills-engineering（修复前） | skills-engineering（修复后） |
|------|:---:|:---:|:---:|
| SKILL.md 主入口 | ✅ | ✅ | ✅ |
| AGENT-BRIEF.md | ✅ | ❌ | ✅ |
| OUT-OF-SCOPE.md | ✅ | ❌ | ✅ |
| .claude-plugin/plugin.json | ✅ | ❌ | ✅ |
| .agents/ 调用指南 | ✅ | ❌（仅有 openai.yaml） | ✅ |
| .out-of-scope/ 仓库约束 | ✅ | ❌ | ✅ |
| docs/ 使用文档 | ✅ | ❌ | ✅ |
| CONTEXT.md | ✅ | ❌ | ✅ |
| CHANGELOG.md | ✅ | ❌ | ✅ |
| list-skills.sh | ✅ | ❌ | ✅ |
| 受控演进 governance | ❌ | ✅ | ✅ |
| 规则 ID 体系 | ❌ | ✅ | ✅ |
| 多端自动同步 | ❌ | ✅ | ✅ |
| 认知对手模式 | ❌ | ✅ | ✅ |
| Usage Ledger | ❌ | ✅ | ✅ |
| Pre-commit/Pre-push 守卫 | ❌ | ✅ | ✅ |

---

## 六、各自适合的使用场景

### 选择 mattpocock/skills 的场景
- 需要轻量级、开箱即用的工程 skill 集合
- 使用 TypeScript/Node.js 技术栈
- 偏好 npm 生态和 changeset 版本管理
- 需要快速集成到 Claude Code 插件体系

### 选择 skills-engineering 的场景
- 需要跨平台 Agent 同步（Claude/Codex/Cursor/Gemini/Xcode）
- 需要可审计的规则变更治理
- 需要 iOS/Swift 垂直领域的专业指导
- 需要"认知对手"模式防止 AI 迎合用户
- 需要精确的路由和按需加载机制（ROUTE 定向）
- 需要规则使用效果的可观测性（Usage Ledger）

---

## 七、总结

两个仓库在设计哲学上有本质区别：

- **mattpocock/skills** 是"轻量级技能市场"——注重可发现性、可安装性、社区贡献友好
- **skills-engineering** 是"受控工程规则平台"——注重正确性保证、变更治理、跨平台一致性

修复后，skills-engineering 在 **工程规范性** 上已经基本对齐 mattpocock/skills 的仓库结构（补齐了 AGENT-BRIEF、OUT-OF-SCOPE、插件清单、文档等），同时保留了自身在 **治理、同步、路由、反迎合** 方面的核心差异化优势。
