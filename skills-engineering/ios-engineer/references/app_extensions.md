<!-- last-verified: 2026-11 -->
# App Extensions 工程规范

## 使用规则
- 涉及 Widget（WidgetKit）、Share Extension、Watch App、Siri Intent、Notification Content Extension、Action Extension 时必须使用本文件。
- Extension 与包含它的 App 不共享进程内状态；共享文件或偏好使用 App Group，共享凭证使用 Keychain Access Group，具体能力由 extension point 与 entitlement 决定。
- 默认输出"类型选型 → 数据共享 → 生命周期 → 构建配置 → 验证"五段。

## Widget（WidgetKit / iOS 14+）
- `TimelineProvider` 分别提供 `placeholder(in:)`、`getSnapshot(in:completion:)` 和 `getTimeline(in:completion:)`；它们对应占位、临时快照和时间线请求，不构成固定调用顺序。
- `TimelineEntry.date` 表示该条目开始展示的时间；后续刷新由时间线条目、`TimelineReloadPolicy` 和 WidgetKit 的系统预算共同决定，App 不能保证精确刷新时刻。
- `WidgetFamily` 决定展示尺寸和内容区域；只声明实际支持的 family，并让视图按 `widgetFamily` 自适应。无需为未声明支持的 family 提供实现。
- `getTimeline` 可以进行受控异步取数，但必须快速完成、限制解码和图片内存峰值并提供缓存/占位降级；扩展预算由系统动态管理，不写死固定内存上限，也不连续重试。
- 与主 App 通信：通过 `UserDefaults(suiteName:)`（App Group）共享轻量数据；大数据或结构化数据建议通过共享 container 的文件 URL。
- 点击 Widget 打开主 App：`widgetURL(_:)` 或 `Link(destination:)` 设置 deep link；`systemSmall` 仅支持单个 `widgetURL`，多目标需用 `systemMedium` 或 `systemLarge`。

## Share Extension
- 接收 `NSExtensionItem` 数组；附件类型为 `NSItemProvider`，支持文本、URL、图片、视频等。
- 必须通过 App Group 共享 UserDefaults / 文件 URL 与主 App 传递数据；不可直接访问主 App 的沙盒目录。
- 生命周期由宿主和系统管理；用户完成或取消后调用 extension context 的完成/取消 API。扩展可能被系统终止，不能依赖进程持续存活。
- UI 和数据处理保持轻量，控制图片/视频解码峰值并及时释放资源；保存中的关键状态需要可恢复，不能依赖固定内存数值。

## Watch App
- watchOS App 运行在独立进程；与 iPhone 通信通过 `WCSession`（WatchConnectivity）。
- `WCSession.sendMessage(_:replyHandler:errorHandler:)` 适合对端可达时的即时消息，不以双方都在前台作为唯一条件；`transferUserInfo(_:)` / `updateApplicationContext(_:)` 用于系统调度的后台传输与最新状态同步。
- Watch 上的持久化独立于 iPhone；需同步的数据通过 WCSession + 共享 container 协调。
- Watch App 需要控制启动、交互延迟、内存和能耗；阈值按目标设备矩阵与实测基线设定，不使用跨型号固定内存上限。

## 跨 Target 数据共享
| 共享方式 | 适用场景 | 限制 |
|---------|---------|------|
| App Group UserDefaults | 非敏感简单键值（配置开关、轻量状态） | 不保证实时同步；不存 token、密码等凭证 |
| App Group Container URL | 大文件、数据库文件 | 需手动管理并发访问 |
| Keychain Group | 敏感凭证（token、密码） | 需在 entitlements 中配置 |
| Darwin Notification | 跨进程轻量信号 | 不携带 payload；不可靠（best-effort） |

## 构建配置
- 每个 Extension Target 必须单独配置 Provisioning Profile 和 Bundle ID（通常为 `com.example.app.widget`）。
- Debug 构建时选择对应 Extension Scheme，并配置合适宿主来启动调试；扩展不能脱离宿主场景独立提供完整运行体验。
- App Group capability 必须在主 App 和 Extension 的 entitlements 中同时开启且 group identifier 一致。

## 常见反模式
- 在主 App 的 `viewDidLoad` 中假定 App Group UserDefaults 已被 Extension 写入——Extension 可能尚未运行。
- Widget `getTimeline` 中进行重请求和复杂 image processing——应在主 App 中预处理并通过 App Group 共享。
- Share Extension 中通过 Keychain 直接读主 App 的 token（未配置 Keychain Group）——Extension 不可访问主 App 的 Keychain。
- Widget 刷新间隔设太短（< 5 分钟）——系统会节流刷新频率。
