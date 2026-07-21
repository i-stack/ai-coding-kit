# 多平台模型路由抽象（设计说明）

对齐 Hermes Agent 的 `model_metadata.py`：把各平台散落的模型 / provider 配置抽象为**统一 provider 层**，降低新增模型或厂商的成本。

## 现状

`env/platforms/*.json` 每个文件遵循该平台的官方 spec，模型相关字段命名不统一：

- Codex：`model_providers.<name>.base_url` + `env.<API_KEY>`
- Claude：`env` / `hooks`
- Gemini：`env` 变量
- 其他平台各异

新增一个模型往往要在多个平台 JSON 里分别改字段，容易遗漏或写错。

## 目标抽象（建议形态）

```
统一 Provider 层（env/model_providers.json，规划中）
┌──────────────────────────────────────────┐
│ provider: nous-portal / openrouter / ...  │
│   models: [ {id, context, cost}, ... ]    │
│   auth:   ${provider.key}  ← 统一密钥     │
└──────────────────────────────────────────┘
        │ 渲染
        ▼
env/platforms/*.json  （各平台官方格式，自动生成）
```

要点：

1. **统一密钥（tool gateway 式）**：所有 provider key 集中到 `env/secrets.json` 的 `providers.<name>.key`，同步时按平台 spec 注入，避免每个平台各写一份。
2. **模型目录即真理源**：`model_providers.json` 描述「有哪些模型、上下文、成本、默认路由」，平台 JSON 只描述「怎么接」。
3. **新增模型 = 改一处**：加一个 model 条目，所有平台同步受益。

## 当前可用工具

- `sync/list_models.sh`：只读抽取各平台 JSON 中的 model / provider / base_url / api_key 字段，统一成表，便于核对「哪里配了什么」。
- `env/templates/platform.template.json`：新增平台时的起点。

> 本文件为设计说明；统一 Provider 层的实际渲染器尚未实现，当前仍由各平台 JSON 直接描述。引入前需评估与现有「零字段映射」原则的兼容性。
