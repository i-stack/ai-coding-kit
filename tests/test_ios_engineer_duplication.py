import importlib.util
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace


REPO_ROOT = Path(__file__).resolve().parents[1]
TOOL_PATH = REPO_ROOT / "tools" / "duplication" / "analyze_duplication.py"


def load_duplication_tool():
    spec = importlib.util.spec_from_file_location("ios_engineer_analyze_duplication", TOOL_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


dup = load_duplication_tool()


class IosEngineerDuplicationTests(unittest.TestCase):
    def test_extract_shell_functions_normalizes_equivalent_bodies(self) -> None:
        text_a = """
lock_one() {
  for _ in 1 2 3; do
    if mkdir "$LOCK_DIR" 2>/dev/null; then break; fi
    sleep 0.1
  done
  trap cleanup EXIT
}
"""
        text_b = """
lock_two() {
  for attempt in 1 2 3; do
    if mkdir "${other_lock}" 2>/dev/null; then break; fi
    sleep 0.1
  done
  trap cleanup EXIT
}
"""

        funcs_a = dup.extract_shell_functions(text_a)
        funcs_b = dup.extract_shell_functions(text_b)

        self.assertEqual(funcs_a[0].name, "lock_one")
        self.assertEqual(funcs_b[0].name, "lock_two")
        self.assertEqual(funcs_a[0].normalized_body, funcs_b[0].normalized_body)

    def test_repeated_blocks_detects_cross_file_copied_logic(self) -> None:
        block = """
if [ -z "$input" ]; then
  echo "missing input"
  exit 1
fi
mkdir -p "$output"
printf "%s\\n" "$input" > "$output/file.txt"
"""
        fps = [
            SimpleNamespace(rel="scripts/a.sh", ext=".sh", content=f"a() {{\n{block}\n}}"),
            SimpleNamespace(rel="scripts/b.sh", ext=".sh", content=f"b() {{\n{block}\n}}"),
            SimpleNamespace(rel="scripts/c.sh", ext=".sh", content="echo unrelated"),
        ]

        repeated = dup.extract_repeated_blocks(fps, block_size=4)

        self.assertTrue(repeated)
        self.assertEqual(repeated[0]["files"], ["scripts/a.sh", "scripts/b.sh"])

    def test_representative_blocks_collapse_same_file_set(self) -> None:
        repeated = [
            {"files": ["a.sh", "b.sh"], "occurrences": [], "lines": 8, "sample": ()},
            {"files": ["a.sh", "b.sh"], "occurrences": [], "lines": 8, "sample": ()},
            {"files": ["a.sh", "c.sh"], "occurrences": [], "lines": 8, "sample": ()},
        ]

        selected = dup.select_representative_blocks(repeated)

        self.assertEqual(len(selected), 2)
        self.assertEqual(selected[0]["files"], ["a.sh", "b.sh"])
        self.assertEqual(selected[1]["files"], ["a.sh", "c.sh"])

    def test_usage_function_is_noisy_name(self) -> None:
        self.assertIn("usage", dup.NOISY_FUNCTION_NAMES)

    def test_markdown_paragraphs_ignore_tables_and_code_blocks(self) -> None:
        text = """
# Title

This paragraph is intentionally long enough to be considered for duplication detection because it describes a real rule body and not just a heading.

| A | B |
|---|---|
| 1 | 2 |

```bash
This code block is intentionally long enough but should be ignored by paragraph extraction.
```
"""

        paragraphs = dup.extract_markdown_paragraphs(text)

        self.assertEqual(len(paragraphs), 1)
        self.assertIn("intentionally long enough", paragraphs[0][1])

    def test_root_entrypoint_analyzes_arbitrary_directory_without_modifying_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "target"
            output = root / "reports"
            target.mkdir()
            source = target / "sample.sh"
            original = """#!/usr/bin/env bash
first() {
  echo "hello"
}
"""
            source.write_text(original, encoding="utf-8")

            report_path = dup.main([str(target), "--output-dir", str(output)])

            self.assertEqual(source.read_text(encoding="utf-8"), original)
            self.assertTrue(Path(report_path).exists())
            self.assertFalse((output / "all_fingerprints.json").exists())
            self.assertFalse((target / ".analysis_output").exists())

    def test_default_output_uses_cwd_analysis_dir_named_after_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "target-name"
            target.mkdir()
            source = target / "sample.md"
            original = "A short markdown file.\n"
            source.write_text(original, encoding="utf-8")

            old_cwd = Path.cwd()
            try:
                os.chdir(root)
                report_path = Path(dup.main([str(target)]))
            finally:
                os.chdir(old_cwd)

            expected_dir = root / ".analysis_output" / "target-name"
            self.assertEqual(report_path.parent.resolve(), expected_dir.resolve())
            self.assertTrue(report_path.exists())
            self.assertEqual(source.read_text(encoding="utf-8"), original)
            self.assertFalse((target / ".analysis_output").exists())


if __name__ == "__main__":
    unittest.main()
