import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from collections.abc import Mapping
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SYNC_DIR = REPO_ROOT / "sync"
if str(SYNC_DIR) not in sys.path:
    sys.path.insert(0, str(SYNC_DIR))

from cli import sync_config  # noqa: E402
from core import common  # noqa: E402


@contextlib.contextmanager
def patched_sync_environment(root: Path):
    """Redirect HOME and module-level paths for isolated Gemini sync tests."""
    old_env = {k: os.environ.get(k) for k in ("HOME",)}
    old_paths = (common.MCP_DIR, common.PLATFORMS_DIR, common.SECRETS_PATH)
    old_argv = sys.argv[:]
    try:
        os.environ["HOME"] = str(root / "home")
        common.MCP_DIR = root / "env" / "mcp"
        common.PLATFORMS_DIR = root / "env" / "platforms"
        common.SECRETS_PATH = root / "env" / "secrets.json"
        yield
    finally:
        for key, value in old_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        common.MCP_DIR, common.PLATFORMS_DIR, common.SECRETS_PATH = old_paths
        sys.argv = old_argv


class GeminiSyncTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "home" / ".gemini").mkdir(parents=True, exist_ok=True)
        self.platform_cfg = json.loads(
            (REPO_ROOT / "env" / "platforms" / "gemini.json").read_text()
        )
        self._write_json(
            self.root / "env" / "mcp" / "sample.json",
            {
                "name": "sample",
                "type": "stdio",
                "command": "echo",
                "args": ["hello"],
                "platforms": ["gemini"],
            },
        )
        self._write_json(
            self.root / "env" / "secrets.json",
            {"gemini": {"url": "https://generativelanguage.googleapis.com", "key": "sk-test-gemini"}},
        )

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _write_json(self, path: Path, data: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=4) + "\n", encoding="utf-8")

    def _read_json(self, path: Path) -> dict:
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))

    def _run_gemini_sync(self, cfg: dict | None = None) -> dict:
        """Run Gemini sync and return the parsed settings.json content."""
        target_cfg = cfg if cfg is not None else self.platform_cfg
        self._write_json(self.root / "env" / "platforms" / "gemini.json", target_cfg)
        with patched_sync_environment(self.root):
            sys.argv = ["sync_config.py", "--target", "gemini"]
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                sync_config.main()
        return self._read_json(self.root / "home" / ".gemini" / "settings.json")

    def assert_nested_equal(self, data: Mapping, expected: Mapping, path: str) -> None:
        for key, expected_value in expected.items():
            current_path = f"{path}.{key}"
            self.assertIn(key, data, current_path)
            actual_value = data[key]
            if isinstance(expected_value, Mapping):
                self.assertIsInstance(actual_value, Mapping, current_path)
                self.assert_nested_equal(actual_value, expected_value, current_path)
            else:
                self.assertEqual(actual_value, expected_value, current_path)

    # ── MCP servers ──────────────────────────────────────────────────────────

    def test_mcp_servers_synced_to_settings_json(self) -> None:
        settings = self._run_gemini_sync()

        self.assertIn("mcpServers", settings)
        self.assertIn("sample", settings["mcpServers"])
        self.assertEqual(settings["mcpServers"]["sample"]["command"], "echo")
        self.assertEqual(settings["mcpServers"]["sample"]["args"], ["hello"])

    # ── Managed settings ─────────────────────────────────────────────────────

    def test_settings_json_contains_managed_keys(self) -> None:
        settings = self._run_gemini_sync()

        self.assert_nested_equal(
            settings,
            {
                "model": {
                    "name": "gemini-3.5-flash",
                    "maxSessionTurns": -1,
                    "compressionThreshold": 0.5,
                    "skipNextSpeakerCheck": True,
                },
            },
            "settings",
        )
        self.assertEqual(settings["context"]["fileName"], "GEMINI.md")
        self.assertTrue(settings["context"]["includeDirectoryTree"])
        self.assertEqual(settings["context"]["importFormat"], "tree")
        self.assertTrue(settings["tools"]["useRipgrep"])
        self.assertEqual(settings["tools"]["sandbox"], "sandbox-exec")
        self.assertTrue(settings["tools"]["sandboxNetworkAccess"])
        self.assertTrue(settings["tools"]["shell"]["enableInteractiveShell"])
        self.assertTrue(settings["skills"]["enabled"])
        self.assertTrue(settings["hooksConfig"]["enabled"])
        self.assertTrue(settings["security"]["folderTrust"]["enabled"])
        self.assertTrue(settings["experimental"]["directWebFetch"])
        self.assertTrue(settings["experimental"]["enableAgents"])
        self.assertTrue(settings["experimental"]["autoMemory"])
        self.assertTrue(settings["experimental"]["contextManagement"])

    def test_settings_json_excludes_internal_keys(self) -> None:
        settings = self._run_gemini_sync()

        # Internal keys must NOT leak into settings.json
        self.assertNotIn("_comment", settings)
        self.assertNotIn("export_env_to_zshrc", settings)

    def test_settings_json_preserves_existing_user_keys(self) -> None:
        """User-added keys outside the managed set are preserved after sync."""
        settings_path = self.root / "home" / ".gemini" / "settings.json"
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        settings_path.write_text(
            json.dumps(
                {
                    "ui": {"theme": "dark", "hideBanner": True},
                    "general": {"preferredEditor": "cursor"},
                },
                indent=4,
            )
            + "\n",
            encoding="utf-8",
        )

        settings = self._run_gemini_sync()

        self.assertEqual(settings["ui"]["theme"], "dark")
        self.assertTrue(settings["ui"]["hideBanner"])
        self.assertEqual(settings["general"]["preferredEditor"], "cursor")
        # Managed keys should also be present
        self.assertEqual(settings["model"]["name"], "gemini-3.5-flash")
        self.assertIn("mcpServers", settings)

    def test_settings_json_deep_merges_nested_user_keys(self) -> None:
        """Nested dicts are recursively merged: user sub-keys preserved, managed overrides applied."""
        settings_path = self.root / "home" / ".gemini" / "settings.json"
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        settings_path.write_text(
            json.dumps(
                {
                    "model": {"maxSessionTurns": 50, "customUserField": "keep-me"},
                    "context": {
                        "fileFiltering": {
                            "respectGitIgnore": False,
                            "customUserFilter": "keep-me",
                        }
                    },
                    "tools": {
                        "shell": {"customShellSetting": "keep-me"},
                        "customToolSetting": True,
                    },
                },
                indent=4,
            )
            + "\n",
            encoding="utf-8",
        )

        settings = self._run_gemini_sync()

        # Managed value overrides existing
        self.assertEqual(settings["model"]["maxSessionTurns"], -1)
        # User custom fields preserved
        self.assertEqual(settings["model"]["customUserField"], "keep-me")
        # User custom top-level sub-keys preserved
        self.assertTrue(settings["tools"]["customToolSetting"])
        # User custom nested sub-keys preserved
        self.assertEqual(settings["context"]["fileFiltering"]["customUserFilter"], "keep-me")
        self.assertEqual(settings["tools"]["shell"]["customShellSetting"], "keep-me")
        # Managed nested values still override existing values at the same path
        self.assertTrue(settings["context"]["fileFiltering"]["respectGitIgnore"])

    # ── Xcode target ─────────────────────────────────────────────────────────

    def test_xcode_target_receives_same_settings(self) -> None:
        xcode_root = self.root / "home" / "Library" / "Developer" / "Xcode" / "CodingAssistant"
        xcode_root.mkdir(parents=True, exist_ok=True)
        xc_settings_path = (
            xcode_root / "gemini" / "settings.json"
        )

        self._run_gemini_sync()

        self.assertTrue(xc_settings_path.exists(), "Xcode Gemini settings.json was not created")

        native = self._read_json(self.root / "home" / ".gemini" / "settings.json")
        xcode = self._read_json(xc_settings_path)
        self.assertEqual(native, xcode)

    def test_xcode_target_preserves_existing_user_keys(self) -> None:
        xcode_root = self.root / "home" / "Library" / "Developer" / "Xcode" / "CodingAssistant"
        xcode_root.mkdir(parents=True, exist_ok=True)
        xc_settings_path = (
            xcode_root / "gemini" / "settings.json"
        )
        self._write_json(
            xc_settings_path,
            {
                "ui": {"theme": "dark"},
                "context": {"fileFiltering": {"customXcodeFilter": "keep-me"}},
            },
        )

        xcode = self._run_gemini_sync()
        xcode = self._read_json(xc_settings_path)

        self.assertEqual(xcode["ui"]["theme"], "dark")
        self.assertEqual(xcode["context"]["fileFiltering"]["customXcodeFilter"], "keep-me")
        self.assertTrue(xcode["context"]["fileFiltering"]["respectGitIgnore"])
        self.assertIn("mcpServers", xcode)

    def test_missing_xcode_path_skips_xcode_gemini_target_only(self) -> None:
        native = self._run_gemini_sync()

        self.assertEqual(native["model"]["name"], "gemini-3.5-flash")
        self.assertIn("mcpServers", native)
        self.assertFalse(
            (
                self.root
                / "home"
                / "Library"
                / "Developer"
                / "Xcode"
                / "CodingAssistant"
            ).exists()
        )

    # ── zshrc env export ─────────────────────────────────────────────────────

    def test_export_env_to_zshrc_creates_managed_block(self) -> None:
        cfg = dict(self.platform_cfg)
        cfg["export_env_to_zshrc"] = {
            "GEMINI_API_KEY": "sk-test-gemini",
            "GOOGLE_GEMINI_BASE_URL": "https://generativelanguage.googleapis.com",
            "GEMINI_MODEL": "gemini-3.5-flash",
        }

        self._run_gemini_sync(cfg)

        zshrc = self.root / "home" / ".zshrc"
        self.assertTrue(zshrc.exists())
        zshrc_text = zshrc.read_text(encoding="utf-8")

        self.assertIn("# BEGIN GEMINI ENV SYNC (from env/platforms/gemini.json)", zshrc_text)
        self.assertIn("export GEMINI_API_KEY=sk-test-gemini", zshrc_text)
        self.assertIn("export GOOGLE_GEMINI_BASE_URL=https://generativelanguage.googleapis.com", zshrc_text)
        self.assertIn("export GEMINI_MODEL=gemini-3.5-flash", zshrc_text)
        self.assertIn("# END GEMINI ENV SYNC", zshrc_text)

    def test_export_env_to_zshrc_replaces_existing_block(self) -> None:
        zshrc = self.root / "home" / ".zshrc"
        zshrc.parent.mkdir(parents=True, exist_ok=True)
        zshrc.write_text(
            "before\n"
            "# BEGIN GEMINI ENV SYNC (from env/platforms/gemini.json)\n"
            "export GEMINI_API_KEY=old-key\n"
            "export GEMINI_MODEL=old-model\n"
            "# END GEMINI ENV SYNC\n"
            "after\n",
            encoding="utf-8",
        )

        cfg = dict(self.platform_cfg)
        cfg["export_env_to_zshrc"] = {
            "GEMINI_API_KEY": "sk-test-gemini",
            "GOOGLE_GEMINI_BASE_URL": "https://generativelanguage.googleapis.com",
            "GEMINI_MODEL": "gemini-3.5-flash",
        }
        self._run_gemini_sync(cfg)

        zshrc_text = zshrc.read_text(encoding="utf-8")
        self.assertTrue(zshrc_text.startswith("before\n"))
        self.assertTrue(zshrc_text.endswith("after\n"))
        self.assertNotIn("old-key", zshrc_text)
        self.assertNotIn("old-model", zshrc_text)
        self.assertIn("export GEMINI_API_KEY=sk-test-gemini", zshrc_text)
        self.assertIn("export GEMINI_MODEL=gemini-3.5-flash", zshrc_text)
        # Block should appear exactly once
        self.assertEqual(zshrc_text.count("# BEGIN GEMINI ENV SYNC"), 1)
        self.assertEqual(zshrc_text.count("# END GEMINI ENV SYNC"), 1)

    def test_missing_gemini_root_skips_sync_and_env_export(self) -> None:
        (self.root / "home" / ".gemini").rmdir()
        zshrc = self.root / "home" / ".zshrc"
        zshrc.parent.mkdir(parents=True, exist_ok=True)
        zshrc.write_text("export OTHER=value\n", encoding="utf-8")

        cfg = dict(self.platform_cfg)
        cfg["export_env_to_zshrc"] = {
            "GEMINI_API_KEY": "sk-test-gemini",
            "GOOGLE_GEMINI_BASE_URL": "https://generativelanguage.googleapis.com",
            "GEMINI_MODEL": "gemini-3.5-flash",
        }
        self._write_json(self.root / "env" / "platforms" / "gemini.json", cfg)

        with patched_sync_environment(self.root):
            sys.argv = ["sync_config.py", "--target", "gemini"]
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                sync_config.main()

        self.assertFalse((self.root / "home" / ".gemini").exists())
        self.assertFalse(
            (
                self.root
                / "home"
                / "Library"
                / "Developer"
                / "Xcode"
                / "CodingAssistant"
                / "gemini"
            ).exists()
        )
        self.assertEqual(zshrc.read_text(encoding="utf-8"), "export OTHER=value\n")

    # ── Property coverage ────────────────────────────────────────────────────

    def test_gemini_json_properties_are_mapped_or_excluded_as_expected(self) -> None:
        """Every key in gemini.json must be either in settings.json or in _INTERNAL_SKIP."""
        settings = self._run_gemini_sync()

        covered_keys = {
            "model",
            "context",
            "tools",
            "skills",
            "hooksConfig",
            "security",
            "experimental",
            "contextManagement",
            "export_env_to_zshrc",
            "_comment",
            "preamble",
        }
        self.assertEqual(set(self.platform_cfg), covered_keys)

        # Keys that should appear in settings.json
        managed_keys = covered_keys - {"export_env_to_zshrc", "_comment", "preamble"}
        for key in managed_keys:
            self.assertIn(key, settings, f"Managed key '{key}' missing from settings.json")

        # Internal keys that should NOT appear
        self.assertNotIn("_comment", settings)
        self.assertNotIn("export_env_to_zshrc", settings)
        self.assertNotIn("preamble", settings)

    # ── Sidecar recovery ─────────────────────────────────────────────────────

    def test_dropped_managed_key_is_pruned_on_next_sync(self) -> None:
        """A managed key removed from gemini.json is pruned on the next sync."""
        cfg_with = dict(self.platform_cfg)
        cfg_with["extraManagedKey"] = {"foo": "bar"}
        settings = self._run_gemini_sync(cfg_with)
        self.assertIn("extraManagedKey", settings)

        settings = self._run_gemini_sync(dict(self.platform_cfg))
        self.assertNotIn("extraManagedKey", settings)
        sidecar = self._read_json(
            self.root / "home" / ".gemini" / ".managed_settings_keys.json"
        )
        self.assertNotIn("extraManagedKey", sidecar["managedKeys"])

    # ── Edge cases ───────────────────────────────────────────────────────────

    def test_empty_mcp_servers_does_not_break(self) -> None:
        """Sync with no MCP servers (empty mcp/ dir) exits gracefully without crash."""
        # Remove the MCP server we wrote in setUp
        mcp_dir = self.root / "env" / "mcp"
        for f in mcp_dir.glob("*.json"):
            f.unlink()

        # main() returns early when mcp_all is empty — no crash, no settings.json
        target_cfg = self.platform_cfg
        self._write_json(self.root / "env" / "platforms" / "gemini.json", target_cfg)
        with patched_sync_environment(self.root):
            sys.argv = ["sync_config.py", "--target", "gemini"]
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                sync_config.main()

        # main() returned early — no crash is the pass condition
        self.assertTrue(True)

    def test_settings_json_not_found_graceful(self) -> None:
        """When ~/.gemini/settings.json doesn't exist, sync creates it."""
        settings = self._run_gemini_sync()

        self.assertIn("model", settings)
        self.assertIn("mcpServers", settings)

    def test_no_export_env_to_zshrc_skips_zshrc(self) -> None:
        """When export_env_to_zshrc is absent/empty, zshrc is not touched."""
        cfg = dict(self.platform_cfg)
        del cfg["export_env_to_zshrc"]

        self._run_gemini_sync(cfg)

        zshrc = self.root / "home" / ".zshrc"
        self.assertFalse(zshrc.exists(), "zshrc should not be created without export_env_to_zshrc")


if __name__ == "__main__":
    unittest.main()
