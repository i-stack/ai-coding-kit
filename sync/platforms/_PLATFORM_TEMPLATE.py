"""Platform renderer template for ai-coding-kit sync engine.

USAGE
-----
To add a new platform:

  Step 1 — Create env/platforms/<name>.json
  -----------------------------------------
  Declare the platform's native config and sync metadata:

      {
        "install_root": "~/.myplatform",  // optional: custom install root
        "preamble": {
          "target": "MYPLATFORM.md",      // relative to install root
          "mode": "full",                 // "full" | "recall" | "none"
          "tool": "myplatform"
        },
        "mcpServers": { ... }             // native MCP config if needed
      }

  If "install_root" is omitted, the engine falls back to:
    1. secrets.json paths override  (env/secrets.json > paths key)
    2. paths.py Mac default         (defined in sync/platforms/paths.py)
    3. ~/.{platform_name}           (automatic fallback for unknown platforms)

  Step 2 — (Optional) Create sync/platforms/<name>.py
  -----------------------------------------------------
  Only needed when the platform uses a non-standard config format. Copy this
  template and implement the sync() function. If the platform's MCP config is
  plain JSON (mcp_target field), no .py file is required at all.

  INTERFACE CONTRACT
  ------------------
  Every renderer module MUST export exactly this function:

      def sync(mcp_servers: dict, platform_cfg: dict) -> None

  Parameters
  ----------
  mcp_servers : dict
      MCP servers filtered for this platform from env/mcp/*.json.
      Already resolved (secrets substituted).

  platform_cfg : dict
      Full contents of env/platforms/<name>.json with secrets resolved.
      The ``path`` and ``preamble`` keys are sync-engine metadata and can
      be read but should not be written to the native config output.

  The function must be idempotent: calling it multiple times must produce
  the same result as calling it once.

  PATHS
  -----
  Use helpers from sync/platforms/paths.py for file paths:

      from platforms.paths import myplatform_root_dir, myplatform_config_path

  If the platform is new (not yet in paths.py), add the path helpers there.
  The engine injects any JSON "install_root" override into paths._PATH_OVERRIDES before
  calling sync(), so your helpers automatically pick up custom roots.

  Alternatively, read the install root from platform_cfg directly:

      from pathlib import Path
      install_root = Path(platform_cfg.get("path", "~/.myplatform")).expanduser()
"""

# ── Example renderer ──────────────────────────────────────────────────────────
#
# from pathlib import Path
# from typing import Any
#
# from .common import write_json
# from .paths import myplatform_root_dir
#
#
# def sync(mcp_servers: dict[str, Any], platform_cfg: dict[str, Any]) -> None:
#     root = myplatform_root_dir()
#     root.mkdir(parents=True, exist_ok=True)
#
#     config = {
#         "mcpServers": mcp_servers,
#         # ... add platform-specific keys from platform_cfg ...
#     }
#     write_json(root / "config.json", config)
