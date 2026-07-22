import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SYNC_DIR = REPO_ROOT / "sync"
if str(SYNC_DIR) not in sys.path:
    sys.path.insert(0, str(SYNC_DIR))

from cli.validate_env_schema import known_fields_for_platform, validate_platform_file  # noqa: E402


class PlatformSchemaValidationTests(unittest.TestCase):
    def test_known_fields_are_platform_scoped(self) -> None:
        self.assertIn("theme", known_fields_for_platform("claude"))
        self.assertNotIn("theme", known_fields_for_platform("codebuddy"))
        self.assertNotIn("enabled", known_fields_for_platform("codebuddy"))
        self.assertIn("install_root", known_fields_for_platform("codebuddy"))
        self.assertIn("preamble", known_fields_for_platform("codebuddy"))

    def test_cross_platform_field_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "codebuddy.json"
            path.write_text(
                json.dumps(
                    {
                        "models": [],
                        "availableModels": [],
                        "theme": "dark",
                    }
                ),
                encoding="utf-8",
            )

            errors = validate_platform_file(path)

        self.assertEqual(["codebuddy.json: unknown fields: theme"], errors)

    def test_platform_enabled_field_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "codebuddy.json"
            path.write_text(json.dumps({"enabled": False}), encoding="utf-8")

            errors = validate_platform_file(path)

        self.assertEqual(["codebuddy.json: unknown fields: enabled"], errors)


if __name__ == "__main__":
    unittest.main()
