# 测试执行与失败修复

当用户要求构建 iOS 测试体系、补全核心业务测试、执行测试并修复失败时，按本流程执行。

目标不是“补几个测试”，而是构建可靠的测试体系，并在测试暴露缺陷后进行最小可验证修复，直到核心业务逻辑具备可上线信心。

## 项目背景
- 这是 iOS 工程，不要使用 macOS 目标进行编译或测试。
- 如果出现 “building for macOS” 或 macOS 相关编译失败，优先检查 scheme / destination / platform 设置。
- 编译与测试必须使用 iPhone 模拟器或真机目标。
- 优先使用 XCTest / XCUITest / 项目现有测试框架，不引入不必要的新依赖。

## 验证命令
- 对包含 `UIKit` / iOS-only API / 仅面向 iOS 的 framework 的 SPM 包，不要用裸 `swift test` 做最终验证；它默认按当前主机平台构建，常见失败是 `no such module 'UIKit'`。这种失败通常表示验证命令目标平台错了，不等价于源码在 iOS 下不可编译。
- 先查 workspace / project 的 scheme 与可用模拟器：

  ```sh
  xcodebuild -list -workspace <App.xcworkspace>
  xcodebuild -showdestinations -workspace <App.xcworkspace> -scheme <Scheme>
  ```

  只有 `.xcodeproj` 时，把 `-workspace <App.xcworkspace>` 替换为 `-project <App.xcodeproj>`。

- 用 iOS Simulator SDK 构建包或 app scheme：

  ```sh
  xcodebuild build \
    -workspace <App.xcworkspace> \
    -scheme <PackageOrAppScheme> \
    -destination 'platform=iOS Simulator,name=<SimulatorName>,OS=<OSVersion>'
  ```

- 用同一个模拟器执行测试：

  ```sh
  xcodebuild test \
    -workspace <App.xcworkspace> \
    -scheme <AppScheme> \
    -destination 'platform=iOS Simulator,name=<SimulatorName>,OS=<OSVersion>'
  ```

- 若存在多个同名 destination，优先使用 `-showdestinations` 输出中的 `id` 精确指定：

  ```sh
  xcodebuild test \
    -workspace <App.xcworkspace> \
    -scheme <AppScheme> \
    -destination 'platform=iOS Simulator,id=<SimulatorUDID>'
  ```

## 核心要求
1. 测试范围
- 覆盖所有核心业务逻辑。
- 优先覆盖边界条件、异常路径、空数据、网络失败、解析失败、超时、取消、状态切换、并发回调、过期结果、重复请求、缓存命中/失效、用户输入校验。
- 不要求为了覆盖率测试纯 UI 样式、简单 getter/setter、无业务分支的样板代码。

2. 测试质量
- 每个测试必须有明确断言。
- 禁止无效测试，例如只调用方法但没有断言、只验证“不崩溃”、断言实现细节而非业务结果、为提高覆盖率而测试无意义代码、依赖真实网络/真实时间/随机结果/外部不可控状态。
- 测试命名必须表达业务场景、输入条件和期望结果。
- 优先使用 mock / stub / fake / dependency injection 隔离外部依赖。

3. 代码设计
如果发现代码设计不利于测试，例如强耦合、直接依赖单例、直接访问真实网络/文件/时间/UserDefaults、异步生命周期不清晰、ViewModel 与 View/网络/存储混杂、状态由多个 Bool 拼接导致不可验证，允许进行最小重构，但必须说明：
- 为什么当前设计难以测试。
- 重构边界是什么。
- 是否改变线上行为。
- 如何保证兼容。
- 重构后如何提升可测试性。

禁止为了测试大规模重写模块。

4. 执行流程
必须按以下流程循环，最多 3 轮：
- 分析：识别核心业务逻辑入口，梳理依赖关系、状态流、错误路径、异步边界，明确单测/集成测试/UI 测试边界，并给出测试计划。
- 生成测试：新增或补全测试文件，每个测试具备 Arrange / Act / Assert 结构；异步测试设置明确 expectation / timeout；并发或取消逻辑验证过期结果不会污染当前状态。
- 执行测试：使用 iPhone 模拟器或真机执行 build / test；不要使用 macOS destination；如果 destination 不存在，先列出可用模拟器或改用当前可用 iPhone 模拟器；记录执行命令和关键失败信息。
- 失败分析：不要盲改，先判断失败类型是测试写错、产品代码缺陷、环境/scheme/destination 问题、异步时序问题还是依赖未隔离，并输出根因、为什么、修法、验证方式。
- 修复：优先最小修复；不允许绕过测试、删除断言、放宽断言来让测试通过；不允许用 force unwrap / force cast / fatalError 掩盖问题；UI 或状态更新必须保证在主线程；异步任务必须明确创建者、持有者、取消时机和释放时机。
- 回归测试：重新执行相关测试；必要时执行更大范围测试；最多循环 3 次；如果 3 次后仍失败，停止继续扩大修改，输出阻塞原因和建议。

5. 最终输出
必须输出：
- 测试体系总结：新增/修改了哪些测试，覆盖了哪些核心业务逻辑、边界条件和异常路径。
- 执行结果：build 是否通过，test 是否通过，使用的 destination、关键命令、失败测试列表。
- 覆盖率：如果能获取覆盖率，输出整体覆盖率和关键模块覆盖率；如果无法获取覆盖率，说明原因，并给出替代判断依据。
- 缺陷与修复：发现了哪些真实缺陷，修复了哪些问题，是否有为了可测试性进行重构，重构是否改变线上行为。
- 风险点：未覆盖路径、仍可能存在的边界风险、环境或 CI 风险、异步/并发/状态残留风险。
- 上线判断：是否可以上线 Yes / No，理由必须具体；如果是 No，说明上线前必须完成哪些事项。

## 工作原则
- 以可靠性为目标，不以测试数量为目标。
- 以真实业务断言为准，不制造虚假覆盖率。
- 优先证明核心路径正确，再补边界与异常路径。
- 最小改动，避免无关重构。
- 所有结论必须来自代码分析、测试结果或明确证据。
