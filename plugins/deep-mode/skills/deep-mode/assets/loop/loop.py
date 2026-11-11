#!/usr/bin/env python3
"""Drive an agent toward a goal file until its check passes (deep-mode "Self-authoring" playbook).

    python loop.py check <goal.md>                      validate the goal file, run its check once
    python loop.py run <goal.md> [--harness omp|claude|codex] [--max-iterations N] [--dry-run]

A goal file is Markdown with frontmatter (one `key: value` per line):
    goal: one-line objective
    check: shell command; exit 0 means done
    protect: tests/test_x.py scripts/check.sh  (required: files and folders the check runs, which the agent must not
                                              change; `none` when the check reads nothing the agent could edit)
    harness: omp | claude | codex            (default omp)
    max_iterations: 10                       (hard cap, required)
    max_cost_usd: 2                          (per iteration; omp --max-cost, claude --max-budget-usd; required for
                                              both; codex has none)
    stall_after: 3                           (stop after N iterations that changed neither the check output nor
                                              the working tree)
    harness_args: --model sonnet             (extra flags for the harness, split like a shell)

Each iteration runs the harness headless in the project root on the user's subscription (API-key variables are
removed from the child's environment), then runs the check. Logs go to <root>/.scratch/goals/<slug>/: trail.tsv plus
one <run>-iteration-N.log per iteration. --dry-run prints the harness command and runs nothing. Exit codes: 0 done,
2 iteration cap, 3 stalled, 4 the agent changed the goal's frontmatter or a protected file, 5 the harness exited
nonzero (omp exits 3 at its cost cap), 1 error.
"""
import argparse
import hashlib
import os
import re
import shlex
import shutil
import subprocess
import sys
import time

API_KEY_VARS = ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "OPENAI_API_KEY", "CODEX_API_KEY")
REQUIRED = ("goal", "check", "protect", "max_iterations")
COST_FLAGS = {"omp": "--max-cost", "claude": "--max-budget-usd"}
CACHE_PARTS = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
PROMPT = (
    "Work toward the goal in {goal_file}. Read it first, then the trail of earlier iterations in {trail} if it exists. "
    "Do the next smallest verifiable step toward the goal, run its check (`{check}`), and commit progress you would keep. "
    "Stop after that one step. Never edit the goal file's frontmatter (goal, check, limits) or the files the check runs "
    "({protect}): if the goal or the check is wrong, say so and stop. This is iteration {i} of at most {n}."
)


def parse(goal_path):
    with open(goal_path, encoding="utf-8") as handle:
        text = handle.read()
    match = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n", text, re.S)
    if not match:
        raise SystemExit(f"{goal_path}: missing frontmatter")
    fields = {}
    for line in match.group(1).splitlines():
        if ":" in line and not line.lstrip().startswith("#"):
            key, value = line.split(":", 1)
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            fields[key.strip()] = value
    missing = [key for key in REQUIRED if not fields.get(key)]
    if missing:
        raise SystemExit(f"{goal_path}: frontmatter needs {', '.join(missing)}")
    if not fields["max_iterations"].isdigit() or int(fields["max_iterations"]) < 1:
        raise SystemExit(f"{goal_path}: max_iterations must be a positive integer")
    if not fields.get("stall_after", "3").isdigit() or int(fields.get("stall_after", "3")) < 1:
        raise SystemExit(f"{goal_path}: stall_after must be a positive integer")
    return fields, hashlib.sha256(match.group(1).encode()).hexdigest()


def git(root, *args):
    return subprocess.run(["git", "-C", root, *args], capture_output=True, text=True, encoding="utf-8", errors="replace")


def project_root(path):
    out = git(os.path.dirname(os.path.abspath(path)), "rev-parse", "--show-toplevel")
    if out.returncode:
        raise SystemExit("the goal file must live inside a git repo (deep-mode: Contain the work)")
    return os.path.normpath(out.stdout.strip())


def protected_paths(fields, root, goal_path):
    """Resolve `protect` to root-relative paths. Each must exist inside the root and not be the root itself."""
    if fields["protect"].strip().lower() == "none":
        return []
    paths = []
    for entry in shlex.split(fields["protect"]):
        full = os.path.normpath(os.path.join(root, entry))
        rel = os.path.relpath(full, root)
        if rel == "." or rel.startswith(".."):
            raise SystemExit(f"{goal_path}: protect path {entry!r} must be inside the project root and not the root")
        if not os.path.exists(full):
            raise SystemExit(f"{goal_path}: protect path {entry!r} does not exist")
        paths.append(rel.replace(os.sep, "/"))
    return paths


def walk_files(root, rel, skip=()):
    """Yield the root-relative path of every file under rel, git-ignored or not, in sorted order, without following
    symlinked folders. Skips .git, tool caches, and the root-relative folders in skip. A missing rel yields itself."""
    full = os.path.join(root, rel)
    if not os.path.isdir(full):
        yield rel
        return
    for folder, dirs, files in os.walk(full):
        dirs[:] = sorted(d for d in dirs if d != ".git" and d not in CACHE_PARTS
                         and os.path.relpath(os.path.join(folder, d), root).replace(os.sep, "/") not in skip)
        for name in sorted(files):
            yield os.path.relpath(os.path.join(folder, name), root).replace(os.sep, "/")


def protect_digest(root, paths):
    """Content hash of every file under the protected paths, git-ignored files included, so edits, deletions, and new
    files (a conftest.py that skips every test) all show up. Tool caches are skipped: running the check writes them."""
    digests = {}
    for path in paths:
        for rel in walk_files(root, path):
            try:
                with open(os.path.join(root, rel), "rb") as handle:
                    digests[rel] = hashlib.sha256(handle.read()).hexdigest()
            except FileNotFoundError:
                digests[rel] = "missing"
    return digests


def workspace_state(root, skip):
    """HEAD plus the path, size, and mtime of every file in the working tree, git-ignored files included, minus .git,
    tool caches, and the loop's own logs and temp folder. Read-only: nothing is written to git's object store.
    Changes when the agent edits, adds, deletes, or commits anything."""
    state = hashlib.sha256(git(root, "rev-parse", "--verify", "-q", "HEAD").stdout.encode())
    for rel in walk_files(root, ".", skip):
        try:
            info = os.stat(os.path.join(root, rel), follow_symlinks=False)
        except FileNotFoundError:
            continue
        state.update(f"{rel}\0{info.st_size}\0{info.st_mtime_ns}\0".encode())
    return state.hexdigest()


def find_bash():
    """Checks are written for bash. On Windows, prefer Git Bash: System32\\bash.exe is WSL and sees other paths."""
    bash = shutil.which("bash")
    if os.name != "nt" or (bash and "system32" not in bash.lower()):
        return bash
    git_exe = shutil.which("git")
    for rel in ("../bin/bash.exe", "../usr/bin/bash.exe", "../../bin/bash.exe"):
        candidate = os.path.normpath(os.path.join(os.path.dirname(git_exe), rel)) if git_exe else ""
        if candidate and os.path.exists(candidate):
            return candidate
    return None


def run_check(command, root):
    bash = find_bash()
    argv = [bash, "-c", command] if bash else command
    proc = subprocess.run(argv, shell=not bash, cwd=root, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return proc.returncode, (proc.stdout + proc.stderr)[-4000:]


def cost_cap(fields, harness, goal_path):
    """omp and Claude Code have a per-run cost flag; the playbook requires it for unattended runs."""
    cost = fields.get("max_cost_usd")
    if harness not in COST_FLAGS:
        return None
    if not cost:
        raise SystemExit(f"{goal_path}: max_cost_usd is required for harness {harness} ({COST_FLAGS[harness]})")
    try:
        if float(cost) <= 0:
            raise ValueError
    except ValueError:
        raise SystemExit(f"{goal_path}: max_cost_usd must be a positive number")
    return cost


def harness_command(fields, harness, prompt, cost):
    extra = shlex.split(fields.get("harness_args", ""))
    if harness == "omp":
        cmd = ["omp", "-p", "--no-title", "--max-cost", cost, *extra, prompt]
    elif harness == "claude":
        cmd = ["claude", "-p", "--permission-mode", "acceptEdits", "--max-budget-usd", cost, *extra, prompt]
    elif harness == "codex":
        cmd = ["codex", "exec", "--sandbox", "workspace-write", *extra, prompt]
    else:
        raise SystemExit(f"unknown harness {harness!r}; use omp, claude, or codex")
    if not shutil.which(cmd[0]):
        raise SystemExit(f"`{cmd[0]}` is not on PATH")
    return [shutil.which(cmd[0]), *cmd[1:]]


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("action", choices=["check", "run"])
    parser.add_argument("goal")
    parser.add_argument("--harness")
    parser.add_argument("--max-iterations", type=int)
    parser.add_argument("--dry-run", action="store_true", help="print the harness command and run nothing, not even the check")
    opts = parser.parse_args()

    fields, digest = parse(opts.goal)
    root = project_root(opts.goal)
    protect = protected_paths(fields, root, opts.goal)
    harness = opts.harness or fields.get("harness", "omp")
    if harness not in ("omp", "claude", "codex"):
        raise SystemExit(f"unknown harness {harness!r}; use omp, claude, or codex")
    cost = cost_cap(fields, harness, opts.goal)
    goal_rel = os.path.relpath(os.path.abspath(opts.goal), root).replace(os.sep, "/")
    limit = min(opts.max_iterations or 10**9, int(fields["max_iterations"]))
    stall_after = int(fields.get("stall_after", "3"))
    slug = re.sub(r"[^A-Za-z0-9_-]+", "-", os.path.splitext(os.path.basename(opts.goal))[0]).strip("-") or "goal"
    log_dir = os.path.join(root, ".scratch", "goals", slug)
    trail = os.path.join(log_dir, "trail.tsv")
    trail_rel = os.path.relpath(trail, root).replace(os.sep, "/")
    protect_text = " ".join(protect) or "none"

    def prompt(i):
        return PROMPT.format(goal_file=goal_rel, trail=trail_rel, check=fields["check"], protect=protect_text, i=i, n=limit)

    if opts.action == "run" and opts.dry_run:
        print(" ".join(shlex.quote(part) for part in harness_command(fields, harness, prompt(1), cost)))
        return 0

    code, output = run_check(fields["check"], root)
    if opts.action == "check":
        print(f"goal ok: {fields['goal']}\nprotected: {protect_text}\n"
              f"check exit {code}{' (already done)' if code == 0 else ''}\n{output.strip()}")
        return 0
    if code == 0:
        print("check already passes; nothing to do")
        return 0

    tmp = os.path.join(root, ".scratch", "tmp")
    os.makedirs(tmp, exist_ok=True)
    os.makedirs(log_dir, exist_ok=True)
    ignore = os.path.join(root, ".scratch", ".gitignore")
    if not os.path.exists(ignore):
        with open(ignore, "w") as handle:
            handle.write("*\n")
    if not os.path.exists(trail):
        with open(trail, "w", encoding="utf-8") as handle:
            handle.write("ts\trun\titeration\tharness\tharness_exit\tcheck_exit\tseconds\n")
    env = {k: v for k, v in os.environ.items() if k not in API_KEY_VARS}
    env.update(TMPDIR=tmp, TMP=tmp, TEMP=tmp)
    run_id = f"{time.strftime('%Y%m%dT%H%M%S')}-{os.getpid()}"
    guard = protect_digest(root, protect)
    own = {os.path.relpath(path, root).replace(os.sep, "/") for path in (tmp, log_dir)}

    last_output, last_state, unchanged = output, workspace_state(root, own), 0
    for i in range(1, limit + 1):
        cmd = harness_command(fields, harness, prompt(i), cost)
        started = time.time()
        with open(os.path.join(log_dir, f"{run_id}-iteration-{i}.log"), "x", encoding="utf-8", errors="replace") as log:
            harness_exit = subprocess.run(cmd, cwd=root, env=env, stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL).returncode
        if parse(opts.goal)[1] != digest:
            print(f"iteration {i}: the agent changed the goal's frontmatter; stopping")
            return 4
        current = protect_digest(root, protect)
        if current != guard:
            changed = sorted(rel for rel in guard.keys() | current.keys() if guard.get(rel) != current.get(rel))
            print(f"iteration {i}: the agent changed protected files ({', '.join(changed[:5])}); stopping")
            return 4
        code, output = run_check(fields["check"], root)
        with open(trail, "a", encoding="utf-8") as handle:
            handle.write(f"{time.strftime('%Y-%m-%dT%H:%M:%S')}\t{run_id}\t{i}\t{harness}\t{harness_exit}\t{code}\t{time.time() - started:.0f}\n")
        print(f"iteration {i}: harness exit {harness_exit}, check exit {code}")
        if code == 0:
            print("goal met")
            return 0
        if harness_exit != 0:
            print(f"harness exited {harness_exit} (a cost cap, auth, or terminal failure); stopping. Log: "
                  f"{os.path.relpath(log.name, root)}")
            return 5
        state = workspace_state(root, own)
        unchanged = unchanged + 1 if output == last_output and state == last_state else 0
        last_output, last_state = output, state
        if unchanged >= stall_after:
            print(f"neither the check output nor the working tree changed for {unchanged} iterations; stopping as stalled")
            return 3
    print(f"iteration cap {limit} reached; goal not met")
    return 2


if __name__ == "__main__":
    sys.exit(main())
