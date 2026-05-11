# Skill Evolution Proposal

## Metadata
- Proposal ID: 20260508-155946-tighten-route-017-playbook-entry-condition
- Created At: 2026-05-08 15:59:46 +0800
- Active Version At Creation: v51

## 问题信号
- v47 SKILL.md 审查发现 [ROUTE-017] 剧本入口与多条单点 ROUTE 的关键词重叠：
  - "排查偶现 Crash" ↔ [ROUTE-001] "偶现问题 / Crash"
  - "性能优化" ↔ [ROUTE-010] "性能 / 启动 / 列表卡顿 / 内存 / 过度刷新 / 能耗"
  - "并发迁移" ↔ [ROUTE-007] "并发 / 取消链路 / actor / Sendable"
  - "大型重构" ↔ [ROUTE-012] "重构落地 / 迁移 / 灰度 / 回滚"（v51 刚收紧过）
- ROUTE-017 的设计意图是"复杂 / 多步 / 长周期"任务才走剧本；但当前措辞没有写出这个条件，单说"接手遗留页 / 排查偶现 Crash / 性能优化 / 并发迁移 / 大型重构"时，上述任一单点关键词都可能优先命中剧本入口。
- 结果：用户一次单点排障也可能被带进 execution_playbooks.md 剧本，造成 ref 加载过宽。自进化触发信号「某条规则持续带来过度展开」命中。

## 变更类型
- 修正表达（保留 ROUTE-017 ID；重写入口条件，让剧本触发变成"前置条件 + 专属语义"的双约束；其它 ROUTE 不动）

## 变更内容
- 修改文件：
  - `SKILL.md` 第 51 行：[ROUTE-017] 重写为——
    - 入口条件前置：**需满足"跨多日 / 跨多模块 / 已尝试常规排障无果 / 需要分阶段落地"至少一项才走剧本；否则走 SYM 与 ROUTE 单点路由**
    - 剧本涵盖语义收紧：
      - 排查偶现 Crash → **反复偶现 Crash 系统排查**（强化"长期反复"）
      - 性能优化 → **性能专项**（强化"项目级专项"而非单点）
      - 并发迁移 → **并发架构迁移**（强化"架构级"，避免与 ROUTE-007 单点并发混淆）
      - 大型重构 → **大型重构落地**（与 v51 ROUTE-012 "重构落地" 词形一致，剧本层与执行层的差异留在入口条件）
      - 接手遗留页 → 保留（独特语义，不与其它 ROUTE 重叠）
- 不修改：
  - [ROUTE-001] / [ROUTE-007] / [ROUTE-010] / [ROUTE-012] 的主关键词与主读 ref。
  - execution_playbooks.md ref 内容（剧本定义不动）。
  - rule_index.md ROUTE-017 摘要（当前摘要 "复杂任务剧本 → execution_playbooks.md" 已够精炼，不需要跟随 SKILL.md 的入口条件扩写）。
- 替代或合并旧规则：无（ROUTE-017 ID 沿用）

## 预期收益
- 剧本入口 vs 单点 ROUTE 的双层边界显化：
  - 用户说"这个 Crash 偶现"→ ROUTE-001（单点排障）
  - 用户说"这个 Crash 复现了 3 天都没抓到 / 已经 grep 过日志" → 满足"已尝试常规排障无果"→ ROUTE-017 剧本
- 减少误触剧本导致的 ref 过度加载。
- SKILL.md 行数不变（第 51 行仍是一行），但单行内容更长，可读性略降；用剧本前置条件换可路由性，净收益为正。

## 验证
- 结构校验：
  - `bash scripts/validate_rule_ids.sh` 保持通过（ID 不动）。
  - `SKIP_SNAPSHOT_CONSISTENCY=1 bash scripts/validate_skill_evolution.sh` 12 步全绿。
- 场景回放：
  - 6 个固定场景里无"剧本"专属场景；本提案不改任何 SYM / IR / OUT，不动主读 ref；预期全部 pass。
- 残留风险：
  - 剧本前置条件由 4 项组成（跨多日 / 跨多模块 / 常规排障无果 / 分阶段落地），条件语义边界模糊（何谓"常规排障"本身依赖 ROUTE-001 定义），实际命中效果需要 usage_ledger 数据验证。
  - ROUTE-017 单行长度增加（约 2x），若后续有"SKILL.md 单行长度硬上限"约束，需再压缩。目前 validate_skill_evolution.sh 只限制总行数（500），无单行上限。
  - 用户如果习惯性用"性能优化""大型重构"词直接触发剧本，本提案后会先路由到 ROUTE-010 / ROUTE-012 单点分支——这是设计内的行为迁移。

## 状态
- promoted
