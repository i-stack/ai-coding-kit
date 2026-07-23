# plan-reviews knowledge base

> 本地嵌入式知识库 —— 将 `.plan-reviews/` 目录下的 plan-grill、cross-model-review 与 auto-code-review 产物自动索引，提供语义搜索和实体图谱。Embedding API 为可选依赖；未配置时退化为本地关键词 / 实体检索，无需数据库。

> **auto-code-review 产物（code-review 类）现已纳入索引**：含 `REVIEW-LOG.md` + `diff.patch` 的目录会被识别为代码审查产物，其 diff 文本与审查结论作为可检索 chunk 进入 `.kb-index.json`，实现 PRD FR-8「审查结果回灌知识库，下次提问优先检索」。

### 召回与新陈代谢（闭环命令）

```bash
# 检索注入：先增量同步，再根据用户问题返回最相关历史摘要
node dist/cli.js recall "给登录接口加速率限制"

# 同步：把 .plan-reviews/ 的新归档产物增量索引进 .kb-index.json
node dist/cli.js sync

# 新陈代谢：有 embedding 时按相似度合并；无 embedding 时合并跨 plan 完全相同的知识点
#   → 生成 .plan-reviews/.kb-merged.json + .plan-reviews/MERGED-KNOWLEDGE.md
node dist/cli.js merge
```

用户显式启动 `auto-code-review` 后，由全局 `historical-recall` 在动手前 best-effort 执行 `recall`，`auto-code-review` 归档后负责 `sync`+`merge`。`plan-grill` 进入盘问前，历史召回同样由全局 `historical-recall` 统一负责，本 skill 不再内联。普通明确执行任务不会因此进入盘问。

`cosine` 仅表示向量余弦相似度，`lexical` 表示本地词法覆盖分，两者都不是经校准的「命中率」或正确概率。

核心思路：`.plan-reviews` 存储的是高度结构化的 PLAN.md / code-review 归档文件，数据量小（几十到几百个 plan），通过内存余弦相似度（有 Embedding 时）或本地关键词检索（无 Embedding 时）+ 单 JSON 缓存文件即可实现召回和知识图谱，完全不需要重型基础设施。

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
│   ├── architecture-analysis.md ─→│                 PG-005 架构分析搜索 chunk
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

> **配置方式**：在 `env/secrets.json` 中添加 `embedding` 字段，填入你的 `key` 和 `url`，即可自动映射为 `EMBEDDING_API_KEY` 和 `EMBEDDING_BASE_URL`。

**无 Embedding API 也能用**：即使不配置 Embedding API，图谱搜索（实体/关系匹配）仍然完全可用。语义搜索会自动降级跳过。
