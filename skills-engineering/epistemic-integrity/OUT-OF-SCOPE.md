# epistemic-integrity 范围外

本 skill 负责**真值接地**——确保结论可被外部验证、自信与正确性匹配。不负责回答的技术正确性本身。

## 不处理的内容

- **技术内容的正确性**：本 skill 定义验证方法论，但不替代具体领域知识。iOS 的具体技术正确性由 `ios-engineer` 负责。
- **论证的内部自洽性**：GR-010（逻辑链内部自洽）由 `logical-reasoning` skill 负责，本 skill 关注的是结论与**外部真实世界**的接地。
- **问题的前置分析**：问题的逻辑有效性检验由 `problem-analysis` skill 负责。

## 分工边界

| Skill | 方向 | 职责 |
|-------|------|------|
| `epistemic-integrity`（本 skill） | outward | 结论与世界是否相符、怎么去核 |
| `logical-reasoning`（GR-010） | inward | 回复自身是否自洽、分层、不确定标清 |
| `problem-analysis`（PA-001/002） | upfront | 问题本身合理性、第一性原理拆解 |
