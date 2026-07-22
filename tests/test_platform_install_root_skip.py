import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SYNC_DIR = REPO_ROOT / "sync"
if str(SYNC_DIR) not in sys.path:
    sys.path.insert(0, str(SYNC_DIR))

from cli import sync_config  # noqa: E402
from core import common  # noqa: E402
from core import paths as _paths  # noqa: E402


@contextlib.contextmanager
def patched_sync_environment(root: Path):
    old_env = {k: os.environ.get(k) for k in ("HOME",)}
    old_common = (common.MCP_DIR, common.PLATFORMS_DIR, common.SECRETS_PATH)
    old_paths_sp = _paths.SECRETS_PATH
    old_overrides = _paths._PATH_OVERRIDES
    old_argv = sys.argv[:]
    try:
        os.environ["HOME"] = str(root / "home")
        common.MCP_DIR = root / "env" / "mcp"
        common.PLATFORMS_DIR = root / "env" / "platforms"
        common.SECRETS_PATH = root / "env" / "secrets.json"
        # Isolate platform install-root resolution: point paths at the same
        # patched secrets and drop any module-level cache so a developer's
        # local env/secrets.json overrides can't leak into this test.
        _paths.SECRETS_PATH = root / "env" / "secrets.json"
        _paths._PATH_OVERRIDES = None
        yield
    finally:
        for key, value in old_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        common.MCP_DIR, common.PLATFORMS_DIR, common.SECRETS_PATH = old_common
        _paths.SECRETS_PATH = old_paths_sp
        _paths._PATH_OVERRIDES = old_overrides
        sys.argv = old_argv


class PlatformInstallRootSkipTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.home = self.root / "home"
        self._write_json(
            self.root / "env" / "mcp" / "sample.json",
            {
                "name": "sample",
                "type": "stdio",
                "command": "echo",
                "args": ["hello"],
            },
        )
        self._write_json(self.root / "env" / "secrets.json", {})

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _write_json(self, path: Path, data: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=4) + "\n", encoding="utf-8")

    def _run_target(self, target: str) -> str:
        with patched_sync_environment(self.root):
            sys.argv = ["sync_config.py", "--target", target]
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(io.StringIO()):
                sync_config.main()
            return stdout.getvalue()

    def test_missing_cline_root_skips_all_cline_outputs(self) -> None:
        self._write_json(
            self.root / "env" / "platforms" / "cline.json",
            {
                "globalState": {"apiProvider": "gemini", "geminiBaseUrl": "https://example.test"},
                "secrets": {"geminiApiKey": "sk-test"},
            },
        )
        vscode_mcp = (
            self.home
            / "Library/Application Support/Code/User/globalStorage/"
            / "saoudrizwan.claude-dev/settings/cline_mcp_settings.json"
        )
        self._write_json(vscode_mcp, {"mcpServers": {"keep": {"command": "keep"}}})

        output = self._run_target("cline")

        self.assertIn("Platform 'cline' root not found", output)
        self.assertFalse((self.home / ".cline").exists())
        self.assertEqual(
            json.loads(vscode_mcp.read_text(encoding="utf-8")),
            {"mcpServers": {"keep": {"command": "keep"}}},
        )

    def test_missing_continue_root_skips_continue_config(self) -> None:
        self._write_json(
            self.root / "env" / "platforms" / "continue.json",
            {
                "path": str(self.root / "external-continue.yaml"),
                "models": [{"name": "managed"}],
            },
        )
        target = self.root / "external-continue.yaml"
        target.write_text("name: existing\n", encoding="utf-8")

        output = self._run_target("continue")

        self.assertIn("Platform 'continue' root not found", output)
        self.assertFalse((self.home / ".continue").exists())
        self.assertEqual(target.read_text(encoding="utf-8"), "name: existing\n")

    def test_missing_cursor_root_skips_cursor_config(self) -> None:
        # Regression: cursor must participate in the "skip if not installed"
        # contract via platform_install_root(), otherwise an overridden (or
        # default) cursor root would be created instead of skipped.
        self._write_json(
            self.root / "env" / "platforms" / "cursor.json",
            {"mcp_target": str(self.home / ".cursor" / "mcp.json")},
        )

        output = self._run_target("cursor")

        self.assertIn("Platform 'cursor' root not found", output)
        self.assertFalse((self.home / ".cursor").exists())

    def test_existing_continue_root_creates_missing_config_yaml(self) -> None:
        (self.home / ".continue").mkdir(parents=True, exist_ok=True)
        self._write_json(
            self.root / "env" / "platforms" / "continue.json",
            {
                "models": [
                    {
                        "name": "managed-model",
                        "provider": "openai",
                        "model": "managed-model",
                    }
                ],
            },
        )
        target = self.home / ".continue" / "config.yaml"

        output = self._run_target("continue")

        self.assertIn("creating it", output)
        self.assertTrue(target.exists())
        text = target.read_text(encoding="utf-8")
        self.assertIn("mcpServers:", text)
        self.assertIn("- name: sample", text)
        self.assertIn("command: echo", text)
        self.assertIn("models:", text)
        self.assertIn('- name: "managed-model"', text)


if __name__ == "__main__":
    unittest.main()
