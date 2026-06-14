# Skill Evolution Proposal

## Metadata
- Proposal ID: 20260509-105635-ref-last-verified-metadata-and-audit-script
- Created At: 2026-05-09 10:56:35 +0800
- Active Version At Creation: v64

## 问题信号
- iOS API 每年大改一次（WWDC 节奏）。current refs 没有任何"最近一次复核"时间戳，无法判断某条 ref 是否还反映当前 iOS / Swift / SwiftUI / Xcode 实际情况。
- 当 ref 中关于 SwiftUI 行为、并发模型、Xcode 工具链的描述跨多个主版本不更新时，会沉默地误导回答 —— grep "iOS 14" / "Swift 5.5" 也找不到，因为陈述不一定写明版本。
- self_evolution.md 已经治理了"规则缺失 / 冲突 / 重复 / 失效"，但"内容随系统迭代而陈旧"这条信号没有专门治理路径，只能等到真实任务里翻车再触发提案。
- 现状：每个 ref 都没有元数据；后续若加 last-verified 字段，需要先在所有 27 份 ref 同步落地 + 提供审计脚本，才能形成闭环。

## 变更类型
- 新增能力（在 ref 文件级别添加 last-verified 元数据 + 配套 audit 脚本；不改任何规则 ID、不改输出模板）

## 变更内容
- 修改文件：
  - references/*.md（27 份）：每份 ref 的首行（H1 标题之上）追加一行 HTML 注释：`<!-- last-verified: 2026-05 -->`。HTML 注释对 markdown 渲染透明，对 grep / ruby 解析友好；首行位置统一便于脚本扫描。所有 ref 初始值统一设为 `2026-05`，对应本提案晋升到 v65 的月份；后续 ref 内容修改时由作者主动更新该字段。
  - scripts/audit_ref_freshness.sh（新增）：扫描 references/*.md，对每份 ref：
    - 解析首行 `<!-- last-verified: YYYY-MM -->`，缺失则标 `UNDATED`。
    - 计算与脚本运行时间的月份差。
    - 输出三档：`FRESH`（≤ 12 个月）/ `STALE`（13-18 个月）/ `CRITICAL`（> 18 个月）/ `UNDATED`。
    - 默认按"老到新"排序输出，结尾打印汇总。
    - exit code：`CRITICAL` 或 `UNDATED` 数量 > 0 → 非零退出（提示有 ref 急需复核）；只有 STALE 不影响 exit。
    - 阈值 12 / 18 个月通过环境变量覆盖（`STALE_MONTHS=12 CRITICAL_MONTHS=18`）。
  - references/self_evolution.md：在"## 触发信号"末尾追加一条触发信号："- ref 文件首行 `<!-- last-verified -->` 字段超过 12 个月（运行 [scripts/audit_ref_freshness.sh](../scripts/audit_ref_freshness.sh) 检测），且对应 ref 涉及 iOS / Swift / SwiftUI / Xcode 等会随系统迭代变化的内容。"在文件末尾追加一个新章节："## ref 新鲜度审计"，简述字段定义、更新协议、审计周期建议（每季度跑一次 audit）。
- 替代或合并旧规则：本提案不替代任何 ID；新增的是 ref 文件级元数据机制，与既有 IR / SYM / ROUTE / OUT 规则正交。

## 预期收益
- 每份 ref 自带最近复核时间戳，可被脚本机械检查，避免"陈旧但不知道陈旧"的沉默失效。
- 新增 self-evolution 触发信号"ref 长期未复核"，把"内容陈旧"问题纳入与"规则缺失 / 冲突"同等的提案治理路径。
- 脚本可在 CI、定时任务或人工手动运行；可调阈值适配不同 ref 的更新节奏。

## 验证
- 结构校验：scripts/validate_skill_evolution.sh + scripts/validate_rule_ids.sh + scripts/validate_scenario_specs.sh。HTML 注释不影响 markdown 链接解析、孤儿引用检查、唯一所有权检查。
- 脚本自验：在 audit 脚本里跑一遍当前 27 份 ref，预期全部 FRESH（统一设为本月）；再用环境变量把 CRITICAL_MONTHS 设为 0 模拟极端情况，确认非零退出。
- 场景回放：6 场景结构校验。本提案不改输出行为、不改路由识别条件、不改 IR 定义；6 场景通过条件不变。
- 残留风险：
  - last-verified 初始值"2026-05"是统一打的"复核基线"，并非真的对每份 ref 做过逐字复核。提案晋升后第一次审计会显示全部 FRESH，但"FRESH"在初次只代表"晋升时间近"，不代表"内容确认正确"。需要后续按季度真正复核并更新字段。
  - 字段更新依赖作者主动维护；如果作者改了内容但忘记更新 last-verified，审计会误判为陈旧。可后续补一道 git pre-commit 钩子或 CI 检查（"修改 ref 的提交必须同时更新 last-verified"），但本提案不包含。
  - 阈值 12 / 18 个月是静态默认值，不区分 ref 的更新节奏（如 swift_concurrency 应该比 team_collaboration 更新更频繁）。可接受现状，差异化阈值留给后续提案。

## 状态
- promoted
