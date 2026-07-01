# Skill Evolution Proposal

## Metadata
- Proposal ID: 20260701-160500-add-test-priority-layers
- Created At: 2026-07-01 16:05:00 +0800
- Active Version At Creation: v73

## 问题信号
- `test_execution_and_repair.md` 中缺少测试执行的优先级分层说明，导致 agent 和开发者在选择测试方式时缺乏明确指引。
- 新增的 `scripts/run_ios_tests.sh` 自适应脚本需要在 references 中有对应的使用文档。

## 变更类型
- 新增能力 / 补充文档

## 变更内容
- 修改文件：
  - `skills-engineering/ios-engineer/references/test_execution_and_repair.md`：新增「优先级分层」表格，明确 MCP → 自适应脚本 → 裸 xcodebuild 的推荐顺序。
  - `skills-engineering/ios-engineer/scripts/run_ios_tests.sh`：新增自适应测试执行脚本，自动发现 workspace/scheme/simulator。
- 补充内容：
  - 自适应脚本的使用说明、环境变量覆盖方式、配置发现逻辑（env var → .xcodebuildmcp/config.yaml → 自动发现）。
  - xcbeautify 自动检测与 JUnit 报告生成说明。

## 预期收益
- agent 在执行测试时能按优先级选择合适的执行方式，减少裸 xcodebuild 的误用。
- CI / 本地手动回归有统一的脚本入口，降低配置门槛。

## 验证
- 结构校验：SKILL.md 未变更，references 变更为纯文档补充，不触发 rule_id 校验。
- 场景回放：脚本在 macOS + Xcode 环境下已验证可通过 workspace/scheme 自动发现正常执行 xcodebuild test。
- 残留风险：低。纯文档 + 工具脚本补充，不影响现有规则逻辑。

## 状态
- validated
