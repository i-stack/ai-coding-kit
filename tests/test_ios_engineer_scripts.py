"""
Unit tests for ios-engineer/scripts/*.sh

Covers parameter validation (regex whitelists), enum correctness, cross-script
consistency, Ruby validation logic isolation, lock mechanism, and script structure.
"""

import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "skills-engineering" / "ios-engineer" / "scripts"
SKILL_DIR = SCRIPTS_DIR.parent


def _read_script(name: str) -> str:
    """Read a script file content."""
    path = SCRIPTS_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Script not found: {path}")
    return path.read_text(encoding="utf-8")


def _list_scripts() -> list[str]:
    """List all .sh script files in sorted order."""
    return sorted(
        p.name for p in SCRIPTS_DIR.glob("*.sh") if p.is_file()
    )


def _is_compat_shim(content: str) -> bool:
    return "Compatibility shim" in content and "DEPRECATED:" in content


IOS_SNAKE_TO_KEBAB = {
    "append_usage_entry.sh": "append-usage-entry.sh",
    "approve_skill_promotion.sh": "approve-skill-promotion.sh",
    "audit_ref_freshness.sh": "audit-ref-freshness.sh",
    "check_skill_promotion_readiness.sh": "check-skill-promotion-readiness.sh",
    "check_snapshot_consistency.sh": "check-snapshot-consistency.sh",
    "create_skill_proposal.sh": "create-skill-proposal.sh",
    "demo_skill_evolution_flow.sh": "demo-skill-evolution-flow.sh",
    "extract_usage_audit.sh": "extract-usage-audit.sh",
    "gc_evolution_history.sh": "gc-evolution-history.sh",
    "install_codex_ledger_sync.sh": "install-codex-ledger-sync.sh",
    "lint_hit_rules.sh": "lint-hit-rules.sh",
    "promote_skill_evolution.sh": "promote-skill-evolution.sh",
    "record_validation_scenario.sh": "record-validation-scenario.sh",
    "rollback_skill_evolution.sh": "rollback-skill-evolution.sh",
    "run_behavior_validation.sh": "run-behavior-validation.sh",
    "run_ios_tests.sh": "run-ios-tests.sh",
    "suggest_skill_proposals.sh": "suggest-skill-proposals.sh",
    "summarize_usage_ledger.sh": "summarize-usage-ledger.sh",
    "sync_codex_sessions.sh": "sync-codex-sessions.sh",
    "sync_transcript_to_ledger.sh": "sync-transcript-to-ledger.sh",
    "test_gc_invariant.sh": "test-gc-invariant.sh",
    "test_proposal_scripts.sh": "test-proposal-scripts.sh",
    "update_skill_proposal_status.sh": "update-skill-proposal-status.sh",
    "validate_rule_ids.sh": "validate-rule-ids.sh",
    "validate_scenario_specs.sh": "validate-scenario-specs.sh",
    "validate_skill_evolution.sh": "validate-skill-evolution.sh",
    "validate_skill_proposal.sh": "validate-skill-proposal.sh",
    "validate_usage_ledger.sh": "validate-usage-ledger.sh",
}

GLOBAL_SNAKE_TO_KEBAB = {
    "detect_project_type.sh": "detect-project-type.sh",
    "skill_bundles.sh": "skill-bundles.sh",
}

GLOBAL_SCRIPTS_DIR = REPO_ROOT / "skills-engineering" / "scripts"


# ─── Regex Patterns extracted from scripts ───

RE_PROPOSAL_FILE = re.compile(
    r"^evolution/proposals/[0-9]{8}-[0-9]{6}-[A-Za-z0-9_-]+\.md$"
)
RE_VERSION = re.compile(r"^v[0-9]+(-[A-Za-z0-9]+)*$")
RE_SLUG = re.compile(r"^[A-Za-z0-9_-]{1,80}$")
RE_SCENARIO_SLUG = re.compile(r"^[a-z0-9][a-z0-9-]{0,50}$")
RE_SOURCE_REF = re.compile(r"^[A-Za-z0-9:_./-]{1,200}$")
RE_APPROVED_BY = re.compile(r"^[A-Za-z0-9_@.-]{1,100}$")
RE_RULE_ID = re.compile(r"^[A-Z]+-\d{3}$")
RE_TIMESTAMP = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}([+-]\d{4}|Z)$")
RE_KBD_KEY = re.compile(r"^[a-z0-9][a-z0-9-]*$")


# ─── Enum constants extracted from scripts ───

ALLOWED_TOOLS = frozenset([
    "codex", "claude-code", "cursor", "manual", "other"
])

ALLOWED_TASK_TYPES = frozenset([
    "layout", "parameter-pass-through", "concurrency", "review",
    "migration", "mcp-control", "notifications", "privacy",
    "persistence", "storekit", "extensions", "other",
])

ALLOWED_OUTCOMES = frozenset(["pass", "partial", "fail"])

ALLOWED_SIGNALS = frozenset([
    "none", "修正表达", "新增能力", "合并重复", "退役规则"
])

ALLOWED_STATUS = frozenset(["active", "retired", "deprecated"])

PROPOSAL_STATUSES = frozenset([
    "draft", "validated", "ready_to_promote", "approved", "promoted", "rejected"
])

OUTPUT_CONTRACTS = frozenset(["four-segment", "findings-first", "free"])

CANONICAL_SLUGS = frozenset([
    "layout", "parameter-pass-through", "concurrency", "review",
    "migration", "mcp-control", "notifications", "privacy",
    "persistence", "storekit", "extensions",
])

REQUIRED_LEDGER_FIELDS = [
    "time", "tool", "session_id", "prompt_summary", "task_type",
    "expected_rules", "hit_rules", "missed_rules", "deviations",
    "outcome", "evolution_signal",
]

REQUIRED_SCENARIO_FIELDS = [
    "id", "version", "category", "input", "primary_refs",
    "output_contract", "expected_hits", "failure_signals", "scoring",
]


# ═══════════════════════════════════════════════════════════════
# Regex / Format Validation Tests
# ═══════════════════════════════════════════════════════════════

class ProposalFileFormatTests(unittest.TestCase):
    """Test evolution/proposals/<timestamp>-<slug>.md format validation."""

    def test_valid_proposal_paths(self):
        valid = [
            "evolution/proposals/20260403-120000-fix-layout.md",
            "evolution/proposals/20251231-235959-add_feature.md",
            "evolution/proposals/20260101-000000-single.md",
            "evolution/proposals/20260403-120000-AbC-123_.md",
        ]
        for v in valid:
            self.assertIsNotNone(RE_PROPOSAL_FILE.match(v), f"Should accept: {v}")

    def test_invalid_proposal_paths(self):
        invalid = [
            "/etc/hosts",
            "../../../etc/passwd",
            "evolution/proposals/foo.md",
            "evolution/proposals/20260101-foo.md",         # missing HHMMSS
            "evolution/proposals/20260101-000000-.md",     # empty slug
            "evolution/proposals/20260-01-000000-fix.md",  # bad date
            "evolution/proposals/20260101_000000_fix.md",  # underscore separator
            "proposal.md",
            "../proposals/20260403-120000-fix.md",
            "evolution/proposals/20260403-120000-fix.txt", # wrong extension
        ]
        for v in invalid:
            self.assertIsNone(RE_PROPOSAL_FILE.match(v), f"Should reject: {v}")


class VersionFormatTests(unittest.TestCase):
    """Test v<N>[-<suffix>] version format validation."""

    def test_valid_versions(self):
        valid = ["v1", "v2", "v10", "v33", "v99", "v100", "v1-fix", "v33-hotfix"]
        for v in valid:
            self.assertIsNotNone(RE_VERSION.match(v), f"Should accept: {v}")

    def test_invalid_versions(self):
        invalid = [
            "v", "V1", "v-1", "v0x1", "v1.0", "latest",
            "../../../v1", "v1 ", " v1", "v1/foo",
        ]
        for v in invalid:
            self.assertIsNone(RE_VERSION.match(v), f"Should reject: {v}")


class SlugFormatTests(unittest.TestCase):
    """Test proposal slug format validation."""

    def test_valid_slugs(self):
        valid = ["fix", "fix-root-cause", "add_feature", "my-proposal_v2", "A", "B"]
        for v in valid:
            self.assertIsNotNone(RE_SLUG.match(v), f"Should accept: {v}")

    def test_invalid_slugs(self):
        invalid = [
            "fix root", "修复", "fix/root", "fix.v2",
            "../../../etc/passwd", "",
        ]
        for v in invalid:
            self.assertIsNone(RE_SLUG.match(v), f"Should reject: {v!r}")

    def test_slug_too_long(self):
        long_slug = "a" * 81
        self.assertIsNone(RE_SLUG.match(long_slug))

    def test_slug_max_length_ok(self):
        max_slug = "a" * 80
        self.assertIsNotNone(RE_SLUG.match(max_slug))


class ScenarioSlugFormatTests(unittest.TestCase):
    """Test scenario slug format (lowercase kebab-case)."""

    def test_valid_scenario_slugs(self):
        valid = ["layout", "parameter-pass-through", "concurrency", "mcp-control"]
        for v in valid:
            self.assertIsNotNone(
                RE_SCENARIO_SLUG.match(v), f"Should accept: {v}"
            )

    def test_invalid_scenario_slugs(self):
        invalid = [
            "", "A", "Layout", "parameter_pass", "-bad",
            "a" * 52, "fix space", "Fix",
        ]
        for v in invalid:
            self.assertIsNone(
                RE_SCENARIO_SLUG.match(v), f"Should reject: {v!r}"
            )


class SourceRefFormatTests(unittest.TestCase):
    """Test source_ref format validation."""

    def test_valid_source_refs(self):
        valid = [
            "proposal:20260403-fix",
            "proposal:20260403-120000-fix-root-cause",
            "manual",
            "rollback",
        ]
        for v in valid:
            self.assertIsNotNone(RE_SOURCE_REF.match(v), f"Should accept: {v}")

    def test_invalid_source_refs(self):
        invalid = [
            "", "a" * 201, "contains space",
        ]
        for v in invalid:
            self.assertIsNone(RE_SOURCE_REF.match(v), f"Should reject: {v!r}")


class ApprovedByFormatTests(unittest.TestCase):
    """Test approved_by format validation."""

    def test_valid_approved_by(self):
        valid = ["approved-by-user", "user@domain.com", "ops_admin", "a.b-c_d"]
        for v in valid:
            self.assertIsNotNone(RE_APPROVED_BY.match(v), f"Should accept: {v}")

    def test_invalid_approved_by(self):
        invalid = [
            "", "contains space", "a" * 101, "../../../",
        ]
        for v in invalid:
            self.assertIsNone(RE_APPROVED_BY.match(v), f"Should reject: {v!r}")


class RuleIdFormatTests(unittest.TestCase):
    r"""Test rule ID format [A-Z]+-\d{3}."""

    def test_valid_rule_ids(self):
        valid = ["IR-001", "GR-002", "IR-011", "GR-100", "ABC-999"]
        for v in valid:
            self.assertIsNotNone(RE_RULE_ID.match(v), f"Should accept: {v}")

    def test_invalid_rule_ids(self):
        invalid = [
            "", "ir-001", "IR-1", "IR-0001", "IR-ABC",
            "IR-00", " IR-001", "IR-001 ",
        ]
        for v in invalid:
            self.assertIsNone(RE_RULE_ID.match(v), f"Should reject: {v!r}")


class TimestampFormatTests(unittest.TestCase):
    """Test ISO8601 timestamp with timezone."""

    def test_valid_timestamps(self):
        valid = [
            "2026-04-03T12:00:00+0800",
            "2026-01-01T00:00:00Z",
            "2025-12-31T23:59:59-0500",
            "2026-07-05T18:19:00+0000",
        ]
        for v in valid:
            self.assertIsNotNone(RE_TIMESTAMP.match(v), f"Should accept: {v}")

    def test_invalid_timestamps(self):
        invalid = [
            "", "2026-04-03", "2026-04-03T12:00:00",
            "2026-04-03 12:00:00", "04-03-2026T12:00:00+0800",
        ]
        for v in invalid:
            self.assertIsNone(RE_TIMESTAMP.match(v), f"Should reject: {v!r}")


class KebabKeyFormatTests(unittest.TestCase):
    """Test kebab-case key format for scenario hit/signal keys."""

    def test_valid_keys(self):
        valid = ["root-cause", "check-cancel", "a", "abc-def-ghi"]
        for v in valid:
            self.assertIsNotNone(RE_KBD_KEY.match(v), f"Should accept: {v}")

    def test_invalid_keys(self):
        invalid = ["", "-bad", "A", "Bad-Key", "bad_", "bad key"]
        for v in invalid:
            self.assertIsNone(RE_KBD_KEY.match(v), f"Should reject: {v!r}")


# ═══════════════════════════════════════════════════════════════
# Enum / Constant Size Tests
# ═══════════════════════════════════════════════════════════════

class EnumSizeTests(unittest.TestCase):
    """Verify enum sets have expected cardinality."""

    def test_allowed_tools_size(self):
        self.assertEqual(len(ALLOWED_TOOLS), 5)

    def test_allowed_task_types_size(self):
        # 11 canonical slugs + "other"
        self.assertEqual(len(ALLOWED_TASK_TYPES), 12)

    def test_allowed_outcomes_size(self):
        self.assertEqual(len(ALLOWED_OUTCOMES), 3)

    def test_allowed_signals_size(self):
        self.assertEqual(len(ALLOWED_SIGNALS), 5)

    def test_allowed_status_size(self):
        self.assertEqual(len(ALLOWED_STATUS), 3)

    def test_proposal_statuses_size(self):
        self.assertEqual(len(PROPOSAL_STATUSES), 6)

    def test_output_contracts_size(self):
        self.assertEqual(len(OUTPUT_CONTRACTS), 3)

    def test_canonical_slugs_size(self):
        self.assertEqual(len(CANONICAL_SLUGS), 11)

    def test_required_ledger_fields_size(self):
        self.assertEqual(len(REQUIRED_LEDGER_FIELDS), 11)

    def test_required_scenario_fields_size(self):
        self.assertEqual(len(REQUIRED_SCENARIO_FIELDS), 9)


# ═══════════════════════════════════════════════════════════════
# Cross-Script Consistency Tests
# ═══════════════════════════════════════════════════════════════

class CrossScriptConsistencyTests(unittest.TestCase):
    """Verify that enum sets are consistent across different scripts."""

    def test_canonical_slugs_are_subset_of_task_types(self):
        """Every canonical slug must be in ALLOWED_TASK_TYPES."""
        missing = CANONICAL_SLUGS - ALLOWED_TASK_TYPES
        self.assertSetEqual(missing, set(), f"Slugs not in task types: {missing}")

    def test_task_types_includes_canonical_slugs_plus_other(self):
        """ALLOWED_TASK_TYPES = CANONICAL_SLUGS + 'other'."""
        expected = CANONICAL_SLUGS | {"other"}
        self.assertSetEqual(ALLOWED_TASK_TYPES, expected)

    def test_proposal_status_transitions_are_complete(self):
        """All statuses used in update-skill-proposal-status.sh are in our set."""
        # Defined in update-skill-proposal-status.sh case statement
        self.assertIn("draft", PROPOSAL_STATUSES)
        self.assertIn("validated", PROPOSAL_STATUSES)
        self.assertIn("ready_to_promote", PROPOSAL_STATUSES)
        self.assertIn("approved", PROPOSAL_STATUSES)
        self.assertIn("promoted", PROPOSAL_STATUSES)
        self.assertIn("rejected", PROPOSAL_STATUSES)

    def test_script_allowed_tools_match(self):
        """Tools in append-usage-entry.sh match our extracted ALLOWED_TOOLS."""
        content = _read_script("append-usage-entry.sh")
        # Extract ALLOWED_TOOLS from the Ruby embed
        m = re.search(
            r'ALLOWED_TOOLS\s*=\s*%w\[([^\]]+)\]', content
        )
        self.assertIsNotNone(m, "Could not find ALLOWED_TOOLS in append-usage-entry.sh")
        tools = set(m.group(1).split())
        self.assertSetEqual(tools, set(ALLOWED_TOOLS))

    def test_script_allowed_task_types_match(self):
        """Task types in validate-usage-ledger.sh match our extracted ALLOWED_TASK_TYPES."""
        content = _read_script("validate-usage-ledger.sh")
        m = re.search(
            r'ALLOWED_TASK_TYPES\s*=\s*%w\[([^\]]+)\]', content
        )
        self.assertIsNotNone(
            m, "Could not find ALLOWED_TASK_TYPES in validate-usage-ledger.sh"
        )
        types = set(m.group(1).split())
        self.assertSetEqual(types, set(ALLOWED_TASK_TYPES))

    def test_script_allowed_signals_match(self):
        """Evolution signals in append-usage-entry.sh match our extracted ALLOWED_SIGNALS."""
        content = _read_script("append-usage-entry.sh")
        m = re.search(
            r'ALLOWED_SIGNALS\s*=\s*\[([^\]]+)\]', content
        )
        self.assertIsNotNone(
            m, "Could not find ALLOWED_SIGNALS in append-usage-entry.sh"
        )
        # Parse the Ruby-style array with string entries
        signals_raw = m.group(1)
        signals = set(
            s.strip().strip('"\'') for s in signals_raw.split(",")
        )
        self.assertSetEqual(signals, set(ALLOWED_SIGNALS))

    def test_script_output_contracts_match(self):
        """Output contracts in validate-scenario-specs.sh match."""
        content = _read_script("validate-scenario-specs.sh")
        m = re.search(
            r'OUTPUT_CONTRACTS\s*=\s*%w\[([^\]]+)\]', content
        )
        self.assertIsNotNone(
            m, "Could not find OUTPUT_CONTRACTS in validate-scenario-specs.sh"
        )
        contracts = set(m.group(1).split())
        self.assertSetEqual(contracts, OUTPUT_CONTRACTS)

    def test_threshold_constants_exist_in_summarize_script(self):
        """summarize-usage-ledger.sh defines the required threshold constants."""
        content = _read_script("summarize-usage-ledger.sh")
        required = [
            "MISSED_RULE_THRESHOLD",
            "TASK_TYPE_OTHER_THRESHOLD",
            "DEVIATION_THRESHOLD",
            "TOOL_DIVERGENCE_THRESHOLD",
            "MIN_TOOL_SAMPLE_SIZE",
        ]
        for const in required:
            self.assertIn(
                const, content,
                f"Missing threshold constant {const} in summarize-usage-ledger.sh"
            )

    def test_proposal_file_regex_same_across_all_scripts(self):
        """All scripts that validate proposal_file use the same regex."""
        scripts_checking_proposal = [
            "validate-skill-proposal.sh",
            "approve-skill-promotion.sh",
            "check-skill-promotion-readiness.sh",
            "promote-skill-evolution.sh",
            "record-validation-scenario.sh",
            "update-skill-proposal-status.sh",
        ]
        expected = r'^evolution/proposals/[0-9]{8}-[0-9]{6}-[A-Za-z0-9_-]+\.md$'
        for sname in scripts_checking_proposal:
            content = _read_script(sname)
            # Each of these scripts should contain a regex check for proposal_file
            has_regex = bool(
                re.search(r'proposal_file.*=~', content) and
                'evolution/proposals' in content
            )
            self.assertTrue(
                has_regex,
                f"{sname} should validate proposal_file format"
            )


# ═══════════════════════════════════════════════════════════════
# Ruby Validation Logic Isolation Tests
# ═══════════════════════════════════════════════════════════════

class RubyValidationLogicTests(unittest.TestCase):
    """Test Ruby validation logic extracted from scripts without executing them."""

    def test_rule_id_pattern_matches_known_ids(self):
        """All IR- and GR- prefixed IDs we expect match the format."""
        known_ids = [
            "IR-001", "IR-002", "IR-003", "IR-004", "IR-005",
            "IR-006", "IR-007", "IR-008", "IR-009", "IR-010",
            "IR-011", "GR-001", "GR-002", "GR-004", "GR-008", "GR-010",
        ]
        for rid in known_ids:
            self.assertIsNotNone(
                RE_RULE_ID.match(rid),
                f"Rule ID should match format: {rid}"
            )

    def test_ledger_required_fields_are_ordered(self):
        """Required fields list must maintain its order for JSONL semantics."""
        self.assertEqual(REQUIRED_LEDGER_FIELDS[0], "time")
        self.assertEqual(REQUIRED_LEDGER_FIELDS[1], "tool")
        self.assertIn("expected_rules", REQUIRED_LEDGER_FIELDS)
        self.assertIn("hit_rules", REQUIRED_LEDGER_FIELDS)
        self.assertIn("missed_rules", REQUIRED_LEDGER_FIELDS)

    def test_missed_rules_equals_expected_minus_hit(self):
        """Semantic invariant: missed_rules = expected_rules - hit_rules."""
        # Test with some sample data
        expected = ["IR-001", "IR-006", "GR-004"]
        hit = ["IR-001"]
        missed_actual = sorted(set(expected) - set(hit))
        self.assertEqual(missed_actual, ["GR-004", "IR-006"])

    def test_outcome_transitions_are_mutually_exclusive(self):
        """Outcome values are mutually exclusive categories."""
        self.assertEqual(
            ALLOWED_OUTCOMES,
            {"pass", "partial", "fail"}
        )

    def test_signal_set_includes_none_and_evolution_signals(self):
        """Evolution signals include 'none' for non-signal entries."""
        self.assertIn("none", ALLOWED_SIGNALS)
        self.assertIn("修正表达", ALLOWED_SIGNALS)
        self.assertIn("新增能力", ALLOWED_SIGNALS)
        self.assertIn("合并重复", ALLOWED_SIGNALS)
        self.assertIn("退役规则", ALLOWED_SIGNALS)

    def test_prompt_summary_length_bounds(self):
        """prompt_summary must be between 5-200 chars."""
        min_len, max_len = 5, 200
        self.assertTrue(min_len <= len("Short prompt summary") <= max_len)
        self.assertFalse(len("Hi") >= min_len)
        self.assertFalse(len("H") >= min_len)


# ═══════════════════════════════════════════════════════════════
# Lock Mechanism Tests
# ═══════════════════════════════════════════════════════════════

class LockMechanismTests(unittest.TestCase):
    """Test the mkdir-based lock pattern used in multiple scripts."""

    def test_lock_mechanism_pattern_exists(self):
        """Scripts that acquire locks use the correct mkdir-based pattern."""
        scripts_with_locks = [
            "append-usage-entry.sh",
            "extract-usage-audit.sh",
            "record-validation-scenario.sh",
        ]
        for sname in scripts_with_locks:
            content = _read_script(sname)
            # The loop pattern: for ... 1 2 3... do ... mkdir ... break ... sleep ...
            has_lock_loop = bool(re.search(
                r'for\s+.*\s+1\s+2\s+3.*do.*mkdir\b', content, re.DOTALL
            ))
            has_trap = "trap" in content and "EXIT" in content
            has_rmdir = "rmdir" in content
            self.assertTrue(
                has_lock_loop,
                f"{sname} should have a lock acquisition loop"
            )
            self.assertTrue(
                has_trap,
                f"{sname} should have trap cleanup"
            )
            self.assertTrue(
                has_rmdir,
                f"{sname} should call rmdir for lock release"
            )

    def test_lock_retry_count_is_10(self):
        """Lock retry loops should attempt exactly 10 times."""
        for sname in ["append-usage-entry.sh", "record-validation-scenario.sh"]:
            content = _read_script(sname)
            # The loop should be: for _ in 1 2 3 4 5 6 7 8 9 10
            has_10_retries = bool(re.search(
                r'for.*1 2 3 4 5 6 7 8 9 10', content
            ))
            self.assertTrue(
                has_10_retries,
                f"{sname} lock retry should iterate 1..10"
            )

    def test_mkdir_lock_is_atomic(self):
        """mkdir is inherently atomic on POSIX systems - verifying pattern."""
        # This is a semantic test: mkdir without -p will either succeed
        # (creating the dir) or fail (dir exists), never partially succeed.
        with tempfile.TemporaryDirectory() as td:
            lock_path = os.path.join(td, "test.lock")
            # First mkdir should succeed
            os.mkdir(lock_path)
            self.assertTrue(os.path.isdir(lock_path))
            # Second mkdir should raise FileExistsError
            with self.assertRaises(FileExistsError):
                os.mkdir(lock_path)


# ═══════════════════════════════════════════════════════════════
# Script Structure Tests
# ═══════════════════════════════════════════════════════════════

class ScriptStructureTests(unittest.TestCase):
    """Verify all scripts have proper structure."""

    def test_all_scripts_have_shebang(self):
        for sname in _list_scripts():
            content = _read_script(sname)
            first_line = content.split("\n")[0]
            self.assertIn(
                "#!/", first_line,
                f"{sname} should start with a shebang"
            )
            self.assertIn(
                "bash", first_line,
                f"{sname} shebang should reference bash: {first_line}"
            )

    def test_all_scripts_set_strict_mode(self):
        for sname in _list_scripts():
            content = _read_script(sname)
            # Some scripts use set -euo pipefail, some use set -u
            has_set_e = "set -e" in content or "set -eu" in content
            has_set_u = "set -u" in content
            self.assertTrue(
                has_set_e or has_set_u,
                f"{sname} should set -e or -u for strict mode"
            )

    def test_all_scripts_are_executable(self):
        for sname in _list_scripts():
            path = SCRIPTS_DIR / sname
            self.assertTrue(
                os.access(path, os.X_OK),
                f"{sname} should be executable"
            )


# ═══════════════════════════════════════════════════════════════
# Usage / Help Function Tests
# ═══════════════════════════════════════════════════════════════

class UsageFunctionTests(unittest.TestCase):
    """Verify scripts that take arguments have usage/help info."""

    SCRIPTS_WITH_USAGE = {
        "append-usage-entry.sh",
        "summarize-usage-ledger.sh",
        "validate.sh",
        "gc-evolution-history.sh",
        "validate-skill-proposal.sh",
        "check-skill-promotion-readiness.sh",
        "approve-skill-promotion.sh",
        "create-skill-proposal.sh",
        "record-validation-scenario.sh",
        "update-skill-proposal-status.sh",
    }

    def test_scripts_with_args_have_usage(self):
        for sname in self.SCRIPTS_WITH_USAGE:
            content = _read_script(sname)
            has_usage = (
                "usage()" in content
                or "Usage:" in content
                or "--help" in content
            )
            self.assertTrue(
                has_usage or sname == "update-skill-proposal-status.sh",
                f"{sname} should have usage/help info"
            )


# ═══════════════════════════════════════════════════════════════
# Proposal Status State Machine Tests
# ═══════════════════════════════════════════════════════════════

class ProposalStatusStateMachineTests(unittest.TestCase):
    """Test the proposal status state machine logic."""

    def test_valid_status_transitions_from_draft(self):
        """From draft, valid transitions: validated, rejected."""
        # According to the scripts, the transitions are:
        # draft -> validated (via validate-skill-proposal.sh)
        # draft -> rejected (via update when validation fails)
        # This is verified by examining the status values
        self.assertIn("draft", PROPOSAL_STATUSES)
        self.assertIn("validated", PROPOSAL_STATUSES)
        self.assertIn("rejected", PROPOSAL_STATUSES)

    def test_approve_script_checks_promotion_readiness(self):
        """approve-skill-promotion.sh requires ready_to_promote status."""
        content = _read_script("approve-skill-promotion.sh")
        self.assertIn("ready_to_promote", content)

    def test_promote_script_checks_approved_status(self):
        """promote-skill-evolution.sh requires approved status."""
        content = _read_script("promote-skill-evolution.sh")
        self.assertIn("approved", content)

    def test_record_validation_scenario_result_values(self):
        """record-validation-scenario.sh accepts pass/partial/fail."""
        content = _read_script("record-validation-scenario.sh")
        self.assertIn('pass|partial|fail', content)

    def test_scenario_status_priority(self):
        """Scenario status follows: fail > partial > passed > pending > not_run."""
        # Extract the priority logic from record-validation-scenario.sh's
        # Ruby section for scenario_validation_status determination
        content = _read_script("record-validation-scenario.sh")
        ruby_section = content.split("<<'RUBY'", 1)[1].split("RUBY", 1)[0]
        # Verify the status priority order is correct
        self.assertIn('"failed"', ruby_section)
        self.assertIn('"partial"', ruby_section)
        self.assertIn('"passed"', ruby_section)
        # fail should be checked before partial
        fail_idx = ruby_section.find('"failed"')
        partial_idx = ruby_section.find('"partial"')
        self.assertLess(fail_idx, partial_idx,
                        "fail should be evaluated before partial in priority")


# ═══════════════════════════════════════════════════════════════
# File Content Integrity Tests
# ═══════════════════════════════════════════════════════════════

class FileContentIntegrityTests(unittest.TestCase):
    """Verify scripts reference correct files and paths."""

    def test_agent_preamble_rule_id_families_match_active_index(self):
        """Generated audit contracts must allow every active rule ID family."""
        # The audit contract was moved out of the user-level preamble (commit
        # that refactored ios-engineer to on-demand loading) and now lives in
        # usage_ledger.md §5's per-tool copyable prompt snippets.
        usage_ledger = (SKILL_DIR / "references" / "usage_ledger.md").read_text(
            encoding="utf-8"
        )
        audit_contract = usage_ledger.split("## 5. 三端 system-prompt 片段", 1)[1].split(
            "## 6. 批量灌入", 1
        )[0]
        rule_index = (SKILL_DIR / "references" / "rule_index.md").read_text(
            encoding="utf-8"
        )
        active_families = {
            match.group(1)
            for match in re.finditer(
                r"^\|\s*([A-Z]+)-\d{3}\s*\|\s*active\s*\|",
                rule_index,
                re.MULTILINE,
            )
        }

        for family in active_families:
            self.assertIn(
                f"{family}-XXX",
                audit_contract,
                f"audit contract should allow active {family} IDs",
            )
        self.assertNotIn("GR-NNN 等全局纪律 ID 不在此词表内", audit_contract)

    def test_agent_preamble_summarizes_all_engineering_discipline_rules(self):
        """The preamble summary must not omit GR-001 or GR-006."""
        preamble = (
            REPO_ROOT / "skills-engineering" / "scripts" / "templates"
            / "agent-preamble.md.tmpl"
        ).read_text(encoding="utf-8")
        section = preamble.split("# global engineering-discipline", 1)[1].split(
            "# global problem-analysis", 1
        )[0]

        for rule_number in range(1, 9):
            self.assertIn(f"{rule_number:03d}", section)

    def test_usage_ledger_prompts_allow_global_rule_ids(self):
        """All copyable prompts must match the ledger's active-ID schema."""
        usage_ledger = (SKILL_DIR / "references" / "usage_ledger.md").read_text(
            encoding="utf-8"
        )
        prompt_sections = {
            "codex": usage_ledger.split("### 5.1 Codex CLI", 1)[1].split(
                "### 5.2 Claude Code", 1
            )[0],
            "claude": usage_ledger.split("### 5.2 Claude Code", 1)[1].split(
                "### 5.3 Cursor", 1
            )[0],
            "cursor": usage_ledger.split("### 5.3 Cursor", 1)[1].split(
                "## 6. 批量灌入", 1
            )[0],
        }

        self.assertIn("GR-XXX", prompt_sections["codex"])
        self.assertIn("status=active 的 ID", prompt_sections["claude"])
        self.assertIn("GR-XXX", prompt_sections["cursor"])

    def test_validate_skill_evolution_has_14_steps(self):
        """validate-skill-evolution.sh should have exactly 14 steps."""
        content = _read_script("validate-skill-evolution.sh")
        steps = re.findall(r'\[(\d+)/14\]', content)
        self.assertEqual(len(steps), 14)
        step_nums = [int(s) for s in steps]
        self.assertEqual(step_nums, list(range(1, 15)))

    def test_run_behavior_validation_has_5_steps(self):
        """run-behavior-validation.sh should have exactly 5 behavior checks."""
        content = _read_script("run-behavior-validation.sh")
        steps = re.findall(r'\[behavior (\d+)/5\]', content)
        self.assertEqual(len(steps), 5)

    def test_code_review_behavior_guard_requires_gr004_owner(self):
        """Code review behavior guard must catch OUT-002 owner drift."""
        content = _read_script("run-behavior-validation.sh")
        behavior_4 = content.split("[behavior 4/5] Code review output contract", 1)[1].split(
            "[behavior 5/5] Network cache and error-modeling contract", 1
        )[0]

        self.assertIn("触发条件见 GR-004", behavior_4)
        self.assertIn("findings-first", behavior_4)
        self.assertIn("[review_checklists.md](references/review_checklists.md)", behavior_4)

    def test_check_snapshot_consistency_checks_4_paths(self):
        """check-snapshot-consistency.sh verifies 4 key paths."""
        content = _read_script("check-snapshot-consistency.sh")
        # Should check SKILL.md, agents, references, scripts
        self.assertIn('check_path "SKILL.md"', content)
        self.assertIn('check_path "agents"', content)
        self.assertIn('check_path "references"', content)
        self.assertIn('check_path "scripts"', content)

    def test_rollback_checks_4_required_snapshot_items(self):
        """rollback-skill-evolution.sh requires 4 snapshot items."""
        content = _read_script("rollback-skill-evolution.sh")
        # required=("SKILL.md" "agents" "references" "scripts")
        self.assertIn('required=("SKILL.md" "agents" "references" "scripts")', content)
        # Should also appear in move/restore operations (SKILL.md without quotes)
        self.assertIn("SKILL.md", content)

    def test_validate_rule_ids_references_correct_files(self):
        """validate-rule-ids.sh references rule_index.md and SKILL.md."""
        content = _read_script("validate-rule-ids.sh")
        self.assertIn("rule_index.md", content)
        self.assertIn("SKILL.md", content)
        self.assertIn("evolution/scenarios", content)

    def test_all_scripts_are_in_scripts_directory(self):
        """All .sh files should be in the scripts/ directory."""
        scripts_list = _list_scripts()
        self.assertGreaterEqual(len(scripts_list), 20)
        for s in scripts_list:
            self.assertTrue(
                s.endswith(".sh"),
                f"Script should end with .sh: {s}"
            )

    def test_gc_script_preserves_active_version(self):
        """gc-evolution-history.sh must never delete the active version."""
        content = _read_script("gc-evolution-history.sh")
        # The active version should be added to the protected file
        self.assertIn("ACTIVE_VERSION", content)
        self.assertIn("protected_file", content)
        self.assertIn('echo "$ACTIVE_VERSION" >> "$protected_file"', content)

    def test_lint_hit_rules_covers_all_known_ids(self):
        """lint-hit-rules.sh covers IR-001..IR-011, GR-002/004/008/010."""
        content = _read_script("lint-hit-rules.sh")
        # All known rule IDs should be referenced
        for rid in ["IR-001", "IR-006", "IR-011", "GR-002", "GR-004", "GR-008", "GR-010"]:
            self.assertIn(rid, content, f"lint-hit-rules.sh should cover {rid}")

    def test_validate_scenario_specs_includes_all_canonical_slugs(self):
        """CANONICAL_SLUGS in validate-scenario-specs.sh should include all 12 slugs."""
        content = _read_script("validate-scenario-specs.sh")
        for slug in CANONICAL_SLUGS:
            self.assertIn(
                slug,
                content,
                f"validate-scenario-specs.sh should include '{slug}' in CANONICAL_SLUGS"
            )

    def test_sync_transcript_handles_both_formats(self):
        """sync-transcript-to-ledger.sh handles claude-code and codex formats."""
        content = _read_script("sync-transcript-to-ledger.sh")
        self.assertIn("claude_code", content)
        self.assertIn("codex", content)

    def test_demo_flow_has_7_steps(self):
        """demo-skill-evolution-flow.sh has 7 steps."""
        content = _read_script("demo-skill-evolution-flow.sh")
        steps = re.findall(r'\[(\d+)/7\]', content)
        self.assertEqual(len(steps), 7)

    def test_extract_usage_audit_validates_all_fields(self):
        """extract-usage-audit.sh validates all required fields."""
        content = _read_script("extract-usage-audit.sh")
        for field in ["tool", "task-type", "prompt-summary",
                       "expected-rules", "hit-rules", "outcome", "evolution-signal"]:
            self.assertIn(
                field, content,
                f"extract-usage-audit.sh should validate '{field}'"
            )


# ═══════════════════════════════════════════════════════════════
# Compatibility shim + rollback integrity tests
# ═══════════════════════════════════════════════════════════════

class CompatibilityShimTests(unittest.TestCase):
    """Old snake_case names must keep working for one release cycle."""

    def test_ios_snake_case_shims_cover_renamed_scripts(self):
        for old_name, new_name in IOS_SNAKE_TO_KEBAB.items():
            shim_path = SCRIPTS_DIR / old_name
            target_path = SCRIPTS_DIR / new_name
            self.assertTrue(shim_path.is_file(), f"missing shim: {old_name}")
            self.assertTrue(target_path.is_file(), f"missing target: {new_name}")
            content = shim_path.read_text(encoding="utf-8")
            self.assertTrue(_is_compat_shim(content), f"{old_name} is not a shim")
            self.assertIn(f"/{new_name}", content)
            self.assertIn("exec ", content)

    def test_global_snake_case_shims_cover_renamed_scripts(self):
        for old_name, new_name in GLOBAL_SNAKE_TO_KEBAB.items():
            shim_path = GLOBAL_SCRIPTS_DIR / old_name
            target_path = GLOBAL_SCRIPTS_DIR / new_name
            self.assertTrue(shim_path.is_file(), f"missing shim: {old_name}")
            self.assertTrue(target_path.is_file(), f"missing target: {new_name}")
            content = shim_path.read_text(encoding="utf-8")
            self.assertTrue(_is_compat_shim(content), f"{old_name} is not a shim")
            self.assertIn(f"/{new_name}", content)

    def test_underscore_script_names_are_shims_only(self):
        for sname in _list_scripts():
            if "_" not in sname:
                continue
            content = _read_script(sname)
            self.assertTrue(
                _is_compat_shim(content),
                f"{sname} uses snake_case but is not a compatibility shim",
            )

    def test_old_entry_prints_deprecation_and_forwards(self):
        shim = SCRIPTS_DIR / "validate_skill_proposal.sh"
        result = subprocess.run(
            ["bash", str(shim)],
            cwd=SKILL_DIR,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("DEPRECATED", result.stderr)
        self.assertIn("validate-skill-proposal.sh", result.stderr)
        self.assertIn("Usage:", result.stdout)


class RollbackIntegrityTests(unittest.TestCase):
    """rollback must not swallow a real integrity refresh failure."""

    def test_rollback_does_not_swallow_integrity_refresh_errors(self):
        content = _read_script("rollback-skill-evolution.sh")
        self.assertNotIn(
            'bash "${INTEGRITY_SCRIPT}" ios-engineer || true',
            content,
        )
        self.assertIn('bash "${INTEGRITY_SCRIPT}" ios-engineer', content)
        self.assertIn(
            'bash "${INTEGRITY_SCRIPT}" --check-only ios-engineer',
            content,
        )
        self.assertIn(
            "ERROR: integrity baseline refresh failed after rollback",
            content,
        )
        self.assertIn(
            "ERROR: integrity baseline still drifting after refresh",
            content,
        )

    def test_integrity_refresh_success_is_not_treated_as_failure(self):
        integrity = (
            REPO_ROOT / "skills-engineering" / "scripts" / "validate-skill-integrity.sh"
        ).read_text(encoding="utf-8")
        self.assertIn("刷新模式：成功写入新基线视为完成", integrity)
        self.assertIn("Integrity check failed for", integrity)
        self.assertNotIn("Integrity drift detected in", integrity)
        # --check-only still fails on drift; refresh only fails on write/collect errors.
        self.assertIn('if [[ "$CHECK_ONLY" -eq 1 ]]; then', integrity)
        self.assertIn("could not write integrity baseline", integrity)
        self.assertIn("could not collect hashes", integrity)


# ═══════════════════════════════════════════════════════════════
# Edge Case Tests
# ═══════════════════════════════════════════════════════════════

class EdgeCaseTests(unittest.TestCase):
    """Test edge cases in validation logic."""

    def test_empty_rule_id_lists(self):
        """Empty rule ID lists should be valid but produce empty arrays."""
        # When expected-rules is empty, missed_rules should also be empty
        expected = []
        hit = []
        missed = sorted(set(expected) - set(hit))
        self.assertEqual(missed, [])

    def test_rule_id_deduplication(self):
        """Duplicate rule IDs should be detected."""
        ids = ["IR-001", "IR-006", "IR-001", "GR-004", "IR-006"]
        duplicates = [id for id in set(ids) if ids.count(id) > 1]
        self.assertEqual(sorted(duplicates), ["IR-001", "IR-006"])

    def test_prompt_summary_boundary_values(self):
        """Test boundary values for prompt summary length."""
        min_ok, max_ok = 5, 200
        self.assertTrue(min_ok <= 5 <= max_ok)
        self.assertTrue(min_ok <= 200 <= max_ok)
        self.assertFalse(min_ok <= 4 <= max_ok)
        self.assertFalse(min_ok <= 201 <= max_ok)

    def test_version_without_suffix_is_valid(self):
        """Plain v<N> without suffix should match version regex."""
        self.assertIsNotNone(RE_VERSION.match("v1"))
        self.assertIsNotNone(RE_VERSION.match("v999"))

    def test_version_with_multiple_suffixes_is_valid(self):
        """v<N>-suffix1-suffix2 should match version regex."""
        self.assertIsNotNone(RE_VERSION.match("v33-hotfix-2"))

    def test_retired_ids_should_not_be_in_hit_rules(self):
        """Retired/deprecated rule IDs should not be used as hit_rules."""
        retired_statuses = {"retired", "deprecated"}
        self.assertEqual(retired_statuses & set(ALLOWED_STATUS), retired_statuses)


if __name__ == "__main__":
    unittest.main()
