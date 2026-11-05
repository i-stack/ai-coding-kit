<!-- last-verified: 2026-11 -->
# Push Notifications 工程规范

## 使用规则
- 涉及远程推送（APNs）、本地通知（UNUserNotificationCenter）、通知扩展时必须使用本文件。
- 推送设计应区分通知到达、用户点击、前台展示三条链路，不可混为一谈。
- 默认输出"注册链 → payload 结构 → 路由跳转 → 扩展处理"四段。

## 通知注册链
- `UNUserNotificationCenter.requestAuthorization(options:)` 必须提供 `.alert` / `.badge` / `.sound` 的最小组合；provisional 授权用于软开通，不可替代正式授权。
- 注册失败不得静默：记录错误码并给出用户可见的降级路径（如设置页引导）。
- 主 Target 注册 token 通过 `application(_:didRegisterForRemoteNotificationsWithDeviceToken:)` 获取；token 变更时必须重新上报服务端。
- App 每次启动都应根据产品授权策略调用 `registerForRemoteNotifications()`，让系统在需要时提供或更新 device token；不得假设 token 永久不变，也不依赖固定刷新时刻。

## Payload 结构
- APNs payload 顶层 `aps` 字典只放 Apple 定义的通知字段；业务自定义 key 应作为 `aps` 的同级字段，并使用稳定命名空间避免与系统字段混淆。payload 不携带未加密的敏感数据。
- `mutable-content: 1` + Notification Service Extension 允许富媒体附件处理（图片 / 视频 / 音频），但处理超时约 30 秒，必须在 `didReceive(_:withContentHandler:)` 内及时调用 `contentHandler`。
- 静默推送（`content-available: 1`）不保证送达时序，不可依赖其顺序编排业务逻辑。

## 路由跳转
- 通知点击跳转不应在 `AppDelegate` / `SceneDelegate` 内硬编码路由映射；建议通过通知 payload 中的 `route` / `deepLink` 字段驱动导航。
- 用户点击历史通知时可能指向已卸载的内容，路由处理须防御无效 deep link。
- 通知送达时若 App 在前台，默认不展示横幅；需要在 `userNotificationCenter(_:willPresent:withCompletionHandler:)`（或对应 async delegate 方法）返回 `.banner` / `.list` / `.sound` / `.badge` 等展示选项。

## 通知扩展
- Notification Service Extension 运行在独立进程；共享文件或 `UserDefaults(suiteName:)` 需要 App Group，访问共享 Keychain item 需要主 App 与 Extension 配置相同 Keychain Access Group，不可把 App Group 当成 Keychain 共享前提。
- Extension 的内存与执行时间预算由系统动态管理，不依赖固定 MB 数值做设计；处理大图或视频时应控制解码峰值、尽早调用 content handler，并优先下载到临时文件 URL 后创建附件，避免长期持有 raw data。
- Notification Content Extension 用于自定义通知详情展开后的 UI；其生命周期由系统管理，不可在其中发起长时网络请求。

## 常见反模式
- 在 `didFinishLaunching` 中仅因 `launchOptions[.remoteNotification] != nil` 就判定用户来自通知点击——`launchOptions` 存在不代表用户看到了通知内容，应同时检查对应 key 的 payload 是否完整。
- 将 token 上报与推送策略耦合——token 只是地址，推送策略（时间 / 频控 / 分段）应由服务端独立管理。
- 在 Extension 内使用 `shared` URLSession 进行大文件下载——Extension 随时可能被系统终止，下载应在 Extension 内最小化，大文件应由主 App 后台下载。

## 验证清单
- [ ] 通知注册成功/失败均有日志与降级路径。
- [ ] token 变更后服务端在产品定义的 SLO 内完成幂等更新；SLO 数值来自服务端能力和业务要求，不作为 APNs 平台固定值。
- [ ] 富媒体推送（mutable-content）在 Extension 内 30 秒内完成处理。
- [ ] 通知点击路由可处理无效/过期的 deep link。
- [ ] 前台通知展示行为符合预期（横幅/不横幅）。
- [ ] Extension 崩溃率、超时率和附件处理成功率有项目基线与发布门禁；阈值由产品 SLO 和线上数据确定。
