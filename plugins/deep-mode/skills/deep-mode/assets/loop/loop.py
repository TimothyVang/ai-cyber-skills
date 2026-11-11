#!/usr/bin/env python3
"""Drive an agent toward a goal file until its check passes (deep-mode "Self-authoring" playbook).

    python loop.py check <goal.md>                      validate the goal file, run its check once
    python loop.py run <goal.md> [--harness omp|claude|codex] [--max-iterations N] [--dry-run]

A goal file is Markdown with frontmatter (one `key: value` per line):
    goal: one-line objective
    check: shell command; exit 0 means done
    harness: omp | claude | codex            (default omp)
    max_iterations: 10                       (hard cap, required)
    max_cost_usd: 2                          (per iteration; omp --max-cost, claude --max-budget-usd; codex has none)
    stall_after: 3                           (stop after N iterations whose check output did not change)
    harness_args: --model sonnet             (extra flags for the harness, split like a shell)

Each iteration runs the harness headless in the project root on the user's subscription (API-key variables are
removed from the child's environment), then runs the check. Logs go to <root>/.scratch/goals/<slug>/: trail.tsv plus
one iteration-N.log per run. Exit codes: 0 done, 2 iteration cap, 3 stalled, 4 the agent changed the goal's
frontmatter, 1 error.
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
REQUIRED = ("goal", "check", "max_iterations")
PROMPT = (
    "Work toward the goal in {goal_file}. Read it first, then the trail of earlier iterations in {trail} if it exists. "
    "Do the next smallest verifiable step toward the goal, run its check (`{check}`), and commit progress you would keep. "
    "Stop after that one step. Never edit the goal file's frontmatter (goal, check, limits): if the goal itself is wrong, "
    "say so and stop. This is iteration {i} of at most {n}."
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
    return fields, hashlib.sha256(match.group(1).encode()).hexdigest()


def project_root(path):
    out = subprocess.run(["git", "-C", os.path.dirname(os.path.abspath(path)), "rev-parse", "--show-toplevel"],
                         capture_output=True, text=True)
    if out.returncode:
        raise SystemExit("the goal file must live inside a git repo (deep-mode: Contain the work)")
    return os.path.normpath(out.stdout.strip())


def find_bash():
    """Checks are written for bash. On Windows, prefer Git Bash: System32\\bash.exe is WSL and sees other paths."""
    bash = shutil.which("bash")
    if os.name != "nt" or (bash and "system32" not in bash.lower()):
        return bash
    git = shutil.which("git")
    for rel in ("../bin/bash.exe", "../usr/bin/bash.exe", "../../bin/bash.exe"):
        candidate = os.path.normpath(os.path.join(os.path.dirname(git), rel)) if git else ""
        if candidate and os.path.exists(candidate):
            return candidate
    return None


def run_check(command, root):
    bash = find_bash()
    argv = [bash, "-c", command] if bash else command
    proc = subprocess.run(argv, shell=not bash, cwd=root, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return proc.returncode, (proc.stdout + proc.stderr)[-4000:]


def harness_command(fields, harness, prompt):
    extra = shlex.split(fields.get("harness_args", ""))
    cost = fields.get("max_cost_usd")
    if harness == "omp":
        cmd = ["omp", "-p", "--no-title", *(["--max-cost", cost] if cost else []), *extra, prompt]
    elif harness == "claude":
        cmd = ["claude", "-p", "--permission-mode", "acceptEdits", *(["--max-budget-usd", cost] if cost else []), *extra, prompt]
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
    parser.add_argument("--dry-run", action="store_true", help="print the harness command instead of running it")
    opts = parser.parse_args()

    fields, digest = parse(opts.goal)
    root = project_root(opts.goal)
    goal_rel = os.path.relpath(os.path.abspath(opts.goal), root).replace(os.sep, "/")
    code, output = run_check(fields["check"], root)
    if opts.action == "check":
        print(f"goal ok: {fields['goal']}\ncheck exit {code}{' (already done)' if code == 0 else ''}\n{output.strip()}")
        return 0
    if code == 0:
        print("check already passes; nothing to do")
        return 0

    harness = opts.harness or fields.get("harness", "omp")
    limit = min(opts.max_iterations or 10**9, int(fields["max_iterations"]))
    stall_after = int(fields.get("stall_after", "3"))
    slug = re.sub(r"[^A-Za-z0-9_-]+", "-", os.path.splitext(os.path.basename(opts.goal))[0]).strip("-") or "goal"
    log_dir = os.path.join(root, ".scratch", "goals", slug)
    os.makedirs(os.path.join(root, ".scratch", "tmp"), exist_ok=True)
    os.makedirs(log_dir, exist_ok=True)
    ignore = os.path.join(root, ".scratch", ".gitignore")
    if not os.path.exists(ignore):
        with open(ignore, "w") as handle:
            handle.write("*\n")
    trail = os.path.join(log_dir, "trail.tsv")
    if not os.path.exists(trail):
        with open(trail, "w", encoding="utf-8") as handle:
            handle.write("ts\titeration\tharness\tharness_exit\tcheck_exit\tseconds\n")
    env = {k: v for k, v in os.environ.items() if k not in API_KEY_VARS}
    tmp = os.path.join(root, ".scratch", "tmp")
    env.update(TMPDIR=tmp, TMP=tmp, TEMP=tmp)

    last_output, unchanged = output, 0
    for i in range(1, limit + 1):
        prompt = PROMPT.format(goal_file=goal_rel, trail=os.path.relpath(trail, root).replace(os.sep, "/"),
                               check=fields["check"], i=i, n=limit)
        cmd = harness_command(fields, harness, prompt)
        if opts.dry_run:
            print(" ".join(shlex.quote(part) for part in cmd))
            return 0
        started = time.time()
        with open(os.path.join(log_dir, f"iteration-{i}.log"), "w", encoding="utf-8", errors="replace") as log:
            harness_exit = subprocess.run(cmd, cwd=root, env=env, stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL).returncode
        if parse(opts.goal)[1] != digest:
            print(f"iteration {i}: the agent changed the goal's frontmatter; stopping")
            return 4
        code, output = run_check(fields["check"], root)
        with open(trail, "a", encoding="utf-8") as handle:
            handle.write(f"{time.strftime('%Y-%m-%dT%H:%M:%S')}\t{i}\t{harness}\t{harness_exit}\t{code}\t{time.time() - started:.0f}\n")
        print(f"iteration {i}: harness exit {harness_exit}, check exit {code}")
        if code == 0:
            print("goal met")
            return 0
        unchanged = unchanged + 1 if output == last_output else 0
        last_output = output
        if unchanged >= stall_after:
            print(f"check output unchanged for {unchanged} iterations; stopping as stalled")
            return 3
    print(f"iteration cap {limit} reached; goal not met")
    return 2


if __name__ == "__main__":
    sys.exit(main())
