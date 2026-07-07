"""Tests for TOML generation utilities in sync/platforms/common.py."""

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SYNC_DIR = REPO_ROOT / "sync"
if str(SYNC_DIR) not in sys.path:
    sys.path.insert(0, str(SYNC_DIR))

from platforms.common import (  # noqa: E402
    toml_array,
    toml_bare_key_segment,
    toml_header_key_segment,
    toml_inline_table,
    toml_quote,
    toml_section,
    toml_value,
)


class TomlQuoteTests(unittest.TestCase):
    """Tests for toml_quote() — basic string escaping."""

    def test_simple_string(self) -> None:
        self.assertEqual(toml_quote("hello"), '"hello"')

    def test_empty_string(self) -> None:
        self.assertEqual(toml_quote(""), '""')

    def test_backslash_escaped(self) -> None:
        self.assertEqual(toml_quote("a\\b"), '"a\\\\b"')

    def test_double_quote_escaped(self) -> None:
        self.assertEqual(toml_quote('say "hi"'), '"say \\"hi\\""')

    def test_newline_preserved(self) -> None:
        # Newlines inside basic strings must be escaped as \n
        result = toml_quote("line1\nline2")
        self.assertIn("\\n", result)

    def test_tab_preserved(self) -> None:
        result = toml_quote("col1\tcol2")
        self.assertIn("\\t", result)

    def test_unicode_preserved(self) -> None:
        self.assertEqual(toml_quote("café"), '"café"')


class TomlBareKeySegmentTests(unittest.TestCase):
    """Tests for toml_bare_key_segment() — bare key validation."""

    def test_alphanumeric(self) -> None:
        self.assertTrue(toml_bare_key_segment("abc123"))

    def test_with_dash(self) -> None:
        self.assertTrue(toml_bare_key_segment("my-key"))

    def test_with_underscore(self) -> None:
        self.assertTrue(toml_bare_key_segment("my_key"))

    def test_with_dot_fails(self) -> None:
        self.assertFalse(toml_bare_key_segment("my.key"))

    def test_with_space_fails(self) -> None:
        self.assertFalse(toml_bare_key_segment("my key"))

    def test_empty_fails(self) -> None:
        self.assertFalse(toml_bare_key_segment(""))


class TomlHeaderKeySegmentTests(unittest.TestCase):
    """Tests for toml_header_key_segment() — quoted vs bare key in headers."""

    def test_bare_key_unchanged(self) -> None:
        self.assertEqual(toml_header_key_segment("model"), "model")

    def test_key_with_dot_gets_quoted(self) -> None:
        # Dotted keys are split into segments; each segment checked individually
        result = toml_header_key_segment("my.key")
        self.assertEqual(result, "my.key")  # both segments are bare keys

    def test_key_with_special_chars_and_dot(self) -> None:
        # A segment with special chars should be quoted
        result = toml_header_key_segment("my.key/with spaces")
        self.assertIn('"key/with spaces"', result)

    def test_path_like_key_gets_quoted(self) -> None:
        result = toml_header_key_segment("/path/to/project")
        self.assertTrue(result.startswith('"'))


class TomlValueTests(unittest.TestCase):
    """Tests for toml_value() — value serialization."""

    def test_bool_true(self) -> None:
        self.assertEqual(toml_value(True), "true")

    def test_bool_false(self) -> None:
        self.assertEqual(toml_value(False), "false")

    def test_int(self) -> None:
        self.assertEqual(toml_value(42), "42")

    def test_negative_int(self) -> None:
        self.assertEqual(toml_value(-7), "-7")

    def test_float(self) -> None:
        self.assertEqual(toml_value(3.14), "3.14")

    def test_string(self) -> None:
        self.assertEqual(toml_value("hello"), '"hello"')

    def test_list_of_strings(self) -> None:
        result = toml_value(["a", "b", "c"])
        self.assertEqual(result, '["a", "b", "c"]')

    def test_list_of_ints(self) -> None:
        result = toml_value([1, 2, 3])
        self.assertEqual(result, "[1, 2, 3]")

    def test_empty_list(self) -> None:
        self.assertEqual(toml_value([]), "[]")

    def test_bool_not_int(self) -> None:
        # In Python, bool is subclass of int; ensure True -> "true" not "True"
        self.assertEqual(toml_value(True), "true")
        self.assertNotEqual(toml_value(True), "1")


class TomlArrayTests(unittest.TestCase):
    """Tests for toml_array() — array serialization."""

    def test_string_array(self) -> None:
        self.assertEqual(toml_array(["x", "y"]), '["x", "y"]')

    def test_empty_array(self) -> None:
        self.assertEqual(toml_array([]), "[]")

    def test_single_element(self) -> None:
        self.assertEqual(toml_array(["only"]), '["only"]')


class TomlInlineTableTests(unittest.TestCase):
    """Tests for toml_inline_table() — inline table serialization."""

    def test_simple_table(self) -> None:
        result = toml_inline_table({"key": "val"})
        self.assertEqual(result, '{ key = "val" }')

    def test_multiple_keys(self) -> None:
        result = toml_inline_table({"a": "1", "b": "2"})
        self.assertIn('a = "1"', result)
        self.assertIn('b = "2"', result)

    def test_empty_table(self) -> None:
        self.assertEqual(toml_inline_table({}), "{  }")

    def test_mixed_types(self) -> None:
        result = toml_inline_table({"name": "test", "count": 5, "active": True})
        self.assertIn('name = "test"', result)
        self.assertIn("count = 5", result)
        self.assertIn("active = true", result)


class TomlSectionTests(unittest.TestCase):
    """Tests for toml_section() — full TOML section generation."""

    def test_flat_dict(self) -> None:
        result = toml_section({"key1": "val1", "key2": 42})
        self.assertIn('key1 = "val1"', result)
        self.assertIn("key2 = 42", result)

    def test_nested_dict_becomes_table(self) -> None:
        result = toml_section({"parent": {"child_key": "child_val"}})
        self.assertIn("[parent]", result)
        self.assertIn('child_key = "child_val"', result)

    def test_ignore_keys(self) -> None:
        result = toml_section(
            {"keep": "yes", "skip": "no"},
            ignore={"skip"},
        )
        self.assertIn('keep = "yes"', result)
        self.assertNotIn("skip", result)

    def test_default_ignore(self) -> None:
        """Default ignore set should skip env, _comment, projects, model_providers."""
        result = toml_section({
            "model": "gpt-4",
            "env": {"KEY": "val"},
            "_comment": "ignored",
        })
        self.assertIn('model = "gpt-4"', result)
        self.assertNotIn("env", result)
        self.assertNotIn("_comment", result)

    def test_list_values(self) -> None:
        result = toml_section({"items": ["a", "b"]})
        self.assertIn('items = ["a", "b"]', result)

    def test_none_values_skipped(self) -> None:
        result = toml_section({"present": "yes", "absent": None})
        self.assertIn('present = "yes"', result)
        self.assertNotIn("absent", result)

    def test_model_providers_section(self) -> None:
        # model_providers is in default ignore set, so pass empty ignore
        result = toml_section({
            "model_providers": {
                "myprovider": {"base_url": "https://api.example.com", "name": "myprovider"}
            }
        }, ignore=set())
        self.assertIn("[model_providers.myprovider]", result)
        self.assertIn('base_url = "https://api.example.com"', result)

    def test_projects_section(self) -> None:
        # projects is in default ignore set, so pass empty ignore
        result = toml_section({
            "projects": {
                "/path/to/project": {"key": "value"}
            }
        }, ignore=set())
        self.assertIn("[projects.", result)
        self.assertIn('key = "value"', result)

    def test_deeply_nested_dict(self) -> None:
        """Nested dicts within a table should produce sub-tables."""
        result = toml_section({
            "sandbox_write": {
                "nested": {"deep_key": "deep_val"}
            }
        })
        self.assertIn("[sandbox_write]", result)
        self.assertIn("[sandbox_write.nested]", result)
        self.assertIn('deep_key = "deep_val"', result)

    def test_three_level_nesting(self) -> None:
        """Three levels of nesting must produce fully-qualified section headers."""
        result = toml_section({
            "sandbox_write": {
                "nested": {
                    "level3": {"val": "x"}
                }
            }
        })
        self.assertIn("[sandbox_write]", result)
        self.assertIn("[sandbox_write.nested]", result)
        self.assertIn("[sandbox_write.nested.level3]", result)
        self.assertNotIn("[nested.level3]", result)
        self.assertIn('val = "x"', result)


if __name__ == "__main__":
    unittest.main()
