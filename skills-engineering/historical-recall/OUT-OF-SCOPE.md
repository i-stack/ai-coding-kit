# historical-recall 范围外

本 skill 负责**动手前的历史线索召回**（把 `.plan-reviews/` 知识库的可检索 chunk 作为待验证上下文注入），不负责回答内容本身，也不负责计划锁定或代码审查。

## 不处理的内容

- **回答的主体内容**：本 skill 只在动手前注入历史线索，不参与主体回答的生成。
- **计划锁定（plan-grill）**：是否进入盘问、如何盘问由 plan-grill 负责；本 skill 只在其动手前提供历史线索。
- **代码审查（auto-code-review / cross-model-review）**：审查执行、reviewer 仲裁、归档结构由对应 skill 负责；本 skill 只在其动手前提供历史线索，归档后的 `sync` / `merge` 回灌由对应 skill 负责。
- **写入知识库**：本 skill 只 `recall`（读），不执行 `sync` / `merge`（写）。
- **事实性断言的真值接地**：由 `cognitive-reasoning` 负责；本 skill 仅把召回标记为「不可信线索」。

## 触发门控

仅在非平凡构建、修改、方案、迁移、审查、排障类任务、且用户任务消息已出现时触发。事实查询、翻译、简单解释、typo、小命令、纯闲聊跳过。
