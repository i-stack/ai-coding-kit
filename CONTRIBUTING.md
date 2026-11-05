# 贡献指南

感谢你对 ai-coding-kit 的关注！本文档说明如何参与贡献。

---

## 开发环境

```bash
git clone https://github.com/i-stack/ai-coding-kit.git
cd ai-coding-kit
cp env/secrets.json.example env/secrets.json
# 编辑 env/secrets.json 填入你的 API keys
```

运行验证：

```bash
bash skills-engineering/scripts/validate-global-skills.sh
```

---

## 贡献 Reference（新增 / 修改知识条目）

ios-engineer 的规则变更直接改 `SKILL.md` 与 `references/*.md`，由机械门禁保证质量：

```bash
# 1. 实现变更（修改 references/ 或 SKILL.md）

# 2. 结构门 + 文档卫生门
bash skills-engineering/scripts/validate-skill-structure.sh ios-engineer
bash skills-engineering/scripts/validate-doc-hygiene.sh skills-engineering/ios-engineer/SKILL.md

# 3. 刷新完整性基线（与内容变更同一次提交）
bash skills-engineering/scripts/validate-skill-integrity.sh ios-engineer

# 4. 提交 PR，变更理由写进 commit message
```

### Reference 编写规范

- 每个 reference 文件首行必须包含 `<!-- last-verified: YYYY-MM -->`
- 所有规则 ID（如 `IR-001`、`ROUTE-005`）在 `SKILL.md` 内唯一声明，字面细则写在其指向的 reference
- 禁止跨文件重复定义核心概念（unique ownership 原则）
- 退役术语不得在任何 reference 中重新出现（retired term regression 检查）

---

## 翻译贡献

1. 在 `i18n/en-US/references/` 创建与 `references/` 同名的文件
2. 保持结构一致，标题层级不变
3. 规则 ID（如 `IR-001`）不翻译，保持原样
4. 代码示例中的注释可以翻译

---

## 新增平台支持

1. 在 `env/platforms/` 添加平台配置 JSON
2. 更新 `skills-engineering/scripts/sync-skills.sh` 添加新的同步目标
3. 更新 `skills-engineering/scripts/verify-sync.sh` 添加校验逻辑
4. 更新根目录 `README.md` 列出新平台

---

## Commit 规范

```
<type>: <简短描述>

type 取值：
  feat:     新功能
  fix:      修复
  ref:      新增/修改 reference
  evolve:   技能演进（proposal → implementation → promotion）
  chore:    工程基础设施（CI / 脚本 / 配置）
  docs:     文档
```

示例：
```
ref: 新增 CarPlay 场景适配 reference
docs(ios-engineer): 修复 concurrency reference 中版本前提缺失
chore(ci): CI 改为运行全仓结构校验
```

---

## PR 要求

- 所有技能：`SKILL.md` / `references/*.md` 变更须通过结构门与 DH-002 卫生门
- CI 必须全部通过（结构校验 / Reference Freshness / 全仓回归测试）
- 完整性基线（`skills-engineering/.integrity/*.sha256`）须与内容变更同一次提交刷新
- 至少 1 位 [CODEOWNERS](./.github/CODEOWNERS) 批准

---

## 治理体系速览

| 组件 | 文件 | 用途 |
|------|------|------|
| 规则声明 | `SKILL.md` | 规则 ID 的唯一声明点（细则在各自 reference） |
| 认知对手 | `cognitive_adversary_mode.md` | 反 AI 迎合机制 |
| 结构门 | `skills-engineering/scripts/validate-skill-structure.sh` | 引用/链接/孤儿/体积校验 |
| 文档卫生 | `skills-engineering/scripts/validate-doc-hygiene.sh` | DH-002 禁用词扫描 |
| 完整性基线 | `skills-engineering/.integrity/*.sha256` | 内容哈希防意外改动 |
