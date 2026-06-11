# Skill Evolution Proposal

## Metadata
- Proposal ID: 20260608-113813-add-engineering-quality-gates
- Created At: 2026-06-08 11:38:13 +0800
- Active Version At Creation: v73

## 问题信号
- 用户希望把“优秀架构设计与解耦能力”和“代码规范与质量保障”沉淀进项目公用 SKILL。现有规则已覆盖分层、测试、CI，但缺少跨文件一致的工程交付质量门槛，容易把这些原则写成口号或在局部修复中漏掉边界 / 测试 / CI 影响声明。

## 变更类型
- 修正表达 + 新增能力

## 变更内容
- 修改文件：
  - `skills-engineering/engineering-discipline/references/engineering_discipline.md`
  - `skills-engineering/ios-engineer/references/architecture_and_network.md`
  - `skills-engineering/ios-engineer/references/testing_strategy.md`
  - `skills-engineering/ios-engineer/references/build_release_and_ci.md`
- 替代或合并旧规则：
  - 不新增 rule ID；作为 GR-005 最小修复优先的细化门槛，并由 iOS 架构、测试、CI owner 文件承接落地细则。

## 预期收益
- 避免把 MVVM、组件化、测试体系、CI/CD 作为泛化口号直接塞入 SKILL。
- 让架构边界、公共 API、测试分层和 CI 门禁在实现 / 修复 / 重构输出中有明确触发条件。
- 降低跨层偷渡、公共 API 过度公开、只本地验证不说明 CI 覆盖的输出失真。

## 验证
- 结构校验：已运行 `bash scripts/validate_skill_proposal.sh evolution/proposals/20260608-113813-add-engineering-quality-gates.md`，结果通过；验证记录见 `evolution/validations/20260608-113813-add-engineering-quality-gates.json`。
- 场景回放：本次为规则表达与 owner 落点补强，先不追加场景回放；若后续真实任务仍漏掉质量门槛，再补 architecture / migration 类场景。
- 残留风险：未新增可机械校验的 rule ID，当前依赖人工判断这些门槛是否命中；后续若需要强制审计，可单独提案新增 GR 编号和 lint 信号。

## 状态
- approved
