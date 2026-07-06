# 回归场景：cross-model-review × 用户登录速率限制

> 本文件是 cross-model-review skill 的回归场景样例，供人类阅读，不参与 Agent 运行时加载（sync-skills.sh 白名单不同步 examples/）。

## 场景目的

验证 cross-model-review skill 的端到端流程：

1. `detect-review-clis.sh` 探测可用 CLI
2. 推荐两个不同 provider 的组合
3. reviewer 只读审查 PLAN.md
4. 输出 `VERDICT: APPROVED | REVISE`
5. 主 agent 仲裁并写 PLAN-REVIEW-LOG.md
6. reviewer 原始输出保存在当前项目根 `.plan-reviews/<date>-<slug>/raw/`，不使用 `/tmp`

## 前置

plan-grill 盘问后的 PLAN.md（用户登录速率限制方案）。盘问修正了原方案的 4 个缺陷：单实例假设、并发竞态、时钟重置、锁定恢复。

## PLAN.md（盘问锁定版）

```markdown
# Plan: 用户登录速率限制（防暴力破解）

## Goal
防止暴力破解登录，限制每个用户/IP 的登录失败次数，超限后临时锁定。

## Constraints & assumptions
- Web 服务多实例部署（不能依赖单实例内存）
- Redis 可用作共享存储
- 时间精度到秒即可

## Approach
用 Redis 存储失败计数。为 username 和 IP 各维护一个 key（分开，非组合），任一超限即触发锁定。每次登录失败用 INCR 原子递增，首次失败时用 EXPIRE 设置 15 分钟 TTL（固定窗口自动重置）。达到 5 次后，设置一个 15 分钟的锁定 key。锁定期间登录请求直接拒绝并返回 Retry-After 头。锁定结束后 key 过期自动恢复。

## Key decisions & tradeoffs
- 分开两个 key（`loginfail:u:{username}` + `loginfail:ip:{ip}`）而非组合 key：能同时卡住"同账号不同 IP"和"同 IP 不同账号"两种暴破模式；代价是 key 数量翻倍，但 Redis 可承受。
- 固定窗口而非滑动窗口：防暴破不需要精确计量，边界处 2x 突发可接受；换来实现简单（TTL 自动重置）。
- 阈值 5 次/锁定 15 分钟：OWASP 建议的暴破防护下限；15 分钟让攻击成本升高又不致过度惩罚合法用户。
- Redis INCR + EXPIRE 原子操作：天然解决并发竞态，无需额外加锁。
- 不提供提前解锁接口：避免被攻击者社工绕过。

## Validation plan
- 单元测试：模拟 5 次失败后第 6 次被拒；锁定 key TTL 正确；username 和 IP 两个维度独立计数。
- 并发测试：100 并发失败请求，计数器不丢不重（验证 INCR 原子性）。
- 集成测试：多实例部署下，实例 A 的失败在实例 B 可见（验证 Redis 共享）。
- 边界测试：窗口边界（14:59 五次 + 15:01 五次）行为符合固定窗口预期。

## Risks / non-blocking open questions
- Redis 故障时如何降级：可选 fail-open（放行，记日志）或 fail-closed（拒绝所有登录）。当前未决，建议 fail-open + 告警，避免 Redis 故障导致全员无法登录。

## Out of scope
- 验证码/二次认证（本方案只做速率限制）
- 分布式 IP 信誉库
- 异常检测（如地理跃迁检测）
```

## detect-review-clis.sh 输出

```json
{
  "clis": [
    {"name": "codex", "available": false},
    {"name": "gemini", "available": true, "path": "/opt/homebrew/bin/gemini", "version": "0.49.0", "readonly_flag": "--approval-mode plan", "noninteractive_flag": "-p"},
    {"name": "claude", "available": true, "path": "/Users/song/.local/bin/claude", "version": "2.1.195 (Claude Code)", "readonly_flag": "--permission-mode plan", "noninteractive_flag": "-p"}
  ],
  "available_count": 2
}
```

`available_count >= 2`，满足 CMR-001 硬门。推荐组合：gemini + claude（两个不同 provider）。

## Reviewer 调用命令

```bash
REVIEW_DIR="./.plan-reviews/2026-07-06-login-rate-limit"
RAW_DIR="${REVIEW_DIR}/raw"
mkdir -p "${RAW_DIR}"
grep -qxF ".plan-reviews/" .gitignore 2>/dev/null || printf "\n.plan-reviews/\n" >> .gitignore

# Reviewer 1: Claude
claude -p "$REVIEW_PROMPT" --permission-mode plan --output-format text \
  > "${RAW_DIR}/claude-round1.txt"

# Reviewer 2: Gemini
gemini -p "$REVIEW_PROMPT" --approval-mode plan --skip-trust --include-directories ~/.gemini/skills \
  > "${RAW_DIR}/gemini-round1.txt"
```

其中 `REVIEW_PROMPT`（见详规 CMR-003）：

```
You are an adversarial reviewer for an implementation plan. Be skeptical and specific — find what breaks, not to be agreeable. Identify concrete flaws: security holes, race conditions, missing edge cases, schema conflicts, wrong assumptions, observability gaps, simpler alternatives. For each, give a one-line fix. Do NOT modify any files. End your reply with EXACTLY one line: VERDICT: APPROVED if the plan is sound enough to implement, or VERDICT: REVISE if it still has material problems.
```

## Reviewer 1: Claude（8 个缺陷，VERDICT: REVISE）

**Flaw 1 — INCR + EXPIRE are NOT atomic (critical correctness bug)**

计划声称"INCR + EXPIRE 原子操作"——这是事实性错误。它们是两条独立 Redis 命令。若进程在 INCR 返回 1 后、EXPIRE 发送前崩溃，计数器 key 永久存在无 TTL。5 次失败后账号永久锁定，无自动恢复。

Fix: 用 Lua 脚本（EVAL）封装 GET → INCR → 条件 EXPIRE，Redis 保证 Lua 脚本原子性。

**Flaw 2 — Username-dimension key enables targeted account lockout (DoS)**

按 username 分开意味着任何未认证攻击者知道合法用户名即可用轮换 IP 的 5 次请求锁定它。这是可武器化的用户 DoS：攻击者每 15 分钟锁 `admin@company.com`，阻止目标登录。

Fix: 用组合 key `loginfail:u:{username}:ip:{ip}`（只锁配对），或保留 per-username 限制但在阈值 3 加 CAPTCHA，让锁定成本落在攻击者 UX 而非受害者。

**Flaw 3 — IP is not a trustworthy input (injection/bypass)**

计划用 IP 作 key 但未指定如何获取。负载均衡器后 `REMOTE_ADDR` 是代理 IP，所有用户共享一个计数器。若读 `X-Forwarded-For`，攻击者设置 `X-Forwarded-For: 1.2.3.4` 轮换 header 值绕过。

Fix: 只从受控代理设置的可信 header 提取 IP（如 nginx `X-Real-IP` + `set_real_ip_from`），绝不直接读用户提供的 header。

**Flaw 4 — No counter reset on successful authentication**

4 次失败后成功登录，再 1 次失败即被锁。失败计数器在成功时从不清除，跨会话累积。

Fix: 成功认证时 `DEL loginfail:u:{username}`（及 IP key）重置计数器。

**Flaw 5 — Retry-After header value is wrong after partial lock time**

锁 key 10 分钟前设置，剩 5 分钟，但响应 `Retry-After: 900` 告诉客户端等 15 分钟。

Fix: 响应 `Retry-After: PTTL(lock_key) / 1000`（剩余 TTL 秒），非硬编码 900。

**Flaw 6 — After lock expiry, counter is still at 5 (immediate re-lock)**

计数器 key 和锁 key 在不同时间设置（失败 1 vs 失败 5）。锁过期后，计数器可能仍是 5，用户下一次失败立即重新锁定。

Fix: 设置锁 key 时同时 `DEL` 计数器 key，窗口干净重置。

**Flaw 7 — Username key is not normalized (trivial bypass)**

`loginfail:u:Admin` 和 `loginfail:u:admin` 是不同 key。若用户名大小写不敏感，攻击者轮换大小写变体获得 5×N 次尝试。

Fix: 构造 key 前规范化用户名为小写（或规范形式）。

**Flaw 8 — No observability when locks trigger**

验证计划覆盖正确性测试，但完全没提结构化日志或 metrics。安全事件（账号锁定、IP 封禁）必须可观测，用于威胁检测、事件响应、调优。

Fix: 每次写锁 key 时发结构化日志事件 `{"event":"login_locked","reason":"username|ip","key":"...","ts":...}`。

**VERDICT: REVISE**

## Reviewer 2: Gemini（5 个缺陷，VERDICT: REVISE）

**缺陷 1: 账号恶意锁定拒绝服务漏洞**

允许仅通过 username 锁定用户登录会把"暴力破解风险"转化为"拒绝服务风险"。

Fix: 账号维度超限不应直接拒绝，而应强制触发验证码、MFA 或仅对"IP+Username"联合 key 拒绝。

**缺陷 2: INCR 与 EXPIRE 之间非原子性导致的死锁**

INCR 返回 1 后、EXPIRE 执行前若网络中断/崩溃/主从切换，计数器 key 永久存在（TTL = -1）。

Fix: Lua 脚本打包 `local c = redis.call('incr', KEYS[1]); if c == 1 then redis.call('expire', KEYS[1], ARGV[1]) end; return c`。

**缺陷 3: 登录成功时未重置计数器**

用户 15 分钟内错 4 次后第 5 次成功登录，计数器仍是 4，后续错 1 次即被锁。

Fix: 成功后同步/异步 `DEL loginfail:u:{username}` 和 `DEL loginfail:ip:{ip}`。

**缺陷 4: 反向代理下的真实 IP 伪造与误锁风险**

直接读 Socket IP 会误锁反向代理本身；直接信任 `X-Forwarded-For` 会被伪造绕过。

Fix: 配置受信任代理 IP 列表，只从受信代理传递的 `X-Forwarded-For` 最左端提取真实 IP。

**缺陷 5: 观测性缺失**

无 metrics 和 audit log，管理员无法感知暴破攻击，无法对被恶意锁定的正常用户排查。

Fix: 锁定触发时输出包含模糊化用户名、客户端 IP、拦截维度、TTL 的安全审计日志，并增加锁定触发率突增报警。

**VERDICT: REVISE**

## 缺陷重叠分析

| # | 缺陷 | Claude | Gemini | 严重度 | 置信度 |
|---|------|:---:|:---:|---|---|
| 1 | INCR + EXPIRE 非原子（永久锁定） | ✅ | ✅ | Critical | 高（两者都发现） |
| 2 | Username 维度导致用户 DoS | ✅ | ✅ | High | 高 |
| 3 | IP 伪造（X-Forwarded-For） | ✅ | ✅ | High | 高 |
| 4 | 登录成功未重置计数器 | ✅ | ✅ | Medium | 高 |
| 5 | 观测性缺失（无日志/metrics） | ✅ | ✅ | Low | 高 |
| 6 | Retry-After 值错误（硬编码 900） | ✅ | — | Medium | 中（仅 Claude） |
| 7 | 锁定过期后立即重新锁定 | ✅ | — | Medium | 中 |
| 8 | Username 未规范化（大小写绕过） | ✅ | — | Low | 中 |

5 个缺陷**两者都发现**（高置信），3 个仅 Claude 发现（Claude 审查更细）。不同 provider 结构盲区不同，叠加覆盖更全——这正是跨模型对抗的价值。

## 主 agent 仲裁示例（PLAN-REVIEW-LOG.md）

```markdown
# Plan Review Log: 用户登录速率限制（防暴力破解）

MAX_ROUNDS=5
Reviewers:
- claude 2.1.195 (Anthropic)
- gemini 0.49.0 (Google)

## Round 1 - claude
[8 个缺陷，详见上文 Reviewer 1]
VERDICT: REVISE

### Orchestrator response
Accepted:
- Flaw 1 (INCR+EXPIRE 非原子): 采纳，改用 Lua 脚本封装。这修正了主 agent 在 plan-grill 盘问时的错误断言——"INCR + EXPIRE 原子操作"是事实性错误。
- Flaw 2 (用户 DoS): 采纳，改用组合 key `loginfail:u:{username}:ip:{ip}`，只锁配对。
- Flaw 3 (IP 伪造): 采纳，明确只从受信代理 header 提取 IP。
- Flaw 4 (成功未重置): 采纳，成功时 DEL 计数器。
- Flaw 6 (Retry-After 值): 采纳，改用 PTTL 返回剩余秒数。
- Flaw 7 (锁定后立即重锁): 采纳，设锁 key 时 DEL 计数器。
- Flaw 8 (Username 规范化): 采纳，key 前小写化。
- Flaw 8 (观测性): 采纳，加结构化日志 + metrics。

Rejected:
- (无) 本轮所有批评均有证据，全部采纳。

## Round 1 - gemini
[5 个缺陷，详见上文 Reviewer 2]
VERDICT: REVISE

### Orchestrator response
Accepted:
- 缺陷 1-5: 与 Claude 重叠，已在上文 claude 轮采纳。无新增。

Rejected:
- (无)

## Resolution
deadlock（本轮 REVISE，需修订 PLAN.md 后进入 Round 2；本样例到此为止，不演示完整收敛）
```

## 验证结论

| 验证项 | 结果 |
|---|---|
| `detect-review-clis.sh` 探测 | ✅ 正确识别 gemini + claude 可用 |
| claude adapter 调用 | ✅ 输出完整审查 + VERDICT: REVISE |
| gemini adapter 调用 | ✅ 输出完整审查 + VERDICT: REVISE |
| 项目内 raw 输出 | ✅ reviewer 原始输出保存到 `.plan-reviews/2026-07-06-login-rate-limit/raw/` |
| VERDICT 格式 | ✅ 两 reviewer 均以 VERDICT: REVISE 结尾 |
| 跨模型重叠 | ✅ 5 个缺陷两者都发现（高置信） |
| 主 agent 盲区被抓 | ✅ INCR+EXPIRE 非原子——主 agent 在 plan-grill 盘问时错误断言"原子操作"，两 reviewer 都抓到 |

### 核心价值证明

plan-grill 盘问修正了原方案的 4 个缺陷，但**遗漏了** INCR+EXPIRE 非原子这个结构性错误（主 agent 自信地断言错了）。cross-model-review 的跨模型对抗**抓到了**这个盲区。

这证明了流水线的核心价值：**不能让同一模型既规划又评分**——回音室效应会让错误自信通过。跨提供商模型对抗是发现结构性盲区的有效机制。

## gemini adapter 调用注意事项（本场景观察）

- gemini 启动时报 `ContextManager Hot start calibration failed` 503（context-calibrator 模型在第三方 API 中转下不可用），但**不阻止** reviewer 输出完整审查。
- 加 `--include-directories ~/.gemini/skills` 可消除 `Path not in workspace` 噪音。

详见详规 `references/cross_model_review.md` 的「Gemini adapter → 调用注意事项」。
