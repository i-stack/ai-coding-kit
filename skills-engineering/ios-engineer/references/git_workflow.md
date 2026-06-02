<!-- last-verified: 2026-06 -->
# Git 工作流（iOS 工程特化）

## 目录
- 使用规则
- iOS 特有冲突治理
- 依赖与锁文件提交策略
- 分支模型与 hotfix
- 提交与 PR 粒度
- revert / reset / cherry-pick 选型
- .gitignore 基线
- 常见反模式

## 使用规则
- 本文件只覆盖 iOS / Xcode 工程在 git 层的特化战术；通用 PR 拆分、ownership、Review 责任见 [team_collaboration.md](team_collaboration.md)，构建依赖治理见 [build_release_and_ci.md](build_release_and_ci.md)。
- 触发：`project.pbxproj` 冲突、storyboard / xib 合并、Asset Catalog 二进制 diff、Pods 提交策略、`Package.resolved` 冲突、Hotfix 分支策略、Xcode 工程文件多人协作。
- 不触发：仅 Swift 源码冲突 → 走 [team_collaboration.md](team_collaboration.md) PR 规则；CI 失败 / 构建配置问题 → 走 [build_release_and_ci.md](build_release_and_ci.md)。
- 任何 git 战术建议都必须明确「该决策的可逆性 + 是否影响他人本地工作树」，不得只给命令不说后果。

## iOS 特有冲突治理

### project.pbxproj 冲突
- 根因：pbxproj 是单文件 plist，新增文件、调整 Build Phase、修改 Capabilities 都会写入同一文件，多人并行改最易冲突。
- 三级处理顺序（从轻到重）：
  1. **小冲突**：手动按 UUID + isa 字段对齐，保留双方新增节点；用 `xcodeproj` Ruby gem 或 `xUnique` 之类工具规整后再 diff 复核。
  2. **中冲突**：双方在 Xcode 关闭工程的前提下用 `git checkout --ours` / `--theirs` 选一边，再把另一边变更手动重做（新增文件重新拖入 / 重新勾 Target Membership）。
  3. **不可解**：作为冲突预防，团队约定「新增文件 / 改 Build Phase 的 PR 串行合入」，长期方案是迁向 SPM + 模块化以减少根 pbxproj 改动。
- 强制规则：解决完 pbxproj 冲突后**必须本地完整 build 一次**才能 push，不允许"看起来没冲突"就推送。

### storyboard / xib / xcassets 合并
- storyboard / xib 是 XML 但 Xcode 会重排节点顺序，diff 噪音大；冲突时优先**重做** UI 改动而非手 merge XML。
- xcassets 内部的 Contents.json 文本可手动合并，二进制资源（imageset 内的 PNG / PDF）只能"两份都保留 + 在 Xcode 内删重复"。
- 团队约束建议：单个 storyboard 限制为单 Feature owner；多人改同一 storyboard 必须串行；新页面优先 SwiftUI 或独立 xib 而非塞入大 storyboard。

### Asset Catalog / 二进制资源
- 大图、字体、视频不进 git，走 Git LFS 或独立资源仓 + SPM resource bundle；进 git 的资源必须先压缩、统一规格（@2x / @3x 命名固定）。
- 二进制资源冲突时不存在"自动合并"，唯一策略：双方协商保留哪份，删另一份。

## 依赖与锁文件提交策略

### CocoaPods
- `Podfile.lock` **必须**提交：CI / 他人 `pod install` 才能复现同版本。
- `Pods/` 目录：开源项目可不提交（依赖 CI 重装）；闭源 / 私有源 / Pod 体积可控时建议提交，避免开发机离线时无法构建、避免远端源中断卡死全员。
- 选项一旦确定写进 README，团队所有人保持一致；中途切换必须一次性全员清理本地 Pods + 切换 .gitignore。

### SPM
- `Package.resolved` **必须**提交（Xcode 工程下放在 `*.xcodeproj/project.xcworkspace/xcshareddata/swiftpm/`）。冲突时优先以**更新的版本**为准并本地 `Resolve Package Versions` 复核；不得手 merge 该文件 hash。
- 私有 SPM 依赖必须用版本锁定（exact / from），禁止 `branch: "main"`，否则锁文件无法保证可复现。

### 混合（Pods + SPM）
- 两边版本求并集，避免同一 lib 双源装载；冲突表现为「编译能过但运行时符号冲突 / 启动慢」。
- 锁文件冲突按各自策略处理，不互相替代。

## 分支模型与 hotfix
- 默认 trunk-based + 短分支：`main` 是可发布主线，feature 分支寿命 ≤ 5 天，超期必须分阶段合入或砍小。
- gitflow 仅在「同时维护多个 LTS 版本」时使用；否则其 `develop` / `release` 分支会拉长冲突窗口。
- Hotfix 分支必须从「线上 tag」切出（非 `main` HEAD），修完合回 `main` 并 cherry-pick 到所有受影响的发布分支；不得只合到 main 就认为修完。
- 任何分支策略都必须配套：发布点打 annotated tag（含版本号 + commit + 修改人），dSYM 与 tag 一一对应（详见 [build_release_and_ci.md](build_release_and_ci.md) 发布与灰度节）。

## 提交与 PR 粒度
- 单 commit 主题单一：功能 / 重构 / 样式不混；commit message 第一行 ≤ 72 字符 + 动词起始（add / fix / refactor / chore），body 解释**为什么**而非"做了什么"。
- 涉及 pbxproj 改动的 commit 单独提交，便于 revert 时不带源码。
- PR 拆分粒度与团队 PR 规则同步见 [team_collaboration.md](team_collaboration.md) PR 规则节；本节只补充 iOS 特化点：
  - 「新增模块 / Target」单独 PR，不与业务改动混。
  - 「依赖升级」单独 PR，必带变更日志与回滚说明。
  - 「Xcode 版本切换 / Swift 版本升级」单独 PR，需团队同步本地工具链。

## revert / reset / cherry-pick 选型

| 操作 | 适用场景 | 风险 | 是否影响他人 |
|------|----------|------|--------------|
| `git revert <sha>` | 已合入主线的错误改动需撤销 | 留下反向 commit；history 完整 | 不影响（推荐默认） |
| `git reset --soft HEAD~N` | 本地未推送的 commit 重新组织 | 仅本地，未 push 前安全 | 不影响 |
| `git reset --hard <sha>` | 本地误改要彻底丢弃 | **不可恢复**未提交工作 | 不影响（前提：未 push） |
| `git reset --hard` 已推送分支 | 几乎从不该做 | 改写 history，破坏他人本地 | **强影响**，禁止用于共享分支 |
| `git cherry-pick <sha>` | 修复回灌到发布分支 / 把单个 commit 搬运 | 上下文丢失风险，可能引入隐式依赖 | 不影响主线，但搬运链路要追溯 |
| `git rebase -i` | 本地未推送的 commit 整理 | 仅本地安全 | 不影响（前提：未 push） |
| `git push --force-with-lease` | 个人分支整理后必要 push | 比 `--force` 安全（远端未变才允许） | 不影响他人协作分支 |

强制规则：**任何会改写已推送 history 的操作**（force-push、reset --hard 后 push、rebase 已推送分支），在共享分支上**一律不允许**；仅在个人 feature 分支且明确知会 reviewer 时允许。

## .gitignore 基线
必须忽略：
```
# Xcode 用户数据
xcuserdata/
*.xcuserstate
*.xcuserdatad/

# DerivedData
DerivedData/
Build/

# Pods（按团队策略二选一，与依赖治理节保持一致）
# Pods/

# SPM 解析缓存（保留 Package.resolved，忽略本地 build 缓存）
.swiftpm/xcode/package.xcworkspace/
.build/

# 系统与编辑器
.DS_Store
*.swp
.vscode/
.idea/

# Fastlane / 本地凭据
fastlane/report.xml
fastlane/Preview.html
fastlane/test_output
*.p12
*.mobileprovision
```

必须**不忽略**：`Podfile.lock`、`Package.resolved`、`*.xcodeproj/project.pbxproj`、`*.xcworkspace/contents.xcworkspacedata`、共享 scheme（`*.xcodeproj/xcshareddata/xcschemes/`）。

## 常见反模式
- pbxproj 冲突没本地 build 就 push，结果 CI 全员红
- 用 storyboard XML 手 merge，merge 完看似正确但运行时崩
- `Pods/` 既未忽略又部分提交，导致团队成员本地 `pod install` 后无谓 diff
- Hotfix 直接从 `main` HEAD 切（带入未发布的脏改动），合回后还污染主线
- 共享分支 `git push --force`，把别人本地工作树搞乱
- 一个 commit 同时改 pbxproj + 业务源码，revert 时撕扯
- `Package.resolved` 不提交，CI 与本地版本漂移
- Xcode 版本升级与业务改动混在同一 PR，回滚时只能整体回滚
