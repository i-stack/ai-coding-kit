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

from core.common import sync_json_mcp  # noqa: E402


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
        self.assertEqual(data["mcpServers"], {"new": {"command": "echo"}})

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
        self.assertEqual(data["mcpServers"], {"new": {"command": "echo"}})

    def test_broken_symlink_does_not_crash(self) -> None:
        link = self.root / "mcp.json"
        link.symlink_to(self.root / "does_not_exist.json")

        sync_json_mcp(link, {"new": {"command": "echo"}})

        self.assertFalse(link.is_symlink())
        data = self._read(link)
        self.assertEqual(data["mcpServers"], {"new": {"command": "echo"}})


if __name__ == "__main__":
    unittest.main()
