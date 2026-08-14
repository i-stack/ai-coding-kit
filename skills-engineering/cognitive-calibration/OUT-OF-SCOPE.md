# cognitive-calibration 范围外

本 skill 提供**反迎合 / 挑战用户结论**的认知校准结构（CAM），不负责约束 AI 自身论证质量或结论与外部世界的接地。

## 不处理的内容

- **AI 自身论证质量（inward）**：由 `logical-reasoning`（GR-010）负责。
- **结论与外部真实的接地**：由 `epistemic-integrity`（GR-011/012/013）负责。
- **工程输出结构**：由 `engineering-discipline`（GR-004 四段式）负责。
- **需求/问题本身合理性**：由 `problem-analysis`（PA-001）负责。

## 边界说明

CAM 是**校准用户结论**的协议（outward-to-user-claim），与 GR-010（inward）、GR-011（outward-to-world）正交：
- 一条回复可对用户结论做了充分 red team，但自身论证结构仍可能乱（需 GR-010）。
- 一条回复可内部逻辑自洽且对用户结论有挑战，但所引用事实可能未接地（需 GR-011）。
- 三者同时命中时并行执行，CAM 保留完整机械格式（GR-004 合并规则适用）。

## 真值归属

CAM 的 platform-agnostic 真值 owner 为 `cognitive-calibration`；真值文件即 `cognitive-calibration/references/cognitive_adversary_mode.md`。`ios-engineer` 经 `depends_on: [cognitive-calibration]` 引用本 skill，并维护指向本真值的镜像（`ios-engineer/references/cognitive_adversary_mode.md`），不持有 CAM 真值。
