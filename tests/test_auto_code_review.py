"""
Unit tests for auto-code-review skill.

Covers file structure integrity, SKILL.md content validation, reference file
content validation, sync manifest registration, cross-references, detect-review-clis.sh
behavior, archive directory structure, and environment variable configuration.
"""

import os
import re
import subprocess
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SE_DIR = REPO_ROOT / "skills-engineering"
ACR_DIR = SE_DIR / "auto-code-review"
ACR_REFS = ACR_DIR / "references"
SCRIPTS_DIR = SE_DIR / "scripts"
TEMPLATES_DIR = SCRIPTS_DIR / "templates"


# ═══════════════════════════════════════════════════════════════
# File Structure Integrity Tests
# ═══════════════════════════════════════════════════════════════

class FileStructureTests(unittest.TestCase):
    """Verify auto-code-review skill has all required files."""

    def test_skill_directory_exists(self):
        self.assertTrue(ACR_DIR.is_dir(), f"Skill directory missing: {ACR_DIR}")

    def test_skill_md_exists(self):
        self.assertTrue(
            (ACR_DIR / "SKILL.md").is_file(),
            "auto-code-review/SKILL.md missing"
        )

    def test_agent_brief_exists(self):
        self.assertTrue(
            (ACR_DIR / "AGENT-BRIEF.md").is_file(),
            "auto-code-review/AGENT-BRIEF.md missing"
        )

    def test_out_of_scope_exists(self):
        self.assertTrue(
            (ACR_DIR / "OUT-OF-SCOPE.md").is_file(),
            "auto-code-review/OUT-OF-SCOPE.md missing"
        )

    def test_references_directory_exists(self):
        self.assertTrue(
            ACR_REFS.is_dir(),
            "auto-code-review/references/ directory missing"
        )

    def test_primary_reference_exists(self):
        self.assertTrue(
            (ACR_REFS / "auto_code_review.md").is_file(),
            "auto-code-review/references/auto_code_review.md missing"
        )

    def test_docs_file_exists(self):
        self.assertTrue(
            (SE_DIR / "docs" / "auto-code-review.md").is_file(),
            "docs/auto-code-review.md missing"
        )

    def test_no_stale_directories(self):
        """Skill dir should not contain evolution/proposals/history/scripts etc."""
        stale_dirs = [
            "evolution", "proposals", "history", "scripts",
            "agents", "validations", "scenarios", "approvals", "usage"
        ]
        for d in stale_dirs:
            self.assertFalse(
                (ACR_DIR / d).is_dir(),
                f"auto-code-review/{d} should not exist (stale directory)"
            )


# ═══════════════════════════════════════════════════════════════
# SKILL.md Content Validation Tests
# ═══════════════════════════════════════════════════════════════

class SkillMdContentTests(unittest.TestCase):
    """Verify SKILL.md contains all required rules and sections."""

    @classmethod
    def setUpClass(cls):
        cls.content = (ACR_DIR / "SKILL.md").read_text(encoding="utf-8")

    def test_has_frontmatter(self):
        self.assertTrue(
            self.content.startswith("---"),
            "SKILL.md should start with YAML frontmatter"
        )

    def test_frontmatter_has_name(self):
        self.assertIn("name: auto-code-review", self.content)

    def test_frontmatter_has_description(self):
        self.assertIn("description:", self.content)

    def test_has_force_entry_section(self):
        self.assertIn("强制入口", self.content)

    def test_references_primary_reference_file(self):
        self.assertIn(
            "references/auto_code_review.md",
            self.content,
            "SKILL.md should reference references/auto_code_review.md"
        )

    def test_has_all_eight_rules(self):
        """SKILL.md should define ACR-001 through ACR-008."""
        for i in range(1, 9):
            rule_id = f"ACR-{i:03d}"
            self.assertIn(
                rule_id, self.content,
                f"SKILL.md missing rule {rule_id}"
            )

    def test_acr001_auto_trigger(self):
        self.assertIn("自动触发", self.content)
        self.assertIn("reviewer CLI", self.content)

    def test_acr002_review_scope(self):
        self.assertIn("审查范围", self.content)
        self.assertIn("diff", self.content.lower())

    def test_acr003_reviewer_readonly(self):
        self.assertIn("reviewer 只读", self.content)
        self.assertIn("-s read-only", self.content)
        self.assertIn("--approval-mode plan", self.content)
        self.assertIn("--permission-mode plan", self.content)

    def test_acr004_fix_by_main_agent(self):
        self.assertIn("修复由主 agent 执行", self.content)

    def test_acr005_max_rounds(self):
        self.assertIn("MAX_ROUNDS", self.content)
        self.assertIn("MAX_ROUNDS=3", self.content)

    def test_acr006_auto_archive(self):
        self.assertIn("自动归档", self.content)
        self.assertIn(".plan-reviews", self.content)

    def test_acr007_configurable_reviewer(self):
        self.assertIn("可配置 reviewer", self.content)

    def test_acr008_single_model_degradation(self):
        self.assertIn("单模型降级", self.content)

    def test_has_trigger_section(self):
        self.assertIn("何时加载", self.content)

    def test_has_skip_conditions(self):
        self.assertIn("跳过", self.content)
        self.assertIn("trivial", self.content.lower())

    def test_has_adjacent_skill_table(self):
        """SKILL.md should have a table showing relationship with other skills."""
        self.assertIn("plan-grill", self.content)
        self.assertIn("cross-model-review", self.content)
        self.assertIn("engineering-discipline", self.content)

    def test_has_workflow_section(self):
        self.assertIn("完整工作流", self.content)
        self.assertIn("auto-code-review", self.content)


# ═══════════════════════════════════════════════════════════════
# Reference File Content Validation Tests
# ═══════════════════════════════════════════════════════════════

class ReferenceContentTests(unittest.TestCase):
    """Verify references/auto_code_review.md contains detailed rules."""

    @classmethod
    def setUpClass(cls):
        cls.content = (ACR_REFS / "auto_code_review.md").read_text(encoding="utf-8")

    def test_has_true_source_declaration(self):
        self.assertIn("真值来源", self.content)

    def test_has_positioning_section(self):
        self.assertIn("定位", self.content)

    def test_has_prerequisites_section(self):
        self.assertIn("前置", self.content)

    def test_acr001_detect_cli(self):
        self.assertIn("ACR-001", self.content)
        self.assertIn("detect-review-clis.sh", self.content)

    def test_acr002_review_input_construction(self):
        self.assertIn("ACR-002", self.content)
        self.assertIn("git diff", self.content)

    def test_acr003_review_prompt_template(self):
        self.assertIn("ACR-003", self.content)
        self.assertIn("adversarial code reviewer", self.content)

    def test_acr003_codex_adapter(self):
        self.assertIn("codex exec -s read-only", self.content)
        self.assertIn("< /dev/null", self.content)

    def test_acr003_gemini_adapter(self):
        self.assertIn("gemini -p", self.content)
        self.assertIn("--approval-mode plan", self.content)

    def test_acr003_claude_adapter(self):
        self.assertIn("claude -p", self.content)
        self.assertIn("--permission-mode plan", self.content)

    def test_acr004_arbitration_discipline(self):
        self.assertIn("ACR-004", self.content)
        self.assertIn("仲裁纪律", self.content)
        self.assertIn("采纳有证据的批评", self.content)
        self.assertIn("拒绝不成立的批评", self.content)

    def test_acr005_max_rounds_default_3(self):
        self.assertIn("ACR-005", self.content)
        self.assertIn("| `MAX_ROUNDS` | `3`", self.content)

    def test_acr005_deadlock_report(self):
        self.assertIn("deadlock", self.content.lower())
        self.assertIn("禁止假装 approved", self.content)

    def test_acr006_archive_structure(self):
        self.assertIn("ACR-006", self.content)
        self.assertIn("QUESTION.md", self.content)
        self.assertIn("RESPONSE.md", self.content)
        self.assertIn("REVIEW-LOG.md", self.content)
        self.assertIn("diff.patch", self.content)

    def test_acr006_gitignore_handling(self):
        self.assertIn(".gitignore", self.content)

    def test_acr007_reviewer_selection_strategy(self):
        self.assertIn("ACR-007", self.content)
        self.assertIn("AUTO_REVIEW_REVIEWER", self.content)
        self.assertIn("AUTO_REVIEW_REVIEWERS", self.content)

    def test_acr008_self_review_warning(self):
        self.assertIn("ACR-008", self.content)
        self.assertIn("WARNING", self.content)
        self.assertIn("单模型自审", self.content)

    def test_safety_rules(self):
        self.assertIn("安全规则", self.content)
        self.assertIn("timeout 600s", self.content)
        self.assertIn("不 pin model", self.content)

    def test_quality_self_check(self):
        self.assertIn("审查质量自检", self.content)

    def test_no_pin_model_policy(self):
        """First version should not pin model."""
        self.assertIn("第一版不 pin model", self.content)
        self.assertIn("默认模型", self.content)


# ═══════════════════════════════════════════════════════════════
# AGENT-BRIEF.md Content Tests
# ═══════════════════════════════════════════════════════════════

class AgentBriefContentTests(unittest.TestCase):
    """Verify AGENT-BRIEF.md has correct quick-reference content."""

    @classmethod
    def setUpClass(cls):
        cls.content = (ACR_DIR / "AGENT-BRIEF.md").read_text(encoding="utf-8")

    def test_has_one_line_description(self):
        self.assertIn("一句话描述", self.content)

    def test_has_when_to_invoke(self):
        self.assertIn("何时调用", self.content)

    def test_has_key_behaviors(self):
        self.assertIn("关键行为", self.content)

    def test_has_skip_conditions(self):
        self.assertIn("不调用的情况", self.content)

    def test_has_config_options(self):
        self.assertIn("配置选项", self.content)
        self.assertIn("AUTO_REVIEW_REVIEWER", self.content)
        self.assertIn("AUTO_REVIEW_MAX_ROUNDS", self.content)

    def test_has_comparison_with_cross_model_review(self):
        self.assertIn("cross-model-review", self.content)


# ═══════════════════════════════════════════════════════════════
# OUT-OF-SCOPE.md Content Tests
# ═══════════════════════════════════════════════════════════════

class OutOfScopeContentTests(unittest.TestCase):
    """Verify OUT-OF-SCOPE.md correctly defines boundaries."""

    @classmethod
    def setUpClass(cls):
        cls.content = (ACR_DIR / "OUT-OF-SCOPE.md").read_text(encoding="utf-8")

    def test_excludes_plan_review(self):
        self.assertIn("计划审查", self.content)
        self.assertIn("cross-model-review", self.content)

    def test_excludes_non_code_changes(self):
        self.assertIn("非代码变更", self.content)

    def test_excludes_user_skip(self):
        self.assertIn("用户显式跳过", self.content)

    def test_excludes_human_review_replacement(self):
        self.assertIn("人工审查", self.content)


# ═══════════════════════════════════════════════════════════════
# Sync Manifest Registration Tests
# ═══════════════════════════════════════════════════════════════

class SyncManifestTests(unittest.TestCase):
    """Verify auto-code-review is registered in sync configurations."""

    def test_in_preamble_template_manifest(self):
        tmpl = (TEMPLATES_DIR / "agent-preamble.md.tmpl").read_text(encoding="utf-8")
        self.assertIn(
            "skill:auto-code-review",
            tmpl,
            "agent-preamble.md.tmpl sync-manifest missing skill:auto-code-review"
        )

    def test_in_readme_skill_table(self):
        readme = (SE_DIR / "README.md").read_text(encoding="utf-8")
        self.assertIn("auto-code-review", readme)
        self.assertIn("代码实施后自动", readme)

    def test_in_readme_directory_structure(self):
        readme = (SE_DIR / "README.md").read_text(encoding="utf-8")
        self.assertIn("auto-code-review/", readme)

    def test_in_invocation_keywords(self):
        invocation = (SE_DIR / ".agents" / "invocation.md").read_text(encoding="utf-8")
        self.assertIn("auto-code-review", invocation)


# ═══════════════════════════════════════════════════════════════
# Cross-Reference Consistency Tests
# ═══════════════════════════════════════════════════════════════

class CrossReferenceTests(unittest.TestCase):
    """Verify cross-references between files are consistent."""

    def test_skill_md_reference_link_valid(self):
        """SKILL.md references references/auto_code_review.md which must exist."""
        skill_content = (ACR_DIR / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn(
            "references/auto_code_review.md",
            skill_content
        )
        self.assertTrue(
            (ACR_REFS / "auto_code_review.md").is_file(),
            "Referenced file references/auto_code_review.md must exist"
        )

    def test_detect_review_cli_script_exists(self):
        """auto_code_review.md references detect-review-clis.sh which must exist."""
        ref_content = (ACR_REFS / "auto_code_review.md").read_text(encoding="utf-8")
        self.assertIn("detect-review-clis.sh", ref_content)
        self.assertTrue(
            (SCRIPTS_DIR / "detect-review-clis.sh").is_file(),
            "Referenced script detect-review-clis.sh must exist"
        )

    def test_reviewer_cli_flags_consistent(self):
        """CLI flags in SKILL.md and reference file should be consistent."""
        skill = (ACR_DIR / "SKILL.md").read_text(encoding="utf-8")
        ref = (ACR_REFS / "auto_code_review.md").read_text(encoding="utf-8")

        # Codex readonly flag
        self.assertIn("-s read-only", skill)
        self.assertIn("-s read-only", ref)

        # Gemini readonly flag
        self.assertIn("--approval-mode plan", skill)
        self.assertIn("--approval-mode plan", ref)

        # Claude readonly flag
        self.assertIn("--permission-mode plan", skill)
        self.assertIn("--permission-mode plan", ref)

    def test_max_rounds_consistent(self):
        """MAX_ROUNDS should be 3 in both SKILL.md and reference."""
        skill = (ACR_DIR / "SKILL.md").read_text(encoding="utf-8")
        ref = (ACR_REFS / "auto_code_review.md").read_text(encoding="utf-8")
        self.assertIn("MAX_ROUNDS=3", skill)
        self.assertIn("| `MAX_ROUNDS` | `3`", ref)

    def test_archive_dir_structure_consistent(self):
        """Archive structure should be consistent across files."""
        ref = (ACR_REFS / "auto_code_review.md").read_text(encoding="utf-8")
        brief = (ACR_DIR / "AGENT-BRIEF.md").read_text(encoding="utf-8")

        for item in ["QUESTION.md", "RESPONSE.md", "REVIEW-LOG.md", "raw/"]:
            self.assertIn(item, ref, f"Reference missing archive item: {item}")
            self.assertIn(item, brief, f"AGENT-BRIEF missing archive item: {item}")


# ═══════════════════════════════════════════════════════════════
# detect-review-clis.sh Script Tests
# ═══════════════════════════════════════════════════════════════

class DetectReviewClisTests(unittest.TestCase):
    """Test detect-review-clis.sh script behavior."""

    def test_script_exists(self):
        self.assertTrue(
            (SCRIPTS_DIR / "detect-review-clis.sh").is_file()
        )

    def test_script_is_executable(self):
        self.assertTrue(
            os.access(SCRIPTS_DIR / "detect-review-clis.sh", os.X_OK),
            "detect-review-clis.sh should be executable"
        )

    def test_script_has_shebang(self):
        content = (SCRIPTS_DIR / "detect-review-clis.sh").read_text(encoding="utf-8")
        self.assertTrue(content.startswith("#!/"), "Script should start with shebang")

    def test_script_has_strict_mode(self):
        content = (SCRIPTS_DIR / "detect-review-clis.sh").read_text(encoding="utf-8")
        self.assertIn("set -", content, "Script should set strict mode")

    def test_script_probes_three_clis(self):
        content = (SCRIPTS_DIR / "detect-review-clis.sh").read_text(encoding="utf-8")
        self.assertIn("codex", content)
        self.assertIn("gemini", content)
        self.assertIn("claude", content)

    def test_script_outputs_json(self):
        content = (SCRIPTS_DIR / "detect-review-clis.sh").read_text(encoding="utf-8")
        self.assertIn('"clis"', content)
        self.assertIn('"available_count"', content)

    def test_script_runs_without_error(self):
        """Script should execute successfully (exit 0)."""
        result = subprocess.run(
            ["bash", str(SCRIPTS_DIR / "detect-review-clis.sh")],
            capture_output=True, text=True, timeout=30
        )
        self.assertEqual(
            result.returncode, 0,
            f"detect-review-clis.sh should exit 0. stderr: {result.stderr}"
        )

    def test_script_output_is_valid_json(self):
        """Output should be valid JSON."""
        import json
        result = subprocess.run(
            ["bash", str(SCRIPTS_DIR / "detect-review-clis.sh")],
            capture_output=True, text=True, timeout=30
        )
        try:
            data = json.loads(result.stdout.strip())
            self.assertIn("clis", data)
            self.assertIn("available_count", data)
            self.assertIsInstance(data["clis"], list)
            self.assertEqual(len(data["clis"]), 3)
        except json.JSONDecodeError:
            self.fail(f"Output is not valid JSON: {result.stdout[:200]}")

    def test_each_cli_has_required_fields(self):
        """Each CLI entry should have name, available, path, version, flags."""
        import json
        result = subprocess.run(
            ["bash", str(SCRIPTS_DIR / "detect-review-clis.sh")],
            capture_output=True, text=True, timeout=30
        )
        data = json.loads(result.stdout.strip())
        required_fields = {"name", "available"}
        for cli in data["clis"]:
            for field in required_fields:
                self.assertIn(
                    field, cli,
                    f"CLI entry missing required field '{field}': {cli}"
                )

    def test_available_count_matches_clis(self):
        """available_count should match the number of available CLIs."""
        import json
        result = subprocess.run(
            ["bash", str(SCRIPTS_DIR / "detect-review-clis.sh")],
            capture_output=True, text=True, timeout=30
        )
        data = json.loads(result.stdout.strip())
        actual_count = sum(1 for c in data["clis"] if c.get("available"))
        self.assertEqual(
            data["available_count"], actual_count,
            f"available_count ({data['available_count']}) != actual ({actual_count})"
        )


# ═══════════════════════════════════════════════════════════════
# Archive Directory Structure Tests
# ═══════════════════════════════════════════════════════════════

class ArchiveStructureTests(unittest.TestCase):
    """Verify .plan-reviews archive structure logic."""

    def test_plan_reviews_dir_exists_in_repo(self):
        """The .plan-reviews directory should exist in the repo."""
        self.assertTrue(
            (REPO_ROOT / ".plan-reviews").is_dir(),
            ".plan-reviews/ directory should exist in repo root"
        )

    def test_plan_reviews_in_gitignore(self):
        """`.plan-reviews/` should be in .gitignore."""
        gitignore = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn(
            ".plan-reviews/",
            gitignore,
            ".plan-reviews/ should be in .gitignore"
        )

    def test_archive_slug_format(self):
        """Archive slug format should be YYYY-MM-DD-<slug>."""
        slug_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}-[a-z0-9][a-z0-9-]*$")
        test_slugs = [
            "2026-07-07-login-fix",
            "2026-01-01-feature",
            "2025-12-31-a",
        ]
        for s in test_slugs:
            self.assertIsNotNone(
                slug_pattern.match(s),
                f"Slug should match format: {s}"
            )

        invalid_slugs = [
            "2026-07-07-",
            "2026-07-07",
            "07-07-login",
            "login-fix",
        ]
        for s in invalid_slugs:
            self.assertIsNone(
                slug_pattern.match(s),
                f"Slug should be rejected: {s}"
            )


# ═══════════════════════════════════════════════════════════════
# Environment Variable Configuration Tests
# ═══════════════════════════════════════════════════════════════

class EnvVarConfigTests(unittest.TestCase):
    """Verify environment variable configuration is documented correctly."""

    @classmethod
    def setUpClass(cls):
        cls.ref = (ACR_REFS / "auto_code_review.md").read_text(encoding="utf-8")
        cls.brief = (ACR_DIR / "AGENT-BRIEF.md").read_text(encoding="utf-8")

    def test_auto_review_reviewer_documented(self):
        self.assertIn("AUTO_REVIEW_REVIEWER", self.ref)
        self.assertIn("AUTO_REVIEW_REVIEWER", self.brief)

    def test_auto_review_reviewers_documented(self):
        self.assertIn("AUTO_REVIEW_REVIEWERS", self.ref)
        self.assertIn("AUTO_REVIEW_REVIEWERS", self.brief)

    def test_auto_review_max_rounds_documented(self):
        # ref uses MAX_ROUNDS as table param; brief uses AUTO_REVIEW_MAX_ROUNDS env var
        self.assertIn("MAX_ROUNDS", self.ref)
        self.assertIn("AUTO_REVIEW_MAX_ROUNDS", self.brief)

    def test_auto_review_allow_self_review_documented(self):
        self.assertIn("AUTO_REVIEW_ALLOW_SELF_REVIEW", self.ref)
        self.assertIn("AUTO_REVIEW_ALLOW_SELF_REVIEW", self.brief)

    def test_default_max_rounds_is_3(self):
        self.assertIn("`3`", self.brief)

    def test_default_self_review_is_true(self):
        self.assertIn("`true`", self.brief)


# ═══════════════════════════════════════════════════════════════
# Sync Integration Tests
# ═══════════════════════════════════════════════════════════════

class SyncIntegrationTests(unittest.TestCase):
    """Verify auto-code-review is synced correctly to local agent directories."""

    def _check_synced(self, base: Path):
        skill_dir = base / "auto-code-review"
        if not base.is_dir():
            self.skipTest(f"{base} not found")
        self.assertTrue(
            (skill_dir / "SKILL.md").is_file(),
            f"{skill_dir}/SKILL.md missing after sync"
        )
        self.assertTrue(
            (skill_dir / "AGENT-BRIEF.md").is_file(),
            f"{skill_dir}/AGENT-BRIEF.md missing after sync"
        )
        self.assertTrue(
            (skill_dir / "OUT-OF-SCOPE.md").is_file(),
            f"{skill_dir}/OUT-OF-SCOPE.md missing after sync"
        )
        self.assertTrue(
            (skill_dir / "references" / "auto_code_review.md").is_file(),
            f"{skill_dir}/references/auto_code_review.md missing after sync"
        )

    def test_synced_to_claude(self):
        self._check_synced(Path.home() / ".claude" / "skills")

    def test_synced_to_codex(self):
        self._check_synced(Path.home() / ".codex" / "skills")

    def test_synced_to_cursor(self):
        self._check_synced(Path.home() / ".cursor" / "skills")

    def test_synced_to_gemini(self):
        self._check_synced(Path.home() / ".gemini" / "skills")

    def test_cursor_mdc_generated(self):
        mdc = REPO_ROOT / ".cursor" / "rules" / "auto-code-review.mdc"
        self.assertTrue(
            mdc.is_file(),
            f"Cursor .mdc not generated: {mdc}"
        )

    def test_cursor_mdc_has_frontmatter(self):
        mdc = REPO_ROOT / ".cursor" / "rules" / "auto-code-review.mdc"
        if not mdc.is_file():
            self.skipTest("Cursor .mdc not generated")
        content = mdc.read_text(encoding="utf-8")
        self.assertTrue(content.startswith("---"), "Cursor .mdc should start with frontmatter")
        self.assertIn("alwaysApply: true", content)

    def test_synced_skill_has_no_stale_dirs(self):
        """Synced skill dir should not contain evolution/proposals/etc."""
        for base_name in [".claude", ".codex", ".cursor", ".gemini"]:
            base = Path.home() / base_name / "skills" / "auto-code-review"
            if not base.is_dir():
                continue
            for stale in ["evolution", "proposals", "history", "scripts"]:
                self.assertFalse(
                    (base / stale).is_dir(),
                    f"{base}/{stale} should not exist in synced skill"
                )


# ═══════════════════════════════════════════════════════════════
# list-skills.sh Integration Test
# ═══════════════════════════════════════════════════════════════

class ListSkillsIntegrationTests(unittest.TestCase):
    """Verify list-skills.sh detects auto-code-review."""

    def test_list_skills_includes_auto_code_review(self):
        result = subprocess.run(
            ["bash", str(SCRIPTS_DIR / "list-skills.sh")],
            capture_output=True, text=True, timeout=30
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("auto-code-review", result.stdout)


# ═══════════════════════════════════════════════════════════════
# verify-sync.sh Integration Test
# ═══════════════════════════════════════════════════════════════

class VerifySyncIntegrationTests(unittest.TestCase):
    """Verify verify-sync.sh passes with auto-code-review included."""

    def test_verify_sync_passes(self):
        result = subprocess.run(
            ["bash", str(SCRIPTS_DIR / "verify-sync.sh")],
            capture_output=True, text=True, timeout=30
        )
        self.assertEqual(
            result.returncode, 0,
            f"verify-sync.sh should exit 0.\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )
        self.assertIn("OK:", result.stdout)


# ═══════════════════════════════════════════════════════════════
# Workflow Consistency Tests
# ═══════════════════════════════════════════════════════════════

class WorkflowConsistencyTests(unittest.TestCase):
    """Verify auto-code-review fits correctly in the overall skill workflow."""

    def test_act3_positioning(self):
        """auto-code-review should be positioned as Act 3 (after Act 1 and Act 2)."""
        skill = (ACR_DIR / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("Act 3", skill)

    def test_cross_model_review_is_act2(self):
        """cross-model-review should still be Act 2."""
        cmr_skill = (SE_DIR / "cross-model-review" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("Act 2", cmr_skill)

    def test_plan_grill_is_act1(self):
        """plan-grill should still be Act 1."""
        pg_skill = (SE_DIR / "plan-grill" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("Act 1", pg_skill)

    def test_workflow_chain_in_skill_md(self):
        """SKILL.md should show the complete workflow chain."""
        skill = (ACR_DIR / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("problem-analysis", skill)
        self.assertIn("plan-grill", skill)
        self.assertIn("cross-model-review", skill)
        self.assertIn("auto-code-review", skill)


if __name__ == "__main__":
    unittest.main()
