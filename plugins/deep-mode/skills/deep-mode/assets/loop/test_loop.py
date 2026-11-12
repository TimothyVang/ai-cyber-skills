"""Tests for loop.py, driven through a fake `omp` on PATH.

Run: python -m unittest discover -s <this folder> -p "test_*.py"
Needs git and bash (Git for Windows ships both).
"""
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

LOOP = Path(__file__).resolve().parent / "loop.py"

FAKE = """
import json, os, sys, time
action = os.environ.get("FAKE_ACTION", "noop")
record = os.environ.get("FAKE_RECORD")
if record:
    with open(record, "w", encoding="utf-8") as handle:
        json.dump({"env": dict(os.environ), "argv": sys.argv[1:], "cwd": os.getcwd(), "stdin": sys.stdin.read()}, handle)
if action == "hang":
    time.sleep(120)
elif action == "forge-cache":
    os.makedirs("tests/__pycache__", exist_ok=True)
    open("tests/__pycache__/test_x.cpython-313.pyc", "w").close()
if action == "done":
    open("ok.txt", "w").close()
elif action == "progress":
    with open("progress.txt", "a") as handle:
        handle.write("x")
elif action == "tamper-goal":
    text = open("goals/g.md", encoding="utf-8").read()
    open("goals/g.md", "w", encoding="utf-8").write(text.replace("max_iterations: ", "max_iterations: 9"))
elif action == "tamper-protect":
    with open("check.sh", "a") as handle:
        handle.write("exit 0\\n")
if action == "fail":
    sys.exit(3)
"""


def git(cwd, *args):
    subprocess.run(["git", "-C", str(cwd), "-c", "user.name=t", "-c", "user.email=t@example.com", *args],
                   check=True, capture_output=True)


def remove_tree(path):
    """git marks its object files read-only, which stops shutil.rmtree on Windows and leaves the folder behind."""
    for folder, _, files in os.walk(path):
        for name in files:
            os.chmod(os.path.join(folder, name), stat.S_IREAD | stat.S_IWRITE)
    shutil.rmtree(path, ignore_errors=True)


class LoopCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="loop-test-")).resolve()
        self.addCleanup(remove_tree, self.tmp)
        self.repo = self.tmp / "proj"
        (self.repo / "goals").mkdir(parents=True)
        (self.repo / "check.sh").write_text("test -f ok.txt\n", encoding="utf-8", newline="\n")
        git(self.repo, "init", "-q", "-b", "main")
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-q", "-m", "init")
        bin_dir = self.tmp / "bin"
        bin_dir.mkdir()
        (bin_dir / "fake.py").write_text(FAKE, encoding="utf-8")
        if os.name == "nt":
            (bin_dir / "omp.cmd").write_text(f'@"{sys.executable}" "%~dp0fake.py" %*\r\n', encoding="utf-8")
        else:
            wrapper = bin_dir / "omp"
            wrapper.write_text(f'#!/bin/sh\nexec "{sys.executable}" "$(dirname "$0")/fake.py" "$@"\n', encoding="utf-8")
            wrapper.chmod(wrapper.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        self.path = str(bin_dir) + os.pathsep + os.environ["PATH"]

    def goal(self, **fields):
        merged = {"goal": "ok.txt exists", "check": "sh ./check.sh", "protect": "check.sh", "max_iterations": 3, "max_cost_usd": 1, **fields}
        body = "".join(f"{key}: {value}\n" for key, value in merged.items() if value is not None)
        (self.repo / "goals" / "g.md").write_text(f"---\n{body}---\nCreate ok.txt.\n", encoding="utf-8", newline="\n")

    def loop(self, *args, action="noop", **env):
        full_env = {**os.environ, "PATH": self.path, "FAKE_ACTION": action, **env}
        return subprocess.run([sys.executable, str(LOOP), *args], cwd=self.repo, env=full_env, capture_output=True, text=True)

    def trail_rows(self):
        trail = self.repo / ".scratch" / "goals" / "g" / "trail.tsv"
        return trail.read_text(encoding="utf-8").strip().splitlines()[1:]

    def test_stops_with_0_when_the_check_passes(self):
        self.goal()
        run = self.loop("run", "goals/g.md", action="done")
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertIn("goal met", run.stdout)
        self.assertEqual(len(self.trail_rows()), 1)

    def test_nothing_runs_when_the_check_already_passes(self):
        self.goal()
        (self.repo / "ok.txt").write_text("", encoding="utf-8")
        run = self.loop("run", "goals/g.md", action="fail")
        self.assertEqual(run.returncode, 0)
        self.assertIn("already passes", run.stdout)

    def test_iteration_cap_exits_2(self):
        self.goal(max_iterations=2, stall_after=9)
        run = self.loop("run", "goals/g.md", action="progress")
        self.assertEqual(run.returncode, 2, run.stdout + run.stderr)
        self.assertEqual(len(self.trail_rows()), 2)

    def test_no_progress_exits_3_as_stalled(self):
        self.goal(max_iterations=5, stall_after=2)
        run = self.loop("run", "goals/g.md", action="noop")
        self.assertEqual(run.returncode, 3, run.stdout + run.stderr)
        self.assertEqual(len(self.trail_rows()), 2)

    def test_editing_the_goal_or_a_protected_file_exits_4(self):
        for action in ("tamper-goal", "tamper-protect"):
            with self.subTest(action=action):
                self.goal()
                git(self.repo, "checkout", "-q", "--", "check.sh")
                run = self.loop("run", "goals/g.md", action=action)
                self.assertEqual(run.returncode, 4, run.stdout + run.stderr)

    def test_a_failing_harness_exits_5(self):
        self.goal()
        run = self.loop("run", "goals/g.md", action="fail")
        self.assertEqual(run.returncode, 5, run.stdout + run.stderr)

    def test_goal_files_need_protect_and_a_cost_cap(self):
        self.goal(protect=None)
        run = self.loop("check", "goals/g.md")
        self.assertNotEqual(run.returncode, 0)
        self.assertIn("protect", run.stdout + run.stderr)
        self.goal(max_cost_usd=None)
        run = self.loop("run", "goals/g.md")
        self.assertNotEqual(run.returncode, 0)
        self.assertIn("max_cost_usd", run.stdout + run.stderr)

    def test_check_reports_without_running_the_harness(self):
        self.goal()
        run = self.loop("check", "goals/g.md", action="done")
        self.assertEqual(run.returncode, 0)
        self.assertIn("check exit 1", run.stdout)
        self.assertFalse((self.repo / "ok.txt").exists())

    def test_dry_run_prints_the_command_and_touches_nothing(self):
        self.goal()
        run = self.loop("run", "goals/g.md", "--dry-run", action="done")
        self.assertEqual(run.returncode, 0)
        self.assertIn("--max-cost", run.stdout)
        self.assertFalse((self.repo / "ok.txt").exists())
        self.assertFalse((self.repo / ".scratch").exists())

    def test_the_harness_runs_in_the_root_without_api_keys_and_with_in_repo_temp(self):
        self.goal()
        record = self.tmp / "record.json"
        run = self.loop("run", "goals/g.md", action="done", FAKE_RECORD=str(record),
                        ANTHROPIC_API_KEY="k", OPENAI_API_KEY="k", CODEX_API_KEY="k")
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        seen = json.loads(record.read_text(encoding="utf-8"))
        for key in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "CODEX_API_KEY"):
            self.assertNotIn(key, seen["env"])
        self.assertEqual(Path(seen["cwd"]).resolve(), self.repo)
        self.assertEqual(Path(seen["env"]["TMPDIR"]).resolve(), self.repo / ".scratch" / "tmp")
        self.assertIn("--max-cost", seen["argv"])

    def test_the_prompt_travels_on_stdin_not_in_the_command(self):
        # On Windows the harness is a .cmd shim: cmd.exe would run `& echo INJECTED` if the prompt were an argument.
        self.goal(check='sh ./check.sh || { echo "a" & echo INJECTED >/dev/null; false; }', max_iterations=1)
        record = self.tmp / "seen.json"
        run = self.loop("run", "goals/g.md", FAKE_RECORD=str(record))
        self.assertEqual(run.returncode, 2, run.stdout + run.stderr)
        seen = json.loads(record.read_text(encoding="utf-8"))
        self.assertIn("echo INJECTED", seen["stdin"])
        self.assertIn("goals/g.md", seen["stdin"])
        self.assertFalse([arg for arg in seen["argv"] if "INJECTED" in arg or "goals/g.md" in arg])

    def test_a_hung_harness_is_stopped_and_exits_5(self):
        self.goal(iteration_minutes=0.03)
        run = self.loop("run", "goals/g.md", action="hang")
        self.assertEqual(run.returncode, 5, run.stdout + run.stderr)
        self.assertIn("ran past 0.03 minutes", run.stdout)

    def test_a_hung_check_stops_the_run_before_any_harness_call(self):
        self.goal(check="sleep 120", check_minutes=0.02, protect="none")
        record = self.tmp / "seen.json"
        run = self.loop("run", "goals/g.md", FAKE_RECORD=str(record))
        self.assertEqual(run.returncode, 5, run.stdout + run.stderr)
        self.assertIn("check ran past 0.02 minutes", run.stdout)
        self.assertFalse(record.exists())

    def test_a_check_that_exits_124_is_a_failing_check_not_a_timeout(self):
        self.goal(check="exit 124", protect="none", max_iterations=1)
        run = self.loop("run", "goals/g.md")
        self.assertEqual(run.returncode, 2, run.stdout + run.stderr)

    def test_time_limits_must_be_finite(self):
        for value in ("inf", "nan", "0", "-1", "soon"):
            with self.subTest(value=value):
                self.goal(check_minutes=value)
                run = self.loop("check", "goals/g.md")
                self.assertNotEqual(run.returncode, 0)
                self.assertIn("check_minutes must be a positive number", run.stdout + run.stderr)

    def test_caches_under_protected_paths_are_cleared_before_the_check(self):
        (self.repo / "tests").mkdir()
        (self.repo / "tests" / "test_x.py").write_text("", encoding="utf-8")
        self.goal(protect="check.sh tests", max_iterations=1)
        run = self.loop("run", "goals/g.md", action="forge-cache")
        self.assertEqual(run.returncode, 2, run.stdout + run.stderr)
        self.assertFalse((self.repo / "tests" / "__pycache__").exists())

    def test_caches_beside_a_protected_file_are_cleared_too(self):
        (self.repo / "tests").mkdir()
        (self.repo / "tests" / "test_x.py").write_text("", encoding="utf-8")
        self.goal(protect="check.sh tests/test_x.py", max_iterations=1)
        run = self.loop("run", "goals/g.md", action="forge-cache")
        self.assertEqual(run.returncode, 2, run.stdout + run.stderr)
        self.assertFalse((self.repo / "tests" / "__pycache__").exists())


if __name__ == "__main__":
    unittest.main()
