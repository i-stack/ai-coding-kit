"""Shared historical-recall preamble rendering for all sync targets.

Single source of truth
----------------------
The historical-recall managed block lives in
``skills-engineering/scripts/templates/agent-preamble.md.tmpl``. Both the
Python sync engine (codebuddy.py, continue.py) and the Bash
``sync-agent-preamble.sh`` render it from that template, so every sync path
stays byte-consistent.

Declarative discovery
---------------------
Which platforms receive a preamble, where it lands, and in which mode is
declared once in ``env/platforms/<platform>.json`` under a ``preamble`` key,
e.g.::

    "preamble": { "target": "CODEBUDDY.md", "mode": "recall", "tool": "codebuddy" }

Adding a platform = add one JSON declaration — no engine code changes.
"""
import re
from pathlib import Path
from typing import Any

_TEMPLATE = (
    Path(__file__).resolve().parents[2]
    / "skills-engineering"
    / "scripts"
    / "templates"
    / "agent-preamble.md.tmpl"
)

_RECALL_BEGIN = "<!-- managed-block:historical-recall:begin"
_RECALL_END = "<!-- managed-block:historical-recall:end"


def _extract_recall_raw() -> tuple[str, str, str] | None:
    """Return (begin_marker_line, body, end_marker_line) of the
    historical-recall managed block from the template, or None if the
    template or its managed block is missing.
    """
    if not _TEMPLATE.exists():
        return None
    text = _TEMPLATE.read_text(encoding="utf-8")
    m = re.search(
        re.escape(_RECALL_BEGIN) + r".*?" + re.escape(_RECALL_END) + r"\s*-->",
        text,
        re.DOTALL,
    )
    if not m:
        return None
    lines = m.group(0).splitlines()
    if len(lines) < 2:
        return None
    return lines[0], "\n".join(lines[1:-1]), lines[-1]


def render_recall_block(
    historical_recall_skills_dir: str, cli_path: str
) -> str | None:
    """Render the historical-recall managed block (with its markers) from the
    template, substituting ``{{HISTORICAL_RECALL_SKILLS_DIR}}`` and
    ``{{RECALL_CLI_PATH}}``.

    ``historical_recall_skills_dir`` is the absolute path to the synced
    ``historical-recall`` skill directory (trailing slash optional).
    Returns None when the template or its managed block is missing so callers
    can skip gracefully (e.g. layout changes upstream).
    """
    raw = _extract_recall_raw()
    if raw is None:
        return None
    begin_marker, body, end_marker = raw
    body = body.replace("{{HISTORICAL_RECALL_SKILLS_DIR}}", str(historical_recall_skills_dir))
    body = body.replace("{{RECALL_CLI_PATH}}", str(cli_path))
    return f"{begin_marker}\n{body}\n{end_marker}"


def recall_block_body(
    historical_recall_skills_dir: str, cli_path: str
) -> str | None:
    """Same as :func:`render_recall_block` but returns only the inner body
    (markers stripped), so callers that wrap it with their own marker comment
    (e.g. Continue's YAML ``rules``) keep their existing marker wording.
    """
    raw = _extract_recall_raw()
    if raw is None:
        return None
    _, body, _ = raw
    body = body.replace("{{HISTORICAL_RECALL_SKILLS_DIR}}", str(historical_recall_skills_dir))
    body = body.replace("{{RECALL_CLI_PATH}}", str(cli_path))
    return body


def merge_recall_block_markdown(target: Path, block: str) -> None:
    """Idempotently merge the historical-recall managed block into a markdown
    file (e.g. CODEBUDDY.md).

    Replaces any existing managed block (same marker), preserves user content
    outside the block, and appends when no block exists yet.
    """
    if target.exists():
        text = target.read_text(encoding="utf-8")
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        text = ""
    pattern = re.compile(
        re.escape(_RECALL_BEGIN) + r".*?" + re.escape(_RECALL_END) + r"(?:\s*-->)?",
        re.DOTALL,
    )
    if pattern.search(text):
        new_text = pattern.sub(block, text)
    elif text.strip():
        new_text = text.rstrip() + "\n\n" + block + "\n"
    else:
        new_text = block + "\n"
    if new_text != text:
        target.write_text(new_text, encoding="utf-8")
        print(f"Merged historical-recall block into {target}.")
    else:
        print(f"[recall] No change: {target}.")
