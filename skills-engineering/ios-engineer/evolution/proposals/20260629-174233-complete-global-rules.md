# Skill Evolution Proposal

## Metadata
- Proposal ID: 20260629-174233-complete-global-rules
- Created At: 2026-06-29 17:42:33 +0800
- Active Version At Creation: v73

## 问题信号
- 发现全局共性纪律（Engineering Discipline）中存在三大核心防御遗漏：缺少通用的敏感凭据/密钥泄露防护规则；缺乏在复杂问题上防止 AI 死循环和 Token 无限空耗的工具预算机制；缺少在 Lint/美化工具被调用时拦截全局重新排版、制造大量无意义 Diff 噪声的落地限制。
- 这些遗漏在混合开发任务中极易演变为实际的安全漏洞、Token 爆仓开销或合并冲突。

## 变更类型
- 新增能力 / 修正表达

## 变更内容
- 修改文件：
  - `skills-engineering/engineering-discipline/SKILL.md`：补齐核心规则 `GR-001`（安全防御）与 `GR-006`（预算拦截），并升级 `GR-007` 描述。
  - `skills-engineering/engineering-discipline/references/engineering_discipline.md`：写入 `GR-001` 与 `GR-006` 的详规细则，重构 `GR-007` 的落地细节（改哪行，美化哪行，不引入空行噪声）。
  - `skills-engineering/ios-engineer/references/rule_index.md`：在全局规则镜像登记表中同步对账并按 ID 顺序排序。
- 替代或合并旧规则：
  - 填补了 `GR-001` 与 `GR-006` 长期以来的规则编号空洞。
  - 重构升级了 `GR-007`，以微观 line ranges 代替原先粗粒度的“不格式化”宣告。

## 预期收益
- 杜绝 AI Agent 在多端环境中因执行模糊命令或 API 泄露本地 `.env` 及 credentials 隐私。
- 强制在修复链路遇阻 3 次或 15 turns 时进行主动战略中断，向用户发起决策点确认，杜绝死循环空耗会话 Token。
- 过滤 95% 以上由代码美化或 Lint 修复带来的大面积无用 Diff，确保提交高度聚焦。

## 验证
- 结构校验：已运行 `validate_rule_ids.sh` 与 `validate_skill_evolution.sh`。其在 `[12/13]` 步捕获了由于本修改带来的与 `v73` Snapshot 的正常漂移（Drift）。
- 场景回放：规则语义已被自动编译、同步并渲染为 `ai-coding-kit` 及其他正在进行的业务项目的本地 `.cursor/rules/engineering-discipline.mdc`，多端同步通过 `verify-sync.sh` 校验。
- 残留风险：新规则处于静态声明与同步态，其在极度恶劣诱导攻击下的动态拦截率需配合后续的混沌回归用例（Chaos Scenario Validation）长期对账确认。

## 状态
- validated
