<!-- last-verified: 2026-08 -->
# AGENT-BRIEF（cognitive-reasoning）

> 仅给执行 agent 的极简操作卡。完整细则在 `references/` 各文件。

## 你是什么
全局认知与论证纪律技能（平台无关）。统一承载四域：认知对手模式（CAM，Tier 2）、论证质量（GR-010）、真值接地（GR-011~013）、认知拓展（CE-*，Tier 0/3）。

## 强制动作
1. 触发时**先完整读**对应 `references/*.md`，不得用摘要替代。
2. 四类纪律按 `SKILL.md` 的「何时加载」表判定是否命中；可多域同时命中。
3. 规则 ID 全球唯一，双向一致由 `validate-skill-behavior.sh` Check 2 校验。

## 不做什么
- 不替代 `engineering-discipline` 的工程交付结构纪律。
- 不在 CAM 命中时仍单独输出 Tier 0 尾注（见 CE-006 互斥）。
- 不删除或复用已发布规则 ID。
