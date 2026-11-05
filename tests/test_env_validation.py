import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SYNC_DIR = REPO_ROOT / "sync"
if str(SYNC_DIR) not in sys.path:
    sys.path.insert(0, str(SYNC_DIR))

from cli.validate_env_schema import (  # noqa: E402
    known_fields_for_platform,
    validate_mcp_file,
    validate_platform_file,
)


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

    def test_platform_api_enabled_boolean_is_valid(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "claude.json"
            path.write_text(json.dumps({"api": {"enabled": True}}), encoding="utf-8")

            errors = validate_platform_file(path)

        self.assertEqual([], errors)

    def test_platform_api_enabled_must_be_boolean(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "claude.json"
            path.write_text(json.dumps({"api": {"enabled": "yes"}}), encoding="utf-8")

            errors = validate_platform_file(path)

        self.assertEqual(["claude.json: 'api.enabled' must be a boolean"], errors)

    def test_platform_api_rejects_unknown_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "claude.json"
            path.write_text(json.dumps({"api": {"unknown": True}}), encoding="utf-8")

            errors = validate_platform_file(path)

        self.assertEqual(["claude.json: unknown api fields: unknown"], errors)

    def test_platform_preamble_agents_boolean_is_valid(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "claude.json"
            path.write_text(
                json.dumps({"preamble": {"mode": "full", "agents": True}}),
                encoding="utf-8",
            )

            errors = validate_platform_file(path)

        self.assertEqual([], errors)

    def test_platform_preamble_router_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "claude.json"
            path.write_text(
                json.dumps({"preamble": {"mode": "full", "router": True}}),
                encoding="utf-8",
            )

            errors = validate_platform_file(path)

        self.assertEqual(["claude.json: unknown preamble fields: router"], errors)

    def test_platform_preamble_mode_must_be_known(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "continue.json"
            path.write_text(json.dumps({"preamble": {"mode": "continue"}}), encoding="utf-8")

            errors = validate_platform_file(path)

        self.assertEqual(
            ["continue.json: 'preamble.mode' must be one of: full, none, recall"],
            errors,
        )


class McpSchemaValidationTests(unittest.TestCase):
    _BASE = {
        "name": "github",
        "type": "sse",
        "url": "https://api.example.com/mcp",
        "capabilities": {
            "authority": "read",
            "reversible": True,
            "data_sensitivity": "public",
            "parallel_safe": True,
            "fallback": "none",
            "verification": "read response",
        },
    }

    def test_mcp_enabled_boolean_is_valid(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "github.json"
            path.write_text(
                json.dumps({**self._BASE, "enabled": True}),
                encoding="utf-8",
            )

            errors = validate_mcp_file(path)

        self.assertEqual([], errors)

    def test_mcp_enabled_must_be_boolean(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "github.json"
            path.write_text(
                json.dumps({**self._BASE, "enabled": "yes"}),
                encoding="utf-8",
            )

            errors = validate_mcp_file(path)

        self.assertEqual(["github.json: 'enabled' must be a boolean"], errors)

    def test_mcp_enabled_missing_is_valid(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "github.json"
            path.write_text(json.dumps(self._BASE), encoding="utf-8")

            errors = validate_mcp_file(path)

        self.assertEqual([], errors)


if __name__ == "__main__":
    unittest.main()
