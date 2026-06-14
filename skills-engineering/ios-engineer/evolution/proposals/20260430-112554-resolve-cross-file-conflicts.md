# Skill Evolution Proposal

## Metadata
- Proposal ID: 20260430-112554-resolve-cross-file-conflicts
- Created At: 2026-04-30 11:25:54 +0800
- Active Version At Creation: v15

## 问题信号
- **错误分层双重定义**：
  - `domain_modeling.md` "ErrorModel 建模规则" 分 5 层：网络错误、解码错误、鉴权错误、业务错误、展示错误。
  - `networking_patterns.md` "错误分层" 分 6 层：传输错误、状态码错误、解码错误、鉴权错误、业务错误、展示错误。
  - 两份文件层数不一致（5 vs 6），且 "网络错误" vs "传输错误 + 状态码错误" 的拆分粒度不同；措辞、命名都不完全一致。
  - AI 看到两份不一致定义无法确定该用哪套，或者会混用。
- **状态分层维度未说明**：
  - `ui_state_patterns.md` 分 "领域状态 / 页面状态 / 组件状态"（运行时语义分层）
  - `domain_modeling.md` 分 "DTO / Entity / ViewState / ErrorModel"（结构/类型分层）
  - 两份都用"状态/建模分层"描述，但一个说运行时语义、一个说数据类型结构，维度不同没有说明，读者容易混淆。

## 变更类型
- 合并重复：错误分层统一到 `domain_modeling.md`，`networking_patterns.md` 改为引用。
- 修正表达：`ui_state_patterns.md` 加脚注说明与 `domain_modeling.md` 的分层维度不同。

## 变更内容
- 修改文件：`references/domain_modeling.md`
  - 升级 "ErrorModel 建模规则" 为错误分层的完整单一来源：
    - 将 `networking_patterns.md` 的 6 层（传输 / 状态码 / 解码 / 鉴权 / 业务 / 展示）整合进来，统一为 6 层（传输错误 → 状态码错误 → 解码错误 → 鉴权错误 → 业务错误 → 展示错误）。
    - 保留现有"必须可映射为标题、文案、操作动作"、"必须说明可恢复性和用户动作"。
    - 新增"每层错误归属"说明：
      - 传输错误（网络不通、超时）→ APIClient 层捕获，转为 ErrorModel.network
      - 状态码错误（4xx / 5xx）→ APIClient 层根据 code 映射
      - 解码错误 → Decoder 层抛出，不回退到展示层
      - 鉴权错误 → AuthInterceptor 统一处理
      - 业务错误 → Repository / UseCase 层识别
      - 展示错误 → ViewModel 映射为用户可见文案和动作
- 修改文件：`references/networking_patterns.md`
  - 退役 "错误分层" 小节（L104-116）的完整定义。
  - 替换为引用：
    ```
    ## 错误分层
    错误分层、每层归属、面向 UI 的映射规则，完整定义见 [domain_modeling.md](domain_modeling.md#ErrorModel-建模规则)。
    
    网络层（APIClient）职责：捕获传输错误 / 状态码错误 / 解码错误，转为 ErrorModel 后向上抛出；不直接把 NSError 或 HTTP code 暴露给 Repository 以上层。
    ```
- 修改文件：`references/ui_state_patterns.md`
  - 在 "状态分层" 小节（L19-25）之后追加脚注：
    ```
    > 本文 "状态分层" 是**运行时语义**分层（领域 / 页面 / 组件），定义某个状态属于哪个语义层级；
    > `domain_modeling.md` "建模分层"（DTO / Entity / ViewState / ErrorModel）是**数据类型结构**分层，定义某个数据在代码层的类型归属。
    > 两者正交：同一个"正在加载"的语义状态，既属于页面状态层，又用 ViewState 类型表达。
    ```
- 替代或合并旧规则：
  - `networking_patterns.md` 的错误分层约束退役，由 `domain_modeling.md` 统一承担。新版本把 5/6 层差异固化为 6 层标准（传输 / 状态码 / 解码 / 鉴权 / 业务 / 展示），消除歧义。
  - `ui_state_patterns.md` 保留原有状态分层，只加说明不与 `domain_modeling.md` 冲突。

## 预期收益
- 错误分层有唯一来源：AI 读任一 ref 时，要么直接看到完整定义（domain_modeling.md），要么看到明确引用（networking_patterns.md → domain_modeling.md）。未来增加错误类型时只改一处。
- 错误分层的"每层归属"明确后，AI 可机械判断"某个错误应该在哪一层捕获 / 转换 / 展示"。
- 状态分层的维度说明避免 AI 在 "UI 状态" vs "数据类型" 之间混淆，输出架构分析时能明确指出两者的正交关系。
- 消除 2 处跨文件隐性冲突，References 一致性提升。

## 验证
- 结构校验：
  - `SKILL.md` frontmatter 合法，行数 ≤ 500（本提案不改 SKILL.md）。
  - `SKILL.md` 引用的所有 `references/*.md` 文件存在。
  - `root_cause_enforcement.md` / `examples.md` 分层守卫不受影响。
- 场景回放：
  - 场景 `parameter-pass-through`：用户输入"新增 currentModel 字段 A 类里拿不到"。期望 AI 命中参数透传规则；若涉及错误处理时，按 domain_modeling.md 的 6 层分层而不是 networking_patterns.md 的独立版本。
  - 隐式验证：用户问"这个 HTTP 404 错误应该在哪捕获"时，AI 能引用 domain_modeling.md 的"状态码错误 → APIClient 层" 归属规则。
- 残留风险：
  - ui_state_patterns.md 的脚注是说明性文本，AI 读到时需要能识别"维度不同"的含义；若脚注被忽略，仍可能混淆。
  - 错误分层从 5 层升级到 6 层后，引用了 5 层定义的历史代码或文档（例如 domain_modeling.md 自己的"适合的设计方式"段）需要一致化。

## 状态
- promoted
