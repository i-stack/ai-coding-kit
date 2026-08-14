"""
Regression guard: en-US i18n distribution mirrors stay in sync with the
zh-CN source for the multi-skill coordination clauses edited in D1-D5.

Background: the en-US mirrors under ``skills-engineering/*/i18n/en-US/`` are the
artifacts that get distributed (see sync-skills.sh whitelist). Previously the
en-US copies of engineering-discipline / plan-grill / ios-engineer /
cognitive-expansion shipped stale wording because nothing asserted they tracked
the zh source. This test locks each coordinated clause on BOTH sides so a future
edit that touches only one language fails CI / pre-push instead of silently
drifting.

Each entry pairs a zh-CN anchor (must stay in the source) with its en-US anchor
(must stay in the mirror). If either side loses the clause, the test breaks and
reminds the author to update both.
"""

import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SE = REPO_ROOT / "skills-engineering"


class EnUsMirrorSyncTests(unittest.TestCase):
    """Lock D1-D5 coordination clauses across zh-CN source and en-US mirror."""

    def _assert_pairs(self, zh_rel, en_rel, pairs):
        zh = (SE / zh_rel).read_text(encoding="utf-8")
        en = (SE / en_rel).read_text(encoding="utf-8")
        for zh_anchor, en_anchor, label in pairs:
            self.assertIn(zh_anchor, zh, f"zh source missing clause: {label}")
            self.assertIn(en_anchor, en, f"en-US mirror missing clause: {label}")

    def test_engineering_discipline(self):
        self._assert_pairs(
            "engineering-discipline/references/engineering_discipline.md",
            "engineering-discipline/i18n/en-US/references/engineering_discipline.md",
            [
                (
                    "**协同（与 PG-000 / GR-006 / PA-003）：**",
                    "Coordination (with PG-000 / GR-006 / PA-003):",
                    "GR-002 coordination with PG-000/GR-006/PA-003",
                ),
                (
                    "同一回复内所有置信 / 强度信号必须**同源**",
                    "Cross-block Confidence Coordination",
                    "GR-004 cross-block confidence co-sourcing",
                ),
                (
                    "#### 多 SKILL 叠加时的读取与预算上限（缓解叠加爆炸）",
                    "Read and Budget Ceiling when Multiple SKILLs Stack",
                    "GR-004 multi-skill read/budget ceiling",
                ),
                (
                    "**协同（与 GR-002 / PG-000）**",
                    "Coordination (with GR-002 / PG-000):",
                    "GR-006 coordination with GR-002/PG-000",
                ),
            ],
        )

    def test_plan_grill(self):
        self._assert_pairs(
            "plan-grill/references/plan_grill.md",
            "plan-grill/i18n/en-US/references/plan_grill.md",
            [
                (
                    "**与 engineering-discipline GR-002 的衔接**",
                    "Handoff with engineering-discipline GR-002",
                    "PG-000 handoff with GR-002",
                ),
                (
                    "吸收为盘问首问",
                    "absorbed as the first grill question",
                    "PG-001 absorbs GR-002 as first grill question",
                ),
            ],
        )

    def test_ios_engineer_cam(self):
        # CAM true source now lives in cognitive-calibration (platform-agnostic owner).
        # The zh source and en-US mirror are tracked there; ios-engineer is a down-stream
        # mirror and no longer the source of truth.
        self._assert_pairs(
            "cognitive-calibration/references/cognitive_adversary_mode.md",
            "cognitive-calibration/i18n/en-US/references/cognitive_adversary_mode.md",
            [
                (
                    "不得省略或并入其它块",
                    "must not be omitted or merged into other blocks",
                    "CAM fields preserved, not merged/omitted (D4 GR-004 alignment)",
                ),
            ],
        )

    def test_cognitive_expansion(self):
        self._assert_pairs(
            "cognitive-expansion/SKILL.md",
            "cognitive-expansion/i18n/en-US/references/skill.md",
            [
                (
                    "该互斥同时扩展到 preamble 轻量校准段",
                    "exclusion also extends to the preamble lightweight calibration section",
                    "CE-006 preamble mutual-exclusion extension (D1)",
                ),
            ],
        )


if __name__ == "__main__":
    unittest.main()
