import importlib
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SYNC_DIR = REPO_ROOT / "sync"
if str(SYNC_DIR) not in sys.path:
    sys.path.insert(0, str(SYNC_DIR))

# `continue` is a Python keyword, so import via importlib like sync_config.py does.
continue_mod = importlib.import_module("platforms.continue")


MODELS = [
    {
        "name": "deepseek-v4-pro",
        "provider": "openai",
        "model": "deepseek-v4-pro",
        "apiKey": "${continue.key}",
        "apiBase": "${continue.url}",
        "defaultCompletionOptions": {"maxTokens": 128000},
    }
]


class ContinueApiToggleTests(unittest.TestCase):
    def test_api_enabled_default_true(self) -> None:
        self.assertTrue(continue_mod._api_enabled({}))
        self.assertTrue(continue_mod._api_enabled({"api": {}}))

    def test_api_enabled_explicit(self) -> None:
        self.assertTrue(continue_mod._api_enabled({"api": {"enabled": True}}))
        self.assertFalse(continue_mod._api_enabled({"api": {"enabled": False}}))


class ContinueRemoveYamlRootKeyTests(unittest.TestCase):
    def test_removes_key_with_nested_block(self) -> None:
        text = (
            "name: x\n"
            "models:\n"
            "  - name: a\n"
            "    provider: openai\n"
            "version: 1\n"
        )
        out = continue_mod._remove_yaml_root_key(text, "models")
        self.assertNotIn("models:", out)
        self.assertIn("name: x", out)
        self.assertIn("version: 1", out)

    def test_removes_missing_key_is_noop(self) -> None:
        text = "name: x\nversion: 1\n"
        out = continue_mod._remove_yaml_root_key(text, "models")
        self.assertEqual(out, text)


class ContinueSyncModelsTests(unittest.TestCase):
    def setUp(self) -> None:
        # continue.sync() reads the module-global continue_root_dir(); some
        # tests monkeypatch it, so save and restore to avoid leaking the patch
        # into other test modules that share this process.
        self._orig_root_dir = continue_mod.continue_root_dir

    def tearDown(self) -> None:
        continue_mod.continue_root_dir = self._orig_root_dir  # type: ignore[assignment]

    def _sync(self, tmp: Path, cfg: dict, mcp: dict | None = None) -> Path:
        root = tmp / ".continue"
        root.mkdir(parents=True, exist_ok=True)
        continue_mod.continue_root_dir = lambda: root  # type: ignore[assignment]
        cfg = dict(cfg)
        cfg_path = tmp / "config.yaml"
        cfg["path"] = str(cfg_path)
        continue_mod.sync(mcp or {}, cfg)
        return cfg_path

    def test_enable_by_default_writes_models(self) -> None:
        # No `api` block at all -> historical always-sync behavior preserved.
        with tempfile.TemporaryDirectory() as d:
            cfg_path = self._sync(Path(d), {"models": MODELS, "preamble": {"mode": "none"}})
            text = cfg_path.read_text(encoding="utf-8")
            self.assertIn("models:", text)
            self.assertIn("deepseek-v4-pro", text)

    def test_enable_explicit_writes_models(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            cfg_path = self._sync(
                Path(d),
                {"api": {"enabled": True}, "models": MODELS, "preamble": {"mode": "none"}},
            )
            text = cfg_path.read_text(encoding="utf-8")
            self.assertIn("models:", text)
            self.assertIn("deepseek-v4-pro", text)

    def test_disable_removes_models_preserves_user_fields(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            cfg_path = self._sync(
                tmp,
                {
                    "api": {"enabled": False},
                    "models": MODELS,
                    "preamble": {"mode": "none"},
                },
            )
            # Seed a pre-existing config with user-owned keys + managed models.
            cfg_path.write_text(
                "name: myconfig\n"
                "version: 1\n"
                "models:\n"
                "  - name: user-model\n"
                "    provider: openai\n",
                encoding="utf-8",
            )
            # Re-run with API disabled; models block must be removed but user
            # keys must survive.
            root = tmp / ".continue"
            continue_mod.continue_root_dir = lambda: root  # type: ignore[assignment]
            continue_mod.sync(
                {},
                {
                    "path": str(cfg_path),
                    "api": {"enabled": False},
                    "models": MODELS,
                    "preamble": {"mode": "none"},
                },
            )
            text = cfg_path.read_text(encoding="utf-8")
            self.assertNotIn("models:", text)
            self.assertIn("name: myconfig", text)
            self.assertIn("version: 1", text)

    def test_disable_still_syncs_mcp(self) -> None:
        # MCP servers are independent of API sync.
        with tempfile.TemporaryDirectory() as d:
            cfg_path = self._sync(
                Path(d),
                {
                    "api": {"enabled": False},
                    "models": MODELS,
                    "preamble": {"mode": "none"},
                },
                mcp={"demo": {"url": "https://example.com/mcp", "type": "sse"}},
            )
            text = cfg_path.read_text(encoding="utf-8")
            self.assertNotIn("models:", text)
            self.assertIn("mcpServers:", text)
            self.assertIn("demo", text)

    def test_idempotent_resync(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            # First run creates the file from an absent target.
            cfg_path = self._sync(Path(d), {"models": MODELS, "preamble": {"mode": "none"}})
            # Second and third runs operate on an already-present file; the
            # output must reach a fixpoint and the managed block must not be
            # duplicated.
            root = Path(d) / ".continue"
            for _ in range(2):
                continue_mod.continue_root_dir = lambda: root  # type: ignore[assignment]
                continue_mod.sync(
                    {},
                    {
                        "path": str(cfg_path),
                        "models": MODELS,
                        "preamble": {"mode": "none"},
                    },
                )
            text = cfg_path.read_text(encoding="utf-8")
            self.assertEqual(text.count("models:"), 1)
            self.assertIn("deepseek-v4-pro", text)
            # Re-running on the fixpoint yields no further change.
            before = text
            continue_mod.continue_root_dir = lambda: root  # type: ignore[assignment]
            continue_mod.sync(
                {},
                {
                    "path": str(cfg_path),
                    "models": MODELS,
                    "preamble": {"mode": "none"},
                },
            )
            self.assertEqual(cfg_path.read_text(encoding="utf-8"), before)

    def test_reenable_restores_models(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            root = tmp / ".continue"
            root.mkdir(parents=True, exist_ok=True)
            continue_mod.continue_root_dir = lambda: root  # type: ignore[assignment]
            cfg_path = tmp / "config.yaml"

            # First sync with API disabled (models removed).
            continue_mod.sync(
                {},
                {
                    "path": str(cfg_path),
                    "api": {"enabled": False},
                    "models": MODELS,
                    "preamble": {"mode": "none"},
                },
            )
            self.assertNotIn("models:", cfg_path.read_text(encoding="utf-8"))

            # Then re-enable -> models block restored.
            continue_mod.sync(
                {},
                {
                    "path": str(cfg_path),
                    "api": {"enabled": True},
                    "models": MODELS,
                    "preamble": {"mode": "none"},
                },
            )
            text = cfg_path.read_text(encoding="utf-8")
            self.assertIn("models:", text)
            self.assertIn("deepseek-v4-pro", text)


if __name__ == "__main__":
    unittest.main()
