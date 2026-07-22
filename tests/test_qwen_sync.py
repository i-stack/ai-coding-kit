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
from platforms import qwen as qwen_mod  # noqa: E402
from core import common  # noqa: E402


DEFAULT_QWEN_CFG = {
    "env": {
        "DASHSCOPE_API_KEY": "${qwen.dashscopeApiKey}",
    },
    "models": [
        {
            "id": "qwen3-coder-plus",
            "name": "Qwen3 Coder Plus",
            "vendor": "qwen",
            "url": "${qwen.url}",
            "apiKey": "${qwen.dashscopeApiKey}",
            "maxInputTokens": 262144,
            "maxOutputTokens": 8192,
            "supportsToolCall": True,
            "supportsImages": False,
        },
        {
            "id": "qwen3-coder",
            "name": "Qwen3 Coder",
            "vendor": "qwen",
            "url": "${qwen.url}",
            "apiKey": "${qwen.dashscopeApiKey}",
            "maxInputTokens": 262144,
            "maxOutputTokens": 8192,
            "supportsToolCall": True,
            "supportsImages": False,
        },
        {
            "id": "qwen-max",
            "name": "Qwen Max",
            "vendor": "qwen",
            "url": "${qwen.url}",
            "apiKey": "${qwen.dashscopeApiKey}",
            "maxInputTokens": 131072,
            "maxOutputTokens": 8192,
            "supportsToolCall": True,
            "supportsImages": True,
        },
    ],
    "availableModels": [
        "qwen3-coder-plus",
        "qwen3-coder",
        "qwen-max",
    ],
}


@contextlib.contextmanager
def patched_sync_environment(root: Path):
    """Redirect HOME and common module paths for isolated Qwen sync tests."""
    home = root / "home"
    old_env = {k: os.environ.get(k) for k in ("HOME",)}
    old_paths = (common.MCP_DIR, common.PLATFORMS_DIR, common.SECRETS_PATH)
    old_argv = sys.argv[:]
    try:
        os.environ["HOME"] = str(home)
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


class QwenSyncTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "home" / ".qwen").mkdir(parents=True, exist_ok=True)
        self.platform_cfg = DEFAULT_QWEN_CFG
        self._write_json(
            self.root / "env" / "mcp" / "sample.json",
            {
                "name": "sample",
                "type": "stdio",
                "command": "echo",
                "args": ["hello"],
                "platforms": ["qwen"],
            },
        )
        self._write_json(
            self.root / "env" / "secrets.json",
            {
                "qwen": {
                    "url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                    "dashscopeApiKey": "sk-test-qwen",
                }
            },
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

    def _run_qwen_sync(self, cfg: dict | None = None) -> dict[str, dict]:
        """Run Qwen sync and return parsed {settings, models} contents."""
        target_cfg = cfg if cfg is not None else self.platform_cfg
        self._write_json(self.root / "env" / "platforms" / "qwen.json", target_cfg)
        with patched_sync_environment(self.root):
            sys.argv = ["sync_config.py", "--target", "qwen"]
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                sync_config.main()
        return {
            "settings": self._read_json(self.root / "home" / ".qwen" / "settings.json"),
            "models": self._read_json(self.root / "home" / ".qwen" / "models.json"),
        }

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

    # ── Env sync ──────────────────────────────────────────────────────────────

    def test_env_synced_to_settings_json(self) -> None:
        result = self._run_qwen_sync()

        self.assertIn("env", result["settings"])
        self.assertEqual(
            result["settings"]["env"]["DASHSCOPE_API_KEY"], "sk-test-qwen"
        )

    def test_settings_json_preserves_existing_user_keys(self) -> None:
        """User-added keys in settings.json outside env are preserved."""
        settings_path = self.root / "home" / ".qwen" / "settings.json"
        self._write_json(
            settings_path,
            {"userPref": "keep-me", "env": {"USER_VAR": "should-stay"}},
        )

        result = self._run_qwen_sync()

        self.assertEqual(result["settings"]["userPref"], "keep-me")
        # Managed env key merged; unrelated user env key preserved.
        self.assertEqual(result["settings"]["env"]["DASHSCOPE_API_KEY"], "sk-test-qwen")
        self.assertEqual(result["settings"]["env"]["USER_VAR"], "should-stay")

    # ── Models sync ───────────────────────────────────────────────────────────

    def test_models_synced_to_models_json(self) -> None:
        result = self._run_qwen_sync()

        self.assertIn("models", result["models"])
        self.assertEqual(len(result["models"]["models"]), 3)
        self.assertEqual(result["models"]["models"][0]["id"], "qwen3-coder-plus")
        self.assertEqual(result["models"]["models"][0]["name"], "Qwen3 Coder Plus")
        self.assertEqual(result["models"]["models"][0]["vendor"], "qwen")
        self.assertEqual(
            result["models"]["models"][0]["url"],
            "https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        self.assertEqual(
            result["models"]["models"][0]["apiKey"], "sk-test-qwen"
        )
        self.assertEqual(result["models"]["models"][0]["maxInputTokens"], 262144)
        self.assertEqual(result["models"]["models"][0]["maxOutputTokens"], 8192)
        self.assertTrue(result["models"]["models"][0]["supportsToolCall"])
        self.assertFalse(result["models"]["models"][0]["supportsImages"])
        # qwen-max supports images
        self.assertEqual(result["models"]["models"][2]["id"], "qwen-max")
        self.assertTrue(result["models"]["models"][2]["supportsImages"])

    def test_available_models_synced(self) -> None:
        result = self._run_qwen_sync()

        self.assertIn("availableModels", result["models"])
        self.assertEqual(
            result["models"]["availableModels"],
            ["qwen3-coder-plus", "qwen3-coder", "qwen-max"],
        )

    def test_models_json_preserves_existing_user_keys(self) -> None:
        """User-added top-level keys outside models/availableModels survive sync."""
        models_path = self.root / "home" / ".qwen" / "models.json"
        self._write_json(
            models_path,
            {
                "meta": {"version": 2, "description": "Custom config"},
                "uiPreference": "compact",
            },
        )

        result = self._run_qwen_sync()

        self.assertEqual(result["models"]["meta"]["version"], 2)
        self.assertEqual(result["models"]["uiPreference"], "compact")

    def test_user_added_models_preserved_during_sync(self) -> None:
        """User-added model entries not in config are preserved alongside managed ones."""
        models_path = self.root / "home" / ".qwen" / "models.json"
        self._write_json(
            models_path,
            {
                "models": [
                    {
                        "id": "custom-model",
                        "name": "Custom Model",
                        "vendor": "custom",
                    }
                ],
                "availableModels": ["custom-model"],
            },
        )

        result = self._run_qwen_sync()

        # 3 config-managed + 1 user-added = 4
        self.assertEqual(len(result["models"]["models"]), 4)
        model_ids = [m["id"] for m in result["models"]["models"]]
        self.assertIn("custom-model", model_ids)
        self.assertIn("qwen3-coder-plus", model_ids)
        self.assertIn("qwen3-coder", model_ids)
        self.assertIn("qwen-max", model_ids)
        # Config-managed entries appear first (in config order)
        self.assertEqual(model_ids[0], "qwen3-coder-plus")
        self.assertEqual(model_ids[1], "qwen3-coder")
        self.assertEqual(model_ids[2], "qwen-max")
        self.assertEqual(model_ids[3], "custom-model")
        # User's availableModels entry is preserved
        self.assertIn("custom-model", result["models"]["availableModels"])

    def test_config_models_update_existing_by_id(self) -> None:
        """Config-managed models update existing entries with the same id instead of duplicating."""
        models_path = self.root / "home" / ".qwen" / "models.json"
        self._write_json(
            models_path,
            {
                "models": [
                    {
                        "id": "qwen3-coder-plus",
                        "name": "OLD Qwen3 Coder Plus",
                        "vendor": "old-vendor",
                        "url": "https://old.example/v1",
                        "apiKey": "sk-old-key",
                    }
                ],
                "availableModels": [],
            },
        )

        result = self._run_qwen_sync()

        # qwen3-coder-plus is UPDATED (not duplicated); the other two are ADDED
        self.assertEqual(len(result["models"]["models"]), 3)
        model_ids = [m["id"] for m in result["models"]["models"]]
        self.assertEqual(
            model_ids, ["qwen3-coder-plus", "qwen3-coder", "qwen-max"]
        )
        pro = result["models"]["models"][0]
        self.assertEqual(pro["name"], "Qwen3 Coder Plus")
        self.assertEqual(
            pro["url"], "https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
        self.assertEqual(pro["apiKey"], "sk-test-qwen")

    # ── Skills sync ───────────────────────────────────────────────────────────

    def test_skills_synced_from_claude_to_qwen(self) -> None:
        claude_skills = self.root / "home" / ".claude" / "skills"
        skill_dir = claude_skills / "test-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Test Skill\n", encoding="utf-8")
        (skill_dir / "helper.py").write_text("# helper script\n", encoding="utf-8")

        self._run_qwen_sync()

        dest = self.root / "home" / ".qwen" / "skills" / "test-skill"
        self.assertTrue(dest.exists(), "Skill directory was not synced to Qwen")
        self.assertTrue((dest / "SKILL.md").exists(), "SKILL.md was not synced")
        self.assertTrue((dest / "helper.py").exists(), "helper.py was not synced")
        self.assertEqual(
            (dest / "SKILL.md").read_text(encoding="utf-8"), "# Test Skill\n"
        )

    def test_skills_missing_claude_dir_skips_gracefully(self) -> None:
        """When ~/.claude/skills doesn't exist, skill sync is skipped without error."""
        result = self._run_qwen_sync()

        skills_dir = self.root / "home" / ".qwen" / "skills"
        self.assertFalse(skills_dir.exists(), "skills dir should not be created when claude skills missing")
        # Env and models should still sync fine
        self.assertIn("env", result["settings"])
        self.assertIn("models", result["models"])

    # ── Edge cases ────────────────────────────────────────────────────────────

    def test_no_models_config_skips_model_sync(self) -> None:
        """When config has no 'models' or 'availableModels', model sync is skipped."""
        cfg: dict = {"env": self.platform_cfg["env"]}
        result = self._run_qwen_sync(cfg)

        # Env still works
        self.assertIn("env", result["settings"])
        # Models target should be empty (not created with stale data)
        models_path = self.root / "home" / ".qwen" / "models.json"
        self.assertFalse(models_path.exists(), "models.json should not be created without model config")

    def test_no_models_config_removes_existing_managed_model_keys(self) -> None:
        """When model config is absent, previously synced model keys are removed."""
        models_path = self.root / "home" / ".qwen" / "models.json"
        self._write_json(
            models_path,
            {
                "meta": {"version": 2},
                "models": [
                    {
                        "id": "qwen3-coder-plus",
                        "name": "Stale Qwen3 Coder Plus",
                        "vendor": "old",
                    }
                ],
                "availableModels": ["qwen3-coder-plus"],
            },
        )

        result = self._run_qwen_sync({"env": self.platform_cfg["env"]})

        self.assertEqual(result["models"], {"meta": {"version": 2}})

    def test_models_only_sync(self) -> None:
        """When config has only 'models' but no 'availableModels', only models are synced."""
        cfg: dict = {"models": self.platform_cfg["models"]}
        self._write_json(self.root / "env" / "platforms" / "qwen.json", cfg)

        result = self._run_qwen_sync(cfg)

        self.assertIn("models", result["models"])
        self.assertEqual(len(result["models"]["models"]), 3)
        self.assertNotIn("availableModels", result["models"])

    def test_available_models_only_sync(self) -> None:
        """When config has only 'availableModels' but no 'models', only availableModels synced."""
        cfg: dict = {"availableModels": self.platform_cfg["availableModels"]}
        self._write_json(self.root / "env" / "platforms" / "qwen.json", cfg)

        result = self._run_qwen_sync(cfg)

        self.assertEqual(
            result["models"]["availableModels"],
            ["qwen3-coder-plus", "qwen3-coder", "qwen-max"],
        )
        self.assertNotIn("models", result["models"])

    # ── API toggle (api.enabled) ──────────────────────────────────────────────

    def test_api_enabled_by_default(self) -> None:
        """Missing api block defaults to enabled — normal model sync runs."""
        cfg = {
            "env": self.platform_cfg["env"],
            "models": self.platform_cfg["models"],
            "availableModels": self.platform_cfg["availableModels"],
        }
        result = self._run_qwen_sync(cfg)

        self.assertEqual(len(result["models"]["models"]), 3)
        self.assertEqual(
            result["models"]["availableModels"],
            ["qwen3-coder-plus", "qwen3-coder", "qwen-max"],
        )

    def test_api_disabled_empties_available_models(self) -> None:
        """When api.enabled=false, availableModels is set to [] (CodeBuddy special handling)."""
        cfg = {
            "api": {"enabled": False},
            "env": self.platform_cfg["env"],
            "models": self.platform_cfg["models"],
            "availableModels": self.platform_cfg["availableModels"],
        }
        result = self._run_qwen_sync(cfg)

        self.assertEqual(result["models"]["availableModels"], [])
        # Model definitions are NOT synced while disabled, so the key is absent.
        self.assertNotIn("models", result["models"])

    def test_api_disabled_cleans_env_keys(self) -> None:
        """When api.enabled=false, managed env keys are removed from settings.json."""
        settings_path = self.root / "home" / ".qwen" / "settings.json"
        self._write_json(
            settings_path,
            {"env": {"DASHSCOPE_API_KEY": "old", "USER_VAR": "keep"}},
        )

        cfg = {
            "api": {"enabled": False},
            "env": self.platform_cfg["env"],
            "models": self.platform_cfg["models"],
            "availableModels": self.platform_cfg["availableModels"],
        }
        result = self._run_qwen_sync(cfg)

        # Managed key removed; unrelated user key preserved.
        self.assertNotIn("DASHSCOPE_API_KEY", result["settings"]["env"])
        self.assertEqual(result["settings"]["env"]["USER_VAR"], "keep")

    def test_api_disabled_preserves_user_models(self) -> None:
        """User-added model definitions survive a disabled API sync."""
        models_path = self.root / "home" / ".qwen" / "models.json"
        self._write_json(
            models_path,
            {
                "models": [
                    {
                        "id": "custom-model",
                        "name": "Custom Model",
                        "vendor": "custom",
                    }
                ],
                "availableModels": ["custom-model"],
            },
        )

        cfg = {
            "api": {"enabled": False},
            "env": self.platform_cfg["env"],
            "models": self.platform_cfg["models"],
            "availableModels": self.platform_cfg["availableModels"],
        }
        result = self._run_qwen_sync(cfg)

        # User model kept; availableModels emptied by the disabled sync.
        model_ids = [m["id"] for m in result["models"]["models"]]
        self.assertIn("custom-model", model_ids)
        self.assertEqual(result["models"]["availableModels"], [])

    def test_api_disabled_is_idempotent(self) -> None:
        """Re-running a disabled sync keeps availableModels empty and models intact."""
        cfg = {
            "api": {"enabled": False},
            "env": self.platform_cfg["env"],
            "models": self.platform_cfg["models"],
            "availableModels": self.platform_cfg["availableModels"],
        }
        self._run_qwen_sync(cfg)
        result = self._run_qwen_sync(cfg)

        self.assertEqual(result["models"]["availableModels"], [])
        # Disabled sync never writes the models key, so it stays absent.
        self.assertNotIn("models", result["models"])

    def test_api_enabled_after_disabled_restores_models(self) -> None:
        """Re-enabling API sync restores availableModels from config."""
        models_path = self.root / "home" / ".qwen" / "models.json"
        self._write_json(
            models_path,
            {
                "models": [
                    {
                        "id": "qwen3-coder-plus",
                        "name": "Stale Qwen3 Coder Plus",
                        "vendor": "old",
                    }
                ],
                "availableModels": ["qwen3-coder-plus"],
            },
        )

        disabled = {
            "api": {"enabled": False},
            "env": self.platform_cfg["env"],
            "models": self.platform_cfg["models"],
            "availableModels": self.platform_cfg["availableModels"],
        }
        self._run_qwen_sync(disabled)
        self.assertEqual(self._read_json(models_path)["availableModels"], [])

        enabled = {
            "env": self.platform_cfg["env"],
            "models": self.platform_cfg["models"],
            "availableModels": self.platform_cfg["availableModels"],
        }
        result = self._run_qwen_sync(enabled)
        self.assertEqual(
            result["models"]["availableModels"],
            ["qwen3-coder-plus", "qwen3-coder", "qwen-max"],
        )
        self.assertEqual(len(result["models"]["models"]), 3)

    # ── MCP handling ──────────────────────────────────────────────────────────

    def test_mcp_servers_are_ignored(self) -> None:
        """Qwen sync does not write a managed mcpServers file."""
        self._run_qwen_sync()

        mcp_path = self.root / "home" / ".qwen" / "mcp.json"
        self.assertFalse(mcp_path.exists(), "Qwen sync should not write mcp.json")

    # ── Internal key exclusion ───────────────────────────────────────────────

    def test_internal_keys_excluded_from_output(self) -> None:
        """_comment and platform-internal keys do not leak into output files."""
        result = self._run_qwen_sync()

        self.assertNotIn("_comment", result["settings"])
        self.assertNotIn("_comment", result["models"])

    # ── Recall preamble ──────────────────────────────────────────────────────

    def test_recall_preamble_not_rendered_by_qwen_engine(self) -> None:
        """qwen.py does not render the recall managed block (engine gap, not error)."""
        self._run_qwen_sync()

        md = self.root / "home" / ".qwen" / "QWEN.md"
        self.assertFalse(md.exists(), "Qwen engine does not render recall preamble yet")

    # ── Missing root ─────────────────────────────────────────────────────────

    def test_missing_qwen_root_skips_sync(self) -> None:
        """When ~/.qwen does not exist, sync should not create Qwen files."""
        (self.root / "home" / ".qwen").rmdir()

        result = self._run_qwen_sync()

        self.assertFalse((self.root / "home" / ".qwen").exists())
        self.assertEqual(result["settings"], {})
        self.assertEqual(result["models"], {})

    # ── Secret resolution ────────────────────────────────────────────────────

    def test_secret_resolution_in_models(self) -> None:
        """Secrets ${qwen.url} and ${qwen.dashscopeApiKey} are resolved in model fields."""
        result = self._run_qwen_sync()

        model = result["models"]["models"][0]
        self.assertEqual(
            model["url"], "https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
        self.assertEqual(model["apiKey"], "sk-test-qwen")

    def test_invalid_models_config_fails_fast(self) -> None:
        """Invalid models config is rejected before writing models.json."""
        with self.assertRaisesRegex(ValueError, "platforms.qwen.models must be a list"):
            self._run_qwen_sync({"models": {"id": "bad"}})

    def test_invalid_available_models_config_fails_fast(self) -> None:
        """Invalid availableModels config is rejected before writing models.json."""
        with self.assertRaisesRegex(
            ValueError,
            r"platforms\.qwen\.availableModels\[0\] must be a non-empty string",
        ):
            self._run_qwen_sync({"availableModels": [123]})


if __name__ == "__main__":
    unittest.main()
