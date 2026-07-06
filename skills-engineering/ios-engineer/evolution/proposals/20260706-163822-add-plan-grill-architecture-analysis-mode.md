# Skill Evolution Proposal

## Metadata
- Proposal ID: 20260706-163822-add-plan-grill-architecture-analysis-mode
- Created At: 2026-07-06 16:38:22 +0800
- Active Version At Creation: v73

## 问题信号
- plan-grill PG-005 盘问中涉及少量文件（通常 ≤10 个）的跨文件依赖关系时，需要委托 ios-engineer 做快速架构分析；但现有 `architecture_analysis.md` 只有完整 Phase 1-4 流程（含健康度评分、10 必备字段、重构路线图），缺少轻量级「只描述现状、不评价优劣」的快速模式。
- plan-grill 与 ios-engineer 协作时，需要明确委托契约：输出格式、纪律边界、与完整架构体检的区别。

## 变更类型
- 新增能力

## 变更内容
- 修改文件：
  - `references/architecture_analysis.md`：新增「快速架构分析模式（plan-grill PG-005 委托用）」节，定义适用条件、输出格式、纪律约束。
- 替代或合并旧规则：无替代；快速模式与完整 Phase 1-4 是互补关系，不存在重叠或冲突。

## 预期收益
- plan-grill PG-005 委托 ios-engineer 时，有明确的轻量级输出契约，避免产出不必要的健康度评分、技术债等级或重构建议。
- 快速模式输出只包含涉及文件、调用链、修改影响面、潜在风险 4 项，减少上下文浪费。
- 纪律约束（不评价好坏、不输出优化建议、影响面必须具体到文件/方法）防止模糊结论。

## 验证
- 结构校验：SKILL.md 未变更，references 变更为纯文档补充，不触发 rule_id 校验。
- 场景回放：无新增场景；快速模式是 PG-005 的委托子流程，由 plan-grill 侧调用触发。
- 残留风险：低。纯文档补充，不影响现有架构分析流程和规则逻辑。

## 状态
- validated
