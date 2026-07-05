# 可移植性与社区生态提升方法论

> 本文档记录了 ai-coding-kit 从「内部工具」到「社区可复用项目」的 4 阶段实践（P0–P3）。  
> 其他项目可直接复用「优先级与 ROI 矩阵」「问题诊断清单」「里程碑模板」。

---

## 问题诊断清单

在开始改造前，用以下清单快速扫描项目薄弱点：

| 维度 | 检查项 | 诊断手段 |
|------|--------|----------|
| **平台覆盖** | 支持几个 AI 编码平台？目标用户用哪些？ | 统计 `SYNC_TARGETS` 或平台配置数 |
| **语言锁定** | 内容是否强制单一语言？是否阻断了非母语用户？ | grep 输出语言相关规则 |
| **安装体验** | 用户如何安装？是否有包管理器支持？ | 检查是否存在 `brew`/`npm`/`pip` 等入口 |
| **版本管理** | 是否有 Git Tag / Release Notes？用户能否 pin 版本？ | `git tag --list` |
| **CI/CD** | 是否有自动化质量门禁？每次变更是否自动校验？ | 检查 `.github/workflows/` |
| **贡献体系** | 外部贡献者是否知道如何参与？ | 检查 `CONTRIBUTING.md` / `CODEOWNERS` |
| **文档可发现性** | 用户能否通过搜索引擎找到文档？ | Google 搜索项目名 |
| **硬编码路径** | 是否存在个人机器路径？其他人 clone 后能否直接运行？ | `grep -r '/Users/' --include="*.sh"` |

---

## 优先级与 ROI 矩阵

| 优先级 | 任务 | 工作量 | 影响面 | ROI | 适用于 |
|--------|------|--------|--------|-----|--------|
| **P0** | CI 自动验证流水线（规则一致性 / 场景校验 / 新鲜度审计 / 硬编码扫查） | 2h | 每次 PR 自动拦截回归 | 🔴 极高 | 所有含自动化脚本的项目 |
| **P0** | 清理硬编码路径 + CI grep 守卫 | 0.5h | 消除"clone 后报错" | 🔴 极高 | 存在 shell 脚本或个人路径配置的项目 |
| **P1** | CONTRIBUTING.md + CODEOWNERS | 1h | 打通社区参与通道 | 🟠 高 | 所有公开仓库 |
| **P1** | i18n 分层：元指令层英文化 + 治理层翻译 | 4h | 解锁国际用户 | 🟠 高 | 内容驱动型项目（Agent Skill / 文档 / 规则体系） |
| **P2** | Git Tag + Release Notes + CHANGELOG | 1h | 外部可 pin 版本 | 🟡 中 | 所有发布型项目 |
| **P2** | Homebrew Formula / npm package / 包管理器分发 | 2h | 扩大安装渠道 | 🟡 中 | CLI 工具 / 可安装技能包 |
| **P3** | VitePress / Docusaurus 文档站 + GitHub Pages 部署 | 3h | 搜索引擎可发现，降低学习曲线 | 🟢 锦上添花 | 含技术文档的公开仓库 |
| **P3** | 多语言文档站（中/英） | 2h | 覆盖非英语开发群体 | 🟢 锦上添花 | 文档量大的项目 |

### ROI 计算逻辑

- **P0（立即止血）**：不改则持续漏血。CI 缺失 → 每个合并都可能引入回归；硬编码路径 → 每个新贡献者 clone 后第一步就失败。
- **P1（快速见效）**：改动小但打开流量入口。国际化让潜在用户数放大 10–100 倍；CONTRIBUTING 让外部开发者从"看了不会做"变为"照着文档即可提交 PR"。
- **P2（基础设施）**：不是紧急项但一旦上线就会持续产生价值（每个新用户都会走包管理器安装）。
- **P3（放大收益）**：锦上添花，适合 P0+P1 完成后再做。文档站让内容可被 Google 索引，带来有机用户增长。

---

## 实施指南

### P0 — CI 自动验证

**核心原则**：每次 PR 都应触发自动化校验，无需人工介入。

```yaml
# .github/workflows/validate.yml 关键 Job
validate:
  - 规则 ID 双向一致性（定义文件 ↔ 入口文件）
  - 场景规格校验（JSON/Markdown schema）
  - 参考文件新鲜度审计（last-verified 日期扫描）
  - 使用台账校验
  - 演进流水线完整校验（跳过需运行时环境的步骤）

hardcoded-paths:
  - 扫描所有提交文件，正则匹配 '/Users/' 个人路径
  - 白名单排除模板路径（如 '/Users/you/...'）
```

**适用条件**：项目有自动化脚本（shell/python）即可，不挑语言栈。

### P0 — 硬编码路径清理

**常见硬编码模式**：

```bash
# ❌ 坏
PROJECT_PATH="/Users/song/Desktop/iOS/MyApp"
# ✅ 好
PROJECT_PATH="${PROJECT_PATH:-~/path/to/your/project}"
```

**CI 挡板**：

```bash
find . -type f -not -path './.git/*' -print0 \
  | xargs -0 grep -n '/Users/' \
  | grep -v '/Users/you/' \
  | grep -v '/Users/YourName/'
```

### P1 — i18n 分层架构

**核心设计**：不移动现有文件，以镜像层叠加。

```
project/
├── SKILL.md              # 元指令层 → 英文（路由/优先级/判据）
├── references/           # 中文源文件（不移动）
│   └── rule_index.md
└── i18n/
    └── en-US/            # 英文镜像层
        └── references/
            └── rule_index.md
```

**翻译优先级**：
1. 治理层文件（rule_index / self_evolution / cognitive_adversary_mode）—— 理解体系运作的入口
2. 架构概述（architecture_and_network / architecture_analysis）—— 高频引用
3. 其余领域 reference —— 按引用频率排序

**IR-001 语义升级**：
```
旧: 强制中文输出
新: 输出语言与用户输入语言一致（auto-match）
```

### P1 — 贡献指南

`CONTRIBUTING.md` 必备板块：

```markdown
## 新增 Reference（提案驱动）
1. 创建 proposal
2. 实现 + 校验
3. 提交 PR

## 翻译贡献
1. 在 i18n/{locale}/ 创建对应文件
2. 保持结构一致
3. CI 自动校验中英文件数量

## Commit 规范
feat / fix / ref / evolve / chore / docs
```

### P2 — 包管理器分发

**Homebrew Formula 要素**：

```ruby
class MyProject < Formula
  desc "One-line description"
  homepage "https://github.com/user/repo"
  url "https://github.com/user/repo/archive/refs/tags/v1.0.0.tar.gz"
  license "MIT"

  def install
    prefix.install Dir["*"]
    bin.install_symlink prefix/"run.sh" => "myproject"
  end
end
```

**npm package.json 要素**：

```json
{
  "name": "@scope/pkg",
  "version": "1.0.0",
  "bin": { "myproject": "./run.sh" },
  "files": ["src/", "run.sh", "README.md"],
  "keywords": ["relevant", "search", "terms"]
}
```

### P3 — 文档站

**VitePress 最小启动**：

```bash
mkdir docs && cd docs
# 创建 .vitepress/config.ts + index.md
npm install -D vitepress
npm run docs:dev    # 本地预览
npm run docs:build  # 构建静态站
```

**GitHub Pages 自动部署**：

```yaml
# .github/workflows/deploy-docs.yml
on:
  push:
    paths: ['docs/**', 'package.json']

jobs:
  build:
    steps:
      - uses: actions/setup-node@v4
        with: { node-version: 22 }
      - run: npm ci && npm run docs:build
      - uses: actions/upload-pages-artifact@v3

  deploy:
    needs: build
    steps:
      - uses: actions/deploy-pages@v4
```

**前置条件**：GitHub 仓库 Settings → Pages → Source → GitHub Actions（启用一次）。

---

## 里程碑模板

| 周 | 目标 | 产出 |
|----|------|------|
| **W1 — 止住出血点** | CI + 硬编码清理 + CONTRIBUTING | 每次 PR 自动校验 + 任何人 clone 后可直接运行 |
| **W2 — 打开国际通道** | i18n 分层 + SKILL.md 英文化 | 非母语用户可直接使用 |
| **W3 — 正式发布** | Git Tag + CHANGELOG + Homebrew + 文档站上线 | 通过 `brew install` 或 `npm i` 安装，文档可被搜索 |

---

## 常见反模式

| 反模式 | 为什么不行 | 正确做法 |
|--------|-----------|----------|
| 先做文档站再做 CI | 文档站引流的用户看到 broken 项目就流失了 | CI 先于文档站 |
| 翻译全部 references 再发布 | 30+ 份文件翻译周期长，阻塞发布 | 先翻治理层 3 份，其余渐进 |
| 只打 Tag 无 Release Notes | 用户不知道新版本有什么变化 | Tag + CHANGELOG 同时发布 |
| Homebrew Formula 含硬编码 sha256 | 每个版本都要手动更新 | 首次留空，提示用户 `shasum` 补填 |

---

## 适用场景判断

| 项目特征 | 适用优先级 |
|----------|-----------|
| 只有 README 没有文档站 | **P3** 文档站，P3 多语言 |
| 只有英文内容没有中文 | **P1** i18n 分层（反方向：en-US → zh-CN） |
| 有 CI 但没有规则校验 | **P0** 补充业务规则校验 Job |
| 无 CHANGELOG 无版本号 | **P2** Git Tag + CHANGELOG |
| 有 shell 脚本但无包管理器 | **P2** Homebrew / npm |
| 公开仓库无贡献指南 | **P1** CONTRIBUTING + CODEOWNERS |

---

> 最后更新：2026-07-05 · ai-coding-kit v3.0.0
