# Skill Evolution Proposal

## Metadata
- Proposal ID: 20260430-165137-fix-v31-drift-and-script-hardening
- Created At: 2026-04-30 16:51:37 +0800
- Active Version At Creation: v31

## 问题信号
- v31 快照存在四处可证伪缺陷，`rollback_skill_evolution.sh v31` 会将已知缺陷恢复为 active：
  - `references/code_templates.md` 的 Repository 模板使用 `logger.error(...)` 但未注入 `logger`，复制后不可编译。
  - `references/ios_conventions.md` line 22 `避免可见性交错。` 中 `性交` 两字相邻，肉眼与分词器均易误读。
  - `scripts/check_skill_promotion_readiness.sh` 缺 `proposal_file` 路径白名单，与另外四个 proposal 脚本不一致。
  - `scripts/create_skill_proposal.sh` 对 slug 无校验，可生成后续脚本拒绝的 proposal 文件名（空格/中文/斜杠/点号/路径穿越），造成"创建成功但无法验证/晋升"的断链。

## 变更类型
- 修正表达（code_templates / ios_conventions）
- 新增能力（script 入参白名单）

## 变更内容
- 修改文件：
  - `references/code_templates.md`：Repository 模板补 `private let logger: LoggerProtocol`，init 增加 `logger:` 入参，与模板自身"缓存读写失败必须记录"的纪律一致。
  - `references/ios_conventions.md` line 22：`避免可见性交错。` → `避免不同访问级别的属性穿插分布。`；术语与同文件第 28 行"访问控制"对齐。
  - `scripts/check_skill_promotion_readiness.sh`：在 `proposal_file="$1"` 之后补入 `^evolution/proposals/[0-9]{8}-[0-9]{6}-[A-Za-z0-9_-]+\.md$` 白名单，与 `approve_skill_promotion.sh` / `promote_skill_evolution.sh` / `validate_skill_proposal.sh` / `record_validation_scenario.sh` / `update_skill_proposal_status.sh` 一致。
  - `scripts/create_skill_proposal.sh`：在 `slug="$1"` 之后补入 `^[A-Za-z0-9_-]{1,80}$` 白名单，严格度等同下游 proposal_file regex 的 slug 部分。
- 替代或合并旧规则：无

## 预期收益
- 六个 proposal 脚本在入参校验上彻底同构，任意入口接到非法 `proposal_file` 都在同一处失败，错误信息一致，不再依赖下游拦截。
- Repository 模板复制后可编译，不再传递"先声明纪律再违反纪律"的矛盾样本给使用者。
- 规则文本摆脱肉眼易误读、分词易切歧义的相邻串。
- 关闭 "create 成功但下游拒绝" 的断链，proposal 文件名在创建环节即与下游契约对齐。

## 验证
- 结构校验：`bash scripts/validate_skill_evolution.sh` 全部 7 步通过（YAML / SKILL.md 行数 / 引用完整 / 分层守卫 / 内链 / 无孤儿 / 唯一所有权与退役词）。
- 场景回放：
  - `script-path-whitelist`：六个脚本分别以合法路径、含时间戳但缺 slug 的路径、`/etc/hosts`、`../../../etc/passwd` 输入，预期合法通过、非法在相同文案处被拦。
  - `code-template-compiles`：Repository 模板中 `logger` 声明、init 参数、`logger.error(...)` 调用三处完整闭环。
  - `conventions-readable`：`ios_conventions.md` line 22 不再包含易误读相邻串，语义保留"不同访问级别属性不应穿插"的本意。
- 残留风险：
  - 新引入的 `LoggerProtocol` 在该模板中为占位协议名；若下游引用希望绑定到具体类型，需另起 proposal 定义。
  - `create_skill_proposal.sh` 的 slug 长度上限 80 与下游 proposal_file regex 的无限长不完全对齐，但语义上"创建环节更严"是合理的。

## 状态
- promoted
