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

import sync_config  # noqa: E402
from platforms import codebuddy as codebuddy_mod  # noqa: E402
from platforms import common  # noqa: E402


DEFAULT_CODEBUDDY_CFG = {
    "models": [
        {
            "id": "deepseek-v4-pro",
            "name": "DeepSeek V4 Pro",
            "vendor": "dataeyes",
            "url": "${codebuddy.url}",
            "apiKey": "${codebuddy.key}",
            "maxInputTokens": 128000,
            "maxOutputTokens": 8192,
            "supportsToolCall": True,
            "supportsImages": False,
            "relatedModels": {
                "lite": "deepseek-v4-flash",
                "reasoning": "deepseek-v4-pro",
            },
        },
        {
            "id": "deepseek-v4-flash",
            "name": "DeepSeek V4 Flash",
            "vendor": "dataeyes",
            "url": "${codebuddy.url}",
            "apiKey": "${codebuddy.key}",
            "maxInputTokens": 128000,
            "maxOutputTokens": 8192,
            "supportsToolCall": True,
            "supportsImages": False,
        },
    ],
    "availableModels": [
        "deepseek-v4-pro",
        "deepseek-v4-flash",
    ],
}


@contextlib.contextmanager
def patched_sync_environment(root: Path):
    """Redirect HOME and common module paths for isolated CodeBuddy sync tests."""
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


class CodeBuddySyncTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.platform_cfg = DEFAULT_CODEBUDDY_CFG
        self._write_json(
            self.root / "env" / "mcp" / "sample.json",
            {
                "name": "sample",
                "type": "stdio",
                "command": "echo",
                "args": ["hello"],
                "platforms": ["codebuddy"],
            },
        )
        self._write_json(
            self.root / "env" / "secrets.json",
            {"codebuddy": {"url": "https://codebuddy.example/v1", "key": "sk-test-codebuddy"}},
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

    def _run_codebuddy_sync(self, cfg: dict | None = None) -> dict[str, dict]:
        """Run CodeBuddy sync and return parsed {mcp, models} contents."""
        target_cfg = cfg if cfg is not None else self.platform_cfg
        self._write_json(self.root / "env" / "platforms" / "codebuddy.json", target_cfg)
        with patched_sync_environment(self.root):
            sys.argv = ["sync_config.py", "--target", "codebuddy"]
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                sync_config.main()
        return {
            "mcp": self._read_json(self.root / "home" / ".codebuddy" / "mcp.json"),
            "models": self._read_json(self.root / "home" / ".codebuddy" / "models.json"),
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

    # ── MCP servers ──────────────────────────────────────────────────────────

    def test_mcp_servers_synced_to_mcp_json(self) -> None:
        result = self._run_codebuddy_sync()

        self.assertIn("mcpServers", result["mcp"])
        self.assertIn("sample", result["mcp"]["mcpServers"])
        self.assertEqual(result["mcp"]["mcpServers"]["sample"]["command"], "echo")
        self.assertEqual(result["mcp"]["mcpServers"]["sample"]["args"], ["hello"])

    def test_mcp_json_preserves_existing_user_keys(self) -> None:
        """User-added keys outside mcpServers are preserved after sync."""
        mcp_path = self.root / "home" / ".codebuddy" / "mcp.json"
        mcp_path.parent.mkdir(parents=True, exist_ok=True)
        mcp_path.write_text(
            json.dumps(
                {
                    "meta": {"version": 1, "lastModified": "2025-01-01"},
                    "mcpServers": {"customServer": {"command": "custom-cmd"}},
                },
                indent=4,
            )
            + "\n",
            encoding="utf-8",
        )

        result = self._run_codebuddy_sync()

        self.assertEqual(result["mcp"]["meta"]["version"], 1)
        self.assertEqual(result["mcp"]["meta"]["lastModified"], "2025-01-01")
        # Managed MCP servers overwrite mcpServers key
        self.assertIn("sample", result["mcp"]["mcpServers"])
        self.assertNotIn("customServer", result["mcp"]["mcpServers"])

    # ── Models sync ──────────────────────────────────────────────────────────

    def test_models_synced_to_models_json(self) -> None:
        result = self._run_codebuddy_sync()

        self.assertIn("models", result["models"])
        self.assertEqual(len(result["models"]["models"]), 2)
        # Model 0: deepseek-v4-pro (with relatedModels)
        self.assertEqual(result["models"]["models"][0]["id"], "deepseek-v4-pro")
        self.assertEqual(result["models"]["models"][0]["name"], "DeepSeek V4 Pro")
        self.assertEqual(result["models"]["models"][0]["vendor"], "dataeyes")
        self.assertEqual(result["models"]["models"][0]["url"], "https://codebuddy.example/v1")
        self.assertEqual(result["models"]["models"][0]["apiKey"], "sk-test-codebuddy")
        self.assertEqual(result["models"]["models"][0]["maxInputTokens"], 128000)
        self.assertEqual(result["models"]["models"][0]["maxOutputTokens"], 8192)
        self.assertTrue(result["models"]["models"][0]["supportsToolCall"])
        self.assertFalse(result["models"]["models"][0]["supportsImages"])
        self.assertEqual(
            result["models"]["models"][0]["relatedModels"],
            {"lite": "deepseek-v4-flash", "reasoning": "deepseek-v4-pro"},
        )
        # Model 1: deepseek-v4-flash (no relatedModels)
        self.assertEqual(result["models"]["models"][1]["id"], "deepseek-v4-flash")
        self.assertEqual(result["models"]["models"][1]["name"], "DeepSeek V4 Flash")
        self.assertNotIn("relatedModels", result["models"]["models"][1])

    def test_available_models_synced(self) -> None:
        result = self._run_codebuddy_sync()

        self.assertIn("availableModels", result["models"])
        self.assertEqual(
            result["models"]["availableModels"],
            ["deepseek-v4-pro", "deepseek-v4-flash"],
        )

    def test_models_json_preserves_existing_user_keys(self) -> None:
        """User-added top-level keys outside models/availableModels survive sync."""
        models_path = self.root / "home" / ".codebuddy" / "models.json"
        models_path.parent.mkdir(parents=True, exist_ok=True)
        models_path.write_text(
            json.dumps(
                {
                    "meta": {"version": 2, "description": "Custom config"},
                    "uiPreference": "compact",
                },
                indent=4,
            )
            + "\n",
            encoding="utf-8",
        )

        result = self._run_codebuddy_sync()

        # User's top-level keys preserved
        self.assertEqual(result["models"]["meta"]["version"], 2)
        self.assertEqual(result["models"]["uiPreference"], "compact")

    def test_user_added_models_preserved_during_sync(self) -> None:
        """User-added model entries not in config are preserved alongside managed ones."""
        models_path = self.root / "home" / ".codebuddy" / "models.json"
        models_path.parent.mkdir(parents=True, exist_ok=True)
        models_path.write_text(
            json.dumps(
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
                indent=4,
            )
            + "\n",
            encoding="utf-8",
        )

        result = self._run_codebuddy_sync()

        # 2 config-managed + 1 user-added = 3
        self.assertEqual(len(result["models"]["models"]), 3)
        model_ids = [m["id"] for m in result["models"]["models"]]
        self.assertIn("custom-model", model_ids)
        self.assertIn("deepseek-v4-pro", model_ids)
        self.assertIn("deepseek-v4-flash", model_ids)
        # Config-managed entries appear first (in config order)
        self.assertEqual(model_ids[0], "deepseek-v4-pro")
        self.assertEqual(model_ids[1], "deepseek-v4-flash")
        self.assertEqual(model_ids[2], "custom-model")
        # User's availableModels entry is preserved
        self.assertIn("custom-model", result["models"]["availableModels"])

    def test_config_models_update_existing_by_id(self) -> None:
        """Config-managed models update existing entries with the same id instead of duplicating."""
        models_path = self.root / "home" / ".codebuddy" / "models.json"
        models_path.parent.mkdir(parents=True, exist_ok=True)
        models_path.write_text(
            json.dumps(
                {
                    "models": [
                        {
                            "id": "deepseek-v4-pro",
                            "name": "OLD DeepSeek V4 Pro",
                            "vendor": "old-vendor",
                            "url": "https://old.example/v1",
                            "apiKey": "sk-old-key",
                        }
                    ],
                    "availableModels": [],
                },
                indent=4,
            )
            + "\n",
            encoding="utf-8",
        )

        result = self._run_codebuddy_sync()

        # deepseek-v4-pro is UPDATED (not duplicated), deepseek-v4-flash is ADDED
        self.assertEqual(len(result["models"]["models"]), 2)
        model_ids = [m["id"] for m in result["models"]["models"]]
        self.assertEqual(model_ids, ["deepseek-v4-pro", "deepseek-v4-flash"])
        # Verify the updated model uses config values
        pro = result["models"]["models"][0]
        self.assertEqual(pro["name"], "DeepSeek V4 Pro")
        self.assertEqual(pro["url"], "https://codebuddy.example/v1")
        self.assertEqual(pro["apiKey"], "sk-test-codebuddy")

    # ── Skills sync ──────────────────────────────────────────────────────────

    def test_skills_synced_from_claude_to_codebuddy(self) -> None:
        claude_skills = self.root / "home" / ".claude" / "skills"
        # Create a SKILL.md for a valid skill
        skill_dir = claude_skills / "test-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Test Skill\n", encoding="utf-8")
        (skill_dir / "helper.py").write_text("# helper script\n", encoding="utf-8")

        self._run_codebuddy_sync()

        dest = self.root / "home" / ".codebuddy" / "skills" / "test-skill"
        self.assertTrue(dest.exists(), "Skill directory was not synced to CodeBuddy")
        self.assertTrue((dest / "SKILL.md").exists(), "SKILL.md was not synced")
        self.assertTrue((dest / "helper.py").exists(), "helper.py was not synced")
        self.assertEqual(
            (dest / "SKILL.md").read_text(encoding="utf-8"), "# Test Skill\n"
        )

    def test_skills_skip_dirs_without_skill_md(self) -> None:
        claude_skills = self.root / "home" / ".claude" / "skills"
        (claude_skills / "no-skill-md").mkdir(parents=True)
        (claude_skills / "no-skill-md" / "readme.md").write_text("no SKILL.md\n", encoding="utf-8")

        self._run_codebuddy_sync()

        dest = self.root / "home" / ".codebuddy" / "skills" / "no-skill-md"
        self.assertFalse(dest.exists(), "Dir without SKILL.md should not be synced")

    def test_skills_missing_claude_dir_skips_gracefully(self) -> None:
        """When ~/.claude/skills doesn't exist, skill sync is skipped without error."""
        # setUp doesn't create claude skills, so dir doesn't exist
        result = self._run_codebuddy_sync()

        skills_dir = self.root / "home" / ".codebuddy" / "skills"
        self.assertFalse(skills_dir.exists(), "skills dir should not be created when claude skills missing")
        # MCP and models should still sync fine
        self.assertIn("mcpServers", result["mcp"])
        self.assertIn("models", result["models"])

    def test_skills_overwrites_existing_skill_dir(self) -> None:
        """Existing CodeBuddy skill dir is removed and replaced with Claude version."""
        claude_skills = self.root / "home" / ".claude" / "skills"
        (claude_skills / "test-skill").mkdir(parents=True)
        (claude_skills / "test-skill" / "SKILL.md").write_text("Claude version\n", encoding="utf-8")

        cb_skills = self.root / "home" / ".codebuddy" / "skills" / "test-skill"
        cb_skills.mkdir(parents=True)
        (cb_skills / "SKILL.md").write_text("Old CodeBuddy version\n", encoding="utf-8")
        (cb_skills / "stale-file.txt").write_text("should be removed\n", encoding="utf-8")

        self._run_codebuddy_sync()

        self.assertTrue((cb_skills / "SKILL.md").exists())
        self.assertEqual((cb_skills / "SKILL.md").read_text(encoding="utf-8"), "Claude version\n")
        self.assertFalse((cb_skills / "stale-file.txt").exists(), "Stale files should be removed")

    def test_skills_copy_failure_preserves_existing_skill_dir(self) -> None:
        """Existing CodeBuddy skill remains when copying the Claude version fails."""
        claude_skills = self.root / "home" / ".claude" / "skills"
        (claude_skills / "test-skill").mkdir(parents=True)
        (claude_skills / "test-skill" / "SKILL.md").write_text("Claude version\n", encoding="utf-8")

        cb_skills = self.root / "home" / ".codebuddy" / "skills" / "test-skill"
        cb_skills.mkdir(parents=True)
        (cb_skills / "SKILL.md").write_text("Old CodeBuddy version\n", encoding="utf-8")

        original_copytree = codebuddy_mod.shutil.copytree

        def failing_copytree(src: Path, dst: Path):
            raise OSError("simulated copy failure")

        codebuddy_mod.shutil.copytree = failing_copytree
        try:
            with self.assertRaises(OSError):
                self._run_codebuddy_sync()
        finally:
            codebuddy_mod.shutil.copytree = original_copytree

        self.assertTrue((cb_skills / "SKILL.md").exists())
        self.assertEqual((cb_skills / "SKILL.md").read_text(encoding="utf-8"), "Old CodeBuddy version\n")

    # ── Edge cases ────────────────────────────────────────────────────────────

    def test_no_models_config_skips_model_sync(self) -> None:
        """When config has no 'models' or 'availableModels', model sync is skipped."""
        cfg: dict = {}
        result = self._run_codebuddy_sync(cfg)

        # MCP should still work
        self.assertIn("mcpServers", result["mcp"])
        # Models target should be empty (not created with stale data)
        models_path = self.root / "home" / ".codebuddy" / "models.json"
        self.assertFalse(models_path.exists(), "models.json should not be created without model config")

    def test_no_models_config_removes_existing_managed_model_keys(self) -> None:
        """When model config is absent, previously synced model keys are removed."""
        models_path = self.root / "home" / ".codebuddy" / "models.json"
        self._write_json(
            models_path,
            {
                "meta": {"version": 2},
                "models": [
                    {
                        "id": "deepseek-v4-pro",
                        "name": "Stale DeepSeek V4 Pro",
                        "vendor": "old",
                    }
                ],
                "availableModels": ["deepseek-v4-pro"],
            },
        )

        result = self._run_codebuddy_sync({})

        self.assertEqual(result["models"], {"meta": {"version": 2}})

    def test_disabled_platform_config_removes_existing_managed_model_keys(self) -> None:
        """enabled=false keeps config JSON valid while disabling managed model sync."""
        models_path = self.root / "home" / ".codebuddy" / "models.json"
        self._write_json(
            models_path,
            {
                "meta": {"version": 2},
                "models": [
                    {
                        "id": "deepseek-v4-pro",
                        "name": "Stale DeepSeek V4 Pro",
                        "vendor": "old",
                    }
                ],
                "availableModels": ["deepseek-v4-pro"],
            },
        )
        cfg = {"enabled": False, **self.platform_cfg}

        result = self._run_codebuddy_sync(cfg)

        self.assertEqual(result["models"], {"meta": {"version": 2}})

    def test_commented_platform_config_removes_existing_managed_model_keys(self) -> None:
        """A fully commented codebuddy.json parses as absent config and clears managed model keys."""
        models_path = self.root / "home" / ".codebuddy" / "models.json"
        self._write_json(
            models_path,
            {
                "models": [
                    {
                        "id": "deepseek-v4-flash",
                        "name": "Stale DeepSeek V4 Flash",
                        "vendor": "old",
                    }
                ],
                "availableModels": ["deepseek-v4-flash"],
            },
        )
        config_path = self.root / "env" / "platforms" / "codebuddy.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(
            "// {\n"
            "//     \"models\": [\n"
            "//         {\"id\": \"deepseek-v4-flash\"}\n"
            "//     ],\n"
            "//     \"availableModels\": [\"deepseek-v4-flash\"]\n"
            "// }\n",
            encoding="utf-8",
        )

        with patched_sync_environment(self.root):
            sys.argv = ["sync_config.py", "--target", "codebuddy"]
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                sync_config.main()

        self.assertEqual(self._read_json(models_path), {})

    def test_models_only_sync(self) -> None:
        """When config has only 'models' but no 'availableModels', only models are synced."""
        cfg: dict = {"models": self.platform_cfg["models"]}
        self._write_json(self.root / "env" / "platforms" / "codebuddy.json", cfg)

        result = self._run_codebuddy_sync(cfg)

        self.assertIn("models", result["models"])
        self.assertEqual(len(result["models"]["models"]), 2)
        self.assertNotIn("availableModels", result["models"])

    def test_available_models_only_sync(self) -> None:
        """When config has only 'availableModels' but no 'models', only availableModels are synced."""
        cfg: dict = {"availableModels": self.platform_cfg["availableModels"]}
        self._write_json(self.root / "env" / "platforms" / "codebuddy.json", cfg)

        result = self._run_codebuddy_sync(cfg)

        self.assertEqual(
            result["models"]["availableModels"],
            ["deepseek-v4-pro", "deepseek-v4-flash"],
        )
        self.assertNotIn("models", result["models"])

    def test_empty_mcp_servers_does_not_break(self) -> None:
        """Sync with no MCP servers still runs CodeBuddy models sync."""
        mcp_dir = self.root / "env" / "mcp"
        for f in mcp_dir.glob("*.json"):
            f.unlink()

        target_cfg = self.platform_cfg
        self._write_json(self.root / "env" / "platforms" / "codebuddy.json", target_cfg)
        with patched_sync_environment(self.root):
            sys.argv = ["sync_config.py", "--target", "codebuddy"]
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                sync_config.main()

        mcp = self._read_json(self.root / "home" / ".codebuddy" / "mcp.json")
        models = self._read_json(self.root / "home" / ".codebuddy" / "models.json")
        self.assertEqual(mcp["mcpServers"], {})
        self.assertEqual(len(models["models"]), 2)

    def test_mcp_json_not_found_creates_new_file(self) -> None:
        """When ~/.codebuddy/mcp.json doesn't exist, sync creates it."""
        result = self._run_codebuddy_sync()

        self.assertIn("mcpServers", result["mcp"])
        self.assertIn("sample", result["mcp"]["mcpServers"])

    def test_models_json_not_found_creates_new_file(self) -> None:
        """When ~/.codebuddy/models.json doesn't exist, sync creates it."""
        result = self._run_codebuddy_sync()

        self.assertIn("models", result["models"])
        self.assertEqual(len(result["models"]["models"]), 2)

    def test_secret_resolution_in_models(self) -> None:
        """Secrets ${codebuddy.url} and ${codebuddy.key} are resolved in model fields."""
        result = self._run_codebuddy_sync()

        model = result["models"]["models"][0]
        self.assertEqual(model["url"], "https://codebuddy.example/v1")
        self.assertEqual(model["apiKey"], "sk-test-codebuddy")

    def test_invalid_models_config_fails_fast(self) -> None:
        """Invalid models config is rejected before writing models.json."""
        with self.assertRaisesRegex(ValueError, "platforms.codebuddy.models must be a list"):
            self._run_codebuddy_sync({"models": {"id": "bad"}})

    def test_invalid_available_models_config_fails_fast(self) -> None:
        """Invalid availableModels config is rejected before writing models.json."""
        with self.assertRaisesRegex(
            ValueError,
            r"platforms\.codebuddy\.availableModels\[0\] must be a non-empty string",
        ):
            self._run_codebuddy_sync({"availableModels": [123]})

    # ── Internal key exclusion ──────────────────────────────────────────────

    def test_internal_keys_excluded_from_output(self) -> None:
        """_comment and platform-internal keys do not leak into output files."""
        result = self._run_codebuddy_sync()

        for key in ("_comment",):
            self.assertNotIn(key, result["mcp"], f"Internal key '{key}' leaked into mcp.json")
            self.assertNotIn(key, result["models"], f"Internal key '{key}' leaked into models.json")


if __name__ == "__main__":
    unittest.main()
