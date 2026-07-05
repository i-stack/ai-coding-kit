<!-- last-verified: 2026-07 -->
# StoreKit / 内购工程规范

## 使用规则
- 涉及 StoreKit 2（iOS 15+）、StoreKit 1（legacy）、内购商品、订阅、收据验证、促销优惠时必须使用本文件。
- iOS 15+ 优先使用 StoreKit 2 的 `Product` / `Transaction` / `Transaction.updates` API；需支持 iOS 14 时回退 StoreKit 1（`SKPaymentQueue` 体系）。
- 默认输出"商品获取 → 购买流程 → 收据验证 → 恢复与同步 → 订阅管理"五段。

## StoreKit 2（iOS 15+ 推荐）
- 商品加载：`Product.products(for:)` 异步返回 `[Product]`；需处理网络失败与空结果（用户无购买权限或地区不可用）。
- 购买：通过 `product.purchase()` 返回 `Product.PurchaseResult`；`.success(.verified(transaction))` 表示购买成功且通过验证；`.success(.unverified(_,_))` 表示购买存在但签名验证失败（需手动处理）。
- 交易监听：`Transaction.updates` 是一个 `AsyncSequence`，在 App 生命周期内监听新交易（包括跨设备同步和订阅续期）；必须在 App 启动时开始监听并持续运行。
- 收据验证：StoreKit 2 通过 `Transaction.currentEntitlements` 获取已验证的交易；服务端验证可选 `AppTransaction` / `Transaction` 的 JWS 签名（通过 Apple 验证端点在线验证）。
- 恢复购买：`AppStore.sync()` 同步跨设备交易，返回之前未在该设备上完成的交易；不应在每次启动时调用——按需触发。

## StoreKit 1（iOS 14 及以下兼容）
- 使用 `SKProductsRequest` 获取商品信息（delegate 模式）。
- 使用 `SKPaymentQueue.default().add(payment)` 发起购买；通过 `SKPaymentTransactionObserver` 监听交易状态变化。
- 收据验证：通过 `Bundle.main.appStoreReceiptURL` 获取收据文件，base64 编码后发送服务端验证。
- 重要：`application(_:didFinishLaunchingWithOptions:)` 中开始监听 `SKPaymentQueue`；忘记添加 observer 会导致购买回调丢失。

## 收据验证双路径
| 路径 | 适用场景 | 优点 | 风险 |
|------|---------|------|------|
| 设备端验证 | 非消耗型 / 自动续期订阅的简单判断 | 离线可用，延迟低 | 容易被越狱绕过 |
| 服务端验证 | 消耗型商品 / 订阅 / 敏感权益 | 安全，Apple 权威 | 增加网络延迟，需处理验证明文超时 |

服务端验证优先级：legacy receipt 校验只有在 production 端点明确返回 sandbox receipt 指示时才 fallback 到 sandbox；其他 production 验证失败必须按网络错误、签名错误、状态码错误或服务端异常分别处理，不可一概吞掉后重试 sandbox；不可在代码中硬编码验证 URL。

## 订阅管理
- 订阅状态通过 `Transaction.currentEntitlements`（StoreKit 2）或收据解析（StoreKit 1）判定；不可仅依赖 `UserDefaults` 中缓存的过期时间。
- 促销优惠（Promotional Offers）：在 App Store Connect 配置后，通过 `paymentQueue(_:shouldAddStorePayment:for:)` 处理。
- 订阅优惠码 / 推介促销：StoreKit 2 通过 `Product.SubscriptionInfo.PromotionalOffer` 处理。
- 必须显示管理订阅的人口（`AppStore.showManageSubscriptions(in:)` iOS 15+ 或打开 `itms-apps://` 链接）。

## 常见反模式
- 用 `UserDefaults` 存储购买状态而不验证收据——极易被破解。
- 每次启动都调用 `AppStore.sync()` / `restoreCompletedTransactions()`——浪费 Apple 服务器资源且有 rate limiting。
- 仅在 App 前台监听 `Transaction.updates`——App 从后台回到前台时需要检查漏掉的交易。
- 购买流程中不用 loading 状态阻塞用户——用户可能多次点击导致重复购买（多次扣款）。
