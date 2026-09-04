"""Tests for the per-MCP ``enabled`` sync toggle.

Covers:
  - ``core.common.mcp_enabled`` semantics (missing defaults to enabled,
    only an explicit ``false`` disables).
  - ``core.common.load_all_mcp`` filtering: disabled servers are skipped and
    the ``enabled`` key is stripped from the synced config.
  - End-to-end prune: disabling a previously-synced managed server removes it
    from the target via the marker merge, while user-owned servers survive.
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[1]
SYNC_DIR = REPO_ROOT / "sync"
if str(SYNC_DIR) not in sys.path:
    sys.path.insert(0, str(SYNC_DIR))

from core import common  # noqa: E402


def _write_mcp(tmp: Path, name: str, **extra: object) -> Path:
    path = tmp / f"{name}.json"
    cfg = {"name": name, "type": "sse", "url": f"https://example.com/{name}"}
    cfg.update(extra)
    path.write_text(json.dumps(cfg), encoding="utf-8")
    return path


class McpEnabledHelperTests(unittest.TestCase):
    def test_missing_enabled_defaults_to_enabled(self) -> None:
        self.assertTrue(common.mcp_enabled({}))
        self.assertTrue(common.mcp_enabled({"name": "github"}))

    def test_explicit_true_is_enabled(self) -> None:
        self.assertTrue(common.mcp_enabled({"enabled": True}))

    def test_explicit_false_is_disabled(self) -> None:
        self.assertFalse(common.mcp_enabled({"enabled": False}))

    def test_non_dict_defaults_to_enabled(self) -> None:
        self.assertTrue(common.mcp_enabled(None))  # type: ignore[arg-type]
        self.assertTrue(common.mcp_enabled("nope"))  # type: ignore[arg-type]


class LoadAllMcpToggleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _load(self) -> dict:
        with mock.patch.object(common, "MCP_DIR", self.root):
            return common.load_all_mcp()

    def test_disabled_server_is_skipped(self) -> None:
        _write_mcp(self.root, "github", enabled=True)
        _write_mcp(self.root, "shell", enabled=False)
        _write_mcp(self.root, "filesystem")  # missing -> enabled

        loaded = self._load()

        self.assertIn("github", loaded)
        self.assertNotIn("shell", loaded)
        self.assertIn("filesystem", loaded)

    def test_enabled_key_is_stripped_from_synced_config(self) -> None:
        _write_mcp(self.root, "github", enabled=True)

        loaded = self._load()

        self.assertNotIn("enabled", loaded["github"])

    def test_only_explicit_false_disables(self) -> None:
        _write_mcp(self.root, "github", enabled=True)
        # Consistent with api_enabled: only the boolean True enables — a
        # non-True value is treated as disabled (schema rejects it anyway).
        _write_mcp(self.root, "apifox", enabled="yes")

        loaded = self._load()

        self.assertIn("github", loaded)
        self.assertNotIn("apifox", loaded)


class DisabledServerPruneTests(unittest.TestCase):
    """Disabling a server removes its previously-synced managed entry."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.mcp_dir = self.root / "mcp"
        self.mcp_dir.mkdir()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_disable_prunes_managed_entry_and_keeps_user_owned(self) -> None:
        # First sync: shell is enabled and gets a managed entry.
        _write_mcp(self.mcp_dir, "shell", enabled=True)
        target = self.root / "target.json"
        target.write_text(
            json.dumps({"mcpServers": {"user": {"command": "u"}}}) + "\n",
            encoding="utf-8",
        )
        with mock.patch.object(common, "MCP_DIR", self.mcp_dir):
            servers = common.load_all_mcp()
        common.sync_json_mcp(target, servers)
        first = json.loads(target.read_text(encoding="utf-8"))["mcpServers"]
        self.assertEqual(first["shell"]["_managed_by"], "ai-coding-kit")

        # Second sync: shell disabled -> config no longer contains it, so the
        # managed entry is pruned while the user-owned server survives.
        _write_mcp(self.mcp_dir, "shell", enabled=False)
        with mock.patch.object(common, "MCP_DIR", self.mcp_dir):
            servers = common.load_all_mcp()
        common.sync_json_mcp(target, servers)

        data = json.loads(target.read_text(encoding="utf-8"))
        self.assertNotIn("shell", data["mcpServers"])
        self.assertEqual(data["mcpServers"]["user"], {"command": "u"})


if __name__ == "__main__":
    unittest.main()
