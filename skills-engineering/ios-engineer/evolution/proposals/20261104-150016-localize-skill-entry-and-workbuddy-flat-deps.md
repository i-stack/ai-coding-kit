# Skill Evolution Proposal

## Metadata
- Proposal ID: 20261104-150016-localize-skill-entry-and-workbuddy-flat-deps
- Created At: 2026-11-04 15:00:16 +0800
- Active Version At Creation: v75

## 问题信号
- `SKILL.md` 是可运行入口文档，但正文长期为英文，与仓库「references 以 zh-CN 为单一真源、en-US 仅作镜像」的本地化策略不一致；中文用户读到的入口文档与它引用的中文 ref 语言断层，且英文正文里夹中文锚点（如「卡顿 / 启动慢」）导致可读性衰减。
- 入口文档缺少显式的执行顺序：铁律、任务分流、输出模板三块内容并列，读者需要自行拼装「先归类 → 再加载 ref → 再建版本前提 → 再认知校准 → 最后按模板输出」的链路，容易出现跳步（如未命中 IR-006 却漏写版本前提、命中 CAM 却先给结论）。
- `references/mcp_control.md` 使用页内锚点链接 `[调用预算](#调用预算)`，该文在其它技能包内联/改写后会失去锚点目标，形成死链风险；同级章节用「」文字引用更稳。
- 同批次的 WorkBuddy 上架打包侧问题由独立改动承载（见「关联改动」），本提案只登记 `ios-engineer` 契约文件的语言与结构变更。

## 变更类型
- 修正表达（本地化 + 结构显式化），不新增、不退役任何规则。

## 变更内容
- 修改文件：`SKILL.md`
  - 头部 `<!-- @locale-support -->` 注释由英文改为中文，保留「en-US 镜像为 PARTIAL、规则 ID 不翻译」的原意。
  - 正文整体由英文改写为 zh-CN，覆盖：认知对手模式、核心铁律（IR-001 / IR-006 / IR-011）、任务分流（路由优先级、症状导航表、ROUTE 表）、输出模板、交付要求等。
  - 新增一级章节「执行流程（强制按顺序执行）」，把原先散落在各节的顺序约束收敛为 6 步：任务归类 → 加载 ref（受 ROUTE-016 预算约束）→ 建立版本前提基线（IR-006）→ 认知校准（CAM + IR-011）→ 按 OUT 模板产出并声明残留风险 → 用用户语言回答（IR-001）。
  - 新增一级章节「输出模板」，把 OUT-001…OUT-006 从散列条目聚为一节，正文语义与触发条件不变。
  - 规则 ID 集合逐项比对与改动前完全一致（`[IR|SYM|ROUTE|OUT|GR]-NNN` 去重排序后 diff 为空）；ROUTE-025 等既有条目仅做中文化，未新增路由。
- 修改文件：`references/mcp_control.md`
  - 「调用约束」首条把 `[调用预算](#调用预算)` / `[防循环退出条件](#防循环退出条件)` 两处页内锚点改为「调用预算」「防循环退出条件」文字引用，避免内联打包后锚点失效；约束语义不变。
- 不替代或合并任何既有规则；rule ID、行为契约、`agents/`、`evolution/` 流程均未变动。
- 关联改动（不属于本 skill 契约，不参与本次 evolution 校验）：`skills-engineering/workbuddy/*` 与 `skills-engineering/README.md` 的依赖内联拍平（`references/dep-<dep>--<file>.md`）及目录层级门禁，见同一提交的 `fix(workbuddy)` 主题。

## 预期收益
- 入口文档语言与 references 真源一致，中文用户不再在入口处经历语言切换；en-US 镜像策略仍以注释形式保留可查。
- 执行顺序从「隐含」变为「显式编号」，IR-006 / IR-011 / ROUTE-016 的落点各有唯一位置，减少跳步与漏项。
- 输出模板聚合后，OUT-00x 的检索成本下降，避免在长 ROUTE 表中翻找渲染要求。
- 去掉页内锚点依赖，内联到其它技能包时不会产生死链。

## 验证
- 结构校验：`scripts/validate-skill-proposal.sh` 走 `validate-skill-evolution.sh`（`SKIP_SNAPSHOT_CONSISTENCY=1`、`SKIP_SWIFT_TYPECHECK=1`）14 步全通过，记录见 `evolution/validations/20261104-150016-localize-skill-entry-and-workbuddy-flat-deps.json`（`status=validated`、`exit_code=0`）。
- 场景回放：`run-behavior-validation.sh` 中的「提案脚本拒绝路径」（39 项）与「GC 不变式」（7 项）全部通过；本轮为纯文档语言/结构变更，未新增或改写行为契约，未登记逐 slug 行为回放（`scenario_validation_status=not_run`），因此记录里 `promotion_readiness=not_ready`，需要在下次 promote 前另行补充场景回放。
- 规则一致性：改动前后 `[IR|SYM|ROUTE|OUT|GR]-NNN` 去重集合 diff 为空，无规则新增/退役/改名。
- 残留风险：本轮只做语言与结构重排，未做行为回归的端到端实测；若下游（`cognitive-reasoning` 镜像、i18n en-US）侧后续同步，需要单独提案对齐，避免两处口径漂移。快照一致性在 `SKIP_SNAPSHOT_CONSISTENCY=1` 下跳过，待下次 promote 生成 v76 快照后自然满足；本机 Xcode-beta 缺 `sys/cdefs.h`，Repository 模板 Swift 编译以 `SKIP_SWIFT_TYPECHECK=1` 跳过（CI 完整 Xcode 不受影响）。

## 状态
- approved
