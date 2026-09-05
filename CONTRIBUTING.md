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
cd skills-engineering/ios-engineer
bash scripts/validate.sh
```

---

## 贡献 Reference（新增 / 修改知识条目）

ios-engineer 采用**提案驱动**的演进流程，所有对 reference 或 SKILL.md 的变更必须先创建提案：

```bash
# 1. 创建提案骨架
bash skills-engineering/ios-engineer/scripts/create-skill-proposal.sh \
  "feat: 新增 CarPlay 适配参考"

# 2. 编辑 evolution/proposals/<id>.md，填写动机、变更范围、影响分析

# 3. 实现变更（修改 references/ 或 SKILL.md）

# 4. 运行完整验证
bash skills-engineering/ios-engineer/scripts/validate-skill-evolution.sh

# 5. 提交 PR，proposal 和变更一起提交
```

### Reference 编写规范

- 每个 reference 文件首行必须包含 `<!-- last-verified: YYYY-MM -->`
- 所有规则 ID（如 `IR-001`、`ROUTE-005`）必须在 `rule_index.md` 中注册
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
evolve: promote v74 — 修复 concurrency reference 中版本前提缺失
chore: CI 加入 rule_id 双向一致性检查
```

---

## PR 要求

- 治理技能（含 `evolution/` 目录，当前为 ios-engineer）：涉及 `SKILL.md` 或
  `references/*.md` 的变更必须绑定 `evolution/proposals/` 中的 proposal（pre-commit
  守卫强制执行）
- 所有技能：`SKILL.md` / `references/*.md` 变更须通过结构门与 DH-002 卫生门
- CI 必须全部通过（Rule IDs / Scenario Specs / Ref Freshness / Snapshot Consistency）
- 至少 1 位 [CODEOWNERS](./.github/CODEOWNERS) 批准

---

## 治理体系速览

| 组件 | 文件 | 用途 |
|------|------|------|
| 规则注册表 | `rule_index.md` | 所有规则 ID 的单一事实来源 |
| 自进化 | `self_evolution.md` | 技能演进闭环流程 |
| Usage Ledger | `usage_ledger.md` | 任务命中观测 |
| 认知对手 | `cognitive_adversary_mode.md` | 反 AI 迎合机制 |
| 验证场景 | `validation_scenarios.md` + `evolution/scenarios/` | 回归验证集 |
