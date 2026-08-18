"""Regression tests for core.common.sync_json_mcp.

Covers the symlink-handling bug where unlinking before reading dropped every
non-mcpServers top-level key from the target file.
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SYNC_DIR = REPO_ROOT / "sync"
if str(SYNC_DIR) not in sys.path:
    sys.path.insert(0, str(SYNC_DIR))

from core.common import merge_managed_dict, sync_json_mcp  # noqa: E402


class SyncJsonMcpTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _read(self, path: Path) -> dict:
        return json.loads(path.read_text(encoding="utf-8"))

    def test_preserves_other_keys_on_plain_file(self) -> None:
        path = self.root / "mcp.json"
        path.write_text(
            json.dumps({"other": {"keep": True}, "mcpServers": {"old": {}}}) + "\n",
            encoding="utf-8",
        )

        sync_json_mcp(path, {"new": {"command": "echo"}})

        data = self._read(path)
        self.assertEqual(data["other"], {"keep": True})
        # old (no marker) is user-owned and preserved; new is config-managed.
        self.assertEqual(data["mcpServers"]["old"], {})
        self.assertEqual(data["mcpServers"]["new"]["command"], "echo")
        self.assertEqual(
            data["mcpServers"]["new"]["_managed_by"], "ai-coding-kit"
        )

    def test_symlink_target_keys_preserved_and_link_replaced(self) -> None:
        # Real config file the symlink points at, holding non-mcp keys.
        real = self.root / "real_config.json"
        real.write_text(
            json.dumps({"other": {"keep": True}, "mcpServers": {"old": {}}}) + "\n",
            encoding="utf-8",
        )
        link = self.root / "mcp.json"
        link.symlink_to(real)

        sync_json_mcp(link, {"new": {"command": "echo"}})

        # The link path is now a regular file (symlink replaced).
        self.assertFalse(link.is_symlink())
        data = self._read(link)
        # Non-mcpServers keys must survive (this was the bug).
        self.assertEqual(data["other"], {"keep": True})
        self.assertEqual(data["mcpServers"]["old"], {})
        self.assertEqual(data["mcpServers"]["new"]["command"], "echo")
        self.assertEqual(
            data["mcpServers"]["new"]["_managed_by"], "ai-coding-kit"
        )

    def test_broken_symlink_does_not_crash(self) -> None:
        link = self.root / "mcp.json"
        link.symlink_to(self.root / "does_not_exist.json")

        sync_json_mcp(link, {"new": {"command": "echo"}})

        self.assertFalse(link.is_symlink())
        data = self._read(link)
        self.assertEqual(data["mcpServers"]["new"]["command"], "echo")
        self.assertEqual(
            data["mcpServers"]["new"]["_managed_by"], "ai-coding-kit"
        )

    def test_marker_merge_preserves_users_and_prunes_managed(self) -> None:
        """Config updates its own servers, keeps user-added ones, prunes stale ones."""
        path = self.root / "mcp.json"
        path.write_text(
            json.dumps(
                {
                    "mcpServers": {
                        # User-added server (no marker) — must survive untouched.
                        "user-files": {"command": "user-tool"},
                        # Ours from a previous sync but no longer in config — pruned.
                        "stale": {
                            "command": "old-tool",
                            "_managed_by": "ai-coding-kit",
                        },
                    }
                }
            )
            + "\n",
            encoding="utf-8",
        )

        sync_json_mcp(path, {"new": {"command": "echo"}})

        data = self._read(path)
        self.assertEqual(data["mcpServers"]["user-files"], {"command": "user-tool"})
        self.assertNotIn("stale", data["mcpServers"])
        self.assertEqual(data["mcpServers"]["new"]["command"], "echo")
        self.assertEqual(
            data["mcpServers"]["new"]["_managed_by"], "ai-coding-kit"
        )

    def test_same_name_user_owned_is_not_overwritten(self) -> None:
        """Unmarked same-name server stays user-owned; config does not overwrite it."""
        path = self.root / "mcp.json"
        path.write_text(
            json.dumps({"mcpServers": {"sample": {"command": "user-tool"}}}) + "\n",
            encoding="utf-8",
        )

        sync_json_mcp(path, {"sample": {"command": "echo", "args": ["hello"]}})

        data = self._read(path)
        self.assertEqual(data["mcpServers"]["sample"], {"command": "user-tool"})
        self.assertNotIn("_managed_by", data["mcpServers"]["sample"])

    def test_legacy_exact_copy_is_claimed(self) -> None:
        """Unmarked exact copy of the current config is claimed and tagged."""
        path = self.root / "mcp.json"
        path.write_text(
            json.dumps({"mcpServers": {"sample": {"command": "echo"}}}) + "\n",
            encoding="utf-8",
        )

        sync_json_mcp(path, {"sample": {"command": "echo"}})

        data = self._read(path)
        self.assertEqual(data["mcpServers"]["sample"]["command"], "echo")
        self.assertEqual(
            data["mcpServers"]["sample"]["_managed_by"], "ai-coding-kit"
        )

    def test_empty_config_prunes_managed_and_keeps_user(self) -> None:
        """Empty config still runs the merge: marked servers go, unmarked stay."""
        path = self.root / "mcp.json"
        path.write_text(
            json.dumps(
                {
                    "other": {"keep": True},
                    "mcpServers": {
                        "managed": {
                            "command": "old-tool",
                            "_managed_by": "ai-coding-kit",
                        },
                        "user-files": {"command": "user-tool"},
                    },
                }
            )
            + "\n",
            encoding="utf-8",
        )

        sync_json_mcp(path, {})

        data = self._read(path)
        self.assertEqual(data["other"], {"keep": True})
        self.assertNotIn("managed", data["mcpServers"])
        self.assertEqual(data["mcpServers"]["user-files"], {"command": "user-tool"})

    def test_opaque_user_value_is_preserved(self) -> None:
        """Non-dict user values cannot carry a marker and must survive sync."""
        path = self.root / "mcp.json"
        path.write_text(
            json.dumps(
                {"mcpServers": {"user": "opaque", "ok": {"command": "x"}}}
            )
            + "\n",
            encoding="utf-8",
        )

        sync_json_mcp(path, {"ok": {"command": "x"}})

        data = self._read(path)
        self.assertEqual(data["mcpServers"]["user"], "opaque")
        self.assertEqual(data["mcpServers"]["ok"]["command"], "x")
        self.assertEqual(
            data["mcpServers"]["ok"]["_managed_by"], "ai-coding-kit"
        )

    def test_payload_name_field_survives_round_trip(self) -> None:
        """Map identity is the dict key; a payload ``name`` must not be stripped."""
        path = self.root / "mcp.json"
        path.write_text(
            json.dumps(
                {"mcpServers": {"srv": {"command": "x", "name": "display"}}}
            )
            + "\n",
            encoding="utf-8",
        )

        sync_json_mcp(path, {})

        data = self._read(path)
        self.assertEqual(
            data["mcpServers"]["srv"], {"command": "x", "name": "display"}
        )


class MergeManagedDictTests(unittest.TestCase):
    def test_preserves_opaque_and_payload_name(self) -> None:
        merged = merge_managed_dict(
            {"user": "opaque", "ok": {"command": "x"}},
            {"ok": {"command": "x"}},
        )
        self.assertEqual(merged["user"], "opaque")
        self.assertEqual(merged["ok"]["command"], "x")
        self.assertEqual(merged["ok"]["_managed_by"], "ai-coding-kit")

        named = merge_managed_dict(
            {"srv": {"command": "x", "name": "display"}},
            {},
        )
        self.assertEqual(named["srv"], {"command": "x", "name": "display"})

    def test_same_key_opaque_wins_over_config_dict(self) -> None:
        merged = merge_managed_dict(
            {"sample": "opaque"},
            {"sample": {"command": "echo"}},
        )
        self.assertEqual(merged, {"sample": "opaque"})


if __name__ == "__main__":
    unittest.main()
