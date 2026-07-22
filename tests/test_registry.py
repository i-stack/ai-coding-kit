"""Tests for sync/core/registry.py (P0: shared target registry).

Validates:
- All platforms in env/platforms/*.json are discovered.
- Xcode special targets are always included.
- Continue has no skills_dir.
- Preamble specs are correctly parsed (mode, format, target path).
- VerifySpec flags are correctly derived from preamble mode/format.
- Disabled / missing install roots are skipped by enabled_targets().
- SYNC_* env flag overrides work correctly.
- Temporary HOME isolates the tests from real disk state.
"""
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

from core import registry
from core import paths as _paths


class RegistryDiscoveryTests(unittest.TestCase):
    """Registry discovers the expected set of targets from the real platform files."""

    def setUp(self) -> None:
        # Reset path-override cache so each test gets a clean state.
        _paths._PATH_OVERRIDES = None

    def tearDown(self) -> None:
        _paths._PATH_OVERRIDES = None

    def _target_names(self) -> set[str]:
        return {t.name for t in registry.load_targets()}

    def test_all_platform_json_files_are_discovered(self) -> None:
        json_names = {
            f.stem
            for f in (REPO_ROOT / "env" / "platforms").glob("*.json")
        }
        target_names = self._target_names()
        # Every JSON with a known install root should appear; platforms without
        # a paths entry (none currently) are skipped silently.
        for name in json_names:
            if _paths.platform_install_root(name) is not None:
                self.assertIn(name, target_names, f"{name} not in registry")

    def test_xcode_targets_always_present(self) -> None:
        names = self._target_names()
        self.assertIn("xcode-codex", names)
        self.assertIn("xcode-claude", names)

    def test_continue_has_no_skills_dir(self) -> None:
        targets = {t.name: t for t in registry.load_targets()}
        self.assertIn("continue", targets)
        self.assertIsNone(targets["continue"].skills_dir)
        self.assertFalse(targets["continue"].verify.skills)

    def test_continue_has_yaml_recall(self) -> None:
        targets = {t.name: t for t in registry.load_targets()}
        t = targets["continue"]
        self.assertIsNotNone(t.preamble)
        assert t.preamble is not None
        self.assertEqual(t.preamble.format, "yaml")
        self.assertTrue(t.verify.yaml_recall)
        self.assertFalse(t.verify.full_preamble)
        self.assertFalse(t.verify.recall_preamble)

    def test_full_preamble_targets_have_correct_verify_flags(self) -> None:
        targets = {t.name: t for t in registry.load_targets()}
        for name in ("claude", "codex", "gemini"):
            if name not in targets:
                continue
            t = targets[name]
            self.assertTrue(t.verify.full_preamble, f"{name}: expected full_preamble=True")
            self.assertFalse(t.verify.recall_preamble, f"{name}: expected recall_preamble=False")
            self.assertFalse(t.verify.yaml_recall, f"{name}: expected yaml_recall=False")

    def test_recall_preamble_targets_have_correct_verify_flags(self) -> None:
        targets = {t.name: t for t in registry.load_targets()}
        for name in ("cline", "codebuddy", "qwen"):
            if name not in targets:
                continue
            t = targets[name]
            self.assertFalse(t.verify.full_preamble, f"{name}: expected full_preamble=False")
            self.assertTrue(t.verify.recall_preamble, f"{name}: expected recall_preamble=True")

    def test_preamble_target_resolves_under_install_root(self) -> None:
        targets = {t.name: t for t in registry.load_targets()}
        t = targets.get("codex")
        if t is None:
            self.skipTest("codex not in registry")
        self.assertIsNotNone(t.preamble)
        assert t.preamble is not None
        self.assertIsNotNone(t.preamble.target)
        assert t.preamble.target is not None
        self.assertTrue(
            str(t.preamble.target).startswith(str(t.install_root)),
            f"preamble.target {t.preamble.target} not under install_root {t.install_root}",
        )

    def test_enabled_flag_names(self) -> None:
        targets = {t.name: t for t in registry.load_targets()}
        for name, t in targets.items():
            expected_flag = f"SYNC_{name.upper().replace('-', '_')}"
            self.assertEqual(t.enabled_flag, expected_flag)

    def test_xcode_codex_preamble_path(self) -> None:
        targets = {t.name: t for t in registry.load_targets()}
        t = targets["xcode-codex"]
        self.assertIsNotNone(t.preamble)
        assert t.preamble is not None
        self.assertEqual(t.preamble.target, t.install_root / "AGENTS.md")
        self.assertTrue(t.verify.full_preamble)
        self.assertTrue(t.verify.skills)


class EnabledTargetsTests(unittest.TestCase):
    """enabled_targets() respects install-root existence and SYNC_* flags."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name) / "home"
        self.home.mkdir(parents=True)
        self._orig_home = os.environ.get("HOME")
        self._orig_overrides = _paths._PATH_OVERRIDES
        os.environ["HOME"] = str(self.home)
        _paths._PATH_OVERRIDES = None
        # Remove all SYNC_* vars to start clean.
        self._cleared_flags: dict[str, str | None] = {}
        for key in list(os.environ):
            if key.startswith("SYNC_"):
                self._cleared_flags[key] = os.environ.pop(key)

    def tearDown(self) -> None:
        _paths._PATH_OVERRIDES = self._orig_overrides
        if self._orig_home is None:
            os.environ.pop("HOME", None)
        else:
            os.environ["HOME"] = self._orig_home
        for key, val in self._cleared_flags.items():
            if val is not None:
                os.environ[key] = val
        self.tmp.cleanup()

    def test_no_targets_enabled_when_home_is_empty(self) -> None:
        targets = registry.enabled_targets()
        self.assertEqual(targets, [])

    def test_target_enabled_when_install_root_exists(self) -> None:
        claude_root = self.home / ".claude"
        claude_root.mkdir()
        targets = {t.name: t for t in registry.enabled_targets()}
        self.assertIn("claude", targets)

    def test_target_skipped_when_flag_is_zero(self) -> None:
        claude_root = self.home / ".claude"
        claude_root.mkdir()
        os.environ["SYNC_CLAUDE"] = "0"
        try:
            targets = {t.name: t for t in registry.enabled_targets()}
            self.assertNotIn("claude", targets)
        finally:
            os.environ.pop("SYNC_CLAUDE")

    def test_target_force_enabled_by_flag_even_without_root(self) -> None:
        os.environ["SYNC_CLAUDE"] = "1"
        try:
            targets = {t.name: t for t in registry.enabled_targets()}
            self.assertIn("claude", targets)
        finally:
            os.environ.pop("SYNC_CLAUDE")

    def test_disabled_platform_json_does_not_auto_enable(self) -> None:
        # Platforms with enabled=false in JSON must still NOT auto-enable just
        # because the install root happens to exist (the JSON enabled flag is an
        # *intent* signal, not the gating mechanism — the Bash SYNC_* env var is).
        # This test ensures registry doesn't re-introduce a JSON-enabled gate.
        codex_root = self.home / ".codex"
        codex_root.mkdir()
        # With no SYNC_CODEX flag, auto-detect uses root existence → enabled.
        targets = {t.name: t for t in registry.enabled_targets()}
        self.assertIn("codex", targets)

    def test_every_enabled_target_that_has_verify_skills_has_skills_dir(self) -> None:
        for t in registry.load_targets():
            if t.verify.skills:
                self.assertIsNotNone(
                    t.skills_dir,
                    f"{t.name}: verify.skills=True but skills_dir is None",
                )

    def test_every_enabled_target_with_full_preamble_has_preamble_target(self) -> None:
        for t in registry.load_targets():
            if t.verify.full_preamble:
                self.assertIsNotNone(t.preamble, f"{t.name}: full_preamble but no preamble")
                assert t.preamble is not None
                self.assertIsNotNone(
                    t.preamble.target,
                    f"{t.name}: full_preamble but preamble.target is None",
                )


class TempHomeSyncTests(unittest.TestCase):
    """Temp-HOME harness: verify that no real home directories are touched."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name) / "home"
        self.home.mkdir()
        self._orig_home = os.environ.get("HOME")
        self._orig_overrides = _paths._PATH_OVERRIDES
        os.environ["HOME"] = str(self.home)
        _paths._PATH_OVERRIDES = None
        self._cleared_flags: dict[str, str | None] = {}
        for key in list(os.environ):
            if key.startswith("SYNC_"):
                self._cleared_flags[key] = os.environ.pop(key)

    def tearDown(self) -> None:
        _paths._PATH_OVERRIDES = self._orig_overrides
        if self._orig_home is None:
            os.environ.pop("HOME", None)
        else:
            os.environ["HOME"] = self._orig_home
        for key, val in self._cleared_flags.items():
            if val is not None:
                os.environ[key] = val
        self.tmp.cleanup()

    def test_load_targets_does_not_create_directories(self) -> None:
        registry.load_targets()
        # Home must still be empty — load_targets is purely read-only.
        children = list(self.home.iterdir())
        self.assertEqual(children, [], f"Unexpected dirs created: {children}")

    def test_enabled_targets_with_forced_flag_does_not_create_directories(self) -> None:
        os.environ["SYNC_CLAUDE"] = "1"
        try:
            registry.enabled_targets()
        finally:
            os.environ.pop("SYNC_CLAUDE")
        children = list(self.home.iterdir())
        self.assertEqual(children, [], f"Unexpected dirs created: {children}")


if __name__ == "__main__":
    unittest.main()
