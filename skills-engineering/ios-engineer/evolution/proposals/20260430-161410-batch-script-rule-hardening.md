# Skill Evolution Proposal

## Metadata
- Proposal ID: 20260430-161410-batch-script-rule-hardening
- Created At: 2026-04-30 16:14:10 +0800
- Active Version At Creation: v30

## 注
本提案按用户显式要求合并 6 个独立问题（Issue 1-6）。违反 self_evolution.md "单问题单提案"约束，但 6 个问题按主题可分 4 组，修复策略差异小，用户明确选择打包。后续若某条改动需回退，只能按文件粒度回退，不能按单个 issue 回退。

## 问题信号

### Issue 1：rollback_skill_evolution.sh 破坏性先删后复制（P0）
- L22-26：先 `rm -rf agents references scripts`，再复制 snapshot，最后才 `bash scripts/validate_skill_evolution.sh`。
- 风险：snapshot 不完整、cp 中途失败、target_version 异常时，当前可用 skill 直接被毁。
- 缺 `target_version` 格式白名单（`../` 等路径注入虽被 `-d` 检查兜住但未显式禁止）。
- validate 在破坏后执行，发现错误已无法用自身回滚。

### Issue 2：演进脚本手写 JSON 未转义（P0）
- `approve_skill_promotion.sh:47-54`、`promote_skill_evolution.sh:63-79`、`validate_skill_proposal.sh:48-60` 全部用 `cat > <<EOF` 拼接 JSON。
- 参数含 `"` / 换行 / `\` / `$` 就生成非法 JSON。
- 现状触发窗口窄（本地手动输入）但长期累积为安全洞，且文件名 / 版本号 / approved_by 等字段无字符集白名单。

### Issue 3：code_templates.md Repository 缓存模板自相矛盾（P1）
- L130-136 用 `try? cache.read()` / `try? cache.write(entity)` 静默吞错。
- 同节 L143 规则："缓存策略必须按业务语义定义，**不得静默污染状态**"。
- 模板与规则直接冲突，AI 照模板生成代码会继承吞错模式。

### Issue 4：ios_conventions.md lazy var 优先与 let 优先冲突（P1）
- L17-18："属性声明除非确有必要...否则**优先使用 `lazy var`**"。
- 同文件 L121："为图省事把所有属性声明为 `var`，不声明 `private(set)` 或 `let`" 列为反模式。
- `lazy var` 本身就是 `var`，与 Swift 社区共识（`let` 优先 / 不可变优先 / 并发安全）冲突。`lazy var` 不是并发安全的（默认非 actor 隔离），优先 `lazy var` 在并发语境会误导 AI。

### Issue 5：ios_conventions.md Snapshot 命名全面禁止过宽（P1）
- L47：禁止使用 `Snapshot` / `快照` 及同类命名。
- 同文档体系 `build_release_and_ci.md:63` 又用"快照测试"作为标准术语。
- Apple API 本身有 `NSDiffableDataSourceSnapshot` / `UIViewControllerContextTransitioning snapshotView` / XCTest snapshot testing 等标准用法，全面禁止误伤合法用法。

### Issue 6：validate_skill_evolution.sh 检查面不足（P2）
- 现有只检查：YAML / SKILL.md 行数 / SKILL.md 引用存在 / 2 处分层守卫。
- 漏检查：
  - references/*.md 内部链接是否有效（EE 规则的自动化）
  - 孤儿 reference（曾是 v1→v2 修复过的问题，当前无自动检查防回归）
  - 关键规则唯一归属（例如 "错误分层 6 层枚举" 应只在 domain_modeling.md）
  - 退役词回归（例如 "协议层" 作为错误分层名不应再出现）

## 变更类型
- 修正表达（Issue 1、3、4、5）：修复脚本破坏性和规则冲突。
- 新增能力（Issue 2、6）：建立 JSON 安全生成模式和增强 validate 检查。

## 变更内容

### 修改文件：`scripts/rollback_skill_evolution.sh`（Issue 1）
- 改为"校验 → 暂存 → 原子替换 + 备份回退 → 验证"流程：
  1. 版本格式白名单：`^v[0-9]+(-[A-Za-z0-9]+)*$`
  2. snapshot 完整性预检查（SKILL.md + agents + references + scripts 都存在）
  3. snapshot 先复制到 mktemp 临时目录，预跑 YAML / 行数基础校验
  4. 当前文件移到备份目录，再把暂存目录 move 成正式位置
  5. 跑完整 validate_skill_evolution.sh，失败自动恢复备份
  6. active_version.json 用 ruby JSON.pretty_generate 生成

### 修改文件：`scripts/approve_skill_promotion.sh` / `scripts/promote_skill_evolution.sh` / `scripts/validate_skill_proposal.sh`（Issue 2）
- 所有 `cat > "$file" <<EOF ... EOF` 生成 JSON 的代码块改为 `ruby -rjson` 脚本，用 `JSON.pretty_generate({...})` 输出。
- 对关键字段做 regex 白名单：
  - `proposal_id`：`^[0-9]{8}-[0-9]{6}-[A-Za-z0-9-]+$`
  - `new_version` / `target_version`：`^v[0-9]+(-[A-Za-z0-9]+)*$`
  - `approved_by`：`^[A-Za-z0-9_@.-]{1,100}$`（宽松允许常用字符）
  - `source_ref`：`^[A-Za-z0-9:_.-/]{1,200}$`
- 校验失败立即 exit 1，不生成 JSON。

### 修改文件：`references/code_templates.md`（Issue 3）
- 重写 Repository 缓存模板 L130-136：
  - `try? cache.read()` → `do { try cache.read() } catch { logger.error(...); /* 显式降级到 remote */ }`
  - `try? cache.write(entity)` → `do { try cache.write(entity) } catch { logger.error(...); /* 不阻塞返回但必须记录 */ }`
  - 缓存读失败时区分"未命中 / 损坏 / 读失败"三种路径，不压成单一 nil 分支。
- 模板注释明确说明："缓存读失败选择降级时必须记录；写失败必须记录但可以不阻塞返回；若业务要求强一致则改为 throw。"

### 修改文件：`references/ios_conventions.md`（Issue 4 + 5）
- L17-18 改写为：
  ```
  ## Swift 属性声明与位置
  - 能 `let` 则 `let`：属性默认不可变，不必要不暴露写入能力。
  - 需要延迟构造且初始化依赖运行时上下文（例如需要 self）时才用 `lazy var`；注意 `lazy var` 不是并发安全的，跨任务访问必须说明线程归属或改为 `actor` 持有。
  - `var` 属性必须最小化对外可见性：优先 `private(set)`；跨类可写 `var` 必须说明状态归属和写入路径。
  - 共享可变状态必须说明隔离策略（`actor` / `@MainActor` / 明确锁）。
  - 属性位置建议统一放在类结构末尾，避免可见性交错。
  ```
- L47 Snapshot 规则改写为：
  ```
  - 禁止把业务临时状态泛化命名为 `Snapshot` / `快照`（例如把"当前某视图的临时数据"命名为 `XxxSnapshot` 而不给业务语义）；改用贴近业务的命名（例如 `pinnedFollowUpIdentifier`、`savedDraft`、`pendingOrder`）。
  - **例外**：Apple API 自身的 Snapshot 类型（例如 `NSDiffableDataSourceSnapshot`、`UIViewControllerContextTransitioning.snapshotView`）保留原名；测试框架的 snapshot testing 概念保留原名。
  ```

### 修改文件：`scripts/validate_skill_evolution.sh`（Issue 6）
- 新增 3 个检查步骤（扩展为 [1/7] - [7/7]）：
  - **[5/7] Validate internal markdown links**：用 ruby 扫 `references/*.md` 中的 `[x](path.md)` 引用，检查相对路径目标文件存在（忽略 `http://` / `https://` / 纯 anchor）。
  - **[6/7] Validate no orphan references**：references/ 中每个 `.md` 文件都必须被 SKILL.md 直接引用，或被其他 reference 引用（传递可达）。
  - **[7/7] Validate unique ownership of key concepts**：用 pattern-to-owner 映射检查：
    - 错误分层 6 层枚举（`传输.*状态码.*解码.*鉴权.*业务.*展示`）只应在 `domain_modeling.md`
    - 完整性能取证工具清单（`Time Profiler.*Core Animation.*Allocations`）只应在 `observability_logging.md`
    - findings-first 骨架（`审查结论.*严重问题.*一般问题.*验证缺口.*最终要求`）只应在 `review_checklists.md`
  - 新增 **退役词检查**（可放 [4/7] 或新建步骤）：
    - "协议层" 作为错误层级（与"错误"相邻）退役后不应回归
    - "四段式" 作为代码审查输出骨架退役后不应在 examples.md 第 3 节回归

## 替代或合并旧规则
- Issue 1/2：新脚本形态替代旧脚本形态；旧脚本行为完全退役，语义由新实现承担。
- Issue 3：code_templates.md 旧缓存模板的"静默吞错"形态退役，新模板显式处理三种错误路径。
- Issue 4：`lazy var` 优先条款退役，改为 `let` 优先 + 条件性 `lazy var`。
- Issue 5：Snapshot 全面禁止退役，改为"业务临时状态禁用 + Apple API / 测试语境例外"。
- Issue 6：不退役任何检查；新增 3 个检查 + 1 组退役词检查补齐覆盖。

## 预期收益
- Issue 1：rollback 成为真正可恢复的命令，脚本错误不会破坏工作版本；路径注入被显式拒绝。
- Issue 2：元数据 JSON 全部通过 ruby 序列化，消除字段含特殊字符导致非法 JSON 的可能；关键字段白名单防止可疑输入提交。
- Issue 3：Repository 缓存模板与"不得静默污染状态"规则一致；AI 按模板生成的代码包含观测日志和显式降级决策。
- Issue 4：属性声明规则与 Swift 社区共识和并发安全一致；AI 不再被 `lazy var` 优先误导。
- Issue 5：Snapshot 禁用只打业务泛化命名，不误伤合法 Apple API / 测试语境。
- Issue 6：人工审查累积发现的 4 类问题（死链接 / 孤儿 / 唯一归属 / 退役词回归）全部自动化，未来 regression 由脚本拦截。

## 验证
- 结构校验：
  - `SKILL.md` frontmatter 合法，行数 ≤ 500（本提案不改 SKILL.md）。
  - `SKILL.md` 引用的所有 `references/*.md` 文件存在。
  - 增强后的 `validate_skill_evolution.sh` 自己跑通（包括新增 3 步）。
  - 关键：新脚本在当前 v30 版本所有文件上必须**全部通过**（因为当前已经没有已知死链 / 孤儿 / 归属冲突 / 退役词回归）。
- 场景回放：
  - 场景 `mcp-control`：隐式验证 rollback 不再破坏当前 skill。
  - 场景 `review`：验证 ios_conventions 新规则不阻塞审查，code_templates 新缓存模板可被引用。
- 残留风险：
  - 退役词检查的关键词列表是当前已知退役词；未来新增退役词需手动维护。后续可以加元数据文件 `evolution/retired_terms.json` 统一管理。
  - 唯一归属 pattern 是人工选定的 3 条；随着 skill 演化新增权威归属概念时需更新 pattern 列表。
  - 脚本改动较大，一次性合并多个主题提案违反"单问题单提案"约束；若某项修改需回退，只能文件粒度回退，不能按 issue 单独回退。该 trade-off 由用户显式接受。
  - Issue 2 的字段白名单可能过严或过松（例如 approved_by 允许的字符集）；在真实使用中按需调整。

## 状态
- promoted
