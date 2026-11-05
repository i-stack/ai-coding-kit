<!-- last-verified: 2026-11 -->
# StoreKit / 内购工程规范

## 使用规则
- 涉及 StoreKit 2（iOS 15+）、StoreKit 1（legacy）、内购商品、订阅、收据验证、促销优惠时必须使用本文件。
- iOS 15+ 优先使用 StoreKit 2 的 `Product` / `Transaction` / `Transaction.updates` API；需支持 iOS 14 时回退 StoreKit 1（`SKPaymentQueue` 体系）。
- 默认输出"商品获取 → 购买流程 → 收据验证 → 恢复与同步 → 订阅管理"五段。

## StoreKit 2（iOS 15+ 推荐）
- 商品加载：`Product.products(for:)` 异步返回 `[Product]`；需处理网络失败与空结果。空结果只说明当前请求没有返回可售商品，可能涉及产品标识、App Store Connect 配置、协议/税务状态、商店地区、传播延迟或测试环境，不能直接归因于用户权限。
- 购买：通过 `product.purchase()` 返回 `Product.PurchaseResult`；`.success(.verified(transaction))` 表示购买成功且通过验证；`.success(.unverified(_,_))` 表示购买存在但签名验证失败（需手动处理）。
- 交易监听：`Transaction.updates` 是一个 `AsyncSequence`，在 App 生命周期内监听新交易（包括跨设备同步和订阅续期）；必须在 App 启动时开始监听并持续运行。
- 权益恢复：遍历 `Transaction.currentEntitlements` 并只接受 `.verified` 结果；消耗型补单还要检查 `Transaction.unfinished`。服务端可验证 `Transaction` / `AppTransaction` 的 JWS，并结合 App Store Server API 与 Server Notifications V2 同步状态。
- `AppStore.sync()` 强制刷新交易与订阅状态，返回 `Void`，且可能触发 App Store 账户认证；只在用户明确点击“恢复购买”等操作时调用。日常启动直接读取 `currentEntitlements` / `all` / `unfinished`。
- 成功交付权益后调用 `transaction.finish()`；未完成交易必须保持幂等处理，避免重复发放或永久挂起。

## StoreKit 1（iOS 14 及以下兼容）
- 使用 `SKProductsRequest` 获取商品信息（delegate 模式）。
- 使用 `SKPaymentQueue.default().add(payment)` 发起购买；通过 `SKPaymentTransactionObserver` 监听交易状态变化。
- 收据验证：通过 `Bundle.main.appStoreReceiptURL` 获取收据文件，base64 编码后发送服务端验证。
- 重要：`application(_:didFinishLaunchingWithOptions:)` 中尽早监听 `SKPaymentQueue`，保证及时处理交易。未完成交易会留在队列并在后续启动或恢复时再次交付，但延迟注册会推迟交付并影响用户体验。

## 收据验证双路径
| 路径 | 适用场景 | 优点 | 风险 |
|------|---------|------|------|
| 设备端 StoreKit 验证 | 低风险或可离线恢复的非消耗型权益 | StoreKit 2 自动验证签名，延迟低 | 服务端无法仅凭客户端状态完成跨设备风控与审计 |
| 服务端 JWS / App Store Server API | 消耗型商品、订阅、敏感权益、跨平台账户 | 可集中做幂等、撤销、退款和订阅状态同步 | 增加网络与服务运维成本，需处理超时和通知重放 |

服务端验证优先级：legacy receipt 校验只有在 production 端点明确返回 sandbox receipt 指示时才 fallback 到 sandbox；其他 production 验证失败必须按网络错误、签名错误、状态码错误或服务端异常分别处理，不可一概吞掉后重试 sandbox；不可在代码中硬编码验证 URL。

## 订阅管理
- 订阅状态通过 `Transaction.currentEntitlements`（StoreKit 2）或收据解析（StoreKit 1）判定；不可仅依赖 `UserDefaults` 中缓存的过期时间。
- Promoted In-App Purchase：StoreKit 2 下用 `PurchaseIntent.intents`（iOS 16.4+）异步序列接收促销购买意图；仍需兼容 StoreKit 1 的项目回退 `paymentQueue(_:shouldAddStorePayment:for:)`。两者均不与订阅 Promotional Offer 混用。
- Promotional Offer 需要服务端使用订阅密钥生成签名，并通过 StoreKit 2 的 `Product.PurchaseOption.promotionalOffer` 参与购买；Offer Code 使用系统兑换入口或相应 StoreKit API。
- 必须提供管理订阅的入口（如 `AppStore.showManageSubscriptions(in:)`，按部署版本选择可用 API）。
- 订阅权益同时处理正常订阅、grace period、billing retry、过期、退款与撤销；服务端通知按 notification UUID 和 transaction ID 幂等消费。

## 常见反模式
- 用 `UserDefaults` 存储购买状态而不验证收据——极易被破解。
- 每次启动都调用 `AppStore.sync()` / `restoreCompletedTransactions()`——浪费 Apple 服务器资源且有 rate limiting。
- 仅在 App 前台监听 `Transaction.updates`——App 从后台回到前台时需要检查漏掉的交易。
- 购买流程中不用 loading 状态阻塞用户——用户可能多次点击导致重复购买（多次扣款）。
