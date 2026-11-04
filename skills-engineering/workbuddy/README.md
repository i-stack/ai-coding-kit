# WorkBuddy 上架包（技能收费）

把 `skills-engineering/` 下的技能打包成 WorkBuddy 开放平台可上传的 zip，用于技能市场售卖。
规范来源：<https://open.workbuddy.cn/docs/skill>

## 一、平台规范（硬约束）

zip 内顶层必须是技能目录，`SKILL.md` 要在技能根的下一级直接可见：

```text
{skill-name}/
├── SKILL.md              # ★ 必须
├── references/           # 参考资料（可选）
├── scripts/              # 可执行脚本（可选）
└── templates/            # 模板文件（可选）
```

`SKILL.md` = YAML frontmatter + Markdown 正文。frontmatter 字段：

| 字段 | 必填 | 说明 |
|------|------|------|
| `name` | 是 | 技能标识，kebab-case，与目录名一致 |
| `display_name` | 是 | 市场中文展示名 |
| `display_name_en` | 是 | 市场英文展示名 |
| `description` | 是 | 写清用途和触发词（Agent 据此触发） |
| `description_zh` | 是 | 详情页中文简介 |
| `description_en` | 是 | 详情页英文简介 |
| `version` | 是 | 版本号 |
| `author` | 是 | 合作方名称 |
| `allowed-tools` | 否 | 工具白名单（逗号分隔） |
| `examples_zh` / `examples_en` | 否 | 详情页【试试这样用】，各 1~3 条 |

`references/` 需在 `SKILL.md` 中以 `@references/xxx.md` 或相对链接引用才会被加载。

审核常见卡点：`description` 写推销话术而不是触发场景、脚本含下载执行或读取敏感目录、zip 内 `SKILL.md` 多包了一层目录。

## 二、本仓库的打包设计

三条不变量：

1. **源 `SKILL.md` 仍是单一真源**。WorkBuddy 专属字段不回写源 `SKILL.md`，避免破坏
   `validate-skill-structure.sh` 的必填键门与 pre-commit 治理门；市场字段集中写在
   `workbuddy/catalog.json`，打包时注入。
2. **`description` 不重复维护**。直接取源 `SKILL.md` 的 `description`（已是触发语义），
   `catalog.json` 只维护展示面字段（展示名、中英简介、示例、定价建议）。
3. **依赖必须拍平内联**。市场侧没有 `depends_on`，用户只装一个技能。市场包仅支持
   根 / 二级目录 / 文件，不能落三层目录；catalog 里声明的 `deps` 在打包时拍平内联为
   `references/dep-<dep>--<file>.md`（用前缀命名代替子目录），跨技能链接自动改写。

包内链接处理规则（`build_workbuddy.py::fix_links`）：

- 包内可解析 → 保持/重写为相对路径；
- 指向内联依赖（`../../cognitive-reasoning/references/x.md`）→ 改写到 `references/dep-<dep>--x.md`；
- 指向 companion 文件（`../AGENT-BRIEF.md`）→ 落到 `references/`；
- 指向包外且包内没有（`../scripts/...`、`../i18n/...`）→ 降级为行内代码，保留标签文本，不留死链。

根目录白名单只有 `SKILL.md + references/ scripts/ templates/`，其余（含 `i18n/`、
`agents/`、`docs/`）一律不进包。

## 三、命令

```bash
bash workbuddy/package-workbuddy.sh list                 # 查看 catalog：版本 / 定价建议 / 依赖
bash workbuddy/package-workbuddy.sh build <skill|--all>  # 构建 + 校验 + 打包 zip
bash workbuddy/package-workbuddy.sh validate --all       # 只校验（无构建产物时先临时 stage）
bash workbuddy/package-workbuddy.sh sheet                # 生成上架填表清单 upload-sheet.md
bash workbuddy/package-workbuddy.sh clean
```

### zip 层级：`--layout flat|nested|both`（默认 both）

平台上传报 **「所选文件夹中未找到 SKILL.md」**，是 zip 内层级不对：解析器看的是"所选文件夹"的
根目录，那里必须直接有 `SKILL.md`。官方文档的 `{skill-name}/SKILL.md` 有两种解读，所以两种都产出：

```text
flat  （默认首选）    nested（备选）
SKILL.md              ios-engineer/
references/             SKILL.md
scripts/                references/
templates/              scripts/
```

```bash
bash workbuddy/package-workbuddy.sh build --all --layout flat     # 只要 flat
bash workbuddy/package-workbuddy.sh build --all                   # 两种都产出，逐个试
bash workbuddy/package-workbuddy.sh expert --layout flat          # 专家包同理
```

文件名区分与实测顺序（flat 已实测被拒，从 2 开始试）：

| 文件 | 解压后根目录 | 状态 |
|---|---|---|
| `<skill>-v1.0.0.zip` | `SKILL.md` + `references/` | ❌ 实测报「未找到 SKILL.md」 |
| `<skill>-v1.0.0-nested.zip` | `<skill>/SKILL.md` | 待试（文档字面结构，优先） |
| `<skill>-v1.0.0-compat.zip` | 上面两者都有 | 两种解析器都能命中的兜底 |
| `dist/workbuddy/<skill>/`（未压缩目录） | `SKILL.md` | 界面若是「选择文件夹」就选它 |

专家包默认 nested（插件包惯例），`-flat.zip` 为备选。

另外两种同样会触发这个报错的情况：把整个 `dist/workbuddy/` 目录（13 个技能并列）打成 zip；
或把专家包 zip 上传到【添加技能】入口（专家包没有根级 `SKILL.md`，应走【我的专家 → 创建专家 → 上传】）。

产物在 `skills-engineering/dist/workbuddy/`（已 gitignore）：

```text
dist/workbuddy/
├── <skill>-v<version>.zip   # 直接上传开放平台
├── <skill>/                 # 未压缩的 stage，便于人工核对
├── build-manifest.json      # 体积 / 依赖 / 降级链接统计
└── upload-sheet.md          # 后台填表逐项清单
```

`build` 内置校验（任一 FAIL 即中止打包）：frontmatter 八项必填、`name` 与目录一致且
kebab-case、`description` 长度、根目录白名单、依赖内联完整性、链接不越界、无类密钥文件、
无本机绝对路径泄露、包体 ≤ 5MB、zip 顶层含 `<skill>/SKILL.md` 且无 `__MACOSX`。

## 三之二、专家包（一个 zip 带全部技能）

技能形态只支持一个技能一个 zip；要一次性带上多个技能，走**专家**形态（<https://open.workbuddy.cn/docs/expert>），
`plugin.json` 的 `skills` 字段就是为它准备的：

```text
ai-engineering-experts/
├── .codebuddy-plugin/plugin.json   # 核心配置（含 skills 路径列表）
├── agents/ai-engineering-expert.md # Agent 定义（路由表 + 加载纪律）
├── avatars/expert.png              # 512×512，≤500KB
├── skills/                         # 13 个技能目录，各自 SKILL.md + references/
└── README.md
```

```bash
bash workbuddy/package-workbuddy.sh expert              # 构建 + 校验 + 打包
bash workbuddy/package-workbuddy.sh expert --allow-placeholder   # 本地自检，跳过占位值门禁
```

配置在 `workbuddy/expert.json`。与技能包的三点差异：

1. **依赖不内联**：13 个技能同在 `skills/` 下，跨技能链接（`../../cognitive-reasoning/references/x.md`）
   天然可解析，因此保留原样，只在 `SKILL.md` 末尾标注兄弟技能路径。链接修复在全部技能落盘后统一执行。
2. **展示面在 `plugin.json`**：`displayName` / `profession` / `displayDescription` / `tags` /
   `quickPrompts` / `categoryId` 都在这里，内嵌技能的 `SKILL.md` 仍带完整市场字段（兼容两种解析器）。
3. **内嵌技能保留根级 companion 文件**（`AGENT-BRIEF.md` / `OUT-OF-SCOPE.md` 留在技能根），
   不受技能包"根级只认 SKILL.md + 三个子目录"的限制。

专家包校验项：`plugin` 与 `name` 一致、小写连字符命名、语义化版本、`expertType`、`categoryId` 在官方
15 类内、双语字段齐备、`displayDescription.zh` 中文字数 40–50、`tags` 与 `quickPrompts` 各 3 条、
`defaultInitPrompt` 等于 `quickPrompts[0]`、头像 512×512 且 ≤500KB、`agentName` 对应 `agents/` 文件名、
team 形态的成员 Agent 文件齐全、`skills` 路径均存在且各自通过技能级校验、整包 ≤5MB、zip 结构完整。

**作者信息与头像**（`--allow-placeholder` 可跳过这两项门禁做本地自检）：

- `expert.json` 的 `author.email` 必须是真实邮箱（平台必填，占位值会被 FAIL 拦下）。
- 头像源图在 `workbuddy/avatars/expert.png`（512×512 PNG，257KB），构建时复制进包；
  文件缺失才回退到脚本生成的渐变占位图。换头像直接覆盖该文件后重建即可。
  当前头像由云端文生图模型生成，**生成结果右下角带「AI 生成」水印**，制作时是先把 1024×1024 原图
  裁成 900×900（`sips -c 900 900 --cropOffset 0 62`）再缩放到 512（`sips -z 512 512`）去掉水印的；
  自行替换时同样要确认画面角落干净。

升级为**专家团**：把 `expert.json` 的 `expert_type` 改成 `team`，补 `team_info{leadAgent, memberAgents}`，
并为每个成员在 `workbuddy/templates/` 下准备同名 Agent 定义，构建器会自动校验成员文件齐全。

## 四、上架流程

1. 开放平台（<https://open.workbuddy.cn/>）注册并完成实名认证（个人或企业均可）。
2. **先发免费技能并过审**——开通收款账户的硬前提之一；本仓库免费项：
   `engineering-discipline`、`problem-analysis`、`checkpoint-persist`、`historical-recall`、`doc-hygiene`。
3. 开通收款账户（微信签约，个人走微信、企业对公），进入「收入变现」。
4. 上传 zip：技能走【技能市场 → 添加技能 → 上传】，专家包走【我的专家 → 创建专家 → 上传】；
   平台自动解析 `SKILL.md` / `plugin.json`。
5. 选定价模式：**一次性买断**（功能完整、更新少）或**按月订阅**（需持续更新）。
   **发布后付费模式不可改，免费转付费也暂不支持**——上架前先定好。
6. 提交审核（约 7 个工作日），审核期不支持快速改版，首版要把触发条件和输出格式写全。

## 五、定价建议（catalog 中的建议值）

| 模式 | 技能 | 建议价 |
|------|------|--------|
| 免费 | engineering-discipline / problem-analysis / checkpoint-persist / historical-recall / doc-hygiene | ¥0 |
| 买断 | project-decision-evaluation | ¥29 |
| 买断 | classics-reading / plan-grill | ¥19 |
| 买断 | prompt-optimizer | ¥9.9 |
| 订阅 | ios-engineer | ¥29/月 |
| 订阅 | auto-code-review / cross-model-review | ¥19/月 |
| 订阅 | cognitive-reasoning | ¥9.9/月 |
| 买断 | 专家包 ai-engineering-experts（13 个技能打包） | ¥99 |

内测期平台服务费约 1%（另含支付通道费）。免费项同时承担两个作用：满足开通收款的前提、
以及作为付费技能的内联依赖（`ios-engineer` 依赖 `cognitive-reasoning` + `engineering-discipline`）。
专家包是"一个产品带走全套"，与单技能包并存不冲突：想单买的用户买技能，想省事的用户买专家。

## 六、维护新技能 / 改字段

- 新增上架技能：在 `catalog.json` 的 `skills` 下加一条，`enabled: true`，补齐展示名、
  中英简介、中英示例、定价建议、依赖。
- 改版本号：改 `catalog.json` 的 `version`。
- 改触发语义：改源 `SKILL.md` 的 `description`，重新 `build` 即生效。
- 临时下架：该条 `enabled: false`，`build --all` 会跳过。
