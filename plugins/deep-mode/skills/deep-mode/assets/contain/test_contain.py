"""Tests for the containment guards (claude_guard.py behind claude-guard.sh, and omp-contain.ts).

Run: python -m unittest discover -s <this folder> -p "test_*.py"
The omp hook cases need `bun` on PATH and are skipped without it.
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

HERE = Path(__file__).resolve().parent
GUARD = HERE / "claude_guard.py"
ENTRY = HERE / "claude-guard.sh"
PLUGIN = HERE.parents[3]  # plugins/deep-mode
HOOK = HERE / "omp-contain.ts"

DRIVER = """
const [hookUrl, casesPath] = process.argv.slice(2);
const mod = await import(hookUrl);
let handler;
mod.default({ on: (_event, fn) => { handler = fn; } });
const cases = JSON.parse(await Bun.file(casesPath).text());
const out = [];
for (const c of cases) {
  const result = await handler({ toolName: c.tool, input: c.input }, { cwd: c.cwd });
  out.push(result && result.block ? "deny" : "allow");
}
console.log(JSON.stringify(out));
"""


def git(cwd, *args):
    subprocess.run(["git", "-C", str(cwd), "-c", "user.name=t", "-c", "user.email=t@example.com", *args],
                   check=True, capture_output=True)


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


class GuardCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="contain-test-")).resolve()
        cls.proj = cls.tmp / "proj"
        cls.proj.mkdir()
        git(cls.proj, "init", "-q", "-b", "main")
        git(cls.proj, "commit", "-q", "--allow-empty", "-m", "init")
        cls.inner = cls.proj / ".worktrees" / "wt"
        git(cls.proj, "worktree", "add", "-q", "--detach", str(cls.inner))
        cls.ext = cls.tmp / "ext"
        git(cls.proj, "worktree", "add", "-q", "--detach", str(cls.ext))
        cls.outside = cls.tmp / "outside"
        cls.outside.mkdir()
        cls.claude_dir = cls.tmp / "claude"
        # The temp folder may sit inside a git repo (TMP pointed at <repo>/.scratch/tmp): stop git's upward search
        # there, so `outside` really is outside git.
        cls.env = {**os.environ, "GIT_CEILING_DIRECTORIES": str(cls.tmp)}

    @classmethod
    def tearDownClass(cls):
        remove_tree(cls.tmp)


class ClaudeGuard(GuardCase):
    def run_guard(self, tool, path, cwd=None, key="file_path", args=(), session="s1"):
        event = {"tool_name": tool, "tool_input": {key: str(path)}, "cwd": str(cwd or self.proj), "session_id": session}
        env = {**self.env, "CLAUDE_CONFIG_DIR": str(self.claude_dir)}
        proc = subprocess.run([sys.executable, str(GUARD), *args], input=json.dumps(event), capture_output=True, text=True, env=env)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return "deny" if '"permissionDecision": "deny"' in proc.stdout else "allow"

    def test_writes_inside_the_root_pass(self):
        self.assertEqual(self.run_guard("Write", self.proj / "src" / "a.txt"), "allow")
        self.assertEqual(self.run_guard("Edit", "src/a.txt"), "allow")

    def test_writes_outside_the_root_are_denied(self):
        for tool, key in (("Write", "file_path"), ("Edit", "file_path"), ("NotebookEdit", "notebook_path")):
            with self.subTest(tool=tool):
                self.assertEqual(self.run_guard(tool, self.outside / "x.txt", key=key), "deny")

    def test_a_sibling_whose_name_extends_the_root_is_outside(self):
        self.assertEqual(self.run_guard("Write", self.tmp / "proj-evil" / "x.txt"), "deny")

    def test_dot_dot_cannot_escape(self):
        self.assertEqual(self.run_guard("Write", self.proj / ".." / "x.txt"), "deny")
        self.assertEqual(self.run_guard("Write", "../x.txt"), "deny")

    def test_reads_are_never_blocked(self):
        self.assertEqual(self.run_guard("Read", self.outside / "x.txt"), "allow")
        self.assertEqual(self.run_guard("Read", self.proj / ".env"), "allow")

    def test_a_linked_worktree_may_write_itself_and_its_main_checkout(self):
        for cwd in (self.inner, self.ext):
            with self.subTest(cwd=cwd.name):
                self.assertEqual(self.run_guard("Write", cwd / "a.txt", cwd=cwd), "allow")
                self.assertEqual(self.run_guard("Write", self.proj / "README.md", cwd=cwd), "allow")
                self.assertEqual(self.run_guard("Write", self.outside / "a.txt", cwd=cwd), "deny")

    def test_outside_git_the_cwd_is_the_root(self):
        self.assertEqual(self.run_guard("Write", self.outside / "a.txt", cwd=self.outside), "allow")
        self.assertEqual(self.run_guard("Write", self.proj / "a.txt", cwd=self.outside), "deny")

    def test_extra_write_roots_open_only_the_named_folder(self):
        config = self.proj / ".deep-mode.json"
        config.write_text(json.dumps({"extraWriteRoots": [str(self.outside / "ok")]}), encoding="utf-8")
        try:
            self.assertEqual(self.run_guard("Write", self.outside / "ok" / "x.txt"), "allow")
            self.assertEqual(self.run_guard("Write", self.outside / "no" / "x.txt"), "deny")
        finally:
            config.unlink()

    def test_claude_plan_files_pass_but_settings_do_not(self):
        self.assertEqual(self.run_guard("Write", self.claude_dir / "plans" / "p.md"), "allow")
        self.assertEqual(self.run_guard("Write", self.claude_dir / "settings.json"), "deny")

    def test_plugin_hook_enforces_only_after_a_deep_mode_command(self):
        data = self.tmp / "plugin-data"
        target = self.outside / "x.txt"

        def send(mode, payload):
            subprocess.run([sys.executable, str(GUARD), mode, str(data)], input=json.dumps(payload), capture_output=True, text=True, check=True)

        self.assertEqual(self.run_guard("Write", target, args=("if-active", str(data))), "allow")
        send("activate", {"prompt": "please run /deep-mode:deep later", "session_id": "s1"})
        self.assertEqual(self.run_guard("Write", target, args=("if-active", str(data))), "allow")
        send("activate", {"prompt": "  /deep-mode:deep fix it", "session_id": "s1"})
        self.assertEqual(self.run_guard("Write", target, args=("if-active", str(data))), "deny")
        self.assertEqual(self.run_guard("Write", target, args=("if-active", str(data)), session="other"), "allow")

    def test_marks_older_than_30_days_are_pruned_on_the_next_activation(self):
        data = self.tmp / "plugin-data-prune"
        marks = data / "active-sessions"
        marks.mkdir(parents=True)
        old, recent = marks / "old", marks / "recent"
        old.touch()
        recent.touch()
        long_ago = old.stat().st_mtime - 31 * 24 * 3600
        os.utime(old, (long_ago, long_ago))
        subprocess.run([sys.executable, str(GUARD), "activate", str(data)], input=json.dumps({"prompt": "/deep-mode:deep x", "session_id": "new"}),
                       capture_output=True, text=True, check=True)
        self.assertEqual(sorted(path.name for path in marks.iterdir()), ["new", "recent"])

    def test_unreadable_input_does_not_block(self):
        proc = subprocess.run([sys.executable, str(GUARD)], input="not json", capture_output=True, text=True)
        self.assertEqual((proc.returncode, proc.stdout), (0, ""))


@unittest.skipUnless(find_bash(), "needs bash")
class ClaudeHookEntry(GuardCase):
    """The commands Claude Code runs: claude-guard.sh, the plugin's hooks.json, and the skill's frontmatter hook."""

    def hook(self, command, event, python=True, **env):
        full_env = {**self.env, "CLAUDE_CONFIG_DIR": str(self.claude_dir), "CLAUDE_PLUGIN_ROOT": PLUGIN.as_posix(),
                    **({} if python else {"DEEP_MODE_GUARD_PYTHONS": "no-such-python"}), **env}
        proc = subprocess.run([find_bash(), "-c", command], input=json.dumps(event), capture_output=True, text=True,
                              env=full_env)
        return proc.returncode, "deny" if '"permissionDecision": "deny"' in proc.stdout else "allow", proc.stderr

    def write(self, path, session="s1"):
        return {"tool_name": "Write", "tool_input": {"file_path": str(path)}, "cwd": str(self.proj),
                "session_id": session}

    def entry(self, *args):
        return f'bash "{ENTRY.as_posix()}" {" ".join(args)}'

    def test_the_skill_hook_denies_outside_writes_and_allows_inside_ones(self):
        text = (PLUGIN / "skills/deep-mode/SKILL.md").read_text(encoding="utf-8")
        command = text.split("command: '", 1)[1].split("'\n", 1)[0]
        self.assertEqual(self.hook(command, self.write(self.outside / "x.txt"))[:2], (0, "deny"))
        self.assertEqual(self.hook(command, self.write(self.proj / "a.txt"))[:2], (0, "allow"))

    def test_the_plugin_hooks_guard_a_session_after_a_deep_mode_command(self):
        hooks = json.loads((PLUGIN / "hooks" / "hooks.json").read_text(encoding="utf-8"))["hooks"]
        activate = hooks["UserPromptSubmit"][0]["hooks"][0]["command"]
        pre = hooks["PreToolUse"][0]["hooks"][0]["command"]
        data = {"CLAUDE_PLUGIN_DATA": (self.tmp / "entry-data").as_posix()}
        outside = self.write(self.outside / "x.txt", session="p1")
        self.assertEqual(self.hook(pre, outside, **data)[:2], (0, "allow"))
        self.hook(activate, {"prompt": "/deep-mode:deep fix it", "session_id": "p1"}, **data)
        self.assertEqual(self.hook(pre, outside, **data)[:2], (0, "deny"))

    def test_without_python_an_active_session_is_denied_every_write(self):
        data = (self.tmp / "no-python-data").as_posix()
        inside = self.write(self.proj / "a.txt", session="n1")
        code, _, err = self.hook(self.entry("enforce"), inside, python=False)
        self.assertEqual(code, 2)
        self.assertIn("Python 3.8", err)
        self.assertEqual(self.hook(self.entry("if-active", f'"{data}"'), inside, python=False)[0], 0)  # not active
        self.hook(self.entry("activate", f'"{data}"'), {"prompt": "just chatting", "session_id": "n1"}, python=False)
        self.assertEqual(self.hook(self.entry("if-active", f'"{data}"'), inside, python=False)[0], 0)
        self.hook(self.entry("activate", f'"{data}"'), {"prompt": " /deep-mode:deep x", "session_id": "n1"},
                  python=False)
        self.assertEqual(self.hook(self.entry("if-active", f'"{data}"'), inside, python=False)[0], 2)
        other = self.write(self.proj / "a.txt", session="n2")
        self.assertEqual(self.hook(self.entry("if-active", f'"{data}"'), other, python=False)[0], 0)


@unittest.skipUnless(shutil.which("bun"), "bun is not on PATH")
class OmpHook(GuardCase):
    def decide(self, cases):
        driver = self.tmp / "driver.mjs"
        driver.write_text(DRIVER, encoding="utf-8")
        cases_path = self.tmp / "cases.json"
        cases_path.write_text(json.dumps([{"tool": t, "input": i, "cwd": str(c)} for t, i, c in cases]), encoding="utf-8")
        proc = subprocess.run([shutil.which("bun"), str(driver), HOOK.as_uri(), str(cases_path)], capture_output=True, text=True,
                              env=self.env)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return json.loads(proc.stdout.strip().splitlines()[-1])

    def test_hook_decisions(self):
        proj, out = self.proj, self.outside
        cases = [
            (("write", {"path": "src/a.txt"}, proj), "allow"),
            (("write", {"path": str(proj / "a.txt")}, proj), "allow"),
            (("write", {"path": str(out / "x.txt")}, proj), "deny"),
            (("edit", {"path": str(out / "x.txt")}, proj), "deny"),
            (("ast_edit", {"path": str(out / "x.ts")}, proj), "deny"),
            (("write", {"path": str(self.tmp / "proj-evil" / "x")}, proj), "deny"),
            (("write", {"path": "../x.txt"}, proj), "deny"),
            (("edit", {"path": "a.txt", "paths": ["a.txt", str(out / "x")]}, proj), "deny"),
            (("write", {"path": "local://notes.md"}, proj), "allow"),
            (("write", {"path": "skill://deep-mode/SKILL.md"}, proj), "deny"),
            (("write", {"path": "out.zip:inner/a.txt"}, proj), "allow"),
            (("write", {"path": "data/app.sqlite:users:42"}, proj), "allow"),
            (("write", {"path": "README.md:../../../../x.txt"}, proj), "deny"),
            (("write", {"path": f"{out / 'out.zip'}:inner/a.txt"}, proj), "deny"),
            (("write", {"path": "[src/a.txt#1A2B]"}, proj), "allow"),
            (("write", {"path": f"[{out / 'x.txt'}#1A2B]"}, proj), "deny"),
            (("write", {"path": "~/evil.txt"}, proj), "deny"),
            (("write", {"path": "[~/evil.txt#1A2B]"}, proj), "deny"),
            (("write", {"path": "conflict://1"}, proj), "allow"),
            (("write", {"path": "out://reply"}, proj), "allow"),
            (("write", {"path": "vault://notes/a.md"}, proj), "deny"),
            (("write", {"path": str(proj / "README.md")}, self.inner), "allow"),
            (("write", {"path": str(self.ext / "a.txt")}, self.ext), "allow"),
            (("write", {"path": str(proj / "a.txt")}, self.ext), "allow"),
            (("write", {"path": str(out / "a.txt")}, self.ext), "deny"),
            (("read", {"path": str(out / "x.txt")}, proj), "allow"),
            (("bash", {"command": "echo hi > /tmp/x"}, proj), "allow"),
        ]
        got = self.decide([case for case, _ in cases])
        for (case, want), decision in zip(cases, got):
            with self.subTest(tool=case[0], input=case[1], cwd=Path(case[2]).name):
                self.assertEqual(decision, want)


if __name__ == "__main__":
    unittest.main()
