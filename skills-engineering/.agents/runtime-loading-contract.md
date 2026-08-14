# 运行时加载契约（Runtime Loading Contract）

> 本文件明确"agent 的阅读义务"与"各运行时的能力边界"，弥补 `.agents/README.md` 只定义 agent 义务、却无平台能力矩阵的缺口。
> 它不替代 SKILL.md 的"必须完整阅读"要求，而是界定**哪些物料由运行时自动注入、哪些需 agent 主动读取、以及阅读完成的机械证明**。

## 物料分类

| 类别 | 含义 | 谁负责提供 | 摘要是否等价 |
|------|------|-----------|-------------|
| `discovery material` | skill 名 / description / 路由表（用于命中判定） | 运行时自动注入 | 是（仅用于路由） |
| `mandatory runtime material` | 命中后必须全文生效的 SKILL.md + 对应 references | **运行时应注入**，缺失时 agent 必须主动 `read_file` | **否** |
| `routed optional material` | 按 ROUTE- 分流才加载的 references（如 iOS 的 2–4 refs 预算） | agent 按路由主动读取 | 否 |
| `runtime-prefetched material` | 运行时预取的 preamble / 缓存摘要 | 运行时 | 仅作导航/门控，**不得作为全文等价替代** |

## 契约规则

1. **真值源唯一**：SKILL.md 仅路由，references 承载字面，rule_index 承载 ID 真值。摘要（含 runtime-prefetched）若与 references 字面冲突，以 references 为准。
2. **最小安全摘要的边界**：`runtime-prefetched material` 与任何"导航摘要"**只能用于**（a）判断是否需加载、（b）定位章节；**不能**替代 `mandatory runtime material` 的全文执行。将其当全文用会引入"摘要漂移"这一新真值源，违反 GR-011 接地纪律。
3. **阅读完成机械证明**：agent 在输出前须能引用其所命中 references 的具体条款（rule_id / Step / 章节）；若无法引用，视为未完整阅读，违反本契约。校验器（`validate-skill-behavior.sh`）未来可增加"输出含 referenced rule_id"的弱校验。
4. **能力矩阵待填**：各运行时（CodeBuddy / Claude / Codex 等）是否自动注入 `mandatory runtime material` 尚未逐端核实；在核实前，agent 一律**主动 `read_file`** 命中 skill 的 SKILL.md 与对应 references，不依赖"可能已注入"的假设。

## 与既有文件关系

- 本契约是对 `.agents/README.md`「命中后完整读取」的工程化补充，不修改其强制语义。
- `composition.md` 的块发射顺序假定相关 skill 已按本契约正确加载。
