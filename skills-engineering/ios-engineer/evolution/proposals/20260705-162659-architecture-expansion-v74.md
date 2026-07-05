# Skill Evolution Proposal

## Metadata
- Proposal ID: 20260705-162659-architecture-expansion-v74
- Created At: 2026-07-05 16:26:59 +0800
- Active Version At Creation: v73

## 问题信号
- 技能树覆盖 5 个 iOS 工程常见领域盲区：Push Notifications（通知扩展/APNs）、隐私权限（定位/相机/ATT）、持久化（SwiftData/Core Data 迁移）、StoreKit 内购、App Extensions（Widget/Share Extension/Watch）。
- 验证场景仅 6 个（layout/concurrency/review/migration/mcp-control/parameter-pass-through），覆盖不足一半 ROUTE，自进化提案的验证质量依赖 LLM 自评偏差。
- IR-001"始终使用简体中文"在代码注释/API 名/编译错误/堆栈等场景与工程实际存在张力，缺少例外条款。
- ROUTE-017 升级判据（跨多日/跨多模块/常规排障无果/需分阶段）依赖 LLM 主观判断，缺少可量化的强制升级信号。
- evolution/history/ 目录 3248 个文件，每次晋升全量快照无清理策略。

## 变更类型
- 新增能力（ROUTE-021 ~ ROUTE-025 + 5 个新 ref + 4 个新场景）
- 修正表达（IR-001 例外条款、ROUTE-017 量化信号、validation_scenarios.md 场景数文档更新）
- 新增能力（validate.sh 统一验证入口、gc_evolution_history.sh 快照 GC、self_evolution.md GC 策略节）

## 变更内容
- 修改文件：
  - `SKILL.md`：IR-001 加例外条款、ROUTE-017 加 4 条量化升级信号、新增 ROUTE-021~025
  - `references/rule_index.md`：新增 ROUTE-021~025 记录、更新 IR-001 摘要
  - `references/self_evolution.md`：新增"进化历史 GC 策略"节
  - `references/validation_scenarios.md`：slug 列表 6→11、新增场景 7~11
  - `scripts/validate_scenario_specs.sh`：CANONICAL_SLUGS 6→11
- 新增文件：
  - `references/notifications.md`、`references/privacy_permissions.md`、`references/persistence.md`、`references/storekit_iap.md`、`references/app_extensions.md`
  - `evolution/scenarios/notifications.json`、`privacy.json`、`persistence.json`、`storekit.json`、`extensions.json`
  - `scripts/validate.sh`（统一验证入口）、`scripts/gc_evolution_history.sh`（快照 GC）
- 替代或合并旧规则：无替代；5 条新 ROUTE 为独立新增能力，不与既有 ROUTE 重叠（TRIGGER/SKIP 已做消歧）

## 预期收益
- ROUTE 覆盖从 20 条扩展到 25 条，补齐 Push/隐私/持久化/内购/Extension 五大盲区
- 验证场景从 6 个扩展到 11 个，覆盖率从 ~33% 提升到 ~44%；
- IR-001 例外条款消除代码输出场景的张力
- ROUTE-017 量化信号（≥5 ref / ≥3 模块 / ≥2 轮 / ≥50 行跨 ≥3 文件）减少主观判断歧义
- validate.sh 统一入口减少脚本碎片化维护成本；专项脚本保留为内部子检查
- GC 策略控制 evolution/history/ 体积

## 验证
- 结构校验：validate.sh --all 全量 13 步
- 场景回放：
  - 新增 5 场景（notifications/privacy/persistence/storekit/extensions）JSON 规格已通过 validate_scenario_specs.sh
  - 6 个原有场景无回归
- 残留风险：
  - StoreKit sandbox 真实交易链路仍需后续人工验证；当前自动场景只覆盖客户端规则与验证 fallback 纪律
  - gc_evolution_history.sh 仅干运行测试，未在生产环境确认删除行为
  - 新 ref 的 last-verified 均为 2026-07，需后续定期审计确认

## 状态
- validated
