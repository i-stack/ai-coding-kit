# doc-hygiene Agent 调用指南

## 一句话描述

文档卫生纪律：写或更新 skills-engineering 下任何 `.md` 时，正文只陈述最终态事实，禁止过程叙事；变更过程进 CHANGELOG / evolution。

## 何时调用

- 任何产生或修改 `.md` 文档的任务（SKILL.md / references / AGENT-BRIEF / OUT-OF-SCOPE / docs / README / .agents）。
- 被 `.agents/writing-docs.md` 约定引用（建议文档写作类任务 `depends_on: [doc-hygiene]`；CI 不强制校验，实际触发靠 invocation.md 关键词行）。

## 关键行为

1. **[DH-001]** 正文只描述当前架构/行为事实，不描述演变过程。
2. **[DH-002]** 禁止出现迁移/owner 纠正/此前承载/待平移等过程叙事关键词。
3. **[DH-003]** 变更过程写入 CHANGELOG.md 或 evolution/（proposals/validations/approvals/history），不进文档正文。

## 不调用的情况

- 纯代码 / 纯脚本改动且不涉及 `.md` 正文。
- 本身就是变更记录文件（CHANGELOG.md / evolution/**）。
