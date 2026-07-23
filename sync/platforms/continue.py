import re

from pathlib import Path
from typing import Any

from core import recall
from core.common import api_enabled as _api_enabled
from core.paths import continue_root_dir


def dump_yaml_scalar(v: Any) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if v is None:
        return "null"
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, dict) and not v:
        return "{}"
    if isinstance(v, list) and not v:
        return "[]"
    s = str(v)
    special_chars = {":", "#", "-", "{", "}", "[", "]", ",", "\n", "@", "`", "&", "*", "!", "|", ">", "?", "<", "=", "%"}
    needs_quotes = (
        any(c in s for c in special_chars)
        or s.lower() in ("true", "false", "null")
        or s.strip() != s
        or (s and s[0] in "-?:,[]{}#&*!|>'\"%@`")
    )
    if needs_quotes:
        return "\"" + s.replace("\\", "\\\\").replace("\"", "\\\"") + "\""
    return s


def dump_yaml(data: Any, indent_level: int = 0) -> str:
    spacing = " " * indent_level
    if isinstance(data, dict):
        if not data:
            return "{}"
        lines = []
        for k, v in data.items():
            if isinstance(v, (dict, list)) and len(v) > 0:
                lines.append(f"{spacing}{k}:")
                lines.append(dump_yaml(v, indent_level + 2))
            else:
                lines.append(f"{spacing}{k}: {dump_yaml_scalar(v)}")
        return "\n".join(lines)
    elif isinstance(data, list):
        if not data:
            return "[]"
        lines = []
        for item in data:
            if isinstance(item, dict):
                dict_lines = []
                for i, (k, v) in enumerate(item.items()):
                    if i == 0:
                        if isinstance(v, (dict, list)) and len(v) > 0:
                            dict_lines.append(f"{spacing}- {k}:")
                            dict_lines.append(dump_yaml(v, indent_level + 4))
                        else:
                            dict_lines.append(f"{spacing}- {k}: {dump_yaml_scalar(v)}")
                    else:
                        if isinstance(v, (dict, list)) and len(v) > 0:
                            dict_lines.append(f"{spacing}  {k}:")
                            dict_lines.append(dump_yaml(v, indent_level + 4))
                        else:
                            dict_lines.append(f"{spacing}  {k}: {dump_yaml_scalar(v)}")
                lines.append("\n".join(dict_lines))
            else:
                lines.append(f"{spacing}- {dump_yaml_scalar(item)}")
        return "\n".join(lines)
    else:
        return dump_yaml_scalar(data)


def update_yaml_root_key(yaml_text: str, key_name: str, new_key_yaml: str) -> str:
    lines = yaml_text.splitlines()
    new_lines = []

    in_key = False
    key_replaced = False

    for line in lines:
        stripped = line.strip()
        is_empty_or_comment = not stripped or stripped.startswith("#")

        is_root_key = False
        if not is_empty_or_comment and not line.startswith(" "):
            if ":" in line:
                is_root_key = True

        if is_root_key:
            if in_key:
                in_key = False

            curr_key = line.split(":", 1)[0].strip()
            if curr_key == key_name:
                in_key = True
                if not key_replaced:
                    new_lines.append(new_key_yaml)
                    key_replaced = True
                continue

        if in_key:
            continue

        new_lines.append(line)

    if not key_replaced:
        if new_lines and new_lines[-1].strip():
            new_lines.append("")
        new_lines.append(new_key_yaml)

    return "\n".join(new_lines) + "\n"


# ── Global historical recall (end-to-end recall, same mechanism as Claude Code) ──
# Injected into config.yaml `rules`, which Continue concatenates into the system
# message for ALL Agent / Chat / Edit requests — its global always-on mechanism.
# The block body is sourced from the SAME template the Bash preamble writer and
# codebuddy.py use (sync/core/recall.py), so all paths stay byte-consistent.

_RECALL_BEGIN = "<!-- managed-block:historical-recall:begin"
_RECALL_END = "<!-- managed-block:historical-recall:end"


def _split_flow_list(inner: str) -> list[str]:
    """Split a YAML flow-list body on commas, honoring quoted segments.

    Quoted commas (single or double) are preserved, so a value like
    ``["rule A, B", "rule C"]`` parses into two items, not three.
    """
    items: list[str] = []
    buf = ""
    quote: str | None = None
    for ch in inner:
        if quote:
            if ch == quote:
                quote = None
            else:
                buf += ch
        elif ch in ("'", '"'):
            quote = ch
        elif ch == ",":
            items.append(buf)
            buf = ""
        else:
            buf += ch
    if buf.strip():
        items.append(buf)
    cleaned: list[str] = []
    for p in items:
        p = p.strip()
        if not p:
            continue
        if len(p) >= 2 and p[0] == p[-1] and p[0] in "\"'":
            p = p[1:-1]
        cleaned.append(p)
    return cleaned


def _needs_yaml_quote(s: str) -> bool:
    """Whether a single-line rule must be quoted to round-trip in YAML.

    Plain (unquoted) scalars keep diffs clean for the common case; only values
    containing YAML indicators / special characters get double-quoted.
    """
    if not s:
        return True
    if s != s.strip():
        return True
    # YAML reserved words that would otherwise be parsed back as non-strings
    # (null/~ -> None, true/false -> bool). Quote so the rule round-trips as
    # literal text. Keep in sync with dump_yaml_scalar's reserved-word set.
    if s.lower() in ("true", "false", "null", "~"):
        return True
    if s[0] in "!&*?|>%@`\"',[]{}#":
        return True
    if ": " in s:
        return True
    if any(c in s for c in "#[]{}&*?|<>=!%@`\"'"):
        return True
    return False


def _parse_rules(yaml_text: str) -> list[str] | None:
    """Return the list of rule strings under the top-level `rules:` key.

    Handles a `rules:` value that is a YAML list of inline strings or block
    scalars (`- |`, `- >`, etc.), a single scalar, or a flow list. Returns
    None when `rules:` is absent.

    Block-scalar content is bounded by indentation: a sibling list item
    (`- `) at the same indentation as the current item terminates the block,
    so sibling rules are never swallowed into the previous block. Relative
    indentation inside a block scalar is preserved so re-rendering is faithful.
    """
    lines = yaml_text.splitlines()
    start = None
    inline = ""
    for i, line in enumerate(lines):
        m = re.match(r"^rules\s*:\s*(.*)$", line)
        if m:
            start = i
            inline = m.group(1).strip()
            break
    if start is None:
        return None
    if inline and not inline.startswith("#"):
        if inline.startswith("["):
            inner = inline[1:-1] if inline.endswith("]") else inline[1:]
            return _split_flow_list(inner)
        val = inline
        if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
            val = val[1:-1]
        return [val]
    items: list[str] = []
    i = start + 1
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if stripped == "" or stripped.startswith("#"):
            i += 1
            continue
        # A non-indented line ends the `rules:` block (next root-level key).
        if not (line.startswith(" ") or line.startswith("\t")):
            break
        m = re.match(r"^(\s*)-\s*(.*)$", line)
        if not m:
            # Indented but not a list item — stop to avoid mis-parsing.
            break
        indent = len(m.group(1))
        content = m.group(2)
        if content in ("|", ">", "|-", ">-", "|+", ">+"):
            folded = content.startswith(">")
            i += 1
            block: list[str] = []
            while i < len(lines):
                cur = lines[i]
                if cur.strip() == "":
                    # Blank lines belong to the block scalar.
                    block.append("")
                    i += 1
                    continue
                if not (cur.startswith(" ") or cur.startswith("\t")):
                    break
                # Block scalar content must be indented MORE than the item;
                # a sibling `- ` at the same indent terminates the block.
                if len(cur) - len(cur.lstrip()) <= indent:
                    break
                block.append(cur)
                i += 1
            if folded:
                # Folded scalar (`>`): newlines are folded into spaces, so the
                # rule becomes a single line. Store it WITHOUT newlines so
                # _render_rules_yaml emits an inline `- value` rather than a
                # literal `|` block, preserving the user's folded intent.
                non_empty = [b for b in block if b.strip() != ""]
                if non_empty:
                    min_indent = min(len(b) - len(b.lstrip()) for b in non_empty)
                    folded_text = " ".join(
                        (b[min_indent:]).strip() for b in non_empty
                    )
                else:
                    folded_text = ""
                items.append(folded_text)
            else:
                # Literal scalar (`|`): preserve newlines and relative layout so
                # _render_rules_yaml emits a faithful `|` block.
                non_empty = [b for b in block if b.strip() != ""]
                if non_empty:
                    min_indent = min(len(b) - len(b.lstrip()) for b in non_empty)
                    block = [
                        (b[min_indent:] if b.strip() != "" else "") for b in block
                    ]
                items.append("\n".join(block).strip("\n"))
        else:
            val = content
            if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
                val = val[1:-1]
            items.append(val)
            i += 1
    return items


def _render_rules_yaml(items: list[str]) -> str:
    out = ["rules:"]
    for it in items:
        if "\n" in it:
            out.append("  - |")
            for sub in it.splitlines():
                out.append("    " + sub)
        elif _needs_yaml_quote(it):
            escaped = it.replace("\\", "\\\\").replace('"', '\\"')
            out.append(f'  - "{escaped}"')
        else:
            out.append(f"  - {it}")
    return "\n".join(out) + "\n"


def _repo_root() -> Path:
    """Locate the ai-coding-kit repo root by walking up to find `skills-engineering/`.

    Avoids a brittle hard-coded `parents[N]` assumption (which would silently
    point at the wrong directory if this file is moved). Falls back to the
    historical `parents[2]` location when the marker dir is not found.
    """
    here = Path(__file__).resolve()
    for ancestor in [here, *here.parents]:
        if (ancestor / "skills-engineering").is_dir():
            return ancestor
    return here.parents[2]


def _remove_yaml_root_key(yaml_text: str, key_name: str) -> str:
    """Remove a top-level key (and its nested block) from YAML text.

    Ownership-aware cleanup: Continue's syncer owns the entire ``models`` block
    (it is replaced wholesale on each sync), so disabling API sync removes the
    key rather than leaving a stale managed block behind.
    """
    lines = yaml_text.splitlines()
    new_lines: list[str] = []
    in_key = False
    for line in lines:
        stripped = line.strip()
        is_empty_or_comment = not stripped or stripped.startswith("#")
        is_root_key = False
        if not is_empty_or_comment and not line.startswith(" "):
            if ":" in line:
                is_root_key = True
        if is_root_key:
            if in_key:
                in_key = False
            curr_key = line.split(":", 1)[0].strip()
            if curr_key == key_name:
                in_key = True
                continue
        if in_key:
            continue
        new_lines.append(line)
    while new_lines and new_lines[-1].strip() == "":
        new_lines.pop()
    return "\n".join(new_lines) + "\n" if new_lines else ""


def _sync_recall(cfg: dict[str, Any], yaml_text: str) -> str:
    """Merge the historical-recall managed block into config.yaml `rules`.

    Idempotent: any previously-managed recall block is replaced; existing user
    rules are preserved. Set platforms.continue.recall=false or
    preamble.mode=none to opt out.

    The block body is sourced from the shared template (sync/core/recall.py)
    so it stays byte-consistent with the Bash preamble writer and codebuddy.py.
    """
    preamble = cfg.get("preamble") or {}
    if cfg.get("recall") is False or preamble.get("mode") == "none":
        return yaml_text
    repo_root = _repo_root()
    skills_dir = str((repo_root / "skills-engineering" / "historical-recall").resolve()) + "/"
    cli_path = str(
        (repo_root / "skills-engineering" / "plan-reviews" / "dist" / "cli.js").resolve()
    )
    body = recall.recall_block_body(skills_dir, cli_path)
    if body is None:
        print("[continue] agent-preamble template not found — skipping recall sync.")
        return yaml_text
    block = f"{_RECALL_BEGIN} (managed by ai-coding-kit; do not edit) -->\n{body}\n{_RECALL_END} -->"
    items = _parse_rules(yaml_text) or []
    items = [it for it in items if _RECALL_BEGIN not in it]
    items.append(block)
    return update_yaml_root_key(yaml_text, "rules", _render_rules_yaml(items))


def sync(mcp_servers: dict[str, Any], cfg: dict[str, Any]) -> None:
    """Sync MCP servers and models to Continue (YAML format)."""
    root = continue_root_dir()
    if not root.exists():
        print(f"[continue] Continue root not found: {root} — skipping (tool not installed).")
        return

    path_str = cfg.get("path", "~/.continue/config.yaml")
    target_path = Path(path_str).expanduser()

    if target_path.exists():
        yaml_text = target_path.read_text(encoding="utf-8")
    else:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        yaml_text = ""
        print(f"[continue] Continue configuration file not found at {target_path} — creating it.")

    # 1. Sync mcpServers
    continue_servers = []
    for name, srv_cfg in sorted(mcp_servers.items()):
        if not isinstance(srv_cfg, dict):
            continue
        srv = {"name": name}
        for k, v in srv_cfg.items():
            srv[k] = v

        # Continue schema mapping for SSE / Remote servers
        if "url" in srv:
            if "type" not in srv:
                srv["type"] = "sse"
            if "headers" in srv:
                headers = srv.pop("headers")
                if headers:
                    srv["requestOptions"] = {"headers": headers}

        continue_servers.append(srv)

    if not continue_servers:
        new_mcp_yaml = "mcpServers: []"
    else:
        new_mcp_yaml = "mcpServers:\n" + dump_yaml(continue_servers, indent_level=2)

    yaml_text = update_yaml_root_key(yaml_text, "mcpServers", new_mcp_yaml)

    # 2. Sync models (API-sync fields, gated by api.enabled)
    #    Continue's syncer owns the entire `models` root key (replaced wholesale
    #    on each sync), so disabling API sync removes the managed block instead
    #    of leaving stale model definitions behind.
    models = cfg.get("models")
    api_enabled = _api_enabled(cfg)
    if not api_enabled:
        yaml_text = _remove_yaml_root_key(yaml_text, "models")
        print("[continue] API sync disabled — removed managed 'models' block from config.")
    elif models is not None:
        if not isinstance(models, list):
            print("[warn] platforms.continue.models must be a list. Skipping model sync.")
        else:
            if not models:
                new_models_yaml = "models: []"
            else:
                new_models_yaml = "models:\n" + dump_yaml(models, indent_level=2)
            yaml_text = update_yaml_root_key(yaml_text, "models", new_models_yaml)
            print("Replaced models in Continue config.")

    # 3. Sync global historical recall (always-on, best-effort, non-blocking)
    yaml_text = _sync_recall(cfg, yaml_text)

    target_path.write_text(yaml_text, encoding="utf-8")
    print(f"Replaced MCP servers in {target_path}.")
