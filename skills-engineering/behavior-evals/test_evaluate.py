import json, subprocess, tempfile, unittest
from pathlib import Path
ROOT = Path(__file__).parent

class BehaviorEvalTests(unittest.TestCase):
    def test_success_is_scored_from_golden_anchors(self):
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as file:
            file.write(json.dumps({"id":"direct-trivial-no-grill","output":"README typo 修正说明"}, ensure_ascii=False)+"\n")
            result_path=file.name
        proc=subprocess.run(["python3",str(ROOT/"evaluate.py"),result_path],capture_output=True,text=True)
        report=json.loads(proc.stdout)
        self.assertEqual(proc.returncode,0); self.assertTrue(report["rows"][0]["task_success"])
    def test_runner_lists_all_scenarios_without_calling_agent(self):
        listed=subprocess.run(["python3",str(ROOT/"run.py"),"--agent","codex","--output","/tmp/unused.jsonl","--list"],capture_output=True,text=True,check=True)
        scenario_count=len(json.loads((ROOT/"scenarios.json").read_text())["scenarios"])
        self.assertEqual(len(listed.stdout.strip().splitlines()),scenario_count)
    def test_infrastructure_failure_is_not_scored_as_model_failure(self):
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as file:
            file.write(json.dumps({"id":"direct-trivial-no-grill","agent":"codex","output":"","exit_code":1})+"\n"); result_path=file.name
        proc=subprocess.run(["python3",str(ROOT/"evaluate.py"),result_path],capture_output=True,text=True)
        report=json.loads(proc.stdout)
        self.assertEqual(report["evaluated"],0); self.assertEqual(len(report["infrastructure_failures"]),1)

if __name__ == "__main__": unittest.main()
