#!/usr/bin/env python3
"""Run behavior scenarios against installed Agent CLIs without shell interpolation."""
from __future__ import annotations
import argparse, json, shutil, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCENARIOS = Path(__file__).with_name("scenarios.json")

def command(agent: str, prompt: str) -> list[str]:
    if agent == "codex": return ["codex", "exec", "-s", "read-only", "-C", str(ROOT), prompt]
    if agent == "claude": return ["claude", "-p", "--permission-mode", "plan", prompt]
    if agent == "gemini": return ["gemini", "-p", prompt, "--approval-mode", "plan"]
    raise ValueError(agent)

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent", required=True, choices=("codex", "claude", "gemini"))
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--scenario", action="append", default=[])
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--list", action="store_true")
    args = parser.parse_args()
    scenarios = json.loads(SCENARIOS.read_text(encoding="utf-8"))["scenarios"]
    if args.scenario:
        wanted = set(args.scenario)
        scenarios = [item for item in scenarios if item["id"] in wanted]
        missing = wanted - {item["id"] for item in scenarios}
        if missing: raise SystemExit(f"unknown scenarios: {', '.join(sorted(missing))}")
    if args.list:
        print("\n".join(item["id"] for item in scenarios)); return 0
    if not shutil.which(args.agent): raise SystemExit(f"Agent CLI not installed: {args.agent}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    failures = 0
    with args.output.open("w", encoding="utf-8") as stream:
        for scenario in scenarios:
            started = time.monotonic()
            proc = subprocess.run(command(args.agent, scenario["prompt"]), cwd=ROOT, stdin=subprocess.DEVNULL, text=True, capture_output=True, timeout=args.timeout, check=False)
            failures += int(proc.returncode != 0)
            record = {"id":scenario["id"],"agent":args.agent,"output":proc.stdout,"stderr":proc.stderr,"exit_code":proc.returncode,"latency_ms":round((time.monotonic()-started)*1000)}
            stream.write(json.dumps(record, ensure_ascii=False)+"\n"); stream.flush()
    return 1 if failures else 0

if __name__ == "__main__": sys.exit(main())
