# Skill Evolution Proposal

## Metadata
- Proposal ID: 20260430-142606-post-Q-T-U-cross-file-cleanup
- Created At: 2026-04-30 14:26:06 +0800
- Active Version At Creation: v24

## 问题信号
Proposal Q（v16）、T（v18）、U（v19）改动后留下 3 处下游未同步的跨文件不一致：

- **网络链路双定义**：
  - `architecture_and_network.md` L72：`Endpoint -> RequestBuilder -> APIClient -> Decoder -> Repository -> UseCase -> ViewModel`（漏 DTO / Entity / Mapper / ViewState）
  - `networking_patterns.md` L24：`Endpoint -> RequestBuilder -> APIClient -> DTO -> Repository -> Entity -> ViewModel`（漏 Decoder / UseCase）
  - 两份链路各漏一半环节，AI 读完仍无法回答 "DTO 应该在哪一层声明 / Entity 映射归谁 / UseCase 什么时候才需要"。
- **examples.md 审查章节仍保留完整骨架**：
  - Proposal U 把 `examples.md` 第 3 节对齐为 findings-first，但保留了完整模板定义（23 行）。
  - `review_checklists.md` L74 "标准输出骨架" 是审查输出的单一归属。
  - examples.md 第 3 节与 review_checklists.md 的骨架内容一致但语义重复，违反"单一归属"原则。
- **domain_modeling.md URLSession 回流**：
  - Proposal Q 在 L82 写入 "传输错误：APIClient / URLSession 层捕获"。
  - Proposal T 在 architecture_and_network.md L76 已改为 "既有网络层按现有抽象扩展，不在局部改动中顺手迁移底层实现"。
  - 具体实现名 URLSession 重新出现在 domain_modeling.md，会诱导 AI 在 Bajoseek（使用 BajoSeekNetWork）等既有项目中误判为需要迁移到 URLSession。

## 变更类型
- 合并重复：网络链路统一到 `architecture_and_network.md` 单一完整定义；examples.md 审查章节改为引用 `review_checklists.md`。
- 修正表达：`domain_modeling.md` 去除 URLSession 具体实现名，改为抽象层描述。

## 变更内容
- 修改文件：`references/architecture_and_network.md`
  - 修改 L72 "基础结构 - 推荐链路"：
    - 原：`Endpoint -> RequestBuilder -> APIClient -> Decoder -> Repository -> UseCase -> ViewModel`
    - 改为完整链路：`Endpoint -> RequestBuilder -> APIClient -> Decoder/DTO -> Repository/Mapper -> Entity -> UseCase -> ViewModel/ViewState`
  - 在链路下方追加每个环节的职责说明：
    ```
    环节职责（完整链路单一定义，其他文件引用此处）：
    - Endpoint：定义路径 / 方法 / Header / Body schema。
    - RequestBuilder：构造 URLRequest（或项目既有网络抽象的等价请求对象）。
    - APIClient：发送请求、接收响应、错误分层转换。
    - Decoder/DTO：把响应字节流解码为 DTO 数据传输对象（接口传输结构）。
    - Repository/Mapper：把 DTO 映射为 Entity 业务实体，聚合远端 / 缓存 / 持久化。
    - Entity：业务语义结构，脱离传输细节。
    - UseCase：业务用例编排（复杂业务场景必要，简单 CRUD 可省略）。
    - ViewModel/ViewState：界面状态编排和渲染结构。
    ```
- 修改文件：`references/networking_patterns.md`
  - 退役 L22-26 独立链路定义（4 行），替换为引用：
    ```
    ## 请求链路
    完整链路和各环节职责定义见 [architecture_and_network.md](architecture_and_network.md) "基础结构"。本文件聚焦具体网络模式（分页 / 重试 / 缓存 / 鉴权刷新 / 上传下载 / 幂等去重），不重复链路骨架。
    ```
- 修改文件：`references/examples.md`
  - 退役 "3. 代码审查答法" 整节（原 23 行完整模板），替换为短引用：
    ```
    ## 3. 代码审查答法
    适用场景和输出结构（findings-first 骨架 + 命中维度过检）见 [review_checklists.md](review_checklists.md)。
    本文件不重复定义代码审查的输出骨架；审查输出格式、可合入判定、分维度检查项全部在 review_checklists.md 单一承担。
    ```
- 修改文件：`references/domain_modeling.md`
  - 修改 L82 "传输错误" 归属：
    - 原：`传输错误：APIClient / URLSession 层捕获，转为 ErrorModel.network，不向上暴露 NSError。`
    - 改为：`传输错误：APIClient / 项目既有网络抽象层捕获（URLSession / 自研 NetworkManager / Alamofire 等），转为 ErrorModel.network，不向上暴露 NSError 或底层 SDK 错误类型。`

## 替代或合并旧规则
- 网络链路的两处独立定义退役，合并为 architecture_and_network.md 单一完整链路；networking_patterns.md 改为引用。
- examples.md 第 3 节完整模板退役，review_checklists.md 成为代码审查输出的唯一归属。
- domain_modeling.md URLSession 具体实现名退役，改为抽象层描述，与 architecture_and_network.md Proposal T 的"既有网络抽象"决定一致。

## 预期收益
- 网络链路有唯一权威定义：AI 在任何文件读到的链路都是同一份完整版本，可回答 DTO / Entity / UseCase / ViewState 各自归属。
- 代码审查输出格式收敛到 review_checklists.md 单一来源；examples.md 不再维护重复骨架，未来修改审查结构只改一处。
- domain_modeling.md 不再诱导 URLSession 迁移；Bajoseek 等既有网络抽象项目的 AI 输出不再与 architecture_and_network.md 冲突。
- 3 处跨文件不一致全部消除。

## 验证
- 结构校验：
  - `SKILL.md` frontmatter 合法，行数 ≤ 500（本提案不改 SKILL.md）。
  - `SKILL.md` 引用的所有 `references/*.md` 文件存在。
  - `root_cause_enforcement.md` / `examples.md` 分层守卫不受影响。
- 场景回放：
  - 场景 `review`：用户输入 "review 这个改动"。期望 AI 读 review_checklists.md findings-first 骨架，不读 examples.md 第 3 节（已改为引用）。
  - 场景 `parameter-pass-through`：用户输入 "新增 currentModel 字段 A 类里拿不到"。期望 AI 读 architecture_and_network.md 完整链路，能明确说出字段应该在 DTO / Entity / UseCase / ViewState 哪一层声明和透传。
  - 隐式验证（Bajoseek 上下文）：涉及网络错误捕获时，AI 应说 "按既有 BajoSeekNetWork 抽象层捕获"，不建议迁移到 URLSession。
- 残留风险：
  - architecture_and_network.md 链路 + 职责说明新增约 10 行，文件总长约 126 行，仍在合理范围。
  - networking_patterns.md 退役链路后，若未来单独阅读该文件的用户找不到链路入门说明，通过引用追溯到 architecture_and_network.md；属于可接受成本。
  - examples.md 第 3 节从 23 行减为 3 行，审查场景细节全部外链到 review_checklists.md；若后续想在 examples.md 补具体 findings 示例，单独提案处理。

## 状态
- promoted
