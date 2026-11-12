#!/usr/bin/env python3
"""Outcome eval: one organic task, with deepmodebot installed and without, scored by hidden checks and blinded judges.

  python evals/outcome/run.py setup [--task billsplit] [--run-id ID] [--ref HEAD] [--compare-ref REF] [--per-variant 2]
  python evals/outcome/run.py run [--task billsplit] [--run-id ID] --model ID [--max-cost 3]
  python evals/outcome/run.py collect [--task billsplit] [--run-id ID]
  python evals/outcome/run.py judge [--task billsplit] [--run-id ID] --judge-model ID --judge-model ID
  python evals/outcome/run.py selftest [--task billsplit]

A task is a folder tasks/<task>/ holding project/ (what candidates get), prompt.txt (the request), rubric.md (judges
only), hidden/ (node:test files run against each final tree at collect time) and reference/ (files that solve it).
setup builds one project folder per candidate under .scratch/<task>-<n>/ and keeps the variant key in
.scratch/<task>-runs/. run starts every candidate at once as its own `omp -p` process. collect runs the hidden checks
on a copy of each result, measures it, and writes a judge pack under .scratch/<task>-review/ with candidates behind
shuffled letters. judge gives each judge model its own copy of the pack under .scratch/judge-<random>/pack and
reports both scores and their agreement. collect and judge mark a run contaminated when a tool call reaches outside
its own folder. selftest proves the hidden checks fail on the original project and pass on the reference.
"""
import argparse
import difflib
import io
import json
import os
import random
import re
import secrets
import shutil
import subprocess
import sys
import tarfile
import time
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
SCRATCH = ROOT / ".scratch"
sys.path.insert(0, str(ROOT / "plugins/deepmodebot/skills/deepmodebot/assets/pr-agent"))
import pr_agent_local
SKIP_DIRS = {".git", ".omp", ".scratch", ".worktrees", "node_modules"}
# Words in replies and action logs that would tell a judge which candidates had deepmodebot installed.
SCRUB = [(r"light[ -]?panel[ -]?", ""), (r"deep[ -]?mode", "the workflow"), (r"\bplaybook(s?)\b", r"checklist\1")]
CHECK_TIMEOUT = 600


def task_paths(name, run_id=None):
    for value in (name, run_id):
        if value is not None and not re.fullmatch(r"[a-z][a-z0-9-]*", value):
            raise ValueError("task and run-id must be lowercase project slugs")
    home = HERE / "tasks" / name
    if not (home / "project").is_dir():
        sys.exit(f"no task {name!r}: {home.relative_to(ROOT)}/project is missing")
    prefix = f"{name}-{run_id}" if run_id else name
    runs = SCRATCH / f"{prefix}-runs"
    return SimpleNamespace(name=name, prefix=prefix, home=home, project=home / "project", runs=runs,
                           key=runs / "key.json", pack=SCRATCH / f"{prefix}-review")


def git(*args, cwd):
    return subprocess.run(["git", "-c", "user.name=Sam Rivera", "-c", "user.email=sam@example.com", *args],
                          cwd=cwd, check=True, capture_output=True, text=True, encoding="utf-8").stdout.strip()


def child_env(folder):
    env = pr_agent_local.scrubbed_env()
    temp = Path(folder) / ".scratch/tmp"
    temp.mkdir(parents=True, exist_ok=True)
    env.update(TMP=str(temp), TEMP=str(temp), TMPDIR=str(temp))
    return env


def skill_snapshot(ref):
    sha = git("rev-parse", "--verify", f"{ref}^{{commit}}", cwd=ROOT)
    brand = json.loads(git("show", f"{sha}:brand/brand.json", cwd=ROOT))
    if any(not isinstance(brand.get(key), str) or not re.fullmatch(r"[a-z][a-z0-9-]*", brand[key])
           for key in ("slug", "commandName")):
        raise ValueError("snapshot brand must name a safe plugin and command")
    plugin = f"plugins/{brand['slug']}"
    archive = subprocess.run(["git", "archive", f"{sha}:{plugin}/skills"],
                             cwd=ROOT, check=True, capture_output=True).stdout
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        skills = sorted(m.name.split("/")[0] for m in tar.getmembers() if re.fullmatch(r"[^/]+/SKILL\.md", m.name))
    command = git("show", f"{sha}:{plugin}/commands/{brand['commandName']}.md", cwd=ROOT)
    return {"ref": sha, "archive": archive, "skills": skills,
            "body": re.sub(r"^---\n.*?\n---\n", "", command, flags=re.S).strip()}


def setup(args):
    t = task_paths(args.task, args.run_id)
    if args.per_variant < 1:
        raise ValueError("per-variant must be positive")
    if t.key.exists():
        sys.exit(f"{t.key.relative_to(ROOT)} exists; choose a new --run-id to preserve its evidence")
    snapshots = {"deepmodebot": skill_snapshot(args.ref)}
    if args.compare_ref:
        snapshots["previous"] = skill_snapshot(args.compare_ref)
    request = (t.home / "prompt.txt").read_text(encoding="utf-8").strip()
    package = json.loads((t.project / "package.json").read_text(encoding="utf-8"))
    variants = [variant for variant in [*snapshots, "plain"] for _ in range(args.per_variant)]
    random.Random(args.seed).shuffle(variants)
    key = {"task": t.name, "run_id": args.run_id, "seed": args.seed,
           "refs": {name: s["ref"] for name, s in snapshots.items()}, "candidates": {}}
    for number, variant in enumerate(variants, 1):
        folder = SCRATCH / f"{t.prefix}-{number}"
        if folder.exists():
            sys.exit(f"{folder} exists")
        shutil.copytree(t.project, folder)
        git("init", "-q", "-b", "main", cwd=folder)
        git("add", "-A", cwd=folder)
        git("commit", "-q", "-m", f"{package['name']} {package['version']}", cwd=folder)
        (folder / ".git/info/exclude").write_text(".omp/\n", encoding="utf-8")
        snapshot = snapshots.get(variant)
        if snapshot:
            target = folder / ".omp/skills"
            target.mkdir(parents=True)
            with tarfile.open(fileobj=io.BytesIO(snapshot["archive"])) as tar:
                tar.extractall(target, filter="data")
        prompt = snapshot["body"].replace("$ARGUMENTS", request) if snapshot else request
        run_dir = t.runs / str(number)
        run_dir.mkdir(parents=True)
        (run_dir / "prompt.txt").write_text(prompt + "\n", encoding="utf-8")
        key["candidates"][str(number)] = {"variant": variant, "folder": str(folder),
            "ref": snapshot["ref"] if snapshot else None, "skills": snapshot["skills"] if snapshot else [],
            "base": git("rev-parse", "HEAD", cwd=folder)}
        print(f"{folder.relative_to(ROOT)}  {variant}")
    t.key.write_text(json.dumps(key, indent=2) + "\n", encoding="utf-8")


def omp_command(omp, run_dir, args, model, extra):
    cmd = [omp, "-p", "--no-title", "--mode", "json", "--max-cost", str(args.max_cost), "--max-time", args.max_time,
           "--session-dir", str(run_dir / "sessions"), "--no-rules", "--no-context-files", "--no-extensions",
           "--no-prewalk", "--wait-async", "--config", str(run_dir / "runtime.yml"), *extra]
    return cmd + ["--model", model]


def runtime_config(run_dir, model):
    config = ("retry:\n  modelFallback: false\n  fallbackChains: {}\nprewalk:\n  enabled: false\n"
              "task:\n  perCallModel: false\n  agentModelOverrides:\n")
    config += "".join(f"    {agent}: {json.dumps(model)}\n"
                      for agent in ("task", "scout", "reviewer", "security-reviewer", "sonic"))
    (run_dir / "runtime.yml").write_text(config, encoding="utf-8")


def run_all(jobs):
    """Start every (name, cmd, cwd, run_dir) at once; return {name: (exit code, wall seconds)}."""
    procs = {}
    for name, cmd, cwd, run_dir in jobs:
        out = open(run_dir / "events.jsonl", "w", encoding="utf-8")
        err = open(run_dir / "stderr.txt", "w", encoding="utf-8")
        procs[name] = (subprocess.Popen(cmd, cwd=cwd, env=child_env(cwd), stdout=out, stderr=err), out, err, time.monotonic())
        print(f"started {name}")
    done = {}
    while len(done) < len(procs):
        for name, (proc, out, err, started) in procs.items():
            if name not in done and proc.poll() is not None:
                out.close()
                err.close()
                done[name] = (proc.returncode, round(time.monotonic() - started))
                print(f"finished {name} exit {proc.returncode} after {done[name][1]}s")
        time.sleep(2)
    return done


def run(args):
    t = task_paths(args.task, args.run_id)
    key = json.loads(t.key.read_text(encoding="utf-8"))
    if any((t.runs / number / "events.jsonl").exists() for number in key["candidates"]):
        sys.exit("candidate outputs already exist; choose a new --run-id instead of overwriting evidence")
    credentials = pr_agent_local.omp_oauth_credentials(args.model)
    key["runtime"] = {"omp": subprocess.run([shutil.which("omp") or "omp", "--version"],
                         capture_output=True, text=True, check=True).stdout.strip(),
                      "model": args.model, "max_cost": args.max_cost, "max_time": args.max_time,
                      "oauth_credential_ids": sorted(credentials)}
    t.key.write_text(json.dumps(key, indent=2) + "\n", encoding="utf-8")
    omp = shutil.which("omp") or sys.exit("omp is not on PATH")
    jobs = []
    for number, info in key["candidates"].items():
        run_dir = t.runs / number
        runtime_config(run_dir, args.model)
        skills = ["--skills", ",".join(info["skills"])] if info["skills"] else ["--no-skills"]
        cmd = omp_command(omp, run_dir, args, args.model, skills)
        jobs.append((number, cmd + [(run_dir / "prompt.txt").read_text(encoding="utf-8").strip()], info["folder"], run_dir))
        (run_dir / "command.json").write_text(json.dumps(jobs[-1][1], indent=2) + "\n", encoding="utf-8")
    for number, (code, seconds) in run_all(jobs).items():
        key["candidates"][number].update({"exit": code, "wall_seconds": seconds, "model": args.model,
                                        "max_cost": args.max_cost, "max_time": args.max_time})
    t.key.write_text(json.dumps(key, indent=2) + "\n", encoding="utf-8")


def read_events(path):
    reply, cost, models, calls = "", 0.0, set(), []
    if not path.exists():
        return reply, cost, [], calls
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        message = event.get("message") if event.get("type") in ("message_end", "message") else None
        if not message or message.get("role") != "assistant":
            continue
        models.add(f"{message.get('provider')}/{message.get('model')}")
        cost += float(message.get("usage", {}).get("cost", {}).get("total") or 0)
        text = "".join(p.get("text", "") for p in message.get("content", []) if p.get("type") == "text")
        if text.strip():
            reply = text
        for part in message.get("content", []):
            if part.get("type") in ("toolCall", "tool_use"):
                calls.append({"name": part.get("name"), "args": part.get("arguments") or part.get("input") or {}})
    return reply.strip(), round(cost, 4), sorted(models), calls


def read_run(run_dir):
    """The main session's reply plus cost, models and tool calls summed over it and every helper it started."""
    reply, cost, models, calls = read_events(run_dir / "events.jsonl")
    for helper in sorted((run_dir / "sessions").glob("*/*.jsonl")):
        _, helper_cost, helper_models, helper_calls = read_events(helper)
        cost = round(cost + helper_cost, 4)
        models = sorted(set(models) | set(helper_models))
        calls += [{**call, "helper": helper.stem} for call in helper_calls]
    return reply, cost, models, calls


def tree_files(folder):
    files = {}
    for path in sorted(folder.rglob("*")):
        rel = path.relative_to(folder)
        if path.is_file() and not SKIP_DIRS & set(rel.parts):
            files[rel.as_posix()] = path.read_text(encoding="utf-8", errors="replace")
    return files


def copy_deliverable(folder, target, supplied_skills):
    shutil.copytree(folder, target, ignore=shutil.ignore_patterns(*SKIP_DIRS))
    skills = folder / ".omp/skills"
    if skills.is_dir():
        for skill in skills.iterdir():
            if skill.is_dir() and not skill.is_symlink() and skill.name not in supplied_skills:
                shutil.copytree(skill, target / ".omp/skills" / skill.name,
                                ignore=shutil.ignore_patterns(*SKIP_DIRS))


def unified_diff(before, after):
    out = []
    for name in sorted(set(before) | set(after)):
        a, b = before.get(name, ""), after.get(name, "")
        if a != b:
            out += difflib.unified_diff(a.splitlines(True), b.splitlines(True), f"a/{name}", f"b/{name}")
    return "".join(line if line.endswith("\n") else line + "\n" for line in out)


def is_spec(name):
    return name.split("/")[0] in ("spec", "test", "tests") or ".spec." in name or ".test." in name


def node_tests(files, cwd):
    """Run node:test files with the TAP reporter; return the summary counts and each top-level result."""
    if not files:
        return {"exit": None, "pass": 0, "fail": 0, "results": []}
    try:
        proc = subprocess.run(["node", "--test", "--test-reporter=tap", *files], cwd=cwd, capture_output=True,
                              text=True, encoding="utf-8", errors="replace", timeout=CHECK_TIMEOUT)
    except subprocess.TimeoutExpired:
        return {"exit": "timeout", "pass": 0, "fail": 0, "results": []}
    counts = dict(re.findall(r"^# (pass|fail) (\d+)$", proc.stdout, re.M))
    results = [{"name": name, "ok": not bad} for bad, name in re.findall(r"^(not )?ok \d+ - (.*?)(?: # .*)?$", proc.stdout, re.M)]
    return {"exit": proc.returncode, "pass": int(counts.get("pass", 0)), "fail": int(counts.get("fail", 0)),
            "results": results}


def run_specs(folder):
    files = [name for name in tree_files(folder) if is_spec(name) and name.endswith((".js", ".mjs", ".cjs"))]
    result = node_tests(files, folder)
    return {key: result[key] for key in ("exit", "pass", "fail")}


def hidden_checks(t, folder, scored):
    """Copy the tree to scored/, add the task's hidden checks, and run them there."""
    if scored.exists():
        shutil.rmtree(scored)
    shutil.copytree(folder, scored, ignore=shutil.ignore_patterns(*SKIP_DIRS))
    shutil.copytree(t.home / "hidden", scored / ".acceptance")
    files = [f".acceptance/{p.name}" for p in sorted((scored / ".acceptance").iterdir())]
    result = node_tests(files, scored)
    return {"passed": sum(r["ok"] for r in result["results"]), "total": len(result["results"]), "exit": result["exit"],
            "failed": [r["name"] for r in result["results"] if not r["ok"]],
            "passing": [r["name"] for r in result["results"] if r["ok"]]}


# Tool-call arguments that name a path, and those that hold shell or code text to scan token by token.
PATH_FIELDS = ("path", "paths", "file", "files", "cwd", "dir", "directory", "output", "destination", "source", "target")
TEXT_FIELDS = ("command", "code")
INTERNAL_URL = re.compile(r"^[a-z][a-z0-9+.-]*://", re.I)
ENV_DIR = re.compile(r"^(?:\$\{?(?:HOME|TEMP|TMP|TMPDIR|USERPROFILE|APPDATA)\b|\$env:|%\w+%)", re.I)
DEVICES = {"/dev/null", "/dev/stdout", "/dev/stderr", "nul"}
# In shell text a leading slash is often a regex or a sed script; only these roots count as absolute paths there.
POSIX_ROOT = re.compile(r"^/(?:[a-z](?:/|$)|tmp|home|users|mnt|etc|var|usr|opt|root|private|proc)\b", re.I)
HEREDOC = re.compile(r"<<-?\s*(['\"]?)(\w+)\1")
SELECTOR = re.compile(r"(?<=[^:/\\])(?::(?:raw|conflicts|img|-?\d[\d,+\-]*))+$|\?.*$")


def escapes(token, cwd, folder, path_field=False):
    """True when token, read as a path from cwd, lands outside folder. `..` segments that climb out count."""
    token = token.strip().strip("'\"`").lstrip("!")
    if not token or INTERNAL_URL.match(token) or token.lower() in DEVICES:
        return False
    if ENV_DIR.match(token) or token.startswith("~"):
        return True
    if not path_field and token.startswith("/") and not POSIX_ROOT.match(token):
        return False
    if not path_field and not re.match(r"^[A-Za-z]:[\\/]|^/", token) and ".." not in re.split(r"[\\/]", token):
        # A plain relative word only leaves the folder when an earlier `cd` already did; count path-shaped ones.
        return bool(re.search(r"[\\/]", token)) and not is_inside(Path(cwd), folder)
    drive = re.match(r"^/([A-Za-z])(?:/|$)(.*)$", token)
    native = f"{drive.group(1)}:/{drive.group(2)}" if drive else token
    return not is_inside(Path(os.path.normpath(os.path.join(cwd, native))), folder)


def is_inside(path, folder):
    path, root = os.path.normcase(os.path.normpath(path)), os.path.normcase(os.path.normpath(folder))
    return path == root or path.startswith(root.rstrip(os.sep) + os.sep)


def split_words(text):
    return [w for w in re.split(r"[\s;&|()<>=,'\"`]+", text) if w]


def shell_words(text, shell=True):
    """(word, in_code) pairs of a command, without here-doc bodies that a redirect writes to a file.

    in_code marks words inside a quoted string that holds code (`node -e "import('../src/a.js')"`) rather than
    being one quoted argument (`cat "../a.txt"`). Relative paths in code resolve against whatever the code decides,
    so only its absolute, home and temp paths are judged.
    """
    lines, kept, skip_to = text.splitlines(), [], None
    for line in lines:
        if skip_to is not None:
            skip_to = None if line.strip() == skip_to else skip_to
            continue
        kept.append(line)
        doc = HEREDOC.search(line)
        if doc and re.search(r">(?!&)", HEREDOC.sub("", line)):
            skip_to = doc.group(2)
    text = "\n".join(kept)
    if not shell:
        return [(word, False) for word in split_words(text)]
    words, pos = [], 0
    for quoted in re.finditer(r"\"(?:\\.|[^\"\\])*\"|'[^']*'", text, re.S):
        words += [(word, False) for word in split_words(text[pos:quoted.start()])]
        inner = quoted.group(0)[1:-1]
        code = bool(re.search(r"[\s()'\";,]", inner.strip()))
        words += [(word, code) for word in split_words(inner)]
        pos = quoted.end()
    return words + [(word, False) for word in split_words(text[pos:])]


def is_relative(word):
    word = word.strip("'\"`")
    return not (re.match(r"^[A-Za-z]:[\\/]|^[/~]", word) or ENV_DIR.match(word))


def system_temp(command):
    """`mktemp` calls that land in the system temp folder: no -p/--tmpdir, no template with a folder, no TMPDIR set first."""
    hits = []
    for call in re.finditer(r"\bmktemp\b([^;&|)\n`]*)", command):
        options = call.group(1)
        if re.search(r"(?:^|\s)(?:-p|--tmpdir)(?:[\s=]|$)|(?:^|\s)[^\s-]\S*/", options):
            continue
        if re.search(r"\bTMPDIR=", command[:call.start()]):
            continue
        hits.append(f"mktemp{options.rstrip()} (system temp)")
    return hits


def outside_paths(calls, folder):
    """Every path in the tool calls that resolves outside folder, relative ones against the call's cwd."""
    folder = Path(folder)
    hits = []
    for call in calls:
        args = call["args"] if isinstance(call["args"], dict) else {}
        cwd = folder
        if isinstance(args.get("cwd"), str):
            cwd = Path(os.path.normpath(os.path.join(folder, args["cwd"])))
        found = []
        for field in PATH_FIELDS:
            values = args.get(field)
            for value in values if isinstance(values, list) else [values]:
                for part in str(value).split(";") if isinstance(value, str) else []:
                    if escapes(SELECTOR.sub("", part.strip()), folder, folder, path_field=True):
                        found.append(part.strip())
        if isinstance(args.get("input"), str):
            for target in re.findall(r"^\[(.+?)#[0-9A-Fa-f]{4}\]$|^MV\s+(.+)$", args["input"], re.M):
                path = target[0] or target[1]
                if escapes(path, folder, folder, path_field=True):
                    found.append(path)
        for field in TEXT_FIELDS:
            if not isinstance(args.get(field), str):
                continue
            here, words = cwd, shell_words(args[field], shell=field == "command")
            if field == "command":
                found += system_temp(args[field])
            i = 0
            while i < len(words):
                word, code = words[i]
                if not (code and is_relative(word)) and escapes(word, here, folder):
                    found.append(word)
                if word in ("cd", "pushd") and not code and i + 1 < len(words) and words[i + 1][0] != "-":
                    # Judge the target from where the cd starts, then move there; never judge it again from inside.
                    target = words[i + 1][0].strip("'\"")
                    if escapes(target, here, folder):
                        found.append(target)
                    drive = re.match(r"^/([A-Za-z])(?:/|$)(.*)$", target)
                    target = f"{drive.group(1)}:/{drive.group(2)}" if drive else target
                    here = Path(os.path.normpath(os.path.join(here, os.path.expanduser(target))))
                    i += 1
                i += 1
        hits += [f"{call.get('helper', 'main')} {call['name']}: {path}" for path in dict.fromkeys(found)]
    return hits


def sanitize(text, folder, name):
    for form in {str(folder), str(folder).replace("\\", "/"), str(folder).replace("\\", "\\\\")}:
        text = re.sub(re.escape(form), "<project>", text, flags=re.I)
    text = re.sub(rf"{re.escape(name)}-\d+", "<project>", text)
    for pattern, replacement in SCRUB:
        text = re.sub(pattern, replacement, text, flags=re.I)
    return text


def describe(call):
    args = call["args"]
    main = args.get("command") or args.get("path") or args.get("pattern") or args.get("input") or json.dumps(args)
    return f"{call['name']}: {str(main)[:400]}".replace("\n", " ")


def git_state(folder):
    """Work a user would not see in the checked-out tree: unmerged branches and extra worktrees."""
    try:
        branches = git("branch", "--format=%(refname:short)", "--no-merged", "HEAD", cwd=folder).split()
        worktrees = git("worktree", "list", "--porcelain", cwd=folder).count("worktree ") - 1
        return {"unmerged_branches": branches, "extra_worktrees": worktrees,
                "uncommitted": bool(git("status", "--porcelain", cwd=folder))}
    except subprocess.CalledProcessError as err:
        return {"error": err.stderr.strip()}


def collect(args):
    t = task_paths(args.task, args.run_id)
    key = json.loads(t.key.read_text(encoding="utf-8"))
    if t.pack.exists():
        shutil.rmtree(t.pack)
    base_files = tree_files(t.project)
    shutil.copytree(t.project, t.pack / "base")
    numbers = sorted(key["candidates"], key=int)
    labels = [chr(ord("A") + i) for i in range(len(numbers))]
    random.Random(key["seed"] + 1).shuffle(labels)
    measurements = {}
    for number, label in zip(numbers, labels):
        info = key["candidates"][number]
        folder = Path(info["folder"])
        run_dir = t.runs / number
        reply, cost, models, calls = read_run(run_dir)
        files = tree_files(folder)
        patch = unified_diff(base_files, files)
        changed = [name for name in sorted(set(base_files) | set(files)) if base_files.get(name) != files.get(name)]
        lines = sum(1 for line in patch.splitlines() if line[:1] in "+-" and line[:3] not in ("+++", "---"))
        # The candidate's own specs, run against the project as it was before the change.
        before = run_dir / "before"
        if before.exists():
            shutil.rmtree(before)
        shutil.copytree(t.project, before)
        for name in changed:
            if is_spec(name) and name in files:
                (before / name).parent.mkdir(parents=True, exist_ok=True)
                (before / name).write_text(files[name], encoding="utf-8")
        measurements[number] = {
            "label": label, "variant": info["variant"], "ref": info.get("ref"), "cost": cost,
            "models": models, "requested_model": info.get("model"), "exit": info.get("exit"),
            "wall_seconds": info.get("wall_seconds"), "tool_calls": len(calls),
            "process_finished": info.get("exit") == 0 and bool(reply), "files_changed": changed,
            "diff_lines": lines, "hidden": hidden_checks(t, folder, run_dir / "scored"),
            "specs_after": run_specs(folder), "specs_on_old_code": run_specs(before),
            "new_or_changed_specs": [name for name in changed if is_spec(name)], "git": git_state(folder),
            "outside_paths": outside_paths(calls, folder),
            "files_read": sorted({str(c["args"].get("path")) for c in calls if c["name"] == "read"}),
        }
        # Any path outside its own folder could reach the hidden checks, the reference, a sibling or the key.
        measurements[number]["contaminated"] = bool(measurements[number]["outside_paths"])
        target = t.pack / label
        copy_deliverable(folder, target / "repo", info.get("skills", []))
        (target / "reply.md").write_text(sanitize(reply, folder, t.name) + "\n", encoding="utf-8")
        (target / "diff.patch").write_text(patch, encoding="utf-8")
        actions = [("[helper] " if "helper" in c else "") + sanitize(describe(c), folder, t.name) for c in calls]
        actions = [a for a in actions if ".omp/skills" not in a and ".omp\\skills" not in a and "skill://" not in a]
        (target / "actions.txt").write_text("\n".join(actions) + "\n", encoding="utf-8")
    (t.runs / "measurements.json").write_text(json.dumps(measurements, indent=2) + "\n", encoding="utf-8")
    for number, m in measurements.items():
        h = m["hidden"]
        print(f"{number} {m['label']} {m['variant']:9} ${m['cost']:<7} hidden {h['passed']}/{h['total']}"
              f"  calls {m['tool_calls']}  wall {m['wall_seconds'] or '-'}s  specs after {m['specs_after']}"
              f"  on old code {m['specs_on_old_code']}  diff {m['diff_lines']} lines  outside {len(m['outside_paths'])}"
              + ("  CONTAMINATED" if m["contaminated"] else ""))
        for hit in m["outside_paths"]:
            print(f"    outside: {hit}")
    print(f"judge pack: {t.pack.relative_to(ROOT)}")


def criteria_count(rubric):
    return len(re.findall(r"^\d+\. \*\*", rubric, re.M))


def judge_prompt(t, letters, rubric):
    request = (t.home / "prompt.txt").read_text(encoding="utf-8").strip()
    count = criteria_count(rubric)
    example = json.dumps({letter: {"scores": [0] * count, "notes": "..."} for letter in letters[:2]})
    return f"""You are scoring finished work on a small software project.
Several developers each got their own copy of the same project and the same request from a user.
This folder holds base/, the project as they received it, and one lettered folder per developer: {", ".join(letters)}.

The user's request was:

<request>
{request}
</request>

Each lettered folder holds:
- repo/: the project as the developer left it
- diff.patch: their changes against base/
- reply.md: their final message to the user
- actions.txt: the tool calls they made, in order. Lines starting [helper] came from helpers they started.

All candidates and this judge run receive TEMP, TMP and TMPDIR pointing inside their own project.
Do not infer a system-temp escape from os.tmpdir(), tempfile or mktemp alone.
Supplied experiment skills are omitted; candidate-authored verification helpers remain so their tests can run.

Score every folder on every criterion of the rubric below.
Read the code and run it; Node is installed. Work only inside this folder.
Never read, list or write anything outside it. To try a project, copy its repo/ to a new folder here first.
Judge each folder on its own merits, on the same scale. Do not guess which tool or model produced it.

<rubric>
{rubric.strip()}
</rubric>

End your reply with one fenced json block and nothing after it.
It maps each letter to its {count} criterion scores, in rubric order, and one or two sentences of notes, like:

```json
{example}
```
"""


def parse_scores(reply, letters, count):
    """The last json block as {letter: scores, total, notes}, or (None, the reason it could not be read)."""
    blocks = re.findall(r"```json\s*(\{.*?\})\s*```", reply, re.S)
    if not blocks:
        return None, "no fenced json block in the reply"
    try:
        data = json.loads(blocks[-1])
    except ValueError as err:
        return None, f"json does not parse: {err}"
    if not isinstance(data, dict):
        return None, "json is not an object"
    scores = {}
    for letter in letters:
        entry = data.get(letter)
        row = entry.get("scores") if isinstance(entry, dict) else None
        if not isinstance(row, list) or len(row) != count:
            return None, f"{letter}: needs a list of {count} scores, got {row!r}"
        if not all(isinstance(s, (int, float)) and not isinstance(s, bool) and s in (0, 1, 2) for s in row):
            return None, f"{letter}: every score must be 0, 1 or 2, got {row!r}"
        row = [int(s) for s in row]
        scores[letter] = {"scores": row, "total": sum(row), "notes": str(entry.get("notes", ""))}
    return scores, None


def ranks(values):
    order = sorted(range(len(values)), key=lambda i: values[i])
    out = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        for k in range(i, j + 1):
            out[order[k]] = (i + j) / 2 + 1
        i = j + 1
    return out


def spearman(a, b):
    ra, rb = ranks(a), ranks(b)
    mean_a, mean_b = sum(ra) / len(ra), sum(rb) / len(rb)
    cov = sum((x - mean_a) * (y - mean_b) for x, y in zip(ra, rb))
    spread = (sum((x - mean_a) ** 2 for x in ra) * sum((y - mean_b) ** 2 for y in rb)) ** 0.5
    return round(cov / spread, 3) if spread else None


def agreement(first, second, letters):
    cells = [(x, y) for letter in letters for x, y in zip(first[letter]["scores"], second[letter]["scores"])]
    totals_a = [first[letter]["total"] for letter in letters]
    totals_b = [second[letter]["total"] for letter in letters]
    return {"exact_cells": round(sum(x == y for x, y in cells) / len(cells), 3),
            "within_one_cells": round(sum(abs(x - y) <= 1 for x, y in cells) / len(cells), 3),
            "mean_abs_total_diff": round(sum(abs(x - y) for x, y in zip(totals_a, totals_b)) / len(letters), 2),
            "spearman_totals": spearman(totals_a, totals_b)}


def judge(args):
    t = task_paths(args.task, args.run_id)
    rubric = (t.home / "rubric.md").read_text(encoding="utf-8")
    letters = sorted(p.name for p in t.pack.iterdir() if p.is_dir() and p.name != "base")
    if not args.reparse and not args.dry_run and any(
            (t.runs / f"judge-{index}").exists() for index in (1, 2)):
        sys.exit("judge evidence already exists; use --reparse or choose a new --run-id")
    if not args.reparse:
        prompt = judge_prompt(t, letters, rubric)
        (t.runs / "judge-prompt.txt").write_text(prompt, encoding="utf-8")
        if args.dry_run:
            print(prompt)
            return
        if not args.judge_model or len(args.judge_model) != 2 or len(set(args.judge_model)) != 2:
            sys.exit("choose two distinct --judge-model IDs; no default model or billing route is assumed")
        (t.runs / "judge-models.json").write_text(json.dumps(args.judge_model), encoding="utf-8")
        start_judges(t, args, prompt)
    count = criteria_count(rubric)
    models = json.loads((t.runs / "judge-models.json").read_text(encoding="utf-8"))
    verdicts = {}
    for index, model in enumerate(models, 1):
        run_dir = t.runs / f"judge-{index}"
        meta = json.loads((run_dir / "meta.json").read_text(encoding="utf-8"))
        reply, cost, models, calls = read_run(run_dir)
        saved = run_dir / "reply.md"
        if args.reparse and saved.exists():
            reply = saved.read_text(encoding="utf-8").strip()
        else:
            saved.write_text(reply + "\n", encoding="utf-8")
        scores, error = parse_scores(reply, letters, count)
        hits = outside_paths(calls, Path(meta["pack"]))
        verdicts[model] = {"cost": cost, "models": models, "exit": meta.get("exit"), "pack": meta["pack"],
                           "scores": scores, "parse_error": error, "outside_paths": hits, "contaminated": bool(hits)}
    result = {"letters": letters, "judges": verdicts}
    first, second = (v["scores"] for v in verdicts.values())
    if first and second:
        result["agreement"] = agreement(first, second, letters)
    (t.runs / "judges.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    report(t, result)


def start_judges(t, args, prompt):
    """Run every judge at once, each in its own copy of the pack under a random folder with no run data beside it."""
    omp = shutil.which("omp") or sys.exit("omp is not on PATH")
    jobs = []
    for index, model in enumerate(args.judge_model, 1):
        pr_agent_local.omp_oauth_credentials(model)
        run_dir = t.runs / f"judge-{index}"
        if run_dir.exists():
            sys.exit("judge evidence already exists; choose a new --run-id")
        run_dir.mkdir(parents=True)
        pack = SCRATCH / f"judge-{secrets.token_hex(4)}" / "pack"
        shutil.copytree(t.pack, pack)
        (run_dir / "meta.json").write_text(json.dumps({"model": model, "pack": str(pack)}, indent=2) + "\n", encoding="utf-8")
        runtime_config(run_dir, model)
        jobs.append((index, omp_command(omp, run_dir, args, model, ["--no-skills"]) + [prompt], pack, run_dir))
    for index, (code, seconds) in run_all(jobs).items():
        meta_path = t.runs / f"judge-{index}" / "meta.json"
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        meta.update({"exit": code, "wall_seconds": seconds})
        meta_path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")


def report(t, result):
    measurements = json.loads((t.runs / "measurements.json").read_text(encoding="utf-8"))
    by_label = {m["label"]: m for m in measurements.values()}
    for model, verdict in result["judges"].items():
        print(f"{model}: ${verdict['cost']}  scores {'parsed' if verdict['scores'] else 'MISSING'}"
              f"  outside {len(verdict['outside_paths'])}" + ("  CONTAMINATED" if verdict["contaminated"] else ""))
        if verdict["parse_error"]:
            print(f"    parse error: {verdict['parse_error']} (fix the reply.md, then judge --reparse)")
        for hit in verdict["outside_paths"]:
            print(f"    outside: {hit}")
    print("letter variant   hidden  cost     calls  wall   " + "  ".join(result["judges"]))
    for letter in result["letters"]:
        m = by_label[letter]
        totals = [str(v["scores"][letter]["total"]) if v["scores"] else "-" for v in result["judges"].values()]
        print(f"{letter}      {m['variant']:9} {m['hidden']['passed']:>2}/{m['hidden']['total']:<3} ${m['cost']:<7}"
              f" {m['tool_calls']:>5}  {m['wall_seconds'] or '-'}s  " + "  ".join(totals)
              + ("  CONTAMINATED" if m.get("contaminated") else ""))
    if "agreement" in result:
        print(f"agreement: {result['agreement']}")


def selftest(args):
    t = task_paths(args.task, args.run_id)
    if not (t.home / "reference").is_dir():
        sys.exit(f"{t.home.relative_to(ROOT)}/reference is missing")
    work = SCRATCH / f"{t.prefix}-selftest"
    if work.exists():
        shutil.rmtree(work)
    original, reference = work / "original", work / "reference"
    shutil.copytree(t.project, original)
    shutil.copytree(t.project, reference)
    shutil.copytree(t.home / "reference", reference, dirs_exist_ok=True)
    on_original = hidden_checks(t, original, work / "scored-original")
    on_reference = hidden_checks(t, reference, work / "scored-reference")
    specs = {"original": run_specs(original), "reference": run_specs(reference)}
    print(f"original:  hidden {on_original['passed']}/{on_original['total']}  specs {specs['original']}")
    print(f"reference: hidden {on_reference['passed']}/{on_reference['total']}  specs {specs['reference']}")
    for name in on_reference["failed"]:
        print(f"  reference fails: {name}")
    problems = []
    if on_original["total"] == 0 or on_original["passed"] == on_original["total"]:
        problems.append("the hidden checks do not fail on the original project")
    if on_reference["total"] == 0 or on_reference["failed"] or on_reference["total"] != on_original["total"]:
        problems.append("the hidden checks do not all pass on the reference")
    if specs["original"]["fail"] or specs["reference"]["fail"]:
        problems.append("the project's own specs fail")
    shutil.rmtree(work)
    if problems:
        sys.exit("selftest failed: " + "; ".join(problems))
    print("selftest OK" + "".join(f"\n  original already passes: {n}" for n in on_original["passing"]))


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="step", required=True)
    steps = {}
    for step, func in (("setup", setup), ("run", run), ("collect", collect), ("judge", judge), ("selftest", selftest)):
        steps[step] = func
        p = sub.add_parser(step)
        p.add_argument("--task", default="billsplit", help="folder under evals/outcome/tasks/")
        p.add_argument("--run-id", help="unique project slug; keeps earlier runs and their evidence untouched")
        if step == "setup":
            p.add_argument("--ref", default="HEAD", help="commit whose deepmodebot skill and /deep command are installed")
            p.add_argument("--compare-ref", help="also run the previous skill revision beside the new revision and plain")
            p.add_argument("--per-variant", type=int, default=2)
            p.add_argument("--seed", type=int, default=7)
        if step in ("run", "judge"):
            p.add_argument("--max-cost", type=float, default=3.0, help="omp --max-cost per process, in USD")
            p.add_argument("--max-time", default="45m")
        if step == "run":
            p.add_argument("--model", required=True, help="explicit omp model ID for every candidate")
        if step == "judge":
            p.add_argument("--judge-model", action="append", help="two distinct explicit model IDs; repeat this option")
            p.add_argument("--dry-run", action="store_true", help="write and print the judge prompt; call no model")
            p.add_argument("--reparse", action="store_true", help="re-read the saved judge replies; call no model")
    args = parser.parse_args()
    steps[args.step](args)


if __name__ == "__main__":
    main()
