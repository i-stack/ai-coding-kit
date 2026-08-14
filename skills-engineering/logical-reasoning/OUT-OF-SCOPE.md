# logical-reasoning 范围外

本 skill 约束 AI **自身回复**的论证质量（inward），不负责检验用户提问逻辑或结论真实性。

## 不处理的内容

- **用户提问的逻辑检验**：由 `problem-analysis`（PA-001）负责。
- **结论与外部世界的接地**：由 `epistemic-integrity`（GR-011/012）负责。
- **认知对手模式**：由 `cognitive-calibration`（platform-agnostic owner）负责（挑战用户结论）；`ios-engineer/references/cognitive_adversary_mode.md` 仅为指向该真值的镜像。
- **工程输出结构**：由 `engineering-discipline`（GR-004 四段式）负责。

## 边界说明

GR-010 是 inward 约束：
- **逻辑链可追溯**：每步推理都能回到上游前提
- **四层区分**：事实 / 推断 / 建议 / 推测
- **强度匹配**：结论强度不超出证据强度
- **不矛盾**：同一回复内部不自相冲突

与 GR-011/012 正交——一条回复可以内部逻辑自洽但与外部世界不符，也可以方向正确但论证结构混乱。两者同时命中时并行执行。
