import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SYNC_DIR = REPO_ROOT / "sync"
if str(SYNC_DIR) not in sys.path:
    sys.path.insert(0, str(SYNC_DIR))

from core import common  # noqa: E402
from core import paths  # noqa: E402


class PathsOverrideTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.env = self.root / "env"
        self.env.mkdir(parents=True, exist_ok=True)
        self.secrets = self.env / "secrets.json"
        self.config = self.env / "config.json"
        # Save globals we monkeypatch BEFORE patching, so tearDown can restore
        # them and avoid leaking a dangling temp path into later tests.
        self._orig_common_secrets_path = common.SECRETS_PATH
        self._orig_paths_config_path = paths.CONFIG_PATH
        # Reset module-level cache so each test re-reads the patched path.
        paths._PATH_OVERRIDES = None
        common.SECRETS_PATH = self.secrets
        paths.CONFIG_PATH = self.config

    def tearDown(self) -> None:
        paths._PATH_OVERRIDES = None
        paths.CONFIG_PATH = self._orig_paths_config_path
        common.SECRETS_PATH = self._orig_common_secrets_path
        self.tmp.cleanup()

    def _write_secrets(self, data: dict) -> None:
        self.secrets.write_text(json.dumps(data) + "\n", encoding="utf-8")

    def _write_config(self, data) -> None:
        if isinstance(data, (dict, list)):
            text = json.dumps(data) + "\n"
        else:
            text = data  # allow writing malformed JSON for negative tests
        self.config.write_text(text, encoding="utf-8")

    def test_defaults_when_no_paths_key(self) -> None:
        self._write_secrets({"github": {"token": "x"}})
        self.assertEqual(paths.codex_root_dir(), Path.home() / ".codex")
        self.assertEqual(paths.claude_root_dir(), Path.home() / ".claude")
        self.assertEqual(paths.gemini_root_dir(), Path.home() / ".gemini")
        self.assertEqual(paths.codebuddy_root_dir(), Path.home() / ".codebuddy")
        self.assertEqual(paths.cursor_mcp_path(), Path.home() / ".cursor" / "mcp.json")
        self.assertEqual(paths.cline_root_dir(), Path.home() / ".cline")
        self.assertEqual(paths.continue_root_dir(), Path.home() / ".continue")
        self.assertEqual(paths.qwen_root_dir(), Path.home() / ".qwen")
        self.assertEqual(
            paths.xcode_coding_assistant_dir(),
            Path.home() / "Library/Developer/Xcode/CodingAssistant",
        )

    def test_overrides_resolve_all_derived_paths(self) -> None:
        self._write_config({
            "paths": {
                "codex": "/opt/codex",
                "claude": "/custom/.claude",
                "gemini": "/custom/.gemini",
                "codebuddy": "/custom/.codebuddy",
                "cursor": "/custom/.cursor",
                "cline": "/custom/.cline",
                "continue": "/custom/.continue",
                "qwen": "/custom/.qwen",
                "xcode_coding_assistant": "~/Xcode/CA",
            }
        })
        # Expand ~ for the xcode case.
        xcode = (Path.home() / "Xcode/CA").resolve()

        self.assertEqual(paths.codex_root_dir(), Path("/opt/codex"))
        self.assertEqual(paths.codex_config_path(), Path("/opt/codex/config.toml"))
        self.assertEqual(paths.codex_skills_base(), Path("/opt/codex/skills"))

        self.assertEqual(paths.claude_root_dir(), Path("/custom/.claude"))
        self.assertEqual(paths.claude_settings_json_path(), Path("/custom/.claude/settings.json"))
        self.assertEqual(paths.claude_config_json_path(), Path("/custom/.claude/config.json"))
        self.assertEqual(paths.claude_hooks_dir_path(), Path("/custom/.claude/hooks"))
        # .claude.json is the global config in $HOME, NOT affected by the
        # install-root override (which only relocates ~/.claude/).
        self.assertEqual(paths.claude_json_path(), Path.home() / ".claude.json")
        self.assertEqual(paths.claude_skills_base(), Path("/custom/.claude/skills"))

        self.assertEqual(paths.gemini_root_dir(), Path("/custom/.gemini"))
        self.assertEqual(paths.gemini_settings_path(), Path("/custom/.gemini/settings.json"))
        self.assertEqual(paths.gemini_skills_base(), Path("/custom/.gemini/skills"))

        self.assertEqual(paths.codebuddy_root_dir(), Path("/custom/.codebuddy"))
        self.assertEqual(paths.codebuddy_mcp_path(), Path("/custom/.codebuddy/mcp.json"))
        self.assertEqual(paths.codebuddy_models_path(), Path("/custom/.codebuddy/models.json"))
        self.assertEqual(paths.codebuddy_skills_base(), Path("/custom/.codebuddy/skills"))

        self.assertEqual(paths.cursor_mcp_path(), Path("/custom/.cursor/mcp.json"))
        self.assertEqual(paths.cursor_skills_base(), Path("/custom/.cursor/skills"))

        self.assertEqual(paths.cline_root_dir(), Path("/custom/.cline"))
        self.assertEqual(paths.cline_data_dir(), Path("/custom/.cline/data"))
        self.assertEqual(paths.cline_global_state_path(), Path("/custom/.cline/data/globalState.json"))
        self.assertEqual(paths.cline_secrets_path(), Path("/custom/.cline/data/secrets.json"))
        self.assertEqual(paths.cline_skills_base(), Path("/custom/.cline/skills"))

        self.assertEqual(paths.continue_root_dir(), Path("/custom/.continue"))

        self.assertEqual(paths.qwen_root_dir(), Path("/custom/.qwen"))
        self.assertEqual(paths.qwen_settings_json_path(), Path("/custom/.qwen/settings.json"))
        self.assertEqual(paths.qwen_skills_base(), Path("/custom/.qwen/skills"))

        self.assertEqual(paths.xcode_coding_assistant_dir(), xcode)
        self.assertEqual(paths.xcode_codex_dir(), xcode / "codex")
        self.assertEqual(paths.xcode_claude_dir(), xcode / "ClaudeAgentConfig/.claude")
        self.assertEqual(paths.xcode_gemini_dir(), xcode / "gemini")
        self.assertEqual(paths.xcode_codex_skills_base(), xcode / "codex" / "skills")
        self.assertEqual(paths.xcode_claude_skills_base(), xcode / "ClaudeAgentConfig/skills")

    def test_empty_string_falls_back_to_default(self) -> None:
        self._write_config({"paths": {"codex": "", "claude": "   "}})
        self.assertEqual(paths.codex_root_dir(), Path.home() / ".codex")
        self.assertEqual(paths.claude_root_dir(), Path.home() / ".claude")

    def test_platform_install_root_reflects_override(self) -> None:
        self._write_config({"paths": {"codex": "/alt/codex"}})
        self.assertEqual(paths.platform_install_root("codex"), Path("/alt/codex"))
        self.assertEqual(paths.platform_install_root("claude"), Path.home() / ".claude")

    def test_malformed_config_is_safe(self) -> None:
        self._write_config("{ not valid json")
        self.assertEqual(paths.codex_root_dir(), Path.home() / ".codex")

    def test_cursor_root_registered_and_override_reflected(self) -> None:
        # Regression for P1: cursor must participate in the "skip if not
        # installed" contract via platform_install_root(), and overrides must
        # propagate to its derived paths.
        self._write_config({"paths": {"cursor": "/opt/cursor"}})
        self._write_secrets({"codex": {"key": "sk-x"}})
        self.assertEqual(paths.platform_install_root("cursor"), Path("/opt/cursor"))
        self.assertFalse(paths.platform_is_installed("cursor"))
        self.assertEqual(paths.cursor_root_dir(), Path("/opt/cursor"))
        self.assertEqual(paths.cursor_mcp_path(), Path("/opt/cursor/mcp.json"))
        self.assertEqual(paths.cursor_skills_base(), Path("/opt/cursor/skills"))

    def test_config_paths_not_exposed_as_secret_placeholder(self) -> None:
        # config.json's `paths` must NOT be flattened into secrets, so
        # ${paths.codex} cannot be resolved / injected into other configs.
        self._write_secrets({"codex": {"key": "sk-real"}})
        self._write_config({"paths": {"codex": "/opt/codex"}})
        common.SECRETS_PATH = self.secrets
        flat = common.load_secrets()
        self.assertIn("codex.key", flat)
        self.assertNotIn("paths", flat)
        self.assertNotIn("paths.codex", flat)
        # A ${paths.codex} reference must remain unresolved.
        self.assertEqual(
            common.resolve_secrets("${paths.codex}", flat),
            "${paths.codex}",
        )

    def test_nested_paths_still_flattened(self) -> None:
        # A nested `paths` key inside a platform must be flattened like any
        # other field, so ${somePlatform.paths} resolves normally.
        self._write_secrets({
            "somePlatform": {"paths": "/nested/path", "key": "sk-x"},
        })
        common.SECRETS_PATH = self.secrets
        flat = common.load_secrets()
        self.assertIn("somePlatform.paths", flat)
        self.assertEqual(flat["somePlatform.paths"], "/nested/path")
        self.assertEqual(
            common.resolve_secrets("${somePlatform.paths}", flat),
            "/nested/path",
        )

    def test_bogus_tilde_user_does_not_crash(self) -> None:
        # Regression for H-1: a dangling `~nonexistent-user` override previously
        # raised KeyError/RuntimeError from expanduser() OUTSIDE the try block,
        # crashing the whole sync engine. It must be skipped, and sibling valid
        # overrides must still resolve.
        self._write_config({
            "paths": {
                "cline": "/custom/.cline",
                "codebuddy": "~nonexistent_user_zzz12345/x",
            }
        })
        import os

        orig = os.path.expanduser
        # Simulate the pre-3.12 behavior that raises on a missing ~user.
        def _raising(p):
            if p.startswith("~nonexistent_user"):
                raise KeyError("expanduser(): unknown user")
            return orig(p)

        os.path.expanduser = _raising
        try:
            # Must not raise.
            overrides = paths._load_path_overrides()
        finally:
            os.path.expanduser = orig
        # Valid sibling override still resolves; bad entry is skipped.
        self.assertEqual(paths.cline_root_dir(), Path("/custom/.cline"))
        self.assertNotIn("codebuddy", overrides)


if __name__ == "__main__":
    unittest.main()
