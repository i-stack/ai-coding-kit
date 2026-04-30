# Skill Evolution Proposal

## Metadata
- Proposal ID: 20260430-144213-unify-network-pattern-ownership
- Created At: 2026-04-30 14:42:13 +0800
- Active Version At Creation: v26

## 问题信号
- 按 self_evolution.md v26 新增的跨文件 grep 约束执行全目录扫描，确认 **重试 / 缓存 / 鉴权刷新** 三组网络模式规则同时定义在 `architecture_and_network.md` 和 `networking_patterns.md` 两份文件：

| 规则 | architecture_and_network.md | networking_patterns.md |
|---|---|---|
| 幂等请求重试 | L95 | L46 |
| 重试次数/退避/终止条件 | L96 | L47 |
| 展示/业务/离线缓存分类 | L100 | L62-69 |
| 缓存键/失效/写入时机 | L101 | L72-74 |
| ViewModel 不感知缓存实现 | L102 | L75 |
| Token 刷新串行化 | L107 | L78 |

- 现状是"双定义 + 交叉引用"混合态：`architecture_and_network.md` L94-102 自己定义了一遍三组规则，L104 才加 "详细见 networking_patterns.md"。读者读 architecture 会先看到重试/缓存/鉴权的条款再看到引用，分不清哪份是权威。
- 在 `networking_patterns.md` 的 L21 已经说 "本文件聚焦具体网络模式（分页 / 重试 / 缓存 / 鉴权刷新 / 上传下载 / 幂等去重）"，说明编写时本意就是该文件承担完整模式定义；architecture 保留的条款是历史遗留。

## 变更类型
- 合并重复：把 `architecture_and_network.md` 的重试 / 缓存 / 鉴权刷新细节退役，全部归属 `networking_patterns.md`；architecture 只保留网络层架构边界 + 跨层安全规则。

## 变更内容
- 修改文件：`references/architecture_and_network.md`
  - 退役 "### 重试与超时"（L94-97）整节，由 networking_patterns.md "## 重试模式" 承担。
  - 退役 "### 缓存策略"（L99-102）整节，由 networking_patterns.md "## 缓存模式" 承担。
  - 修改 "## 鉴权与安全" 节：
    - 退役 L107 "Token 刷新流程必须串行化，避免并发刷新风暴。"（networking_patterns.md L78 已承担）。
    - 保留 L108 "认证信息存储使用 Keychain。"（跨层安全规则，不涉及网络模式）。
    - 保留 L109 "敏感日志脱敏，避免打印完整 Token、手机号、身份证号等。"（跨层安全规则）。
  - 升级 L104 交叉引用为"网络模式完整定义（链路职责 / 分页 / 重试 / 缓存 / 鉴权刷新 / 上传下载 / 幂等去重 / 错误分层 / 常见反模式）全部在 [networking_patterns.md](networking_patterns.md)。本文件只保留网络层**架构边界**和跨层**安全规则**。"
- 不修改 `references/networking_patterns.md`（已经是完整归属）。

## 替代或合并旧规则
- architecture_and_network.md 的 "### 重试与超时" + "### 缓存策略" + "Token 刷新串行化" 全部退役，由 networking_patterns.md 单一承担。
- "## 鉴权与安全" 保留的 Keychain 存储 + 日志脱敏两条属于跨层安全规则，不与 networking_patterns.md 的 "## 鉴权刷新模式"（只讲 Token 刷新时序）重复。
- 升级后的交叉引用显式指出 "架构边界 vs 网络模式" 的职责划分，避免未来再次出现"先定义再引用"的混合态。

## 预期收益
- 重试 / 缓存 / 鉴权刷新规则从"双定义 + 交叉引用"变为"单一归属 + 交叉引用"。
- architecture_and_network.md 从 ~129 行减到 ~115 行，专注架构边界 + 链路 + 安全规则；具体网络模式全部外链。
- 未来修改重试策略、缓存失效条件、Token 刷新时序只需改 networking_patterns.md 一处，不再需要两处同步。
- 符合 self_evolution v26 新约束——把跨文件共享概念（网络模式）规整为单一归属。

## 验证
- 结构校验：
  - `SKILL.md` frontmatter 合法，行数 ≤ 500（本提案不改 SKILL.md）。
  - `SKILL.md` 引用的所有 `references/*.md` 文件存在。
  - `root_cause_enforcement.md` / `examples.md` 分层守卫不受影响。
- 场景回放：
  - 场景 `parameter-pass-through` 作为代理：涉及网络层参数时 AI 仍能命中 architecture 的链路定义 + networking_patterns 的模式细节。
  - 隐式验证（网络任务）：用户问 "这个请求要不要加重试 / 加缓存 / Token 怎么刷新" 时，AI 应直接命中 networking_patterns.md，不再从 architecture 读一套、从 networking 读一套。
- 残留风险：
  - 有些读者习惯从 architecture 入口找网络规则；退役后他们只看到"见 networking_patterns"引用，需要多走一跳。但这是单一归属的正常成本，与 review_checklists.md 输出骨架单一归属同理。
  - networking_patterns.md 的 "常见反模式" 节（L96-106）也有 "无条件自动重试 / 缓存没有失效策略 / Token 刷新并发失控" 等，与本次退役的 architecture 条款语义重叠但不冲突；保留现状（反模式库本身独立于规则库）。

## 状态
- promoted
