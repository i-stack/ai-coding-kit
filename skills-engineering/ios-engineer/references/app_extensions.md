<!-- last-verified: 2026-07 -->
# App Extensions 工程规范

## 使用规则
- 涉及 Widget（WidgetKit）、Share Extension、Watch App、Siri Intent、Notification Content Extension、Action Extension 时必须使用本文件。
- Extension 是独立进程，不与主 App 共享内存空间；数据共享必须通过 App Group 或 Keychain Group。
- 默认输出"类型选型 → 数据共享 → 生命周期 → 构建配置 → 验证"五段。

## Widget（WidgetKit / iOS 14+）
- 使用 `TimelineProvider` 驱动刷新：`snapshot`（预览）→ `timeline`（真实数据）→ `placeholder`（占位）。
- 时间线条目 `TimelineEntry` 的 `date` 字段决定何时显示、何时刷新；超过 `Timeline` 的 `policy` 过期时间后系统会请求新数据。
- `WidgetFamily`（systemSmall / systemMedium / systemLarge / accessory*）决定展示尺寸和内容区域；每个 family 都必须有对应视图。
- 网络请求在 `getTimeline` 内发起，必须在 Extension 的内存 budget 内完成（约 30MB iOS 17+）；不得发起连续重试。
- 与主 App 通信：通过 `UserDefaults(suiteName:)`（App Group）共享轻量数据；大数据或结构化数据建议通过共享 container 的文件 URL。
- 点击 Widget 打开主 App：`widgetURL(_:)` 或 `Link(destination:)` 设置 deep link；`systemSmall` 仅支持单个 `widgetURL`，多目标需用 `systemMedium` 或 `systemLarge`。

## Share Extension
- 接收 `NSExtensionItem` 数组；附件类型为 `NSItemProvider`，支持文本、URL、图片、视频等。
- 必须通过 App Group 共享 UserDefaults / 文件 URL 与主 App 传递数据；不可直接访问主 App 的沙盒目录。
- 生命周期：用户点击"分享"后打开 Extension 视图 → 用户完成操作（post / save）后 Extension 关闭；期间不被 Suspended。
- UI 不可过重——Extension 内存限制严格（~120MB），且用户在完成操作前不可退出。

## Watch App
- watchOS App 运行在独立进程；与 iPhone 通信通过 `WCSession`（WatchConnectivity）。
- `WCSession.sendMessage(_:replyHandler:errorHandler:)` 是实时通信方式（仅当 watch 和 iPhone 都在前台）；`transferUserInfo(_:)` / `updateApplicationContext(_:)` 用于后台同步。
- Watch 上的持久化独立于 iPhone；需同步的数据通过 WCSession + 共享 container 协调。
- Watch App 的性能指标严苛：前端交互延迟 < 200ms，内存上限极小（根据型号 ~60-120MB）。

## 跨 Target 数据共享
| 共享方式 | 适用场景 | 限制 |
|---------|---------|------|
| App Group UserDefaults | 简单键值对（token、配置开关） | 不保证实时同步；大小有限 |
| App Group Container URL | 大文件、数据库文件 | 需手动管理并发访问 |
| Keychain Group | 敏感凭证（token、密码） | 需在 entitlements 中配置 |
| Darwin Notification | 跨进程轻量信号 | 不携带 payload；不可靠（best-effort） |

## 构建配置
- 每个 Extension Target 必须单独配置 Provisioning Profile 和 Bundle ID（通常为 `com.example.app.widget`）。
- Debug 构建时需选择正确的 Scheme（主 App vs Extension）；Extension 不可独立运行。
- App Group capability 必须在主 App 和 Extension 的 entitlements 中同时开启且 group identifier 一致。

## 常见反模式
- 在主 App 的 `viewDidLoad` 中假定 App Group UserDefaults 已被 Extension 写入——Extension 可能尚未运行。
- Widget `getTimeline` 中进行重请求和复杂 image processing——应在主 App 中预处理并通过 App Group 共享。
- Share Extension 中通过 Keychain 直接读主 App 的 token（未配置 Keychain Group）——Extension 不可访问主 App 的 Keychain。
- Widget 刷新间隔设太短（< 5 分钟）——系统会节流刷新频率。
