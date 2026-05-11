# Skill Evolution Proposal

## Metadata
- Proposal ID: 20260511-161346-add-mcp-priority-mapping-to-mcp-control
- Created At: 2026-05-11 16:13:46 +0800
- Active Version At Creation: v65

## 问题信号
- 仓库内 `mcp-sync/mcp-servers.json` 已把 7 个 MCP server（github / playwright / lanhu / apifox / filesystem / shell / XcodeBuildMCP）同步到三家宿主（Claude Code / Cursor / Codex），但 SKILL.md 与 mcp_control.md 没有任何"什么 iOS 场景优先用哪个 MCP"的指引。
- 后果：模型在 iOS 工程任务（构建 / Archive / 模拟器 / 接口契约对齐 / 设计稿对照）里默认拼裸命令（`xcodebuild` / `xcrun simctl` / `gh pr view` / 翻接口截图肉眼比对），浪费 MCP 投入；同样的请求在不同 session 里走不同工具路径，行为不可预测。
- ROUTE-016 主读 mcp_control.md 当前只覆盖"工具调用预算 / 子代理分流 / 防循环"，没有覆盖"MCP 选用偏好"，导致用户提"该用 MCP 还是裸命令"时，skill 没有可指向的位置。
- 现状：MCP 是宿主层注入的工具，模型默认能见，但"见到 ≠ 优先选用"——需要在 skill 文档层显式表达偏好。

## 变更类型
- 新增能力（追加路由偏好与 ref 详细映射；不改任何规则 ID、不改输出模板、不改 IR）

## 变更内容
- 修改文件：
  - `references/mcp_control.md`：末尾新增 `## iOS 场景 MCP 优先映射` 节，含 6 行映射表（场景 / 优先 MCP / 替代做法 / 触发关键词）+ 5 条调用约束（不绕过预算 / 防循环、失败 2 次回退、宿主未注入时不假装、回退须显式说明原因）。目录同步追加该节标题。
  - `SKILL.md`：
    - ROUTE-008 追加子项 `优先 MCP：apifox（接口字段对齐 / 错误码契约取证 / schema 校验）`，引到 mcp_control.md §iOS 场景 MCP 优先映射。
    - ROUTE-013 追加子项 `优先 MCP：XcodeBuildMCP（构建 / Archive / 模拟器 / 跑测试 / 读 Build Settings）`，明确"不要直接拼 xcodebuild / xcrun simctl"。
    - ROUTE-016 标题字面追加 `MCP 优先映射` 关键词；TRIGGER 行追加 `该用哪个 MCP / MCP 还是裸命令` 触发词。
  - `references/rule_index.md`：ROUTE-016 摘要列同步追加 `MCP 优先映射`，兑现"任务分流主关键词集"的修改协议（owner=SKILL.md ROUTE 表，必须同步本表摘要列）。
- 替代或合并旧规则：本提案不替代任何 ID；新增的是路由偏好与 ref 详细映射，与既有 IR / SYM / ROUTE / OUT 规则正交。ROUTE-016 职责扩展但 ID 不变（关键词集变化已同步 rule_index.md）。

## 预期收益
- 模型在构建 / 接口契约 / 设计稿 / 仓库取证任务里默认走对应 MCP，减少裸命令拼接，提升结果可靠性与跨 session 行为一致性。
- ROUTE-016 显式纳入"MCP 优先映射"，用户问"该用哪个 MCP" 时有明确路由落点，不再漂到散文回答。
- 调用约束（失败 2 次回退、宿主未注入时不假装）兜住"MCP 不可用 / 反馈慢"的退化场景，避免静默失败。

## 验证
- 结构校验：scripts/validate_skill_evolution.sh 1-11 步全 PASS（YAML / SKILL 大小 / 引用文件存在 / 分层守卫 / 内部链接 / 场景规格 / rule IDs 双向 39 active / usage ledger / 无孤儿引用 / 唯一所有权 + retired 字面回归 / 阈值文档脚本同步）。第 12 步 snapshot consistency 在 promote 之前预期 FAILED，promote 写 v66 快照后归零。scripts/validate_rule_ids.sh PASS（39/41/39）。
- 场景回放：mcp-control 场景。覆盖点：用户问"iOS 构建该用 MCP 还是裸命令"时，skill 主读 ROUTE-016 → mcp_control.md §iOS 场景 MCP 优先映射，给出"优先 XcodeBuildMCP，宿主未注入时回退裸命令并说明原因"。
- 残留风险：
  - 映射表是路由偏好，不是铁律。当 MCP 反馈速度明显慢于裸命令、或能力不覆盖当前子任务时允许回退；已在 mcp_control.md 调用约束中显式声明，但"何时回退"仍依赖模型判断，存在过度坚持 MCP 或过度回退两端的偏差。
  - lanhu / apifox 等 MCP 是有状态服务（lanhu 走本地 8000 端口，apifox 需 token），宿主未通过 mcp-sync 同步成功时模型可能"看不到"工具但仍按 SKILL 提示尝试调用；约束里已加"宿主未注入时不假装调用"兜底，但跨宿主同步状态由 mcp-sync 脚本与用户操作保证，不属本提案范围。
  - ROUTE-001（排障）/ ROUTE-006（设计稿对照）/ ROUTE-004（DTO 建模）未追加 MCP 子项，属于弱关联场景；模型读到 ROUTE-016 → mcp_control.md 时仍能查到完整映射表，但 ROUTE 一级路由命中率会低于 ROUTE-008 / ROUTE-013。后续若 usage ledger 显示这些 ROUTE 下漏选 MCP 的样本累积，再单开提案补。

## 状态
- promoted
