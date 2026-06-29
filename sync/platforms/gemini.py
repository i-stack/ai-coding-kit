import re
import subprocess
from pathlib import Path
from typing import Any

from .common import env_for_platform, mcp_servers, platform_config, sync_json_mcp

_TARGET = Path.home() / ".gemini/settings.json"

ZSHRC_BEGIN = "# BEGIN GEMINI ENV SYNC (from env/config.json)"
ZSHRC_END = "# END GEMINI ENV SYNC"
ZSHRC_BLOCK_PATTERN = re.compile(
    r"# BEGIN GEMINI ENV SYNC(?: \(from [^)]+\))?"
    + r".*?"
    + re.escape(ZSHRC_END)
    + r"\n?",
    re.DOTALL,
)


def sync_zshrc_env(data: dict[str, Any]) -> None:
    env = env_for_platform(data, "gemini")
    if not env:
        return

    lines = [f'export {k}="{v}"' for k, v in env.items()]
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


def sync(data: dict[str, Any]) -> None:
    sync_json_mcp(_TARGET, mcp_servers(data, "gemini"))
    cfg = platform_config(data, "gemini")
    if cfg.get("needExport"):
        sync_zshrc_env(data)
