<!-- last-verified: 2026-11 -->
# 持久化工程规范（SwiftData / Core Data）

## 使用规则
- 涉及 SwiftData、Core Data、数据持久化、Model Schema、迁移策略时必须使用本文件。
- iOS 17+ 新模块可优先评估 SwiftData；既有 Core Data 项目、需要更成熟迁移/批处理能力或兼容 iOS 16 及以下时优先延续 Core Data。最终选择基于数据规模、迁移复杂度、CloudKit、调试与兼容要求。
- 默认输出"技术选型 → Schema 设计 → 并发模型 → 迁移策略 → 验证"五段。

## SwiftData（iOS 17+）
- 使用 `@Model` 宏标注持久化模型；自动生成 `PersistentModel` 符合。
- `ModelContainer` 未指定 URL 时使用当前 App 容器内的默认持久化位置；只有显式配置共享 container URL 和相应 entitlement 时才写入 App Group。
- CloudKit 集成需要配置 `ModelConfiguration`、CloudKit container 与 entitlement，并验证模型兼容性、账户状态和同步错误；不能把初始化成功等同于云同步已可靠工作。
- `@Query` / `@Transient` / `@Attribute(.unique)` / `@Relationship` 等宏提供声明式约束。
- 局限性：不支持 `NSFetchedResultsController` 层级缓存；大结果集分页需配合 `FetchDescriptor.fetchLimit` + `fetchOffset`；批量操作（`NSBatchDeleteRequest` / `NSBatchUpdateRequest`）需回退到 Core Data API。

## Core Data（通用）
- 常规项目优先使用 `NSPersistentContainer`（iOS 10+）管理 Core Data stack；只有确有多 store、自定义协调或遗留兼容需求时才手动构造 stack，并补充启动、迁移和并发测试。
- `viewContext` 绑定主队列；写操作使用 `performBackgroundTask` 或 `newBackgroundContext()`。
- `NSManagedObject` 不跨 context 传递：在 context A 中获取的对象不能直接在 context B 中使用；必须通过 `objectID` 在目标 context 中重新 fetch。
- `NSFetchedResultsController` 用于列表场景的增量刷新；delegate 回调在主线程，内部不应做重计算。

## Schema 迁移
- 轻量级迁移（Lightweight Migration）：仅修改属性名、类型（兼容转换）、增加/删除可选属性时可自动处理；在 `NSPersistentStoreDescription` 中设置 `shouldMigrateStoreAutomatically = true` + `shouldInferMappingModelAutomatically = true`。
- 重量级迁移（Heavyweight Migration）：涉及实体拆分/合并、关系重构、属性类型不兼容变更时，必须提供 `NSMappingModel` 或使用渐进式迁移（多版本链）。
- SwiftData 迁移通过 `VersionedSchema` 与 `SchemaMigrationPlan` 声明版本链；轻量变化可使用 lightweight stage，复杂变化需要 custom stage，并用真实旧库副本验证逐版本升级。
- 迁移前必须备份数据库文件；迁移失败时不得清空数据，应提示用户并保留原文件。

## 并发模型
- Core Data：`viewContext`（主队列并发类型）用于 UI 读取；`performBackgroundTask` 创建的私有 context 用于写操作；context 间通过 `objectID` 传递对象引用。
- SwiftData：UI 绑定的 `ModelContext` 留在主 actor；后台持久化使用拥有独立 context 的 `@ModelActor` 或明确隔离的执行单元。跨隔离域传递 `PersistentIdentifier` 或值类型快照，不传递绑定到其他 context 的模型实例。
- 批量操作（`NSBatchDeleteRequest` / `NSBatchUpdateRequest`）绕过 context 和内存中的对象，执行后必须刷新相关 context（`mergeChanges` 或重建）。
- 不得在 `viewContext` 的 `perform` 闭包内执行同步网络请求——会阻塞主队列。

## 常见反模式
- 将 `NSManagedObject` 跨线程传递或存储为属性——使用 `objectID`。
- 迁移时不清空 persistent store 直接重建——迁移失败时数据不可逆。
- 在 `viewContext` 中执行长时间写操作——写操作始终在后台 context。
- SwiftData 中混用 `NSFetchedResultsController`——SwiftData 使用 `@Query` 的 Observation 机制，不兼容 FRC。
