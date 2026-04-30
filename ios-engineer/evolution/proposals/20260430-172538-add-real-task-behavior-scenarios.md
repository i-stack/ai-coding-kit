# Skill Evolution Proposal

## Metadata
- Proposal ID: 20260430-172538-add-real-task-behavior-scenarios
- Created At: 2026-04-30 17:25:38 +0800
- Active Version At Creation: v34

## 问题信号
- v34 行为验证层已经覆盖 active snapshot、proposal 脚本拒绝路径和 Repository 模板可用性，但仍偏工程门禁。
- 真实 iOS 使用中最容易回归的两类行为尚未脚本化：代码审查是否坚持 findings-first，以及网络缓存/错误建模是否同时命中 `networking_patterns.md` 与 `domain_modeling.md`。
- 如果这两类行为只靠人工抽检，后续规则调整可能让代码审查回到四段式，或让缓存错误再次被模板吞掉。

## 变更类型
- 新增能力：为行为验证层增加两个真实任务回放场景。

## 变更内容
- 修改文件：
  - `scripts/run_behavior_validation.sh`
- 新增行为场景：
  - `[behavior 4/5] Code review output contract`
    - 检查 `SKILL.md` 明确声明代码审查 / PR Review 例外，走 findings-first。
    - 检查 `review_checklists.md` 包含“审查结论 / 严重问题 / 一般问题 / 验证缺口 / 最终要求”。
    - 检查 `examples.md` 没有把代码审查重新定义为“根因 -> 为什么 -> 修法 -> 验证”的四段式。
  - `[behavior 5/5] Network cache and error-modeling contract`
    - 检查 `SKILL.md` 中“请求失败 / 重试异常 / 鉴权刷新 / 分页重复或漏数据 / 缓存污染”同时路由到 `networking_patterns.md` 和 `domain_modeling.md`。
    - 检查 `networking_patterns.md` 保留缓存键、缓存实现不透 ViewModel 等缓存行为约束。
    - 检查 `domain_modeling.md` 保留 ErrorModel 六层错误契约。
    - 检查 `code_templates.md` 不回归 `try? cache.read/write`，并保留缓存读写失败显式处理要求。
- 替代或合并旧规则：不替代旧规则；把两个高价值人工抽检项固化为脚本回放。

## 预期收益
- 行为验证层从工程门禁扩展到真实任务契约，能更早发现输出结构和网络建模规则回归。
- 代码审查不会因四段式默认输出规则而误伤 findings-first。
- 网络缓存模板、网络模式和错误建模的跨文件协作被固定为可重复检查。

## 验证
- 结构校验：
  - `SKIP_SNAPSHOT_CONSISTENCY=1 bash scripts/validate_skill_evolution.sh` 通过。
- 场景回放：
  - `behavior-review-output`：代码审查入口、review 骨架和 examples 反回归检查通过。
  - `behavior-network-cache-error`：网络缓存路由、缓存约束、ErrorModel 六层契约和模板显式缓存错误处理检查通过。
- 残留风险：
  - 当前仍是文本契约回放，不直接调用模型生成完整回答；后续如需更强验证，可加入固定 prompt + 黄金输出片段比对。

## 状态
- promoted
