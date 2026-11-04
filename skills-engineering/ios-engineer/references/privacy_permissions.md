<!-- last-verified: 2026-11 -->
# 隐私权限工程规范

## 使用规则
- 涉及定位、相机、相册、麦克风、通讯录、HealthKit、ATT 追踪、本地网络等受保护权限时必须使用本文件。
- 访问受保护资源前必须确认该 API 所需的 entitlement、capability、Privacy Manifest 和 `Info.plist` purpose string；缺少必需 purpose string 的 API 访问可能触发运行时终止或审核问题。不是所有授权状态都对应 `*UsageDescription` key。
- 默认输出"权限类型 → 请求时机 → 拒绝降级 → plist 文案 → 审核风险"五段。

## 权限请求最佳实践
- 权限请求必须发生在用户明确行为上下文内（如点击"拍照"按钮时请求相机），禁止在 App 启动时批量弹权限。
- 权限被拒后的降级路径必须可见：禁用按钮、显示引导文案、提供跳转系统设置的入口。
- iOS 权限请求只有 `notDetermined` 状态会触发系统弹窗；`denied` / `restricted` 不应重复请求系统弹窗，必须走可见降级与设置页引导；相册 `limited` 需要单独提供受限访问下的功能路径。
- 定位权限分为 `When In Use` 和 `Always`：先申请 `When In Use`，通过后再申请 `Always`；直接申请 `Always` 极大概率被用户拒绝。

## 必备案底（Info.plist）
| 权限类型 | plist Key | 必填描述示例 |
|---------|-----------|------------|
| 定位 Always | `NSLocationAlwaysAndWhenInUseUsageDescription` | 用于持续记录您的行程轨迹 |
| 定位 WhenInUse | `NSLocationWhenInUseUsageDescription` | 用于在地图上显示您的当前位置 |
| 相机 | `NSCameraUsageDescription` | 用于拍照识别 / 扫码 |
| 相册读取 | `NSPhotoLibraryUsageDescription` | 用于选择照片上传 |
| 相册写入 | `NSPhotoLibraryAddUsageDescription` | 用于保存图片到相册 |
| 麦克风 | `NSMicrophoneUsageDescription` | 用于语音消息录制 |
| 通讯录 | `NSContactsUsageDescription` | 用于邀请好友 |
| ATT 追踪 | `NSUserTrackingUsageDescription` | 用于为您提供个性化广告 |
| 蓝牙 | `NSBluetoothAlwaysUsageDescription` | 用于连接智能设备 |
| 本地网络 | `NSLocalNetworkUsageDescription` | 用于发现并连接同一局域网内的设备 |
| Face ID | `NSFaceIDUsageDescription` | 用于验证身份并保护账户操作 |
| 语音识别 | `NSSpeechRecognitionUsageDescription` | 用于将语音内容转换为文字 |
| HealthKit 读取 | `NSHealthShareUsageDescription` | 用于读取用户明确选择的健康数据 |
| HealthKit 写入 | `NSHealthUpdateUsageDescription` | 用于保存用户确认的健康数据 |

具体 key 以目标 SDK 中对应 framework 文档为准；日历、提醒事项等 key 可能随 SDK 演进而细分，不能凭记忆复用旧 key。

## Privacy Manifest 与 Required Reason API
- App 与纳入发布包的第三方 SDK 都要检查 `PrivacyInfo.xcprivacy`；声明实际收集的数据、用途、tracking 与 required-reason API 使用原因。
- manifest 声明必须与代码、SDK 行为、App Store Connect 隐私问卷和服务端数据流一致；不能用宽泛声明替代实际盘点。
- Required Reason API 在 `NSPrivacyAccessedAPITypes` 中按类别声明。reason code 大小写敏感，必须与真实调用匹配。每个 code 的允许用途、是否得出设备、是否仅限第三方 SDK，以 Apple 文档 [Describing use of required reason API](https://developer.apple.com/documentation/bundleresources/describing-use-of-required-reason-api) 为准；本表只登记类别与 code，不替代官方条文。Xcode 或审核若报未知 code，以报错中的官方链接为准。

| 类别 | `NSPrivacyAccessedAPIType` | Reason code |
|------|----------------------------|-------------|
| 文件时间戳 | `NSPrivacyAccessedAPICategoryFileTimestamp` | `DDA9.1` `C617.1` `3B52.1` `0A2A.1` |
| 系统启动时间 | `NSPrivacyAccessedAPICategorySystemBootTime` | `35F9.1` `8FFB.1` `3D61.1` |
| 磁盘空间 | `NSPrivacyAccessedAPICategoryDiskSpace` | `85F4.1` `E174.1` `7D9E.1` `B728.1` |
| 活动键盘 | `NSPrivacyAccessedAPICategoryActiveKeyboards` | `3EC4.1` `54CD.1` |
| User Defaults | `NSPrivacyAccessedAPICategoryUserDefaults` | `CA92.1` `1C8F.1` `C56D.1` `AC6B.1` |

高频对照（仍须核对官方允许用途后再声明）：
- 只读写本 App 自己的 UserDefaults → `CA92.1`
- 同一 App Group 内共享 UserDefaults → `1C8F.1`
- 访问 App / App Group / CloudKit 容器内文件时间戳或大小 → `C617.1`
- 向用户展示磁盘空间 → `85F4.1`
- 写入前检查空间或空间不足时删除文件 → `E174.1`

仅第三方 SDK 对其包装函数声明、宿主 App 不得拿来替代自身用途：`0A2A.1`、`B728.1`、`C56D.1`。系统启动时间各类 code 的出设备限制不同，必须按官方条文逐条核对。
- 选错 code 可能通过上传校验，但仍违反使用规则，后续审核可能被拒。
- 依赖升级时重新检查签名、privacy manifest 和 required-reason API 变化，并在 Archive 产物上验证最终聚合结果。

## ATT 追踪（AppTrackingTransparency）
- iOS 14.5+ 必须通过 `ATTrackingManager.requestTrackingAuthorization` 获取用户授权后才能获取 IDFA。
- ATT 弹窗只允许出现一次系统弹窗（苹果限制）；如果 dismissed 后想再弹，必须从系统设置的对应 app 页面手动操作。
- ATT 状态为 `notDetermined` 时调用 `requestTrackingAuthorization` 会触发系统弹窗；`denied` 状态下再次调用不会触发弹窗（直接返回 denied），不应依赖弹窗覆盖来重新申请。
- 可在不误导、不施压且不模拟系统弹窗的前提下提供上下文说明；pre-permission 不是 ATT 的系统要求，也不能承诺一定提升授权率。

## 审核拒审风险
- 缺少对应的 `*UsageDescription` key 会导致访问隐私 API 时运行时崩溃。
- 文案与实际用途不符（如声称"用于导航"但实际用于广告）会被审核拒绝或下架。
- 请求权限但不在应用中实际使用（被静态分析检测到调用无后续使用）会触发审核。
- 权限处于 `restricted` / MDM / 家长控制等用户不可自行修改状态时，仍反复引导去设置可能导致审核 flag。

## 常见反模式
- 在 `viewDidLoad` 或 `init` 中同步请求权限——必须响应用户行为。
- 使用被拒绝权限的功能时直接 assert / fatalError——必须给出降级路径。
- 在缺少用户上下文时启动即请求 ATT，或用奖励、阻断功能、误导性文案诱导授权——体验差并可能触发审核问题。
- 缺少 `NSLocationWhenInUseUsageDescription` 而只配置了 `Always`——定位功能直接不可用。
