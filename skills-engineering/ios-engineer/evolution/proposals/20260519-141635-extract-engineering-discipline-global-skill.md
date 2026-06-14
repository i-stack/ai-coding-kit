# Skill Evolution Proposal

## Metadata
- Proposal ID: 20260519-141635-extract-engineering-discipline-global-skill
- Created At: 2026-05-19 14:16:35 +0800
- Active Version At Creation: v70

## 问题信号
- ios-engineer/SKILL.md 的 IR-002/003/004/005/007/008 描述的是平台无关的通用工程纪律（前置确认、单根因锁定、四段式输出、最小修复、不格式化代码、变更覆盖声明），与 iOS 平台毫无绑定关系，但因为它们写在 ios-engineer SKILL.md 里，其他平台 skill 无法复用这些规则。
- 已有先例：IR-010（逻辑链）以相同理由提取为 `logical-reasoning` 全局 skill（GR-010，v69），cognitive-expansion 也已是独立全局 skill；工程纪律类规则应遵循同一架构。
- ios-engineer SKILL.md 核心铁律因为混入了通用规则而过于臃肿，导致 iOS 特有规则（版本前提、认知对手）难以突出。

## 变更类型
- 退役规则（IR-002/003/004/005/007/008 从 ios-engineer 退役）
- 新增能力（提取为 `engineering-discipline` 全局 skill，编号 GR-002/003/004/005/007/008）

## 变更内容
- 新建 `skills-engineering/engineering-discipline/SKILL.md`：六条 GR 规则入口
- 新建 `skills-engineering/engineering-discipline/references/engineering_discipline.md`：GR-002/003/004/005/007/008 完整细则
- 新建 `skills-engineering/scripts/templates/engineering-discipline.mdc.tmpl`：Cursor 规则模板
- `ios-engineer/SKILL.md` 核心铁律删除 IR-002/003/004/005/007/008；OUT-002 中 `IR-004 例外条款` 改为 `GR-004 的 PR review 例外`；保留 IR-001/006/011（iOS 专属）
- `ios-engineer/references/rule_index.md`：IR-002/003/004/005/007/008 改为 `deprecated`，新增 GR-NNN 节（GR-002/003/004/005/007/008），追加退役记录，更新跨文件共享概念索引 Owner（四段式输出→GR-004、残留风险声明→GR-008、前置确认块→GR-002）
- `ios-engineer/scripts/lint_hit_rules.sh`：新增 GR-002/GR-004/GR-008 信号；IR-002/IR-004/IR-008 保留为 deprecated alias
- `ios-engineer/scripts/validate_rule_ids.sh`：退役记录节不再重复解析（skip `## 退役记录` section），GR-NNN 规则豁免 ios-engineer SKILL.md 双向断言
- `ios-engineer/evolution/scenarios/*.json`：6 个场景文件中 rule_id 由 IR-003/004/005/008 更新为 GR-003/004/005/008
- `scripts/templates/agent-preamble.md.tmpl`：sync-manifest 增加 `skill:engineering-discipline`，新增 `# global engineering discipline` 块（含 `{{ENGINEERING_DISCIPLINE_SKILLS_DIR}}` 占位符）
- `scripts/sync-agent-preamble.sh`：`render_managed_block` 新增 `ed_dir`，sed 追加 `{{ENGINEERING_DISCIPLINE_SKILLS_DIR}}` 替换
- `scripts/verify-sync.sh`：`check_preamble_tilde` 新增 engineering-discipline 加载指令检查
- `~/.claude/CLAUDE.md`（及 Codex/Xcode 各端）：managed block 新增 `# global engineering discipline` 段，加载路径指向已同步的 `skills/engineering-discipline/`
- `ios-engineer/evolution/active_version.json`：v69 → v70
- 替代旧规则：IR-002 → GR-002，IR-003 → GR-003，IR-004 (core) → GR-004，IR-005 → GR-005，IR-007 → GR-007，IR-008 → GR-008；IR-004 的 PR review 例外保留在 ios-engineer OUT-002

## 预期收益
- 其他平台 skill（未来的 android-engineer、web-engineer 等）可直接复用 engineering-discipline，无需各自重写通用工程纪律
- ios-engineer SKILL.md 核心铁律从 9 条缩减为 3 条（IR-001/006/011），仅保留 iOS 专属内容，可读性与 on-boarding 成本大幅下降
- usage-audit 命中率更准确：GR-NNN 跨平台可统计，不再因工具不同导致 IR/GR 混用偏差
- 减少上下文浪费：全局 skill 由 preamble 统一加载，ios-engineer SKILL.md 不重复承载通用内容

## 验证
- 结构校验：`validate_rule_ids.sh` 通过（Rule IDs OK: 34 in SKILL.md, 48 in rule_index.md, 41 active）
- 同步验证：`sync-skills.sh`（5 端均写入 engineering-discipline/）+ `sync-agent-preamble.sh`（CLAUDE.md/AGENTS.md 含 engineering discipline 段）+ `verify-sync.sh`（5 targets clean）
- 残留风险：engineering-discipline 尚无独立 validate_rule_ids.sh / validate_skill_evolution.sh（当前由 ios-engineer 侧脚本间接覆盖）；GR-003/005/007 无机械校验 anchor（行为规则，无文字锚点），lint 不能覆盖

## 状态
- approved
