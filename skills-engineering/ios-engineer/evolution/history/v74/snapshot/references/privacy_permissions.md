<!-- last-verified: 2026-07 -->
# 隐私权限工程规范

## 使用规则
- 涉及定位、相机、相册、麦克风、通讯录、HealthKit、ATT 追踪、本地网络等受保护权限时必须使用本文件。
- 每个权限必须补充对应的 `Info.plist` 描述文案（`*UsageDescription` key），缺漏将导致审核拒绝或运行时 crash。
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

## ATT 追踪（AppTrackingTransparency）
- iOS 14.5+ 必须通过 `ATTrackingManager.requestTrackingAuthorization` 获取用户授权后才能获取 IDFA。
- ATT 弹窗只允许出现一次系统弹窗（苹果限制）；如果 dismissed 后想再弹，必须从系统设置的对应 app 页面手动操作。
- ATT 状态为 `notDetermined` 时调用 `requestTrackingAuthorization` 会触发系统弹窗；`denied` 状态下再次调用不会触发弹窗（直接返回 denied），不应依赖弹窗覆盖来重新申请。
- 建议：在 ATT 弹窗前先弹一个 pre-permission 说明弹窗，告知用户为什么需要追踪，提升授权率。

## 审核拒审风险
- 缺少对应的 `*UsageDescription` key 会导致访问隐私 API 时运行时崩溃。
- 文案与实际用途不符（如声称"用于导航"但实际用于广告）会被审核拒绝或下架。
- 请求权限但不在应用中实际使用（被静态分析检测到调用无后续使用）会触发审核。
- 权限处于 `restricted` / MDM / 家长控制等用户不可自行修改状态时，仍反复引导去设置可能导致审核 flag。

## 常见反模式
- 在 `viewDidLoad` 或 `init` 中同步请求权限——必须响应用户行为。
- 使用被拒绝权限的功能时直接 assert / fatalError——必须给出降级路径。
- ATT 弹窗在启动时直接弹出而无 pre-permission 说明——审核可拒。
- 缺少 `NSLocationWhenInUseUsageDescription` 而只配置了 `Always`——定位功能直接不可用。
