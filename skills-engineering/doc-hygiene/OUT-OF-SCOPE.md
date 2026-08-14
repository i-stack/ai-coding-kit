# doc-hygiene 范围外

本 skill 约束**文档正文的卫生**（禁过程叙事、只留最终态），不负责：

- 文档的语法/格式规范——由 `.agents/writing-docs.md` 负责。
- 规则的演进流程本身（proposal→validate→promote）——由 `engineering-discipline`（GR-007）与 evolution 脚本负责；本 skill 只规定「流程产物（文档）里不许出现流程」。
- CHANGELOG / evolution 的写法——那是变更记录的载体，本规则不约束其内容（DH-002 的禁止词在变更记录中允许出现）。

## 边界

DH-001/002 针对**运行期会被加载的文档**（Agent 是读者）；对 `evolution/history/**` 快照与 CHANGELOG 不适用——它们本就是历史/变更载体。
