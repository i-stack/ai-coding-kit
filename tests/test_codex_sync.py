import contextlib
import io
import json
import os
import sys
import tempfile
import tomllib
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
    old_env = {k: os.environ.get(k) for k in ("HOME", "CODEX_HOME", "CODEX_CONFIG")}
    old_paths = (common.MCP_DIR, common.PLATFORMS_DIR, common.SECRETS_PATH)
    old_argv = sys.argv[:]
    try:
        os.environ["HOME"] = str(root / "home")
        os.environ["CODEX_HOME"] = str(root / "home" / ".codex")
        os.environ.pop("CODEX_CONFIG", None)
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


class CodexSyncTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.platform_cfg = json.loads((REPO_ROOT / "env" / "platforms" / "codex.json").read_text())
        self._write_json(
            self.root / "env" / "mcp" / "sample.json",
            {
                "name": "sample",
                "type": "stdio",
                "command": "echo",
                "args": ["hello"],
                "platforms": ["codex"],
            },
        )
        self._write_json(
            self.root / "env" / "secrets.json",
            {"codex": {"url": "https://codex.example/v1", "key": "sk-test-value"}},
        )

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _write_json(self, path: Path, data: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=4) + "\n", encoding="utf-8")

    def _run_codex_sync(self, cfg: dict) -> tuple[str, dict]:
        self._write_json(self.root / "env" / "platforms" / "codex.json", cfg)
        (self.root / "home" / ".codex").mkdir(parents=True, exist_ok=True)
        with patched_sync_environment(self.root):
            sys.argv = ["sync_config.py", "--target", "codex"]
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                sync_config.main()
        config_text = (self.root / "home" / ".codex" / "config.toml").read_text(encoding="utf-8")
        return config_text, tomllib.loads(config_text)

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

    def test_model_provider_value_syncs_selector_and_provider_table(self) -> None:
        cfg = dict(self.platform_cfg)
        cfg["enabled"] = True
        cfg["model_provider"] = "dataeyes"

        config_text, parsed = self._run_codex_sync(cfg)

        self.assertIn('model_provider = "dataeyes"', config_text)
        self.assertIn('preferred_auth_method = "apikey"', config_text)
        self.assertEqual(parsed["model_provider"], "dataeyes")
        self.assertEqual(parsed["model_providers"]["dataeyes"]["name"], "dataeyes")
        self.assertEqual(parsed["model_providers"]["dataeyes"]["base_url"], "https://codex.example/v1")

    def test_model_provider_null_syncs_commented_selector_and_provider_table(self) -> None:
        cfg = dict(self.platform_cfg)
        cfg["model_provider"] = None

        config_text, parsed = self._run_codex_sync(cfg)

        self.assertIn("# model_provider", config_text)
        self.assertNotIn("model_provider", parsed)
        self.assertEqual(parsed["model_providers"]["dataeyes"]["name"], "dataeyes")
        self.assertEqual(parsed["model_providers"]["dataeyes"]["base_url"], "https://codex.example/v1")

    def test_model_provider_null_while_enabled_is_commented_not_literal_none(self) -> None:
        # Regression: with enabled=true and no model_provider, the selector must
        # be commented out — never written as `model_provider = "None"`.
        cfg = dict(self.platform_cfg)
        cfg["enabled"] = True
        cfg["model_provider"] = None

        config_text, parsed = self._run_codex_sync(cfg)

        self.assertNotIn('model_provider = "None"', config_text)
        self.assertIn("# model_provider", config_text)
        self.assertNotIn("model_provider", parsed)

    def test_model_provider_empty_syncs_commented_selector_and_provider_table(self) -> None:
        cfg = dict(self.platform_cfg)
        cfg["model_provider"] = ""

        config_text, parsed = self._run_codex_sync(cfg)

        self.assertIn("# model_provider", config_text)
        self.assertNotIn("model_provider", parsed)
        self.assertEqual(parsed["model_providers"]["dataeyes"]["name"], "dataeyes")
        self.assertEqual(parsed["model_providers"]["dataeyes"]["base_url"], "https://codex.example/v1")

    def test_export_env_to_zshrc_replaces_missing_dataeyes_key_with_managed_block(self) -> None:
        cfg = dict(self.platform_cfg)
        zshrc = self.root / "home" / ".zshrc"
        zshrc.parent.mkdir(parents=True, exist_ok=True)
        zshrc.write_text("export OTHER=value\n", encoding="utf-8")

        self._run_codex_sync(cfg)

        zshrc_text = zshrc.read_text(encoding="utf-8")
        self.assertEqual(zshrc_text.count("DATAEYES_API_KEY"), 1)
        self.assertIn("# BEGIN CODEX ENV SYNC (from env/platforms/codex.json)\n", zshrc_text)
        self.assertIn("export DATAEYES_API_KEY=sk-test-value\n", zshrc_text)
        self.assertTrue(zshrc_text.endswith("# END CODEX ENV SYNC\n"))

    def test_export_env_to_zshrc_replaces_existing_managed_dataeyes_key(self) -> None:
        cfg = dict(self.platform_cfg)
        zshrc = self.root / "home" / ".zshrc"
        zshrc.parent.mkdir(parents=True, exist_ok=True)
        zshrc.write_text(
            "before\n"
            "# BEGIN CODEX ENV SYNC (from env/platforms/codex.json)\n"
            "export DATAEYES_API_KEY=old-value\n"
            "# END CODEX ENV SYNC\n"
            "after\n",
            encoding="utf-8",
        )

        self._run_codex_sync(cfg)

        zshrc_text = zshrc.read_text(encoding="utf-8")
        self.assertNotIn("old-value", zshrc_text)
        self.assertEqual(zshrc_text.count("DATAEYES_API_KEY"), 1)
        self.assertIn("export DATAEYES_API_KEY=sk-test-value\n", zshrc_text)
        self.assertTrue(zshrc_text.startswith("before\n"))
        self.assertTrue(zshrc_text.endswith("after\n"))

    def test_missing_codex_root_skips_sync_and_env_export(self) -> None:
        cfg = dict(self.platform_cfg)
        zshrc = self.root / "home" / ".zshrc"
        zshrc.parent.mkdir(parents=True, exist_ok=True)
        zshrc.write_text("export OTHER=value\n", encoding="utf-8")
        self._write_json(self.root / "env" / "platforms" / "codex.json", cfg)

        with patched_sync_environment(self.root):
            sys.argv = ["sync_config.py", "--target", "codex"]
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                sync_config.main()

        self.assertFalse((self.root / "home" / ".codex").exists())
        self.assertEqual(zshrc.read_text(encoding="utf-8"), "export OTHER=value\n")

    def test_missing_xcode_path_skips_xcode_codex_target_only(self) -> None:
        config_text, parsed = self._run_codex_sync(self.platform_cfg)

        self.assertIn("mcp_servers", parsed)
        self.assertIn("sample", parsed["mcp_servers"])
        self.assertIn("# BEGIN MCP SYNC", config_text)
        self.assertFalse((self.root / "home" / ".codex" / "mcp.generated.toml").exists())
        self.assertFalse(
            (
                self.root
                / "home"
                / "Library"
                / "Developer"
                / "Xcode"
                / "CodingAssistant"
                / "codex"
            ).exists()
        )

    def test_xcode_codex_sync_uses_config_toml_without_generated_toml(self) -> None:
        xcode_root = self.root / "home" / "Library" / "Developer" / "Xcode" / "CodingAssistant"
        xcode_root.mkdir(parents=True, exist_ok=True)

        self._run_codex_sync(self.platform_cfg)

        xcode_codex = xcode_root / "codex"
        config_path = xcode_codex / "config.toml"
        self.assertTrue(config_path.exists())
        self.assertFalse((xcode_codex / "mcp.generated.toml").exists())
        parsed = tomllib.loads(config_path.read_text(encoding="utf-8"))
        self.assertIn("sample", parsed["mcp_servers"])

    def test_codex_json_properties_are_mapped_or_excluded_as_expected(self) -> None:
        config_text, parsed = self._run_codex_sync(self.platform_cfg)

        covered_keys = {
            "model",
            "personality",
            "enabled",
            "model_provider",
            "model_reasoning_effort",
            "model_verbosity",
            "model_reasoning_summary",
            "plan_mode_reasoning_effort",
            "hide_agent_reasoning",
            "sandbox_mode",
            "approval_policy",
            "allow_login_shell",
            "default_permissions",
            "web_search",
            "file_opener",
            "project_doc_max_bytes",
            "project_doc_fallback_filenames",
            "model_providers",
            "history",
            "sandbox_workspace_write",
            "tools",
            "shell_environment_policy",
            "tui",
            "agents",
            "memories",
            "analytics",
            "feedback",
            "features",
            "projects",
            "export_env_to_zshrc",
            "preamble",
        }
        self.assertEqual(set(self.platform_cfg), covered_keys)

        expected_root = {
            "model": "gpt-5.5",
            "personality": "pragmatic",
            "model_reasoning_effort": "medium",
            "model_verbosity": "medium",
            "model_reasoning_summary": "auto",
            "plan_mode_reasoning_effort": "medium",
            "sandbox_mode": "workspace-write",
            "approval_policy": "on-request",
            "allow_login_shell": True,
            "default_permissions": ":workspace",
            "project_doc_max_bytes": 32768,
            "project_doc_fallback_filenames": ["CODEBUDDY.md", "CLAUDE.md"],
        }
        for key, expected in expected_root.items():
            self.assertEqual(parsed[key], expected, key)

        self.assert_nested_equal(
            parsed,
            {
                "sandbox_workspace_write": {
                    "network_access": True,
                    "writable_roots": [],
                    "exclude_tmpdir_env_var": False,
                    "exclude_slash_tmp": False,
                },
                "features": {
                    "skills": True,
                    "multi_agent": True,
                    "hooks": True,
                    "shell_snapshot": True,
                    "unified_exec": True,
                    "shell_tool": True,
                    "memories": True,
                    "personality": True,
                    "fast_mode": True,
                    "enable_request_compression": True,
                    "skill_mcp_dependency_install": True,
                },
            },
            "parsed",
        )
        self.assertEqual(parsed["model_providers"]["dataeyes"]["base_url"], "https://codex.example/v1")
        self.assertEqual(parsed["model_providers"]["dataeyes"]["env_key"], "DATAEYES_API_KEY")
        self.assertEqual(parsed["model_providers"]["dataeyes"]["wire_api"], "responses")

        for host_specific_key in (
            "hide_agent_reasoning",
            "web_search",
            "file_opener",
            "history",
            "tools",
            "shell_environment_policy",
            "tui",
            "agents",
            "memories",
            "analytics",
            "feedback",
            "projects",
            "export_env_to_zshrc",
        ):
            self.assertNotIn(host_specific_key, parsed, host_specific_key)
            self.assertNotIn(f"[{host_specific_key}]", config_text)


if __name__ == "__main__":
    unittest.main()
