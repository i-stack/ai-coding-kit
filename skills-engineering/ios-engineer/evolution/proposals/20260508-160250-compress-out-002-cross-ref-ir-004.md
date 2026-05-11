# Skill Evolution Proposal

## Metadata
- Proposal ID: 20260508-160250-compress-out-002-cross-ref-ir-004
- Created At: 2026-05-08 16:02:50 +0800
- Active Version At Creation: v52

## 问题信号
- v47 SKILL.md 审查发现 [OUT-002] 的内容是 [IR-004] 例外条款的部分复述：
  - IR-004 已明示："默认按'根因 → 为什么 → 修法 → 验证'输出；若任务命中长模板要求，四段式作为摘要层，详细模板作为附加层。**代码审查 / PR Review 例外**：按 findings-first 标准输出骨架输出，骨架段落详见 [review_checklists.md](references/review_checklists.md) 第 8 节。"
  - OUT-002 原文："代码审查 / PR Review：使用 [review_checklists.md](references/review_checklists.md) 第 8 节的 findings-first 标准输出骨架。"
- 两处重复了"代码审查 / PR Review → findings-first 骨架 → review_checklists.md 第 8 节"这组语义三元组。
- 这是 IR 层（行为约束）与 OUT 层（模板索引）之间的合理重叠：IR-004 说"什么时候用这个模板"，OUT-002 说"这个模板在哪找"。但措辞上 OUT-002 没有声明自己是 IR-004 的模板落点，读者要自己在两层间对齐。
- 自进化触发信号「多份文档对同一件事重复下定义」命中，但程度较轻；v47 审查结论也标记为"可保留"。本提案做最小改动：在 OUT-002 加一句交叉引用，显化"模板触发条件来自 IR-004"。

## 变更类型
- 修正表达（保留 OUT-002、IR-004 两个 ID 不动；只在 OUT-002 正文加对 IR-004 的交叉引用）

## 变更内容
- 修改文件：
  - `SKILL.md` 第 59 行：[OUT-002] 改写为——
    - 旧：`[OUT-002] 代码审查 / PR Review：使用 [review_checklists.md](references/review_checklists.md) 第 8 节的 findings-first 标准输出骨架。`
    - 新：`[OUT-002] 代码审查 / PR Review：findings-first 标准骨架（触发条件见 IR-004 例外条款；骨架段落详见 [review_checklists.md](references/review_checklists.md) 第 8 节）。`
    - **注**：IR-004 不加方括号——validate_rule_ids.sh 用 `/\[([A-Z]+-\d{3})\]/` 扫描 inline ID 声明，加方括号会触发 "duplicate ID IR-004" 报警（IR-004 自身在核心铁律里已经有一次 `[IR-004]` 声明）。
  - `references/rule_index.md` 的 OUT-002 摘要同步改写为："代码审查 / PR Review：findings-first 骨架（触发条件见 IR-004）→ review_checklists.md 第 8 节"（rule_index.md 不在 validate_rule_ids.sh 的 skill_id_scan 范围，这里加不加方括号都行，为一致起见不加）。
- 不修改：
  - [IR-004]：例外条款原文保留；它继续作为"何时切换输出模板"的权威。
  - review_checklists.md：ref 内容不动。
- 替代或合并旧规则：无（OUT-002、IR-004 ID 均沿用）

## 预期收益
- 读者从 OUT-002 即可反查到 IR-004 的触发条件，不用自己在两层间对齐。
- 保留 OUT-002 在"输出模板"索引里的存在（不破坏 OUT 层的完整性），但通过交叉引用显式承认 IR-004 是上位约束。
- SKILL.md 单行略长（约 +10 字符），但总行数不变。

## 验证
- 结构校验：
  - `bash scripts/validate_rule_ids.sh` 保持通过（ID 不动）。
  - `SKIP_SNAPSHOT_CONSISTENCY=1 bash scripts/validate_skill_evolution.sh` 12 步全绿。
  - 内部 markdown 链接检查 [5/12]：新增的 `[IR-004]` 不是 markdown 链接（没有 `()` 目标），而是 inline ID 引用 —— validate 脚本只校验真正的 `[text](link)` 格式，不会报错。
- 场景回放：
  - 6 个固定场景中 review 场景会命中 OUT-002 和 IR-004 的 findings-first 骨架；本提案不改语义（只加交叉引用），review 场景预期 pass。
  - 其它 5 个场景不命中 OUT-002，预期 pass。
- 残留风险：
  - 交叉引用改为不加方括号的 "IR-004"（纯文本），视觉上和其它 inline ID 声明（都带方括号）有差异；但这正是 validate_rule_ids.sh 用 bracket 形式做 inline-ID 声明识别的设计——不加方括号=不是 ID 声明、只是文字引用。读者识别无障碍。

## 验证补充（duplicate ID 反向校验，已执行）
- 初版草稿用了 `[IR-004]` 带方括号，首次 `bash scripts/validate_rule_ids.sh` 报 `SKILL.md: duplicate ID IR-004 (line 12, line 57)`，确认方括号会触发 duplicate。
- 改为不带方括号 "IR-004" 后重跑，通过。

## 状态
- promoted
