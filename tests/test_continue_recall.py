import importlib
import json
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

from validate_env_schema import (  # noqa: E402
    known_fields_for_platform,
    validate_platform_file,
)
from validate_platform_keys import (  # noqa: E402
    ENGINE_HANDLED_BY_PLATFORM,
    check_platform,
    load_platform_json,
)


class ContinueRulesParseTests(unittest.TestCase):
    def test_parse_rules_absent(self) -> None:
        self.assertIsNone(continue_mod._parse_rules("name: x\nversion: 1\n"))

    def test_parse_rules_simple_items_no_infinite_loop(self) -> None:
        # Regression: a simple `- scalar` item previously caused an infinite
        # loop because the parser never advanced `i`.
        yaml_text = "rules:\n  - always use typescript\n  - keep functions small\n"
        self.assertEqual(
            continue_mod._parse_rules(yaml_text),
            ["always use typescript", "keep functions small"],
        )

    def test_parse_rules_block_scalar_sibling_not_swallowed(self) -> None:
        # Regression for P1: a block scalar must NOT swallow the next sibling
        # `- simple` list item.
        yaml_text = (
            "rules:\n"
            "  - |\n"
            "    keep line 1\n"
            "      nested indent\n"
            "  - simple\n"
        )
        items = continue_mod._parse_rules(yaml_text)
        self.assertEqual(len(items), 2)
        self.assertEqual(items[1], "simple")
        self.assertIn("keep line 1", items[0])
        self.assertIn("nested indent", items[0])

    def test_parse_rules_preserves_relative_indent(self) -> None:
        yaml_text = (
            "rules:\n"
            "  - |\n"
            "    line a\n"
            "      deeper\n"
            "  - other\n"
        )
        items = continue_mod._parse_rules(yaml_text)
        self.assertEqual(items[0], "line a\n  deeper")

    def test_parse_rules_flow_list(self) -> None:
        yaml_text = 'rules: ["a", "b"]\n'
        self.assertEqual(continue_mod._parse_rules(yaml_text), ["a", "b"])

    def test_parse_rules_flow_list_keeps_quoted_commas(self) -> None:
        # Regression for P3: commas inside quoted flow-list items must NOT be
        # treated as separators (["rule A, B", "rule C"] -> 2 items, not 3).
        yaml_text = 'rules: ["rule A, B", "rule C"]\n'
        self.assertEqual(
            continue_mod._parse_rules(yaml_text),
            ["rule A, B", "rule C"],
        )

    def test_render_rules_avoids_unnecessary_quotes(self) -> None:
        # Regression for P4: plain rules render unquoted (clean diffs); only
        # values with YAML-significant characters get double-quoted.
        rendered = continue_mod._render_rules_yaml(
            ["always use typescript", "rule A, B", "has: colon space"]
        )
        self.assertIn("  - always use typescript\n", rendered)
        self.assertIn("  - rule A, B\n", rendered)  # comma is fine unquoted
        self.assertIn('  - "has: colon space"\n', rendered)  # colon+space quoted

    def test_parse_then_render_roundtrip_preserves_commas(self) -> None:
        # Combined P3+P4: a quoted-comma flow list round-trips without loss.
        yaml_text = 'rules: ["rule A, B", "rule C"]\n'
        items = continue_mod._parse_rules(yaml_text)
        rendered = continue_mod._render_rules_yaml(items)
        self.assertEqual(continue_mod._parse_rules(rendered), items)

    def test_folded_scalar_renders_inline_not_literal(self) -> None:
        # Regression for H-2: a `>` (folded) scalar must NOT be re-emitted as a
        # literal `|` block. Newlines are folded into spaces, so the rule is a
        # single inline value.
        yaml_text = (
            "rules:\n"
            "  - >\n"
            "    line one\n"
            "    line two\n"
            "  - simple\n"
        )
        items = continue_mod._parse_rules(yaml_text)
        self.assertEqual(items[0], "line one line two")
        rendered = continue_mod._render_rules_yaml(items)
        self.assertIn("  - line one line two\n", rendered)
        self.assertNotIn("  - |\n", rendered)

    def test_literal_scalar_renders_as_literal_block(self) -> None:
        # A `|` (literal) scalar must keep newlines and render as a `|` block.
        yaml_text = (
            "rules:\n"
            "  - |\n"
            "    keep raw\n"
            "      deeper\n"
        )
        items = continue_mod._parse_rules(yaml_text)
        self.assertIn("\n", items[0])
        rendered = continue_mod._render_rules_yaml(items)
        self.assertIn("  - |\n", rendered)
        self.assertIn("    keep raw\n", rendered)

    def test_folded_then_literal_roundtrip(self) -> None:
        yaml_text = (
            "rules:\n"
            "  - >\n"
            "    folded line\n"
            "  - |\n"
            "    literal line\n"
            "      indented\n"
        )
        items = continue_mod._parse_rules(yaml_text)
        rendered = continue_mod._render_rules_yaml(items)
        reparsed = continue_mod._parse_rules(rendered)
        self.assertEqual(reparsed[0], "folded line")
        self.assertIn("literal line", reparsed[1])
        self.assertIn("indented", reparsed[1])

    def test_render_rules_quotes_yaml_reserved_words(self) -> None:
        # Regression for P5: a rule whose text equals a YAML reserved word
        # (null/~ -> None, true/false -> bool) must be double-quoted so a real
        # YAML parser reads it back as the literal string, not a non-string.
        rendered = continue_mod._render_rules_yaml(["null", "~", "true", "false"])
        self.assertIn('  - "null"\n', rendered)
        self.assertIn('  - "~"\n', rendered)
        self.assertIn('  - "true"\n', rendered)
        self.assertIn('  - "false"\n', rendered)

    def test_parse_then_render_roundtrip_preserves_reserved_words(self) -> None:
        # Combined P5: reserved-word rules survive a parse->render->parse cycle
        # as the literal strings they started as.
        yaml_text = 'rules: ["null", "~", "true", "false"]\n'
        items = continue_mod._parse_rules(yaml_text)
        self.assertEqual(items, ["null", "~", "true", "false"])
        rendered = continue_mod._render_rules_yaml(items)
        self.assertEqual(continue_mod._parse_rules(rendered), items)


class ContinueSyncRecallTests(unittest.TestCase):
    def test_sync_recall_injects_absolute_paths(self) -> None:
        out = continue_mod._sync_recall({}, "")
        self.assertIn(continue_mod._RECALL_BEGIN, out)
        # Skill path must be absolute and point at the repo source.
        self.assertIn("skills-engineering/historical-recall/SKILL.md", out)
        # CLI path must be absolute (works from any cwd).
        import re

        m = re.search(r"node (\S+) recall", out)
        self.assertIsNotNone(m)
        self.assertTrue(Path(m.group(1)).is_absolute())

    def test_sync_recall_idempotent(self) -> None:
        out1 = continue_mod._sync_recall({}, "")
        out2 = continue_mod._sync_recall({}, out1)
        self.assertEqual(out1.count(continue_mod._RECALL_BEGIN), 1)
        self.assertEqual(out2.count(continue_mod._RECALL_BEGIN), 1)

    def test_sync_recall_opt_out(self) -> None:
        # platforms.continue.recall=false must skip injection entirely.
        yaml_text = "rules:\n  - user rule\n"
        out = continue_mod._sync_recall({"recall": False}, yaml_text)
        self.assertEqual(out, yaml_text)
        self.assertNotIn(continue_mod._RECALL_BEGIN, out)

    def test_sync_recall_preserves_user_rules(self) -> None:
        yaml_text = (
            "name: x\n"
            "rules:\n"
            "  - always use typescript\n"
            "  - |\n"
            "    keep functions small\n"
        )
        out = continue_mod._sync_recall({}, yaml_text)
        self.assertIn("always use typescript", out)
        self.assertIn("keep functions small", out)
        self.assertEqual(out.count(continue_mod._RECALL_BEGIN), 1)

    def test_sync_recall_replaces_prior_block(self) -> None:
        # A pre-existing (stale) recall block is replaced, not duplicated.
        stale = (
            "rules:\n"
            "  - user rule\n"
            "  - <!-- managed-block:historical-recall:begin (old) -->\n"
            "    OLD\n"
            "    <!-- managed-block:historical-recall:end -->\n"
        )
        out = continue_mod._sync_recall({}, stale)
        self.assertEqual(out.count(continue_mod._RECALL_BEGIN), 1)
        self.assertIn("user rule", out)
        self.assertNotIn("OLD", out)

    def test_repo_root_resolves_via_skills_engineering(self) -> None:
        # Regression for M-1: _repo_root() must find the repo root by locating
        # the skills-engineering/ marker, not rely on a brittle parents[N].
        root = continue_mod._repo_root()
        self.assertTrue((root / "skills-engineering").is_dir())
        self.assertEqual(root, REPO_ROOT)


class ContinueRecallValidationTests(unittest.TestCase):
    def test_recall_allowed_in_continue_schema(self) -> None:
        self.assertIn("recall", known_fields_for_platform("continue"))
        self.assertIn("recall", ENGINE_HANDLED_BY_PLATFORM["continue"])

    def test_validate_platform_file_allows_recall(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "continue.json"
            p.write_text(
                json.dumps({"models": [], "path": "x", "recall": False}),
                encoding="utf-8",
            )
            self.assertEqual(validate_platform_file(p), [])

    def test_check_platform_allows_recall(self) -> None:
        # Monkeypatch the loader so we don't touch the real env/platforms file.
        original = load_platform_json
        validate_platform_keys_module = sys.modules[load_platform_json.__module__]
        validate_platform_keys_module.load_platform_json = (
            lambda platform: {"models": [], "path": "x", "recall": False}
        )
        try:
            warnings = check_platform("continue")
            self.assertEqual(warnings, [])
        finally:
            validate_platform_keys_module.load_platform_json = original


if __name__ == "__main__":
    unittest.main()
