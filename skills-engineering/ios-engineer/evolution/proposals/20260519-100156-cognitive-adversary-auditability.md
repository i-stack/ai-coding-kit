# Skill Evolution Proposal

## Metadata
- Proposal ID: 20260519-100156-cognitive-adversary-auditability
- Created At: 2026-05-19 10:01:56 +0800
- Active Version At Creation: v66

## 问题信号
- 当前反迎合修复只新增了规则正文和引用入口，但 active snapshot 未晋升，完整演进校验会报 drift。
- 认知对手模式没有独立 rule ID，usage-audit 无法声明命中；IR-010 也没有 lint 文本锚点，审计只能依赖模型自觉。

## 变更类型
- 新增能力

## 变更内容
- 修改文件：
  - `SKILL.md`：新增 IR-011，要求命中认知对手模式时输出九段认知校准结构。
  - `references/rule_index.md`：登记 IR-011，并把 IR-010 / IR-011 纳入跨文件共享概念索引。
  - `scripts/lint_hit_rules.sh`：新增 IR-010 / IR-011 文本锚点校验。
  - `references/cognitive_adversary_mode.md`、`references/logical_reasoning.md`、`README.md`：保留前置反迎合规则与逻辑性细则。
- 替代或合并旧规则：无。

## 预期收益
- 让“不要迎合用户、主动挑战错误自洽”从说明性文档变为可声明、可审计、可晋升的 active skill 行为。
- 降低模型在 review、架构判断、根因归因等高风险场景里只做弱反驳或省略迎合自检的概率。

## 验证
- 结构校验：`bash scripts/validate_rule_ids.sh` 通过；`SKIP_SNAPSHOT_CONSISTENCY=1 bash scripts/validate_skill_evolution.sh` 通过。
- 场景回放：内置 behavior validation 通过。
- 残留风险：IR-010 的文本锚点只能捕获明显漏写，不能证明推理质量充分；认知对手模式仍只覆盖命中 ios-engineer skill 的任务，不是所有 AI 对话的全局规则。

## 状态
- promoted
