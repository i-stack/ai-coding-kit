# Platform Sync Contract

This document records the Claude cleanup as the reference contract for future
platform sync work. The goal is one-click third-party API sync without turning
platform config into a broad preference or routing policy layer.

## Scope

`env/platforms/<platform>.json` is a sync source, not a complete mirror of the
target tool's local config.

The syncer may only touch fields it explicitly owns:

- MCP server blocks declared by `env/mcp/*.json`.
- API fields declared by the platform config and gated by `api.enabled`.
- Preamble / skills metadata declared under `preamble`.
- Platform-specific generated blocks with stable managed markers or sidecars.

All unrelated user fields in the target config must be preserved.

## Default Layers

Default sync should stay narrow:

- API sync.
- MCP servers.
- Skills / preamble / agents metadata.

Default sync should not include:

- Platform UI preferences.
- Personal editor / shell / notification settings.
- Model preference policy.
- Automatic model routing.
- Complexity scoring, two-stage routing, cost optimization, or fallback policy.

If a platform later needs one of those policies, it must be added as an explicit
opt-in feature, not as a default side effect of API sync.

## API Toggle

Each platform that supports third-party API sync may use:

```json
{
  "api": {
    "enabled": true
  }
}
```

Rules:

- `api.enabled=true` means sync this platform's API fields.
- `api.enabled=false` means do not sync API fields and clean fields owned by the syncer.
- The toggle is local to this repository checkout and this machine.
- Do not add a parallel `SYNC_<PLATFORM>_API` environment switch.
- Do not introduce `<platform>.local.json` for this toggle.
- Missing default is platform-specific and must be documented.

For Claude, missing `api` or missing `api.enabled` defaults to enabled.

## Claude Reference

Claude is the current reference implementation.

`env/platforms/claude.json` should stay close to:

```json
{
  "api": {
    "enabled": true
  },
  "env": {
    "ANTHROPIC_AUTH_TOKEN": "${claude.token}",
    "ANTHROPIC_BASE_URL": "${claude.url}",
    "CLAUDE_CODE_EFFORT_LEVEL": "medium",
    "CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS": "1"
  },
  "preamble": {
    "target": "CLAUDE.md",
    "mode": "full",
    "tool": "claude-code",
    "agents": true
  }
}
```

Claude sync owns these target fields:

| Target | Owned fields |
|--------|--------------|
| `~/.claude.json` | `mcpServers` |
| `~/.claude/settings.json` | API `env` keys declared in `env/platforms/claude.json` |
| `~/.claude/config.json` | `primaryApiKey` only when its value is `self` or API sync is enabled |
| `~/.claude/CLAUDE.md` | Managed preamble blocks only |
| `~/.claude/agents/` | Legacy router agent cleanup only; no default model-routing generation |

Claude API behavior:

- `api.enabled=true`: merge API env into `~/.claude/settings.json` and set
  `~/.claude/config.json` `primaryApiKey` to `self`.
- `api.enabled=false`: remove sync-managed API env keys and remove
  `primaryApiKey` only if its current value is `self`.
- Existing unrelated settings, env keys, and config keys must survive.
- `~/.claude/config.json` is created when Claude root exists and API sync is enabled.

Claude default sync must not write these model routing fields:

```json
{
  "ANTHROPIC_DEFAULT_OPUS_MODEL": "...",
  "ANTHROPIC_DEFAULT_SONNET_MODEL": "...",
  "ANTHROPIC_DEFAULT_HAIKU_MODEL": "..."
}
```

`preamble.agents=true` means the platform participates in preamble / agents
capability sync. It does not mean HAIKU / SONNET / OPUS routing, generated
router agents, or automatic model selection.

## CodeBuddy Reference

CodeBuddy is the second platform with an explicit `api.enabled` toggle.

`env/platforms/codebuddy.json` should stay close to:

```json
{
  "api": {
    "enabled": true
  },
  "models": [
    {
      "id": "deepseek-v4-pro",
      "name": "DeepSeek V4 Pro",
      "vendor": "dataeyes",
      "url": "${codebuddy.url}",
      "apiKey": "${codebuddy.key}",
      "maxInputTokens": 128000,
      "maxOutputTokens": 8192,
      "supportsToolCall": true,
      "supportsImages": false,
      "relatedModels": {
        "lite": "deepseek-v4-flash",
        "reasoning": "deepseek-v4-pro"
      }
    },
    {
      "id": "deepseek-v4-flash",
      "name": "DeepSeek V4 Flash",
      "vendor": "dataeyes",
      "url": "${codebuddy.url}",
      "apiKey": "${codebuddy.key}",
      "maxInputTokens": 128000,
      "maxOutputTokens": 8192,
      "supportsToolCall": true,
      "supportsImages": false
    }
  ],
  "availableModels": [
    "deepseek-v4-pro",
    "deepseek-v4-flash"
  ],
  "preamble": {
    "target": "CODEBUDDY.md",
    "mode": "recall",
    "tool": "codebuddy"
  }
}
```

Answers to the platform-addition questions:

1. Target files: `~/.codebuddy/models.json` (`models` + `availableModels`),
   `~/.codebuddy/mcp.json` (MCP), `~/.codebuddy/CODEBUDDY.md` (recall preamble),
   `~/.codebuddy/skills/` (skills copied from Claude).
2. API sync fields: `models` and `availableModels` inside
   `~/.codebuddy/models.json`.
3. Default for `api.enabled`: `true`. CodeBuddy historically always synced its
   models, so a missing `api` block or missing `api.enabled` keeps the old
   always-sync behavior. Only an explicit `false` disables it.
4. Owned target fields: `~/.codebuddy/models.json` → `models`, `availableModels`
   (both gated by `api.enabled`); MCP servers; the historical-recall managed
   block; synced skill directories.
5. Cleanup when `api.enabled=false`: set `availableModels` to an empty list
   `[]` rather than removing the key (CodeBuddy special handling — provider
   model definitions stay so they can be re-enabled, but nothing is shown in the
   model picker). Config-managed `models` are NOT merged while disabled; existing
   model definitions are neither synced nor deleted.
6. Unrelated user fields preserved: any top-level key other than
   `models`/`availableModels` in `models.json` (e.g. `meta`, `uiPreference`),
   user-added model entries, user-added MCP servers, and user content outside
   the managed block in `CODEBUDDY.md`.
7. MCP servers are independent of API sync — they still sync when `api.enabled=false`.
8. Skills / preamble are independent of API sync — they still sync when
   `api.enabled=false`.
9. No login-bypass field like Claude `primaryApiKey=self`.
10. Tests live in `tests/test_codebuddy_sync.py` and cover enable-by-default,
    disable-empty, user-model preservation, idempotent re-sync, and
    re-enable-restore.

## Gemini Reference

Gemini is the third platform with an explicit `api.enabled` toggle.

`env/platforms/gemini.json` should stay close to:

```json
{
  "api": {
    "enabled": true
  },
  "model": {
    "name": "gemini-3.5-flash",
    "maxSessionTurns": -1,
    "compressionThreshold": 0.5,
    "skipNextSpeakerCheck": true
  },
  "context": { "fileName": "GEMINI.md", "includeDirectoryTree": true },
  "tools": { "sandbox": "sandbox-exec", "sandboxNetworkAccess": true },
  "skills": { "enabled": true },
  "hooksConfig": { "enabled": true },
  "security": { "folderTrust": { "enabled": true } },
  "experimental": {
    "directWebFetch": true,
    "enableAgents": true,
    "autoMemory": true,
    "contextManagement": true
  },
  "contextManagement": {
    "historyWindow": { "maxTokens": 200000, "retainedTokens": 10000 }
  },
  "export_env_to_zshrc": {
    "GEMINI_API_KEY": "${gemini.key}",
    "GOOGLE_GEMINI_BASE_URL": "${gemini.url}",
    "GEMINI_MODEL": "gemini-3.5-flash"
  },
  "preamble": { "target": "GEMINI.md", "mode": "full", "tool": "gemini" }
}
```

Answers to the platform-addition questions:

1. Target files: `~/.gemini/settings.json` (`model` + general settings + `mcpServers`),
   `~/.zshrc` (managed GEMINI env block), `~/.gemini/GEMINI.md` (recall/preamble),
   and the Xcode CodingAssistant mirror
   `~/Library/Developer/Xcode/CodingAssistant/gemini/settings.json`.
2. API sync fields: `model` inside `~/.gemini/settings.json`, and the env vars in
   `export_env_to_zshrc` (`GEMINI_API_KEY`, `GOOGLE_GEMINI_BASE_URL`, `GEMINI_MODEL`)
   written to `~/.zshrc`.
3. Default for `api.enabled`: `true`. Gemini historically always synced its model
   and env vars, so a missing `api` block or missing `api.enabled` keeps the old
   always-sync behavior. Only an explicit `false` disables it.
4. Owned target fields: `~/.gemini/settings.json` → `model` (gated by `api.enabled`),
   `mcpServers` (always synced); `~/.zshrc` → the GEMINI env block (gated); the
   managed recalL/preamble block in `GEMINI.md`.
5. Cleanup when `api.enabled=false`: `model` is excluded from the managed settings
   and pruned from `~/.gemini/settings.json` via the managed-keys sidecar; the
   managed `~/.zshrc` GEMINI env block is removed by `clear_env_block`.
6. Unrelated user fields preserved: any top-level key in `settings.json` other than
   `model` (e.g. user `ui`, `general`, nested custom sub-keys), user-added MCP
   servers, other platforms' `~/.zshrc` blocks, and user content in `GEMINI.md`.
7. MCP servers are independent of API sync — they still sync when `api.enabled=false`.
8. General settings (`context`, `tools`, `skills`, `hooksConfig`, `security`,
   `experimental`, `contextManagement`) and the preamble are independent of API
   sync — they still sync when `api.enabled=false`.
9. No login-bypass field like Claude `primaryApiKey=self`.
10. Tests live in `tests/test_gemini_sync.py` and cover enable-by-default,
    disable-removes-model, disable-cleans-zshrc, idempotent re-sync, and
    re-enable-restore.

## Qwen Reference

Qwen Code is a platform that mirrors `~/.qwen/settings.json`. `env/platforms/qwen.json`
flattens the synced fields to the top level (no `settings` wrapper) so its
structure matches `~/.qwen/settings.json` exactly; model definitions live in
`~/.qwen/models.json`, which Qwen owns and this syncer does **not** manage.

`env/platforms/qwen.json` should stay close to:

```json
{
  "api": {
    "enabled": true
  },
  "security": {
    "auth": {
      "selectedType": "openai"
    }
  },
  "env": {
    "__AUTO__": "${qwen.key}"
  },
  "modelProviders": {
    "openai": [
      {
        "id": "qwen3-coder-plus",
        "name": "Qwen3 Coder Plus",
        "baseUrl": "${qwen.url}",
        "envKey": "__AUTO__",
        "generationConfig": {
          "extra_body": {
            "enable_thinking": true
          }
        }
      },
      {
        "id": "qwen3-coder",
        "name": "Qwen3 Coder",
        "baseUrl": "${qwen.url}",
        "envKey": "__AUTO__",
        "generationConfig": {
          "extra_body": {
            "enable_thinking": true
          }
        }
      },
      {
        "id": "qwen-max",
        "name": "Qwen Max",
        "baseUrl": "${qwen.url}",
        "envKey": "__AUTO__",
        "generationConfig": {
          "extra_body": {
            "enable_thinking": true
          }
        }
      }
    ]
  },
  "model": {
    "name": "qwen3-coder-plus",
    "baseUrl": "${qwen.url}"
  },
  "preamble": {
    "target": "QWEN.md",
    "mode": "recall",
    "tool": "qwen"
  }
}
```

Answers to the platform-addition questions:

1. Target files: `~/.qwen/settings.json` (`env` keys + the top-level managed
   fields `security`, `modelProviders`, `model`), `~/.qwen/skills/` (skills
   copied from Claude), `~/.qwen/QWEN.md` (recall preamble — declared under
   `preamble`, rendered by the same managed-block mechanism as the other
   recall platforms). `~/.qwen/models.json` is **not** a sync target — Qwen
   owns it directly.
2. API sync fields: `env` and the owned top-level fields `security` /
   `modelProviders` / `model` inside `~/.qwen/settings.json`. For custom
   OpenAI-compatible providers, `modelProviders.*[].envKey` must use the
   sentinel `"__AUTO__"` rather than a literal `DASHSCOPE_API_KEY` — Qwen Code
   reserves `DASHSCOPE_API_KEY` for its internal DashScope routing and 401s on
   custom endpoints. The syncer derives the real env var name
   (`QWEN_CUSTOM_API_KEY_<PROTO>_<normalize(baseUrl)>_<sha256(proto\0origin)[:12]>`,
   where `origin` is `scheme://host`) from each provider's `baseUrl`, rewrites
   the sentinel in both `modelProviders.*[].envKey` and the `env` block, and
   remaps the declared token onto the derived name. The legacy `DASHSCOPE_API_KEY`
   is dropped from `settings.env` on every sync unless the config still declares
   it explicitly.
3. Default for `api.enabled`: `true`. Qwen historically always synced its API
   fields, so a missing `api` block or missing `api.enabled` keeps the old
   always-sync behavior. Only an explicit `false` disables it.
4. Owned target fields: `~/.qwen/settings.json` → `env` (gated by `api.enabled`),
   `security`, `modelProviders`, `model` (the last three gated by `api.enabled`);
   synced skill directories.
5. Cleanup when `api.enabled=false`: remove only the syncer-managed `env` keys
   from `~/.qwen/settings.json`; remove the managed top-level fields
   (`security`, `modelProviders` entries by `id`, and `model`)
   ownership-aware. Model definitions are not touched (this syncer never writes
   `models.json`).
6. Unrelated user fields preserved: `~/.qwen/settings.json` → `$version` and any
   other top-level key (e.g. user `modelProviders` entries not in config, user
   `env` keys, user `security` keys outside the managed block); user content
   outside the managed block in `QWEN.md`. `~/.qwen/models.json` is left fully
   intact since it is not a sync target.
7. MCP servers: `sync/platforms/qwen.py` currently ignores `mcp_servers` (Qwen
   Code's MCP wiring is not yet driven by `env/mcp/*.json`).
8. Skills / preamble are independent of API sync — they still sync when
   `api.enabled=false`.
9. No login-bypass field like Claude `primaryApiKey=self`.
10. `$version` is a Qwen-internal marker (`"$version": 4` in the real
    `~/.qwen/settings.json`) and is **never** written or overwritten by the
    syncer — every write reads the existing file and merges only owned keys, so
    `$version` (and any other user key) survives untouched.
11. Tests live in `tests/test_qwen_sync.py` and cover enable-by-default,
    settings-fields merge/cleanup, `$version` preservation, models.json not
    managed, idempotent re-sync, and re-enable-restore.

## Continue Reference

Continue is a platform with an explicit `api.enabled` toggle.

`env/platforms/continue.json` should stay close to:

```json
{
  "_comment": "Continue platform configuration. The 'models' block in config.yaml is synced as a third-party API definition by default; set api.enabled=false to disable API sync and remove the managed 'models' block. MCP servers and the historical-recall preamble are independent of API sync and always sync.",
  "api": {
    "enabled": true
  },
  "path": "~/.continue/config.yaml",
  "models": [
    {
      "name": "deepseek-v4-pro",
      "provider": "openai",
      "model": "deepseek-v4-pro",
      "apiKey": "${continue.key}",
      "apiBase": "${continue.url}",
      "defaultCompletionOptions": {
        "maxTokens": 128000
      }
    }
  ],
  "preamble": {
    "mode": "recall",
    "tool": "continue",
    "format": "yaml"
  }
}
```

Answers to the platform-addition questions:

1. Target files: `~/.continue/config.yaml` (`models` + `mcpServers` + the
   `rules` managed block for global historical recall).
2. API sync fields: `models` inside `~/.continue/config.yaml`.
3. Default for `api.enabled`: `true`. Continue historically always synced its
   model definition, so a missing `api` block or missing `api.enabled` keeps the
   old always-sync behavior. Only an explicit `false` disables it.
4. Owned target fields: `~/.continue/config.yaml` → `models` (gated by
   `api.enabled`); `mcpServers` (always synced); the managed `rules` recall
   block (preamble, always synced).
5. Cleanup when `api.enabled=false`: the entire syncer-owned `models` root key
   is removed from `config.yaml` (Continue replaces the block wholesale on each
   sync, so removal is deterministic and re-enable restores it).
6. Unrelated user fields preserved: any top-level key other than `models` in
   `config.yaml` (e.g. `name`, `version`, `contextProviders`,
   `slashCommands`, user `mcpServers`), and user `rules` entries outside the
   managed recall block.
7. MCP servers are independent of API sync — they still sync when `api.enabled=false`.
8. Skills / preamble are independent of API sync — they still sync when
   `api.enabled=false`. Continue has no standalone preamble markdown file; the
   recall block is injected into `config.yaml` `rules` (preamble.format=yaml,
   target=None by design), so a missing `preamble.target` is intentional.
9. No login-bypass field like Claude `primaryApiKey=self`.
10. Tests live in `tests/test_continue_sync.py` and cover enable-by-default,
    disable-removes-models, user-field preservation, idempotent re-sync, and
    re-enable-restore.

## Cline Reference

Cline is the fourth platform with an explicit `api.enabled` toggle.

`env/platforms/cline.json` should stay close to:

```json
{
  "api": {
    "enabled": true
  },
  "globalState": {
    "openAiBaseUrl": "${cline.url}",
    "planModeOpenAiModelId": "deepseek-ai/deepseek-v4-pro",
    "actModeOpenAiModelId": "deepseek-ai/deepseek-v4-flash"
  },
  "secrets": {
    "openAiApiKey": "${cline.key}"
  },
  "preamble": {
    "target": "rules/ai-coding-kit-recall.md",
    "mode": "recall",
    "tool": "cline"
  }
}
```

Answers to the platform-addition questions:

1. Target files: `~/.cline/data/globalState.json` (`globalState` keys),
   `~/.cline/data/secrets.json` (`secrets` keys), the MCP candidate paths
   under `~/Library/Application Support/<editor>/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json`
   (MCP), `~/.cline/skills/` (skills copied from Claude), and the recall
   preamble `rules/ai-coding-kit-recall.md` (rendered by the Bash
   `sync-agent-preamble.sh`, not by the Python sync — the Python `cline.py`
   does not touch the preamble file).
2. API sync fields: `globalState` and `secrets` inside `~/.cline/data/`.
3. Default for `api.enabled`: `true`. Cline historically always merged its
   globalState + secrets, so a missing `api` block or missing `api.enabled`
   keeps the old always-sync behavior. Only an explicit `false` disables it.
4. Owned target fields: `~/.cline/data/globalState.json` → the keys declared
   under `globalState` (gated by `api.enabled`); `~/.cline/data/secrets.json`
   → the keys declared under `secrets` (gated by `api.enabled`). The set of
   owned keys is tracked in a managed-keys sidecar
   (`~/.cline/data/.managed_keys.json`) so a key dropped from the config, or
   all keys on disable, are pruned on the next sync.
5. Cleanup when `api.enabled=false`: every key the syncer currently owns
   (per the sidecar) is removed from `globalState.json` and `secrets.json`,
   and the sidecar record is cleared so re-enabling re-merges cleanly.
   Existing unrelated keys and user-added keys are left intact.
6. Unrelated user fields preserved: any other key in `globalState.json`
   (e.g. telemetry, welcome state), any other key in `secrets.json` (e.g.
   `anthropicApiKey` for other providers), user-added MCP servers, and user
   content outside the managed block in the preamble file.
7. MCP servers are independent of API sync — they still sync when
   `api.enabled=false`.
8. Skills / preamble are independent of API sync — they still sync when
   `api.enabled=false` (preamble is rendered by the Bash writer, not the
   Python sync).
9. No login-bypass field like Claude `primaryApiKey=self`; Cline's secret key
   is a user-provided `openAiApiKey`, never synthesized by the syncer.
10. Tests live in `tests/test_cline_sync.py` and cover enable-by-default,
    disable-cleans, idempotent re-sync, user-field preservation,
    re-enable-restore, and unresolved-placeholder-skip.

## Cleanup Policy

When removing a previously managed feature, prefer deletion over comments.

Reasons:

- Target configs should remain valid JSON / YAML / TOML.
- Commenting out generated fields still leaves ambiguous ownership.
- Deletion plus sidecar / managed markers gives deterministic re-sync behavior.

Cleanup must be ownership-aware:

- Delete fields recorded by a sidecar.
- Delete fields inside a managed block marker.
- Delete a special field only when the current value proves sync ownership.
- Preserve unrelated user fields.

For Claude, `primaryApiKey` is removed only when the value is `self`; another
value, such as `login`, is treated as user-owned and preserved.

## Schema Guardrails

Schema validation should reject stale or ambiguous metadata.

Current guardrails:

- `api` must be an object.
- `api.enabled` must be boolean.
- Unknown `api.*` fields are rejected.
- `preamble` must be an object.
- `preamble.mode` must be one of `full`, `recall`, `none`.
- `preamble.format` must be one of `markdown`, `yaml`, `cursor-mdc`.
- `preamble.agents` must be boolean.
- `preamble.router` is rejected.

## Adding Another Platform

Before modifying another platform, answer these questions in the implementation
or review notes:

1. What exact target files does this platform load at runtime?
2. Which fields are API sync fields?
3. What is the default for `api.enabled`, and why?
4. Which target fields are owned by the syncer?
5. How are stale fields cleaned when `api.enabled=false`?
6. How are unrelated user fields preserved?
7. Are MCP servers independent of API sync?
8. Are skills / preamble independent of API sync?
9. Does the platform have any special login bypass field like Claude
   `primaryApiKey=self`?
10. Which tests prove enable, disable, idempotent re-sync, and user-field
    preservation?

Do one platform at a time. Do not copy Claude behavior blindly; copy the
ownership model and verification discipline.
