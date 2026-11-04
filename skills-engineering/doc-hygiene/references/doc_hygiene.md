<!-- last-verified: 2026-08 -->
# 文档卫生细则（Doc Hygiene）

> 真值 owner：`doc-hygiene`。本文是 DH-* 规则的条文。SKILL.md 仅路由。

## DH-001：文档正文只陈述最终态事实

写或更新任何 `.md`（SKILL.md / references / AGENT-BRIEF / OUT-OF-SCOPE / docs / README / .agents）时，正文描述的是**当前架构/行为的客观事实**，不描述它如何演变到当前状态。

> **适用范围与自动化边界**：DH-001/002 对**所有**上述 `.md` 生效（契约层面覆盖全部 references）。但 `validate-doc-hygiene.sh` 的自动扫描聚焦于「运行期会被 Agent 加载运行的入口/约定类文档」（SKILL.md / AGENT-BRIEF / OUT-OF-SCOPE / rule_index / README / .agents/*），**普通 `references/*.md` 技术细则不在自动扫描内**——因其常含合法的「迁移期间」等工程叙述，靠 DH-002 的高特异词表 + 写时 self-check 覆盖，而非盲目 CI 扫全仓。规则定义文件 `doc-hygiene/references/doc_hygiene.md` 自身永远排除（它必须列举禁用词来定义规则）。自动扫描的边界不削弱 DH-001 对 references 的契约效力。

**允许的**：事实性指向（如「CAM 真值 owner 为 cognitive-reasoning（platform-agnostic），其 references 为认知对手模式详规；ios-engineer 维护指向该真值的镜像，经 depends_on 引用 cognitive-reasoning」）——这是运行期 Agent 需要的可达性事实。
**禁止的**：迁移叙事（如「此前承载于 ios-engineer，属抽象归属倒置」「待真值文件平移至本 skill后」「迁移期 CAM 仍置于…」）——这是变更过程，不是现状。

## DH-002：禁止过程叙事关键词

以下表述（及同义变体）**不得出现在文档正文中**。它们一旦出现，即说明把变更记录混入了文档：

- 「迁移期 / 迁移说明 / 待平移 / 待真值文件 / 待后续」
- 「owner 纠正 / 抽象归属倒置 / 此前承载 / 之前承载 / 现由 / 现已 / 不再由 X 承载」
- 「我们做了 / 本轮 / 已重构为 / 改为」等第一/第二人称的变更主语

**例外**：`CHANGELOG.md` 本就是变更记录，本规则不适用。

## DH-003：变更过程记入专门去处

所有「为什么变、变了什么、谁批准」**至少**进以下其一：

- 主去处：仓库根 `CHANGELOG.md`（用户可见的变更摘要；路径为 repo 根，非 `skills-engineering/CHANGELOG.md`）
- 兜底去处（主去处不便时仍合法，但不应作为唯一去处）：
  - git commit message（含 why/what；CI 无法读取，故仅作兜底）
  - PR 描述（团队评审场景）

文档正文零负责变更叙事；只反映上述流程落地后的**结果状态**。

## 改写对照示例

| ❌ 过程叙事（禁止） | ✅ 最终态事实（允许） |
|---------------------|----------------------|
| 此前承载于 ios-engineer，属抽象归属倒置；现由 cognitive-reasoning 作为唯一真值 owner 承载。 | cognitive-reasoning 是认知对手模式的 platform-agnostic 真值 owner。 |
| 迁移期 CAM 真值仍置于 ios-engineer，待平移后反向依赖。 | CAM 真值文件置于 cognitive-reasoning/references/cognitive_adversary_mode.md（platform-agnostic owner）；ios-engineer 维护其镜像并经 depends_on 引用 cognitive-reasoning。 |
| 我们本轮把 GR-010 的规则元数据补进了 rule_index。 | GR-010 的 owner/scope/phase 元数据登记在 engineering-discipline/references/rule_index.md（由 composition.md 引用裁决）。 |

## 执行检查（self-check）

在输出/提交任何文档改动前，逐条确认：
1. 正文无 DH-002 关键词。
2. 若读者是 Agent，它读到的只是「现在该读谁、依赖闭包是什么、指向哪」——无需知道历史。
3. 若确有变更需要交代，确认它进了 CHANGELOG 或 commit message，而非文档正文。
