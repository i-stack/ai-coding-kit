# plan-reviews knowledge base

> 本地嵌入式知识库 —— 将 `.plan-reviews/` 目录下的 plan-grill 和 cross-model-review 产物自动索引，提供语义搜索和实体图谱，**无需启动 rag-gateway 服务和数据库**。

## 为什么不用 rag-gateway？

| rag-gateway | plan-reviews-kb |
|---|---|
| Fastify HTTP 服务（常驻进程） | 嵌入式库（import 即用） |
| Qdrant 向量数据库（独立服务） | 内存余弦相似度（进程内计算） |
| PostgreSQL 图数据库（独立服务） | 单 JSON 缓存文件（零原生依赖） |
| LLM 实体提取（API 调用） | 结构化解析（PLAN.md 七段结构） |
| MCP Server（SSE 传输） | 直接调用（同进程） |
| 需要 Embedding API | 需要 Embedding API（唯一外部依赖） |

核心思路：`.plan-reviews` 存储的是高度结构化的 PLAN.md 文件，数据量小（几十到几百个 plan），完全不需要重型基础设施。

## 快速开始

```bash
cd skills-engineering/plan-reviews
npm install
npm run sync   # 同步 .plan-reviews/ 到本地知识库
```

## 使用方式

### 1. 作为库（在 skill 中调用）

```typescript
import { PlanReviewsKB } from "@i-stack/plan-reviews-kb";

const kb = await PlanReviewsKB.init({ projectRoot: process.cwd() });

// 同步所有 plan
await kb.sync();

// 搜索历史 plan
const results = await kb.search({
  query: "Redis rate limiting atomic operations",
  limit: 5,
});

// 格式化输出
console.log(kb.formatResults(results));

console.log(kb.stats);
// { plans: 1, entities: 15, relations: 22, chunks: 8 }

kb.close();
```

### 2. 搜索指定类型的实体

```typescript
const results = await kb.search({
  query: "CAPTCHA",
  entityType: "technology",  // 只搜索技术实体
});
```

### 3. 搜索特定 plan

```typescript
const results = await kb.search({
  query: "atomic Lua script",
  planId: "2026-07-06-login-rate-limit",  // 限定范围
});
```

## 架构

```
.plan-reviews/                     skills-engineering/plan-reviews/
├── 2026-07-06-xxx/                src/
│   ├── PLAN.md        ──sync──→  ├── parser.ts     结构化解析 PLAN.md
│   ├── PLAN-REVIEW-LOG.md  ──→   ├── extractor.ts  实体/关系提取（无 LLM）
│   └── SUMMARY.md      ──→       ├── store.ts      JSON 缓存持久化
│                                  ├── embed.ts      Embedding API
│                                  ├── vector.ts     内存向量索引（余弦相似度）
│                                  ├── search.ts     组合搜索（语义+图谱）
│                                  ├── sync.ts       增量同步引擎
│                                  └── index.ts      主入口
│
└── .kb-index.json  ←── JSON 缓存文件（自动生成）
```

## 数据流

```
1. scanPlansDir()         扫描 .plan-reviews/ 目录
       ↓
2. parsePlan()            解析 PLAN.md 七段结构
       ↓
3. extractFromArtifact()  提取实体（goal/decision/risk/technology...）
                          关系（uses/addresses/constrains...）
       ↓
4. planToChunks()         切分文本段落
       ↓
5. embedBatch()           生成 Embedding 向量
       ↓
6. upsertPlan/Entities/Chunks  写入 JSON 缓存 + 内存向量索引
       ↓
7. search()              语义相似度 + 图谱遍历 → 结果
```

## 知识图谱实体类型

| Entity Type | 来源 | 示例 |
|---|---|---|
| `goal` | PLAN.md → Goal | "Reduce credential-stuffing risk" |
| `constraint` | PLAN.md → Constraints | "Deployed behind trusted reverse proxy" |
| `decision` | PLAN.md → Key Decisions | "Pair-scoped key instead of username-only" |
| `risk` | PLAN.md → Risks | "Distributed low-and-slow attacks" |
| `technology` | Approach/Decisions 文本 | "TypeScript", "Docker" |
| `service` | Approach/Decisions 文本 | "Redis", "PostgreSQL" |
| `out_of_scope` | PLAN.md → Out of Scope | "CAPTCHA, MFA step-up" |

## 关系类型

| Relation | 含义 |
|---|---|
| `uses` | Decision 使用某个 Technology/Service |
| `addresses` | Decision 解决某个 Goal；Risk 威胁某个 Goal |
| `constrains` | Constraint 限制某个 Decision |
| `mitigates` | Decision 缓解某个 Risk |

## 环境变量

| 变量 | 说明 | 默认值 |
|---|---|---|
| `EMBEDDING_API_KEY` | Embedding API 密钥 | （空，跳过语义搜索） |
| `EMBEDDING_BASE_URL` | Embedding API 地址 | `https://api.openai.com/v1` |
| `EMBEDDING_MODEL` | Embedding 模型 | `bge-m3` |
| `VECTOR_SIZE` | 向量维度 | 根据模型自动推断 |

**无 Embedding API 也能用**：即使不配置 Embedding API，图谱搜索（实体/关系匹配）仍然完全可用。语义搜索会自动降级跳过。

## 与 rag-gateway 的对应关系

| rag-gateway 模块 | plan-reviews-kb 模块 | 差异 |
|---|---|---|
| `src/vector/qdrant.ts` | `src/vector.ts` | Qdrant 服务 → 内存余弦相似度 |
| `src/db/graph.ts` | `src/store.ts` | PostgreSQL → JSON 缓存 |
| `src/entity/extractor.ts` | `src/extractor.ts` | LLM 调用 → 结构化解析 |
| `src/entity/store.ts` | `src/sync.ts` + `src/extractor.ts` | 实时管道 → 批量同步 |
| `src/vector/embedding.ts` | `src/embed.ts` | **直接移植**（同逻辑） |
| `src/vector/store.ts` | 内联到 `sync.ts` | 简化 |
| `src/tool/registry.ts` | 不需要 | 无工具系统 |
| `src/mcp/server.ts` | 不需要 | 直接调用 |
