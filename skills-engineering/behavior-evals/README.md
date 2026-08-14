# Behavior evals

`scenarios.json` 是跨 Agent 黄金场景语料，每条场景分别声明行为契约与任务成功 anchors。`run.py` 通过 argv 调用已安装的 Codex、Claude 或 Gemini CLI，保存原始输出、错误输出、退出码与延迟；`evaluate.py` 独立计算契约通过率和任务成功率。

```bash
python3 skills-engineering/behavior-evals/run.py --agent codex --output /tmp/codex-eval.jsonl
python3 skills-engineering/behavior-evals/evaluate.py /tmp/codex-eval.jsonl
```

评测报告规则契约通过率、任务成功率、场景覆盖率与延迟。runner 只发送 prompt，不向被测 Agent 泄露判分 anchors。
