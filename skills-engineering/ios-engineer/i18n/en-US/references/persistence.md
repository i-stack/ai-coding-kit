<!-- last-verified: 2026-07 -->
# Persistence Engineering Specification (SwiftData / Core Data)

> This is an English mirror of the authoritative Chinese `references/persistence.md`.
> In case of discrepancies, the Chinese source takes precedence.

## Usage Rules
- This file MUST be used when dealing with SwiftData, Core Data, data persistence, Model Schema, or migration strategies.
- New tech stack (iOS 17+): prefer SwiftData; legacy projects or iOS 16 and below compatibility: choose Core Data + NSPersistentContainer.
- Default output: "Tech Selection → Schema Design → Concurrency Model → Migration Strategy → Verification" five sections.

## SwiftData (iOS 17+)
- Use `@Model` macro to annotate persistence models; auto-generates `PersistentModel` conformance.
- Default storage location: when `ModelContainer` URL is not specified, stored under App Group / Application Support.
- CloudKit integration: `ModelConfiguration(cloudKitContainerIdentifier:)` automatically enables NSPersistentCloudKitContainer backend.
- Macros like `@Query` / `@Transient` / `@Attribute(.unique)` / `@Relationship` provide declarative constraints.
- Limitations: does not support `NSFetchedResultsController`-level caching; large result set pagination requires `FetchDescriptor.fetchLimit` + `fetchOffset`; batch operations (`NSBatchDeleteRequest` / `NSBatchUpdateRequest`) require falling back to Core Data APIs.

## Core Data (General)
- MUST use `NSPersistentContainer` (iOS 10+); do NOT manually construct `NSManagedObjectModel` / `NSPersistentStoreCoordinator` / `NSManagedObjectContext` three layers.
- `viewContext` is bound to the main queue; write operations use `performBackgroundTask` or `newBackgroundContext()`.
- `NSManagedObject` MUST NOT be passed across contexts: objects obtained in context A cannot be directly used in context B; MUST re-fetch via `objectID` in the target context.
- `NSFetchedResultsController` is for incremental list refresh; delegate callbacks are on the main thread; do NOT perform heavy computation inside.

## Schema Migration
- Lightweight Migration: only for renaming attributes, type changes (with compatible transforms), adding/removing optional attributes; set `shouldMigrateStoreAutomatically = true` + `shouldInferMappingModelAutomatically = true` in `NSPersistentStoreDescription`.
- Heavyweight Migration: for entity splitting/merging, relationship restructuring, incompatible attribute type changes; MUST provide `NSMappingModel` or use progressive migration (multi-version chain).
- SwiftData migration: define version chains via `Schema` and `VersionedSchema`; `ModelContainer` automatically migrates between versions, but complex migrations still require intervention.
- MUST backup database files before migration; on migration failure, do NOT clear data — prompt user and preserve original file.

## Concurrency Model
- Core Data: `viewContext` (main queue concurrency type) for UI reads; private context created by `performBackgroundTask` for write operations; pass object references between contexts via `objectID`.
- SwiftData: `@MainActor ModelContext` for UI; handle async persistence via `ModelActor` or explicit `Task { @MainActor in }`.
- Batch operations (`NSBatchDeleteRequest` / `NSBatchUpdateRequest`) bypass contexts and in-memory objects; after execution, MUST refresh related contexts (`mergeChanges` or recreate).
- Do NOT perform synchronous network requests inside `viewContext`'s `perform` closure — it will block the main queue.

## Common Anti-Patterns
- Passing `NSManagedObject` across threads or storing as properties — use `objectID`.
- Clearing persistent store directly during migration without backup — data is irreversibly lost on migration failure.
- Performing long write operations in `viewContext` — writes always go to background context.
- Mixing `NSFetchedResultsController` in SwiftData — SwiftData uses `@Query`'s Observation mechanism, incompatible with FRC.
