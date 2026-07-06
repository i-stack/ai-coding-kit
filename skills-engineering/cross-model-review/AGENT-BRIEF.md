# cross-model-review Agent 调用指南

## 一句话描述

自动发现可用 CLI（codex/gemini/claude），推荐两个不同 provider 的组合并让用户选择，reviewer 只读运行输出 VERDICT，原始输出和交付日志都写在当前项目根目录下，主 agent 仲裁写进 PLAN-REVIEW-LOG.md，MAX_ROUNDS 不收敛输出 deadlock。

## 何时调用

- **用户触发**：用户说 `cross-model-review` / `cross review` / "对抗审查" / "让两个模型审计划" / "model debate" / "stress-test PLAN.md"
- **接力 plan-grill**：plan-grill 锁定 PLAN.md 后，用户说"让另一个模型审查"
- **前置**：PLAN.md 必须已存在（由 plan-grill 产出）

## 关键行为

1. 阅读 `SKILL.md` + `references/cross_model_review.md` 全文。
2. 直接探测可用 CLI（`command -v codex|gemini|claude` + `--version`；本仓库可选辅助脚本：`skills-engineering/scripts/detect-review-clis.sh`）。可用 provider < 2 则停止。
3. 推荐两个不同 provider 的组合，让用户确认（CMR-002）。
4. reviewer 只读运行（CMR-003）：codex `-s read-only`、gemini `--approval-mode plan`、claude `--permission-mode plan`。
5. 输出落盘（CMR-003/004）：reviewer 原始输出、中间输出和交付日志必须在当前项目根目录下，推荐 `.plan-reviews/<date>-<slug>/raw/`；不得用 `/tmp` 作为 reviewer 输出缓冲。
6. 主 agent 仲裁（CMR-004）：每轮收集所有已选 reviewer；全部 APPROVED 才收敛，任一 REVISE 都要仲裁、修订并记入 PLAN-REVIEW-LOG.md。
7. MAX_ROUNDS（默认 5）不收敛 → deadlock（CMR-005），交用户裁决，不假装 approved。
8. Resolution 后可选归档（用户触发）：把 PLAN.md + PLAN-REVIEW-LOG.md 保存到项目根 `.plan-reviews/<date>-<slug>/`，供相似问题回查。详见 references「归档」章节。

## 不调用的情况

- 无 PLAN.md（先跑 plan-grill）
- trivial 改动
- 用户明确"直接实施"
- 可用 reviewer provider < 2
