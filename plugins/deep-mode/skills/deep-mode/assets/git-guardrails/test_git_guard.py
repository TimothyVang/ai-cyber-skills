"""Tests for the git guard's patterns, run through git-guard.sh --check and through git-guard.ts (needs bun).

Run: python -m unittest discover -s <this folder> -p "test_*.py"
Needs git and bash (Git for Windows ships both).
"""
import json
import os
import shutil
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

GUARD = Path(__file__).resolve().parent / "git-guard.sh"
HOOK = Path(__file__).resolve().parent / "git-guard.ts"

DRIVER = """
const [hookUrl, casesPath, cwd] = process.argv.slice(2);
const mod = await import(hookUrl);
let handler;
mod.default({ on: (_event, fn) => { handler = fn; } });
const out = [];
for (const command of JSON.parse(await Bun.file(casesPath).text())) {
  const result = await handler({ toolName: "bash", input: { command, cwd } });
  out.push(result && result.block ? "block" : "allow");
}
console.log(JSON.stringify(out));
"""

BLOCKED = [
    "git reset --hard",
    "git --no-pager reset --hard",
    'git -C "C:/My Repo" reset --hard',
    "git -c a=b -C dir reset --hard HEAD~1",
    "git --git-dir x/.git reset --hard",
    'git -c user.name="A B" reset --hard',
    'git --git-dir="C:/My Repo/.git" --work-tree="C:/My Repo" reset --hard',
    "git reset \\\n  --hard",
    "git clean -fd",
    "git checkout .",
    "git stash drop",
    "git worktree remove --force .worktrees/x",
    "git branch -D old",
    "git push --force origin feat",
    "git --no-pager push --force origin main",
    "git push -f origin feat",
    "git push origin +feat",
    "git push origin --delete feat",
    "git push origin main",
    "git push origin feat:main",
    "git push origin feat && git push origin main",
    "cd repo; git reset --hard",
]
ALLOWED = [
    "git status",
    "git reset --soft HEAD~1",
    "git worktree remove .worktrees/x",
    "git branch -d merged",
    "git push -u origin feat",
    "git push --force-with-lease origin feat",
    "git push -u origin feat && gh pr create --base main",
    "git push -u origin feat\ngh pr create --base main",
    "git push -u origin feat\ngit log main",
    "git push origin feat; gh pr merge 5 --merge",
    "git commit -m wip && git log main",
    "git fetch origin main",
    "gh pr merge 12 --merge --match-head-commit abc",
]


def find_bash():
    """On Windows, System32\\bash.exe is WSL and cannot see Windows paths; use the bash beside git."""
    bash = shutil.which("bash")
    if os.name != "nt" or (bash and "system32" not in bash.lower()):
        return bash
    git_exe = shutil.which("git")
    for rel in ("../bin/bash.exe", "../usr/bin/bash.exe", "../../bin/bash.exe"):
        candidate = os.path.normpath(os.path.join(os.path.dirname(git_exe), rel)) if git_exe else ""
        if candidate and os.path.exists(candidate):
            return candidate
    return None


def remove_tree(path):
    """git marks its object files read-only, which stops shutil.rmtree on Windows and leaves the folder behind."""
    for folder, _, files in os.walk(path):
        for name in files:
            os.chmod(os.path.join(folder, name), stat.S_IREAD | stat.S_IWRITE)
    shutil.rmtree(path, ignore_errors=True)


@unittest.skipUnless(find_bash() and shutil.which("git"), "needs bash and git")
class GitGuardTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="git-guard-test-")
        cls.addClassCleanup(remove_tree, cls.tmp)
        subprocess.run(["git", "init", "-q", "-b", "feat", cls.tmp], check=True, capture_output=True)

    def verdict(self, command, cwd=None):
        proc = subprocess.run([find_bash(), str(GUARD).replace("\\", "/"), "--check", command], cwd=cwd or self.tmp,
                              capture_output=True, text=True)
        return {0: "allow", 2: "block"}.get(proc.returncode, f"exit {proc.returncode}: {proc.stderr}")

    def test_destructive_commands_are_blocked(self):
        for command in BLOCKED:
            with self.subTest(command=command):
                self.assertEqual(self.verdict(command), "block")

    def test_normal_work_is_allowed(self):
        for command in ALLOWED:
            with self.subTest(command=command):
                self.assertEqual(self.verdict(command), "allow")

    def test_a_bare_push_is_blocked_only_on_the_default_branch(self):
        self.assertEqual(self.verdict("git push"), "allow")
        subprocess.run(["git", "-C", self.tmp, "checkout", "-q", "-b", "main"], check=True, capture_output=True)
        try:
            self.assertEqual(self.verdict("git push"), "block")
            self.assertEqual(self.verdict("git push origin HEAD"), "block")
        finally:
            subprocess.run(["git", "-C", self.tmp, "checkout", "-q", "-b", "feat2"], check=True, capture_output=True)

    @unittest.skipUnless(shutil.which("bun"), "bun is not on PATH")
    def test_the_omp_hook_agrees_with_the_shell_guard(self):
        driver, cases = Path(self.tmp) / "driver.mjs", Path(self.tmp) / "cases.json"
        driver.write_text(DRIVER, encoding="utf-8")
        cases.write_text(json.dumps(BLOCKED + ALLOWED), encoding="utf-8")
        proc = subprocess.run([shutil.which("bun"), str(driver), HOOK.as_uri(), str(cases), self.tmp],
                              capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        got = json.loads(proc.stdout.strip().splitlines()[-1])
        for command, verdict in zip(BLOCKED + ALLOWED, got):
            with self.subTest(command=command):
                self.assertEqual(verdict, "block" if command in BLOCKED else "allow")


if __name__ == "__main__":
    unittest.main()
