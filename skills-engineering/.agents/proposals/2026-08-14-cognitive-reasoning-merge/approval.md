# Approval: 合并组 A 四个认知/论证技能为 `cognitive-reasoning`

- 关联提案：`.agents/proposals/2026-08-14-cognitive-reasoning-merge/proposal.md`
- 审批日期：2026-08-14
- 审批人：song

## 审批结论

**APPROVED**（pre-push 守卫可读此文件放行）。

## 已完成的变更

1. 新建 `cognitive-reasoning/` skill，合并 `cognitive-calibration` / `cognitive-expansion` / `logical-reasoning` / `epistemic-integrity` 四域；保留全部规则 ID（CAM-001~005 / GR-010 / GR-011~013 / CE-001~013）。
2. 删除旧四目录。
3. 更新 `ios-engineer/SKILL.md`：`depends_on` 指向 `cognitive-reasoning`；镜像引用更新为 new owner。
4. 更新 `.agents/invocation.md` / `.agents/composition.md` 触发矩阵与分层表。
5. 更新 `scripts/templates/agent-preamble.md.tmpl`：四段合并为单段；`sync-manifest` 改为 `cognitive-reasoning`。
6. 更新 `scripts/templates/`：删除三个旧 `.mdc.tmpl`，新增 `cognitive-reasoning.mdc.tmpl`。
7. 更新 `scripts/sync-agent-preamble.sh`：`sibling_skill_dir` 合并为 `cr_dir`。
8. 更新 `tests/test_en_us_mirror_sync.py`：路径断言改为 `cognitive-reasoning`。
9. 更新 `README.md` 技能表与目录树、`source-truth.json`。

## 校验结果（执行后）

- `bash skills-engineering/scripts/validate-skill-behavior.sh` → 退出码 0，0 FAIL。
- `python3 tests/test_en_us_mirror_sync.py` → Ran 4 tests, OK。
- `bash skills-engineering/scripts/sync-agent-preamble.sh --dry-run` → 无 error，旧四段正确替换为单段。

## 残留风险

- `ios-engineer` 本地镜像 `references/cognitive_adversary_mode.md` 仍为 downstream mirror，需随 `cognitive-reasoning` 真值变更同步（已在 SKILL.md 标注 new owner）。
- 历史 `.codebuddy` 生成物若含旧 skill 路径，需重跑 `sync-skills.sh` / `sync-agent-preamble.sh` 刷新。
