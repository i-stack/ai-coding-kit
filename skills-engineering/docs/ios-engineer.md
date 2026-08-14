# ios-engineer 使用文档

## 概述

`ios-engineer` 是 skills-engineering 的主技能，覆盖 iOS / Swift / SwiftUI / UIKit / Xcode 工程任务中的架构、并发、网络、UI、性能、测试、审查、迁移和发布风险控制。

## 核心能力

### 1. 认知对手模式
当涉及技术决策、架构取舍、根因归因、审查最终判断或用户强烈确信时，自动启动认知校准流程（Step 0–6），优先接近真实而非维持对话和谐。该模式作为 platform-agnostic 能力，其真值 owner 为独立 `cognitive-calibration` skill，`ios-engineer` 经 `depends_on` 引用（详见该 skill）。

### 2. 智能任务分流
基于 18 条 ROUTE 规则和 7 条 SYM 症状映射，精确路由到最相关的 2–4 份 reference 文件，控制上下文规模。例如：
- Crash / 崩溃 → ROUTE-001（根因排障）
- 架构设计 / 模块拆分 → ROUTE-002（架构设计）
- 网络问题 → ROUTE-008（网络模式）
- 代码审查 → ROUTE-011（审查清单）

### 3. 四段式输出
所有回答遵循：根因 → 为什么 → 修法 → 验证

### 4. 版本前提声明
涉及并发、SwiftUI 行为、可用性 API 时，自动输出显式版本前提（从工程读取或显式假设）。

### 5. 残留风险声明
任何改动必须声明：已覆盖 / 未覆盖 / 残留风险。

## 加载方式

Skill 文件结构：
- `SKILL.md` — 技能主入口（含 frontmatter `description`，是 Cline / Qwen 等 recall-only 端 `use_skill` 命中的唯一闸门；CodeBuddy 已切到 full 模式，见链路 A）
- `AGENT-BRIEF.md` — 触发词参考（随 skill 同步到各端，但当前加载链**不读取它**来判断命中，详见下方说明）
- `references/` — 34 份按主题拆分的规则细则

实际加载链路分两类，取决于目标端是否注入了 ios-engineer preamble 指令：

### A. 已注入 ios-engineer preamble 的目标（Claude / Codex / Gemini / Xcode / CodeBuddy）
`scripts/sync-agent-preamble.sh` 把 `agent-preamble.md.tmpl` 中的指令写入各端全局文件（`~/.claude/CLAUDE.md`、`~/.codex/AGENTS.md` 等），其中硬编码：
> 执行 iOS / Swift / SwiftUI / UIKit / Xcode 工程任务前，必须先加载并遵循 `ios-engineer` SKILL 规则（SKILL.md + references/rule_index.md …）

即「只要是 iOS 任务就强制加载」，命中率最高。Agent 加载完整 `SKILL.md`（约 25KB，已含全部 ROUTE/SYM/IR），再按 ROUTE 表按需读 2–4 份 reference。

### B. recall-only 目标（Cline / Qwen）
这些端只注入 `historical-recall` 托管块，**不注入** ios-engineer 加载指令（`sync-agent-preamble.sh` 中归为 recall 模式）。是否命中完全取决于各端 skill 系统对 `SKILL.md` frontmatter `description` 的匹配（表现为是否调用 `use_skill`）。因此 `description` 的关键词覆盖直接决定命中率——必须包含 Objective-C / Combine / async-await / WidgetKit 及中文触发词（崩溃 / 卡顿 / 布局错位 / 重构 / 代码审查），否则相关任务可能漏命中。

### 关于 AGENT-BRIEF.md
`AGENT-BRIEF.md` 由 `sync-skills.sh` 同步到各端 skills 目录，但**没有任何加载逻辑会先读它来判断命中**（preamble 模板与 `use_skill` 都不引用它）。其丰富的触发词表当前是「已同步但未接入」状态。维护触发词时，应同步更新 `SKILL.md` 的 frontmatter `description`，而非只改 `AGENT-BRIEF.md`，否则改进对命中率无效。

## 常见场景

### 崩溃排障
用户描述：线上用户遇到崩溃
→ Agent 加载：root_cause_enforcement.md + swift_concurrency.md（如涉及并发）

### 架构设计
用户描述：想重构首页，把 MVC 改成 MVVM
→ Agent 加载：architecture_and_network.md + migration_strategy.md

### 代码审查
用户描述：帮我看下这个 PR
→ Agent 加载：review_checklists.md + anti_patterns.md + ios_conventions.md

### 性能优化
用户描述：列表滚动卡顿
→ Agent 加载：performance_optimization.md + observability_logging.md

## 迁移与同步

```bash
# 同步 ios-engineer 到各 Agent 目录
./scripts/sync-skills.sh

# 同步 Agent preamble（包括 ios-engineer 加载指令）
./scripts/sync-agent-preamble.sh
```

同步目标：`~/.codex/skills/ios-engineer`、`~/.claude/skills/ios-engineer`、`~/.cursor/skills/ios-engineer`、`~/.gemini/skills/ios-engineer`。

## 演进治理

规则变更通过受控演进流程：
1. 创建 proposal
2. 运行校验
3. 记录验证与审批
4. 执行晋升

详见 [README.md](../README.md) 的「演进工作流」章节。
