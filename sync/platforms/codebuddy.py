import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from .common import env_for_platform, mcp_servers, platform_config, read_json_object, sync_json_mcp, write_json

MCP_TARGET = Path.home() / ".codebuddy" / "mcp.json"
MODELS_TARGET = Path.home() / ".codebuddy" / "models.json"
CODEBUDDY_SKILLS_DIR = Path.home() / ".codebuddy" / "skills"
CLAUDE_SKILLS_DIR = Path.home() / ".claude" / "skills"

ZSHRC_BEGIN = "# BEGIN CODEBUDDY ENV SYNC (from env/config.json)"
ZSHRC_END = "# END CODEBUDDY ENV SYNC"
ZSHRC_BLOCK_PATTERN = re.compile(
    r"# BEGIN CODEBUDDY ENV SYNC(?: \(from [^)]+\))?"
    + r".*?"
    + re.escape(ZSHRC_END)
    + r"\n?",
    re.DOTALL,
)


def _sync_models(data: dict[str, Any]) -> None:
    cfg = platform_config(data, "codebuddy")
    models = cfg.get("models")
    available_models = cfg.get("availableModels")

    if models is None and available_models is None:
        print("[codebuddy] No models config found — skipping model sync.")
        return

    existing = read_json_object(MODELS_TARGET)
    if models is not None:
        existing["models"] = models
    if available_models is not None:
        existing["availableModels"] = available_models
    write_json(MODELS_TARGET, existing)
    print(f"Replaced models in {MODELS_TARGET}.")


def _sync_skills() -> None:
    if not CLAUDE_SKILLS_DIR.exists():
        print(f"[codebuddy] Claude skills directory not found: {CLAUDE_SKILLS_DIR} — skipping skill sync.")
        return

    CODEBUDDY_SKILLS_DIR.mkdir(parents=True, exist_ok=True)
    synced: list[str] = []

    for skill_dir in sorted(CLAUDE_SKILLS_DIR.iterdir()):
        if not skill_dir.is_dir() or not (skill_dir / "SKILL.md").exists():
            continue

        dest = CODEBUDDY_SKILLS_DIR / skill_dir.name
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(skill_dir, dest)
        synced.append(skill_dir.name)

    print(f"Synced {len(synced)} skills to {CODEBUDDY_SKILLS_DIR}: {', '.join(synced) or '(none)'}.")


def sync_zshrc_env(data: dict[str, Any]) -> None:
    env = env_for_platform(data, "codebuddy")
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
    print(f"Updated codebuddy env vars in {zshrc}.")

    try:
        subprocess.run(["zsh", "-c", f"source {zshrc}"], check=True, capture_output=True)
        print(f"Sourced {zshrc} (current process).")
    except subprocess.CalledProcessError as exc:
        print(f"[warn] source {zshrc} exited {exc.returncode}: {exc.stderr.decode().strip()}")


def sync(data: dict[str, Any]) -> None:
    sync_json_mcp(MCP_TARGET, mcp_servers(data, "codebuddy"))
    _sync_models(data)
    _sync_skills()

    cfg = platform_config(data, "codebuddy")
    if cfg.get("needExport"):
        sync_zshrc_env(data)