import re
import subprocess
from pathlib import Path
from typing import Any

from .common import sync_json_mcp

_TARGET = Path.home() / ".gemini/settings.json"

ZSHRC_BEGIN = "# BEGIN GEMINI ENV SYNC (from env/platforms/gemini.json)"
ZSHRC_END = "# END GEMINI ENV SYNC"
ZSHRC_BLOCK_PATTERN = re.compile(
    r"# BEGIN GEMINI ENV SYNC(?: \(from [^)]+\))?"
    + r".*?"
    + re.escape(ZSHRC_END)
    + r"\n?",
    re.DOTALL,
)


def _sync_zshrc_env(cfg: dict[str, Any]) -> None:
    env = cfg.get("env", {})
    if not isinstance(env, dict) or not env:
        return

    lines = [f'export {k}="{v}"' for k, v in env.items() if isinstance(k, str) and isinstance(v, str) and v]
    if not lines:
        return

    block = f"{ZSHRC_BEGIN}\n" + "\n".join(lines) + f"\n{ZSHRC_END}\n"
    zshrc = Path.home() / ".zshrc"

    if zshrc.exists():
        text = zshrc.read_text(encoding="utf-8")
        if ZSHRC_BLOCK_PATTERN.search(text):
            new_text = ZSHRC_BLOCK_PATTERN.sub(block, text)
        else:
            new_text = text.rstrip() + "\n\n" + block
    else:
        new_text = block

    zshrc.write_text(new_text, encoding="utf-8")
    print(f"Updated gemini env vars in {zshrc}.")

    try:
        subprocess.run(["zsh", "-c", f"source {zshrc}"], check=True, capture_output=True)
        print(f"Sourced {zshrc} (current process).")
    except subprocess.CalledProcessError as exc:
        print(f"[warn] source {zshrc} exited {exc.returncode}: {exc.stderr.decode().strip()}")


def sync(mcp_servers: dict[str, Any], cfg: dict[str, Any]) -> None:
    """Sync MCP servers and env vars to Gemini CLI."""
    sync_json_mcp(_TARGET, mcp_servers)
    if cfg.get("env"):
        _sync_zshrc_env(cfg)
