# Skill Evolution Proposal

## Metadata
- Proposal ID: 20260602-174359-resolve-skill-conflict-clarifications
- Created At: 2026-06-02 17:43:59 +0800
- Active Version At Creation: v72

## 问题信号
- 规则冲突审计发现 3 个软冲突 / 执行歧义：MCP 优先与裸 `xcodebuild` 示例容易被误读为并列默认路径；认知对手 Step 0-6 与工程输出骨架的拼接顺序不够明确；测试策略短模板的"未覆盖风险"容易被误用为 GR-008 "残留风险声明"。

## 变更类型
- 修正表达

## 变更内容
- 修改文件：
  - `references/mcp_control.md`
  - `references/test_execution_and_repair.md`
  - `references/cognitive_adversary_mode.md`
  - `references/testing_strategy.md`
- 替代或合并旧规则：不新增规则 ID；仅收紧既有规则之间的优先级与拼接关系。

## 预期收益
- 降低 agent 在 iOS 测试执行时绕过 XcodeBuildMCP 的概率。
- 降低审查 / 技术判断场景中用工程骨架替代认知校准 Step 0-6 的概率。
- 降低测试策略短模板误替代 GR-008 三字段声明的概率。

## 验证
- 结构校验：运行 `validate_skill_proposal.sh` 和晋升后的 `validate_skill_evolution.sh`。
- 场景回放：本次为表达澄清，不新增场景；依赖现有 behavior validation 覆盖 review / network / snapshot 契约。
- 残留风险：没有新增 rule ID 或场景，因此只能防止已识别的软冲突；未覆盖未来新增 ref 中再次引入同类歧义。

## 状态
- promoted
