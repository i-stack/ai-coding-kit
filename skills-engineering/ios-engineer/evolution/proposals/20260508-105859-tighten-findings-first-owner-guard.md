# Skill Evolution Proposal

## Metadata
- Proposal ID: 20260508-105859-tighten-findings-first-owner-guard
- Created At: 2026-05-08 10:58:59 +0800
- Active Version At Creation: v39

## 问题信号
- v39 把 findings-first 五段标签（审查结论 / 严重问题 / 一般问题 / 验证缺口 / 最终要求）的 owner 锁定在 `references/review_checklists.md` 第 8 节，但 `scripts/validate_skill_evolution.sh` 第 7 步的守卫 regex 只匹配 owner 文件里的代码块多行格式：`/审查结论\s*\n[^\n]*不可合入[^\n]*可合入.../m`。
- 这导致 v39 之前 `SKILL.md:12` 与 `SKILL.md:58` 的"审查结论 / 严重问题 / 一般问题 / 验证缺口 / 最终要求"同行枚举并没有触发守卫失败；owner 漂移是靠人工 grep 发现的，不是靠自动化挡回。
- 即使把 regex 放宽到覆盖同行形式，还有一个更深的 bug：`UNIQUE_OWNERS` 与 `RETIRED_TERMS` 两个守卫 loop 都只迭代 `Dir.glob('references/*.md')`，根本不扫描 `SKILL.md`。v40 之前，SKILL.md 对这两类守卫完全免检。
- 结果是：v39 之前在 SKILL.md 里写五段标签同行形式，哪怕把 regex 修宽也不会被拦截；必须同时扩大文件覆盖范围才能真正关闭漂移口子。

## 变更类型
- 修正表达：把 `validate_skill_evolution.sh` 第 7 步 `UNIQUE_OWNERS` 中 findings-first 条目的 regex 替换为一个更宽的模式，覆盖"5 段标签按顺序出现在短段文字内"的所有形式（同行枚举、代码块块状、散落短句）。
- 新增能力：把 `UNIQUE_OWNERS` 与 `RETIRED_TERMS` 两个守卫 loop 的文件覆盖范围从 `references/*.md` 扩展到包含 `SKILL.md`，关闭 SKILL.md 对这两类守卫的免检漏洞。

## 变更内容
- 修改文件：
  - `scripts/validate_skill_evolution.sh`
    - 第 7 步 `UNIQUE_OWNERS` 哈希中的 findings-first 条目从：
      ```
      /审查结论\s*\n[^\n]*不可合入[^\n]*可合入[\s\S]*?严重问题[\s\S]*?一般问题[\s\S]*?验证缺口[\s\S]*?最终要求/m
      ```
      替换为：
      ```
      /审查结论[\s\S]{0,300}?严重问题[\s\S]{0,300}?一般问题[\s\S]{0,300}?验证缺口[\s\S]{0,300}?最终要求/m
      ```
      新模式的语义：在任意非 owner 文件里只要 5 段标签按顺序出现且相邻两个标签之间不超过 300 个字符，就视为"完整定义"，触发 owner 违例。
    - `UNIQUE_OWNERS` 与 `RETIRED_TERMS` 两处 `Dir.glob('references/*.md').sort.each` 统一替换为"files_to_check = ['SKILL.md'] + Dir.glob('references/*.md').sort"，让 SKILL.md 一起进入守卫循环；owner 判定继续用 `File.basename(file) == owner`，若 owner 为 `review_checklists.md`，SKILL.md 的 basename 不会与之相等，会正常参与检查。
    - 违例描述字符串从 `findings-first 完整骨架定义` 更新为 `findings-first 五段标签完整定义`，与新 regex 的语义保持一致。
- 替代或合并旧规则：
  - 旧 regex 退役：不再只捕获 owner 代码块的特定排版。新 regex 覆盖旧 regex 能捕获的全部情况（owner 代码块被 300 字符窗口完整框住），且额外覆盖同行枚举与散落短段。
  - 旧"只扫 references/*.md"的守卫作用范围退役，改为同时扫 `SKILL.md` + `references/*.md`。

## 预期收益
- 五段标签的同行枚举从此在本地和 CI 都会被 `validate_skill_evolution.sh` 拦住，不需要再靠人工 grep 补漏。
- v39 锁定的 owner 单点变成机器可验证的事实，不再依赖人类自律。
- 为后续给更多跨文件共享概念（四段式、错误分层、任务分流等）追加 owner 守卫打好模板——一个 regex + 一个 owner 文件名即可声明新的共享概念保护。

## 验证
- 结构校验：
  - `bash scripts/validate_skill_evolution.sh` 在当前工作树（v39 已收敛）上 9/9 base + 5/5 behavior 全绿。
  - `bash scripts/test_proposal_scripts.sh` 保持 Passed=39 Failed=0。
- 场景回放：
  - 场景 `owner-guard-catches-inline-regression`：在 `SKILL.md` 第 12 行临时还原 v39 之前的"按 findings-first 结构输出（审查结论 / 严重问题 / 一般问题 / 验证缺口 / 最终要求）"写法，`bash scripts/validate_skill_evolution.sh` 必须在 `[7/9]` 步骤打印 "Unique ownership violated: findings-first 五段标签完整定义 (应只在 review_checklists.md) 却在 SKILL.md 出现" 并以非零退出；随后恢复原状验证再次全绿。
  - 场景 `owner-guard-allows-reference-only`：SKILL.md 第 12 行当前的 "按 findings-first 标准输出骨架输出，骨架段落详见 [review_checklists.md]..." 只含 "findings-first" 词，无 5 段标签，必须不触发守卫。
- 残留风险：
  - 四段式 canonical 措辞（"根因 / 为什么 / 修法 / 验证"）的 owner 守卫本提案不处理：当前多个 ref 以短括注形式引用该序列作为 reminder，在不引入大量假阳性的情况下无法简单用 regex 区分"引用 reminder"与"重新定义"。该项作为 M3 后期或 M4 的独立提案处理，需先明确引用与定义的规则界。
  - 新 regex 使用 300 字符窗口是经验值；如果未来有场景需要在 owner 文件里把标签铺得更散，需要把窗口值调整为更大或改用行数窗口，届时再走提案。

## 状态
- promoted
