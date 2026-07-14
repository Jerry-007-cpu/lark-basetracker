import csv
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts/organize_jobs.py"
INSTALLER = ROOT / "scripts/install_agent.py"


def write_csv(path, rows):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["职位ID", "岗位", "地点"])
        writer.writeheader()
        writer.writerows(rows)


class CLITests(unittest.TestCase):
    def test_snapshot_state_can_be_compared_and_replaced_in_place(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = root / "first.csv"
            second = root / "second.csv"
            state = root / "jobs.state.json"
            write_csv(first, [{"职位ID": "1", "岗位": "产品", "地点": "北京"}])
            write_csv(second, [
                {"职位ID": "1", "岗位": "产品", "地点": "深圳"},
                {"职位ID": "2", "岗位": "研发", "地点": "上海"},
            ])
            subprocess.run([
                sys.executable, str(CLI), "snapshot", "--file", str(first),
                "--key-field", "职位ID", "--state-out", str(state),
            ], cwd=ROOT, check=True, capture_output=True, text=True)
            result = subprocess.run([
                sys.executable, str(CLI), "snapshot", "--file", str(second),
                "--key-field", "职位ID", "--title-field", "岗位",
                "--previous-state", str(state), "--state-out", str(state),
            ], cwd=ROOT, check=True, capture_output=True, text=True)
            self.assertIn("新增 1 · 修改 1 · 删除 0", result.stdout)
            self.assertIn("北京 → 深圳", result.stdout)

    def test_all_install_targets_have_a_dry_run(self):
        for platform in ("codex", "claude-code", "openclaw", "qclaw"):
            result = subprocess.run([
                sys.executable, str(INSTALLER), "--platform", platform, "--dry-run",
            ], cwd=ROOT, check=True, capture_output=True, text=True)
            self.assertTrue(result.stdout.strip(), platform)

    def test_project_and_qclaw_install_layouts(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory) / "project"
            project.mkdir()
            subprocess.run([
                sys.executable, str(INSTALLER), "--platform", "codex",
                "--scope", "project", "--project-dir", str(project),
            ], cwd=ROOT, check=True, capture_output=True, text=True)
            installed = project / ".agents/skills/lark-basetracker"
            self.assertTrue((installed / "SKILL.md").is_file())
            self.assertTrue((installed / "scripts/organize_jobs.py").is_file())

            fake_home = Path(directory) / "home"
            environment = {**os.environ, "HOME": str(fake_home)}
            subprocess.run([
                sys.executable, str(INSTALLER), "--platform", "qclaw",
            ], cwd=ROOT, env=environment, check=True, capture_output=True, text=True)
            qclaw_skill = fake_home / ".quantumclaw/workspace/shared/skills/lark-basetracker.md"
            qclaw_runtime = fake_home / ".quantumclaw/workspace/shared/lark-basetracker/scripts/organize_jobs.py"
            self.assertTrue(qclaw_skill.is_file())
            self.assertTrue(qclaw_runtime.is_file())
            self.assertIn(str(qclaw_runtime), qclaw_skill.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
