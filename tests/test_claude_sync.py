import contextlib
import io
import json
import os
import stat
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
from platforms import claude as claude_module  # noqa: E402


@contextlib.contextmanager
def patched_sync_environment(root: Path):
    """Redirect HOME and common module paths to an isolated test root."""
    import core.paths as _paths
    old_env = {k: os.environ.get(k) for k in ("HOME",)}
    old_paths = (common.MCP_DIR, common.PLATFORMS_DIR, common.SECRETS_PATH)
    old_paths_cfg = _paths.CONFIG_PATH
    old_overrides = _paths._PATH_OVERRIDES
    old_argv = sys.argv[:]
    try:
        os.environ["HOME"] = str(root / "home")
        common.MCP_DIR = root / "env" / "mcp"
        common.PLATFORMS_DIR = root / "env" / "platforms"
        common.SECRETS_PATH = root / "env" / "secrets.json"
        # Isolate path overrides so a developer's local env/config.json
        # can't leak into this test (empty config => default paths).
        _paths.CONFIG_PATH = root / "env" / "config.json"
        _paths._PATH_OVERRIDES = None
        yield
    finally:
        for key, value in old_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        common.MCP_DIR, common.PLATFORMS_DIR, common.SECRETS_PATH = old_paths
        _paths.CONFIG_PATH = old_paths_cfg
        _paths._PATH_OVERRIDES = old_overrides
        sys.argv = old_argv


def _run_claude_sync(root: Path, cfg: dict) -> None:
    """Run sync_config --target claude within the patched environment."""
    # Write platform config and required secrets
    (root / "env" / "platforms").mkdir(parents=True, exist_ok=True)
    (root / "env" / "platforms" / "claude.json").write_text(
        json.dumps(cfg, indent=4) + "\n", encoding="utf-8"
    )
    with patched_sync_environment(root):
        sys.argv = ["sync_config.py", "--target", "claude"]
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            sync_config.main()


class ClaudeSyncTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.home = self.root / "home"
        (self.home / ".claude").mkdir(parents=True, exist_ok=True)
        self.platform_cfg = json.loads(
            (REPO_ROOT / "env" / "platforms" / "claude.json").read_text()
        )
        # api.enabled is a user-configurable local toggle, not a fixed schema
        # value — pin the fixture baseline to enabled=True so tests don't
        # silently inherit whatever value happens to be committed in
        # env/platforms/claude.json. Tests that need the disabled path set
        # cfg["api"] = {"enabled": False} explicitly.
        self.platform_cfg["api"] = {"enabled": True}

        # Seed env/mcp/ with a sample server
        self._write_json(
            self.root / "env" / "mcp" / "sample.json",
            {
                "name": "sample",
                "type": "stdio",
                "command": "echo",
                "args": ["hello"],
                "platforms": ["claude"],
            },
        )
        # Seed secrets for env var resolution
        self._write_json(
            self.root / "env" / "secrets.json",
            {
                "claude": {
                    "token": "sk-ant-test-token",
                    "url": "https://claude.example/v1",
                }
            },
        )

        # Ensure repo hooks/ directory exists for hook script install tests
        self._repo_hooks_dir = REPO_ROOT / "hooks"
        if not self._repo_hooks_dir.exists():
            self._repo_hooks_dir.mkdir(parents=True, exist_ok=True)
        # Ensure at least one hook script exists
        (self._repo_hooks_dir / "xmcp-init.sh").touch()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    # ── helpers ────────────────────────────────────────────────────────────────

    def _write_json(self, path: Path, data: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=4) + "\n", encoding="utf-8")

    def _read_json(self, path: Path) -> dict:
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))

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

    # ── MCP servers sync ───────────────────────────────────────────────────────

    def test_mcp_servers_synced_to_claude_json(self) -> None:
        """~/.claude.json should contain the filtered MCP servers."""
        cfg = dict(self.platform_cfg)
        cfg["api"] = {"enabled": False}
        _run_claude_sync(self.root, cfg)

        data = self._read_json(self.home / ".claude.json")
        self.assertIn("mcpServers", data)
        self.assertIn("sample", data["mcpServers"])
        self.assertEqual(data["mcpServers"]["sample"]["command"], "echo")
        self.assertEqual(data["mcpServers"]["sample"]["args"], ["hello"])

    def test_claude_json_preserves_existing_top_level_keys(self) -> None:
        """Existing top-level keys in ~/.claude.json must survive the sync."""
        (self.home / ".claude.json").parent.mkdir(parents=True, exist_ok=True)
        self._write_json(
            self.home / ".claude.json",
            {"mcpServers": {}, "autoConnectIde": True, "customKey": "keep-me"},
        )

        cfg = dict(self.platform_cfg)
        cfg["api"] = {"enabled": False}
        _run_claude_sync(self.root, cfg)

        data = self._read_json(self.home / ".claude.json")
        self.assertTrue(data.get("autoConnectIde"))
        self.assertEqual(data.get("customKey"), "keep-me")
        self.assertIn("sample", data["mcpServers"])

    def test_claude_config_json_created_with_primary_api_key_self(self) -> None:
        """~/.claude/config.json should be created with primaryApiKey=self when API is enabled."""
        cfg = dict(self.platform_cfg)
        cfg["api"] = {"enabled": True}
        _run_claude_sync(self.root, cfg)

        config = self._read_json(self.home / ".claude" / "config.json")
        self.assertEqual(config["primaryApiKey"], "self")

    def test_claude_config_json_preserves_existing_keys(self) -> None:
        """Existing ~/.claude/config.json keys should survive API-enabled sync."""
        self._write_json(
            self.home / ".claude" / "config.json",
            {"primaryApiKey": "login", "custom": {"keep": True}},
        )

        cfg = dict(self.platform_cfg)
        cfg["api"] = {"enabled": True}
        _run_claude_sync(self.root, cfg)

        config = self._read_json(self.home / ".claude" / "config.json")
        self.assertEqual(config["primaryApiKey"], "self")
        self.assertEqual(config["custom"], {"keep": True})

    def test_api_disabled_cleans_primary_api_key_self(self) -> None:
        """api.enabled=false means API sync is disabled and old primaryApiKey=self is cleaned."""
        self._write_json(
            self.home / ".claude" / "config.json",
            {"primaryApiKey": "self", "custom": {"keep": True}},
        )

        cfg = dict(self.platform_cfg)
        cfg["api"] = {"enabled": False}
        _run_claude_sync(self.root, cfg)

        config = self._read_json(self.home / ".claude" / "config.json")
        self.assertNotIn("primaryApiKey", config)
        self.assertEqual(config["custom"], {"keep": True})

    def test_api_disabled_preserves_non_self_primary_api_key(self) -> None:
        """api.enabled=false must not remove a primaryApiKey value not owned by this syncer."""
        self._write_json(
            self.home / ".claude" / "config.json",
            {"primaryApiKey": "login", "custom": {"keep": True}},
        )

        cfg = dict(self.platform_cfg)
        cfg["api"] = {"enabled": False}
        _run_claude_sync(self.root, cfg)

        config = self._read_json(self.home / ".claude" / "config.json")
        self.assertEqual(config["primaryApiKey"], "login")
        self.assertEqual(config["custom"], {"keep": True})

    # ── settings.json team-shared settings ───────────────────────────────────────

    def test_settings_json_does_not_receive_platform_preferences_by_default(self) -> None:
        """claude.json no longer pushes team-shared platform preferences by default."""
        cfg = dict(self.platform_cfg)
        cfg["api"] = {"enabled": False}
        _run_claude_sync(self.root, cfg)

        settings = self._read_json(self.home / ".claude" / "settings.json")

        for key in ("model", "effortLevel", "alwaysThinkingEnabled", "permissions"):
            self.assertNotIn(key, settings)

    def test_settings_json_excludes_host_specific_keys(self) -> None:
        """settings.json must not receive host-specific keys from claude.json."""
        cfg = dict(self.platform_cfg)
        cfg["api"] = {"enabled": False}
        _run_claude_sync(self.root, cfg)

        settings = self._read_json(self.home / ".claude" / "settings.json")

        # Enforce that NO host-specific key is introduced by platform config sync
        for host_key in claude_module._HOST_SKIP:
            self.assertNotIn(
                host_key,
                settings,
                f"Host-specific key '{host_key}' leaked into settings.json",
            )

    def test_settings_json_excludes_internal_keys(self) -> None:
        """Internal-only keys must not appear in settings.json."""
        cfg = dict(self.platform_cfg)
        cfg["api"] = {"enabled": False}
        _run_claude_sync(self.root, cfg)

        settings = self._read_json(self.home / ".claude" / "settings.json")

        for excluded in ("_comment", "_hostSettings", "export_env_to_zshrc"):
            self.assertNotIn(
                excluded, settings, f"Key '{excluded}' should not be in settings.json"
            )

    # ── Sidecar recovery (prune managed keys on config drop) ───────────────────

    def test_dropped_managed_key_is_pruned_on_next_sync(self) -> None:
        """A managed key removed from claude.json is pruned on the next sync."""
        # First sync with an extra team-shared key
        cfg_with_extra = dict(self.platform_cfg)
        cfg_with_extra["extraManagedKey"] = "value"
        _run_claude_sync(self.root, cfg_with_extra)

        settings = self._read_json(self.home / ".claude" / "settings.json")
        self.assertEqual(settings["extraManagedKey"], "value")

        # Second sync without the extra key -> it must be pruned
        _run_claude_sync(self.root, dict(self.platform_cfg))

        settings = self._read_json(self.home / ".claude" / "settings.json")
        self.assertNotIn("extraManagedKey", settings)
        # Sidecar no longer records the dropped key
        sidecar = self._read_json(self.home / ".claude" / ".managed_settings_keys.json")
        self.assertNotIn("extraManagedKey", sidecar["managedKeys"])

    def test_obsolete_settings_generated_json_removed(self) -> None:
        """Old settings.generated.json should be removed because Claude Code does not load it."""
        generated_path = self.home / ".claude" / "settings.generated.json"
        self._write_json(generated_path, {"model": "stale"})

        cfg = dict(self.platform_cfg)
        cfg["api"] = {"enabled": False}
        _run_claude_sync(self.root, cfg)

        self.assertFalse(generated_path.exists())

    def test_settings_json_syncs_api_env_when_api_enabled_missing(self) -> None:
        """When api.enabled is missing, Claude API sync defaults to enabled."""
        minimal_cfg = {
            "env": {"FOO": "bar"},
            "hooks": {
                "SessionStart": [
                    {"hooks": [{"type": "command", "command": "/bin/true", "timeout": 5}]}
                ]
            },
        }
        _run_claude_sync(self.root, minimal_cfg)

        settings = self._read_json(self.home / ".claude" / "settings.json")
        self.assertNotIn("model", settings)
        self.assertEqual(settings["env"], {"FOO": "bar"})
        self.assertIn("SessionStart", settings["hooks"])

    # ── Env merge ──────────────────────────────────────────────────────────────

    def test_env_merged_into_settings_json(self) -> None:
        """env vars from claude.json must be merged when local API is enabled."""
        cfg = dict(self.platform_cfg)
        cfg["api"] = {"enabled": True}
        _run_claude_sync(self.root, cfg)

        settings = self._read_json(self.home / ".claude" / "settings.json")
        self.assertIn("env", settings)
        # Secrets should have been resolved
        self.assertEqual(settings["env"]["ANTHROPIC_AUTH_TOKEN"], "sk-ant-test-token")
        self.assertEqual(settings["env"]["ANTHROPIC_BASE_URL"], "https://claude.example/v1")
        self.assertEqual(settings["env"]["ANTHROPIC_DEFAULT_OPUS_MODEL"], "claude-opus-4-8")
        self.assertEqual(settings["env"]["ANTHROPIC_DEFAULT_SONNET_MODEL"], "claude-sonnet-5")
        self.assertEqual(
            settings["env"]["ANTHROPIC_DEFAULT_HAIKU_MODEL"],
            "claude-haiku-4-5-20251001-thinking",
        )
        self.assertEqual(settings["env"]["CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS"], "1")

    def test_env_merge_preserves_existing_settings(self) -> None:
        """Existing keys in settings.json (outside env/hooks) must be preserved."""
        (self.home / ".claude").mkdir(parents=True, exist_ok=True)
        self._write_json(
            self.home / ".claude" / "settings.json",
            {
                "env": {"EXISTING_VAR": "existing-value"},
                "theme": "light",
                "editorMode": "vim",
            },
        )

        cfg = dict(self.platform_cfg)
        cfg["api"] = {"enabled": True}
        _run_claude_sync(self.root, cfg)

        settings = self._read_json(self.home / ".claude" / "settings.json")
        self.assertEqual(settings["theme"], "light")
        self.assertEqual(settings["editorMode"], "vim")
        # Existing env should be preserved alongside new ones
        self.assertEqual(settings["env"]["EXISTING_VAR"], "existing-value")
        self.assertEqual(settings["env"]["ANTHROPIC_AUTH_TOKEN"], "sk-ant-test-token")

    def test_api_disabled_cleans_managed_env_and_preserves_other_env(self) -> None:
        """API-disabled sync cleans Claude API env keys while preserving unrelated env vars."""
        self._write_json(
            self.home / ".claude" / "settings.json",
            {
                "env": {
                    "EXISTING_VAR": "existing-value",
                    "ANTHROPIC_AUTH_TOKEN": "old-token",
                    "ANTHROPIC_BASE_URL": "https://old.example/v1",
                }
            },
        )

        cfg = dict(self.platform_cfg)
        cfg["api"] = {"enabled": False}
        _run_claude_sync(self.root, cfg)

        settings = self._read_json(self.home / ".claude" / "settings.json")
        self.assertEqual(settings["env"], {"EXISTING_VAR": "existing-value"})

    def test_env_merge_skips_when_no_env_in_cfg(self) -> None:
        """When platform cfg has no env, settings.json env should be untouched."""
        (self.home / ".claude").mkdir(parents=True, exist_ok=True)
        self._write_json(
            self.home / ".claude" / "settings.json",
            {"env": {"KEEP": "me"}, "editorMode": "vim"},
        )

        cfg_no_env = dict(self.platform_cfg)
        del cfg_no_env["env"]
        _run_claude_sync(self.root, cfg_no_env)

        settings = self._read_json(self.home / ".claude" / "settings.json")
        self.assertEqual(settings["env"], {"KEEP": "me"})
        self.assertEqual(settings["editorMode"], "vim")

    # ── Hooks merge ────────────────────────────────────────────────────────────

    def test_hooks_expanded_and_merged(self) -> None:
        """Hook paths should be expanded and merged into settings.json."""
        cfg = {
            "hooks": {
                "SessionStart": [
                    {
                        "hooks": [
                            {
                                "type": "command",
                                "command": "~/.claude/hooks/xmcp-init.sh",
                                "timeout": 10,
                            }
                        ]
                    }
                ]
            }
        }
        _run_claude_sync(self.root, cfg)

        settings = self._read_json(self.home / ".claude" / "settings.json")
        self.assertIn("hooks", settings)
        self.assertIn("SessionStart", settings["hooks"])
        session_hooks = settings["hooks"]["SessionStart"][0]["hooks"]
        self.assertEqual(session_hooks[0]["type"], "command")
        self.assertEqual(session_hooks[0]["timeout"], 10)
        # Path should be expanded with the patched HOME
        expected_command = str(Path(self.home / ".claude" / "hooks" / "xmcp-init.sh"))
        self.assertEqual(session_hooks[0]["command"], expected_command)

    def test_hooks_merge_preserves_existing_hooks(self) -> None:
        """Existing hook events in settings.json should survive the merge."""
        (self.home / ".claude").mkdir(parents=True, exist_ok=True)
        self._write_json(
            self.home / ".claude" / "settings.json",
            {
                "hooks": {
                    "PostToolUse": [
                        {"hooks": [{"type": "command", "command": "/bin/echo", "timeout": 5}]}
                    ]
                }
            },
        )

        cfg = {
            "hooks": {
                "SessionStart": [
                    {
                        "hooks": [
                            {
                                "type": "command",
                                "command": "~/.claude/hooks/xmcp-init.sh",
                                "timeout": 10,
                            }
                        ]
                    }
                ]
            }
        }
        _run_claude_sync(self.root, cfg)

        settings = self._read_json(self.home / ".claude" / "settings.json")
        self.assertIn("PostToolUse", settings["hooks"])
        self.assertIn("SessionStart", settings["hooks"])

    # ── Hook script installation ───────────────────────────────────────────────

    def test_hook_scripts_installed(self) -> None:
        """Hook scripts from repo hooks/ should be copied to ~/.claude/hooks/."""
        # Write a real script into repo hooks/ for this test
        hook_src = self._repo_hooks_dir / "xmcp-init.sh"
        hook_src.write_text("#!/bin/bash\necho 'hello'\n", encoding="utf-8")
        hook_src.chmod(0o755)

        cfg = {
            "hooks": {
                "SessionStart": [
                    {
                        "hooks": [
                            {
                                "type": "command",
                                "command": "~/.claude/hooks/xmcp-init.sh",
                                "timeout": 10,
                            }
                        ]
                    }
                ]
            }
        }
        _run_claude_sync(self.root, cfg)

        dest = self.home / ".claude" / "hooks" / "xmcp-init.sh"
        self.assertTrue(dest.exists(), f"Hook script not installed at {dest}")
        self.assertEqual(dest.read_text(encoding="utf-8"), "#!/bin/bash\necho 'hello'\n")
        # Verify executable permission
        self.assertTrue(dest.stat().st_mode & stat.S_IXUSR, f"{dest} is not executable")

    # ── Xcode Claude Agent ─────────────────────────────────────────────────────

    def test_xcode_claude_json_root_mcp_servers(self) -> None:
        """Xcode config without projects should get MCP servers at root level."""
        xc_path = self.home / "Library/Developer/Xcode/CodingAssistant/ClaudeAgentConfig/.claude.json"
        xc_path.parent.mkdir(parents=True, exist_ok=True)
        # Pre-existing data without projects key
        data = {"mcpServers": {}, "existingKey": "keep"}
        self._write_json(xc_path, data)

        _run_claude_sync(self.root, self.platform_cfg)

        result = self._read_json(xc_path)
        self.assertEqual(result.get("existingKey"), "keep")
        self.assertIn("sample", result["mcpServers"])

    def test_xcode_claude_json_per_project_mcp_servers(self) -> None:
        """Xcode config with projects should inject MCP servers per project."""
        xc_path = self.home / "Library/Developer/Xcode/CodingAssistant/ClaudeAgentConfig/.claude.json"
        xc_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "projects": {
                "/Users/you/project1": {"otherKey": "val1"},
                "/Users/you/project2": {"otherKey": "val2"},
            }
        }
        self._write_json(xc_path, data)

        _run_claude_sync(self.root, self.platform_cfg)

        result = self._read_json(xc_path)
        for proj_name in ("/Users/you/project1", "/Users/you/project2"):
            self.assertIn("mcpServers", result["projects"][proj_name])
            self.assertIn("sample", result["projects"][proj_name]["mcpServers"])
        # Root level should NOT have mcpServers when projects exist
        self.assertNotIn("mcpServers", result)

    # ── Xcode Claude Agent settings ────────────────────────────────────────────

    def test_xcode_claude_settings_do_not_receive_platform_preferences_by_default(self) -> None:
        """Xcode Claude settings should not receive old team-shared preferences by default."""
        xc_dir = self.home / "Library/Developer/Xcode/CodingAssistant/ClaudeAgentConfig/.claude"
        self._write_json(xc_dir / "settings.generated.json", {"model": "stale"})

        _run_claude_sync(self.root, self.platform_cfg)

        xc_settings = xc_dir / "settings.json"
        self.assertTrue(xc_settings.exists(), f"Missing {xc_settings}")
        settings = self._read_json(xc_settings)

        for key in ("model", "alwaysThinkingEnabled", "permissions"):
            self.assertNotIn(key, settings)
        self.assertFalse((xc_settings.parent / "settings.generated.json").exists())

        # Should NOT leak host-specific keys
        for host_key in claude_module._HOST_SKIP:
            self.assertNotIn(host_key, settings, f"Host key '{host_key}' leaked into Xcode settings")

    def test_xcode_claude_settings_env_merged(self) -> None:
        """env vars must be merged into Xcode settings when local API is enabled."""
        # Pre-seed Xcode settings.json with some existing content
        xc_settings_dir = self.home / "Library/Developer/Xcode/CodingAssistant/ClaudeAgentConfig/.claude"
        xc_settings_dir.mkdir(parents=True, exist_ok=True)
        self._write_json(
            xc_settings_dir / "settings.json",
            {"env": {"XC_LEGACY": "keep-me"}},
        )

        cfg = dict(self.platform_cfg)
        cfg["api"] = {"enabled": True}
        _run_claude_sync(self.root, cfg)

        settings = self._read_json(xc_settings_dir / "settings.json")
        self.assertEqual(settings["env"]["XC_LEGACY"], "keep-me")
        self.assertEqual(settings["env"]["ANTHROPIC_AUTH_TOKEN"], "sk-ant-test-token")
        self.assertEqual(settings["env"]["ANTHROPIC_BASE_URL"], "https://claude.example/v1")

    def test_xcode_claude_settings_api_disabled_cleans_env(self) -> None:
        """API-disabled sync cleans Xcode Claude API env while preserving unrelated env."""
        xc_settings_dir = self.home / "Library/Developer/Xcode/CodingAssistant/ClaudeAgentConfig/.claude"
        xc_settings_dir.mkdir(parents=True, exist_ok=True)
        self._write_json(
            xc_settings_dir / "settings.json",
            {
                "env": {
                    "XC_LEGACY": "keep-me",
                    "ANTHROPIC_AUTH_TOKEN": "old-token",
                    "ANTHROPIC_BASE_URL": "https://old.example/v1",
                }
            },
        )

        cfg = dict(self.platform_cfg)
        cfg["api"] = {"enabled": False}
        _run_claude_sync(self.root, cfg)

        settings = self._read_json(xc_settings_dir / "settings.json")
        self.assertEqual(settings["env"], {"XC_LEGACY": "keep-me"})

    def test_xcode_claude_settings_hooks_merged(self) -> None:
        """hooks must be merged into the Xcode Claude Agent settings.json."""
        xc_settings_dir = self.home / "Library/Developer/Xcode/CodingAssistant/ClaudeAgentConfig/.claude"
        xc_settings_dir.mkdir(parents=True, exist_ok=True)

        cfg = {
            "hooks": {
                "SessionStart": [
                    {
                        "hooks": [
                            {
                                "type": "command",
                                "command": "~/.claude/hooks/xmcp-init.sh",
                                "timeout": 10,
                            }
                        ]
                    }
                ]
            }
        }
        _run_claude_sync(self.root, cfg)

        xc_settings = xc_settings_dir / "settings.json"
        self.assertTrue(xc_settings.exists(), f"Missing {xc_settings}")
        settings = self._read_json(xc_settings)

        self.assertIn("hooks", settings)
        self.assertIn("SessionStart", settings["hooks"])
        session_hooks = settings["hooks"]["SessionStart"][0]["hooks"]
        self.assertEqual(session_hooks[0]["type"], "command")
        self.assertEqual(session_hooks[0]["timeout"], 10)
        expected_command = str(Path(self.home / ".claude" / "hooks" / "xmcp-init.sh"))
        self.assertEqual(session_hooks[0]["command"], expected_command)

    # ── Full property mapping ──────────────────────────────────────────────────

    def test_claude_json_properties_are_mapped_or_excluded_as_expected(self) -> None:
        """Every key in claude.json must be accounted for: mapped or explicitly excluded."""
        # Define the expected complete key set from claude.json
        covered_keys = {
            "_comment",
            "api",
            "env",
            "preamble",
        }
        self.assertEqual(set(self.platform_cfg), covered_keys, "claude.json keys changed — update tests")

        _run_claude_sync(self.root, self.platform_cfg)

        settings = self._read_json(self.home / ".claude" / "settings.json")

        # ── Internal-only keys excluded from settings.json ──
        for excluded_key in ("_comment", "preamble", "export_env_to_zshrc"):
            self.assertNotIn(excluded_key, settings)

        # ── Engine-only API toggle is excluded; API env is written by default ──
        self.assertNotIn("api", settings)
        self.assertEqual(settings["env"]["ANTHROPIC_AUTH_TOKEN"], "sk-ant-test-token")

    def test_missing_xcode_path_skips_xcode_claude_target_only(self) -> None:
        """When Xcode CodingAssistant is absent, native Claude sync still runs."""
        _run_claude_sync(self.root, self.platform_cfg)

        data = self._read_json(self.home / ".claude.json")
        settings = self._read_json(self.home / ".claude" / "settings.json")
        self.assertIn("sample", data["mcpServers"])
        self.assertEqual(settings["env"]["ANTHROPIC_AUTH_TOKEN"], "sk-ant-test-token")
        self.assertNotIn("model", settings)
        self.assertFalse(
            (
                self.home
                / "Library"
                / "Developer"
                / "Xcode"
                / "CodingAssistant"
            ).exists()
        )

    # ── generate_managed_settings unit test ─────────────────────────────────────

    def test_generate_managed_settings_filters_correctly(self) -> None:
        """Unit test for generate_managed_settings() filtering logic."""
        cfg = {
            "model": "custom-shared-model",
            "effortLevel": "high",
            "env": {"FOO": "bar"},
            "hooks": {"SessionStart": []},
            "_comment": "test comment",
            "_hostSettings": {"theme": "dark"},
            "export_env_to_zshrc": {"KEY": "val"},
            "theme": "light",
            "editorMode": "vim",
            "autoConnectIde": False,
        }
        managed = claude_module.generate_managed_settings(cfg)

        # Included
        self.assertEqual(managed["model"], "custom-shared-model")
        self.assertEqual(managed["effortLevel"], "high")

        # Excluded
        for excluded in (
            "env",
            "hooks",
            "_comment",
            "_hostSettings",
            "export_env_to_zshrc",
            "theme",
            "editorMode",
            "autoConnectIde",
        ):
            self.assertNotIn(excluded, managed, f"'{excluded}' should be excluded")

    def test_generate_managed_settings_deep_copies(self) -> None:
        """Modifying the result must NOT affect the original config."""
        cfg = {"permissions": {"allow": ["Bash(git *)"]}}
        managed = claude_module.generate_managed_settings(cfg)
        managed["permissions"]["allow"].append("WebFetch")

        self.assertEqual(
            cfg["permissions"]["allow"],
            ["Bash(git *)"],
            "Original config was mutated — generate_managed_settings must deep copy",
        )

    # ── Edge cases ──────────────────────────────────────────────────────────────

    def test_claude_json_not_found_graceful(self) -> None:
        """When claude.json doesn't exist, sync should not crash and platform is skipped.

        In the auto-discovery architecture, platforms are discovered from
        env/platforms/*.json. A missing JSON means the platform is simply not
        discovered — sync completes without error, and no output file is written.
        """
        if (self.root / "env" / "platforms" / "claude.json").exists():
            (self.root / "env" / "platforms" / "claude.json").unlink()

        out = io.StringIO()
        with patched_sync_environment(self.root):
            sys.argv = ["sync_config.py", "--target", "all"]
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
                sync_config.main()

        # No crash; claude.json was not created because the platform was not discovered.
        self.assertFalse((self.home / ".claude.json").exists())

    def test_missing_claude_root_skips_sync(self) -> None:
        """When ~/.claude does not exist, sync should treat Claude as not installed."""
        self._write_json(
            self.home / "Library/Developer/Xcode/CodingAssistant/ClaudeAgentConfig/.claude.json",
            {"existing": True},
        )
        for path in sorted((self.home / ".claude").glob("**/*"), reverse=True):
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                path.rmdir()
        (self.home / ".claude").rmdir()

        _run_claude_sync(self.root, self.platform_cfg)

        self.assertFalse((self.home / ".claude").exists())
        self.assertFalse((self.home / ".claude.json").exists())
        xcode_data = self._read_json(
            self.home / "Library/Developer/Xcode/CodingAssistant/ClaudeAgentConfig/.claude.json"
        )
        self.assertEqual(xcode_data, {"existing": True})


if __name__ == "__main__":
    unittest.main()
