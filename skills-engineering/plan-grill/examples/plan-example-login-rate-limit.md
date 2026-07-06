# 示例：plan-grill 盘问产出 → 用户登录速率限制 PLAN.md

> 本文件是 plan-grill skill 的例样，供人类和 Agent 参考 PLAN.md 七段格式与填写标准。
> 不参与 Agent 运行时加载（sync-skills.sh 白名单不同步 examples/）。
>
> 此例与 `cross-model-review/examples/regression-login-rate-limit.md` 形成对照：
> - **本文件**：plan-grill 盘问**修正后最终锁定**的 PLAN.md（已修正 INCR+EXPIRE 原子性等缺陷）
> - **cross-model-review example**：展示盘问前的初版 PLAN.md 含哪些缺陷，以及跨模型审查如何发现它们

## 场景

用户提出「给登录接口加速率限制，防暴力破解」。plan-grill 逐一盘问实现方案的决策树，与用户达成共识后锁定以下 PLAN.md。

## 盘问决策树（已解析）

| 决策点 | 提问 | 用户选择 | 理由 |
|--------|------|----------|------|
| 存储后端 | Redis 还是数据库？ | Redis | 低延迟、原生 TTL、INCR 原子性 |
| Key 粒度 | 组合 key 还是分开 key？ | 组合 key `u:{username}:ip:{ip}` | 避免仅 per-username 导致的用户 DoS |
| 原子性 | 如何保证 INCR+EXPIRE？ | Lua 脚本 | 避免 INCR 后崩溃导致 key 永不过期 |
| 窗口类型 | 固定窗口还是滑动窗口？ | 固定窗口 | 防暴破不需要精确计量，实现简单 |
| 阈值/锁定时长 | 几次失败锁定多久？ | 5 次 / 15 分钟 | OWASP 建议下限 |
| IP 来源 | 如何获取真实 IP？ | 受信代理链提取 | 避免 X-Forwarded-For 伪造 |
| 成功处理 | 成功登录是否重置？ | 是，DEL 计数器 | 避免跨会话累积 |
| 锁定响应 | 返回什么给客户端？ | Retry-After = PTTL | 动态剩余时间，非硬编码 |
| Redis 故障 | 降级策略？ | fail-open + 告警 | 避免 Redis 故障导致全员无法登录 |
| Username 规范化 | key 前是否需要？ | 小写规范化 | 避免大小写变体绕过 |

---

## PLAN.md（盘问锁定版）

> 以下为 plan-grill 按 PG-004 产出的标准七段 PLAN.md。

```markdown
# Plan: 用户登录速率限制（防暴力破解）

## Goal
防止暴力破解登录，限制每个用户/IP 配对的登录失败次数，超限后临时锁定该配对。

## Constraints & assumptions
- Web 服务多实例部署，不能依赖单实例进程内存
- Redis 可用作共享低延迟存储
- 应用部署在受信反向代理之后，可从可信 header 提取规范客户端 IP
- Username 大小写不敏感，登录前可规范化
- 本版本接受短固定窗口近似，精确滑动窗口暂不在范围内

## Approach
规范化提交的 username 后构造 Redis key。仅从受信代理链提取客户端 IP。每次登录失败时，通过 Redis Lua 脚本对 `loginfail:v1:u:{hash(username)}:ip:{ip}` 原子递增失败计数并设置 TTL（首次 15 分钟）。配对在 15 分钟内超过 5 次失败后，设置同配对的锁定 key（15 分钟 TTL）并清除计数器 key。锁定期间在密码验证前拒绝请求，返回 `Retry-After`（基于锁定 key 剩余 PTTL）。登录成功时删除该配对的计数器 key。锁定触发时发送结构化安全日志和 metrics。

## Key decisions & tradeoffs
- 配对粒度 key（`u:{username}:ip:{ip}`）而非仅 per-username：降低针对性账号锁定 DoS 风险；对高度分布式攻击较弱，后续可叠加 CAPTCHA 或自适应风险评分
- Lua 脚本而非分开 INCR + EXPIRE：保持计数更新和 TTL 设置原子性；增加 Redis 脚本依赖但避免计数器永不过期
- 固定窗口而非滑动窗口：实现简单，满足初始暴破控制需求；边界突发可接受
- 对 Redis key 和日志中 username 做哈希：避免在基础设施 key 中存储原始标识符；略微增加手动调试复杂度
- Redis 故障时 fail-open + 告警：保持登录可用性；临时削弱暴破防护，必须可观测

## Validation plan
- 单元测试：username 规范化、受信客户端 IP 提取、key 构造、基于剩余 PTTL 的 Retry-After
- Redis 集成测试：Lua 脚本首次失败设 TTL、并发失败不丢计数、脚本路径后无 key 缺 TTL
- 行为测试：第 1-5 次到达密码验证、第 6 次同配对被拒、不同 IP 不自动锁定、登录成功清除配对计数器
- 过期测试：锁定 TTL 自动过期、清除的计数器不立即重新锁定、Retry-After 随时间递减
- 可观测性检查：锁定事件输出结构化日志并递增 metrics（不含原始 username）

## Risks / non-blocking open questions
- 跨多 IP 的分布式低慢攻击可能绕过配对粒度限制；后续可叠加 username 级 CAPTCHA 或自适应风险评分
- NAT 密集型网络下同 username/IP 配对可能遇到共享 IP 摩擦；配对粒度比纯 IP 限制减少了影响范围
- Redis fail-open 在故障期间削弱保护；必须告警以便运维响应

## Out of scope
- CAPTCHA、MFA 升级、基于风险的认证策略
- 全局 IP 信誉或分布式滥用情报源
- 账户恢复、帮助台解锁流程、管理手动覆盖工具
```

## 示例使用说明

### Agent 如何参考本例

执行 plan-grill 时：
1. 盘问结束后，对照本例检查 PLAN.md 是否七段完整
2. 每段内容是否具体（无占位符如「TODO」「待定」）
3. Key decisions 是否有明确的「选 A 而非 B」对比
4. Validation plan 是否包含可执行的测试路径而非含糊描述

### 常见缺失（检查清单）

- [ ] Goal 是否一句话说清「解决什么」，而非「做什么功能」
- [ ] Constraints 是否区分了硬约束和未验证假设
- [ ] Approach 是否足够具体让另一个工程师能实施
- [ ] Key decisions 是否有 tradeoff 说明（选什么、不选什么、为什么）
- [ ] Validation plan 是否可执行（不是「充分测试」这类空话）
- [ ] Risks 是否标注了 non-blocking（明确什么已知但不阻塞实施）
- [ ] Out of scope 是否显式列出不做的事（防止范围蔓延）
