#!/usr/bin/env python3
"""Outcome eval: one organic task, with deep-mode installed and without, scored by hidden checks and blinded judges.

  python evals/outcome/run.py setup [--task billsplit] [--ref HEAD] [--per-variant 2] [--seed N]
  python evals/outcome/run.py run [--task billsplit] [--max-cost 3] [--model ID]
  python evals/outcome/run.py collect [--task billsplit]
  python evals/outcome/run.py judge [--task billsplit] [--max-cost 3] [--dry-run]
  python evals/outcome/run.py selftest [--task billsplit]

A task is a folder tasks/<task>/ holding project/ (what candidates get), prompt.txt (the request), rubric.md (judges
only), hidden/ (node:test files run against each final tree at collect time) and reference/ (files that solve it).
setup builds one project folder per candidate under .scratch/<task>-<n>/ and keeps the variant key in
.scratch/<task>-runs/. run starts every candidate at once as its own `omp -p` process. collect runs the hidden checks
on a copy of each result, measures it, and writes a judge pack under .scratch/<task>-review/ with candidates behind
shuffled letters. judge gives each judge model its own copy of the pack and reports both scores and their agreement.
selftest proves the hidden checks fail on the original project and pass on the reference.
"""
import argparse
import difflib
import io
import json
import os
import random
import re
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
API_KEYS = ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "CODEX_API_KEY")
SKIP_DIRS = {".git", ".omp", ".scratch", ".worktrees", "node_modules"}
JUDGES = ("anthropic/claude-opus-5-5", "openai-codex/gpt-6.1-terra")
# Words in replies and action logs that would tell a judge which candidates had deep-mode installed.
SCRUB = [(r"light[ -]?panel[ -]?", ""), (r"deep[ -]?mode", "the workflow"), (r"\bplaybook(s?)\b", r"checklist\1")]
CHECK_TIMEOUT = 600


def task_paths(name):
    home = HERE / "tasks" / name
    if not (home / "project").is_dir():
        sys.exit(f"no task {name!r}: {home.relative_to(ROOT)}/project is missing")
    runs = SCRATCH / f"{name}-runs"
    return SimpleNamespace(name=name, home=home, project=home / "project", runs=runs, key=runs / "key.json",
                           pack=SCRATCH / f"{name}-review")


def git(*args, cwd):
    return subprocess.run(["git", "-c", "user.name=Sam Rivera", "-c", "user.email=sam@example.com", *args],
                          cwd=cwd, check=True, capture_output=True, text=True, encoding="utf-8").stdout.strip()


def child_env():
    return {name: value for name, value in os.environ.items() if name not in API_KEYS}


def setup(args):
    t = task_paths(args.task)
    if t.key.exists():
        sys.exit(f"{t.key.relative_to(ROOT)} exists; remove .scratch/{t.name}-* first for a fresh run")
    ref_sha = git("rev-parse", args.ref, cwd=ROOT)
    skill_tar = subprocess.run(["git", "archive", f"{ref_sha}:plugins/deep-mode/skills/deep-mode"],
                               cwd=ROOT, check=True, capture_output=True).stdout
    command = git("show", f"{ref_sha}:plugins/deep-mode/commands/deep.md", cwd=ROOT)
    body = re.sub(r"^---\n.*?\n---\n", "", command, flags=re.S).strip()
    request = (t.home / "prompt.txt").read_text(encoding="utf-8").strip()
    package = json.loads((t.project / "package.json").read_text(encoding="utf-8"))
    variants = ["deep-mode"] * args.per_variant + ["plain"] * args.per_variant
    random.Random(args.seed).shuffle(variants)
    key = {"task": t.name, "ref": ref_sha, "seed": args.seed, "candidates": {}}
    for number, variant in enumerate(variants, 1):
        folder = SCRATCH / f"{t.name}-{number}"
        if folder.exists():
            sys.exit(f"{folder} exists")
        shutil.copytree(t.project, folder)
        git("init", "-q", "-b", "main", cwd=folder)
        git("add", "-A", cwd=folder)
        git("commit", "-q", "-m", f"{package['name']} {package['version']}", cwd=folder)
        (folder / ".git/info/exclude").write_text(".omp/\n", encoding="utf-8")
        if variant == "deep-mode":
            target = folder / ".omp/skills/deep-mode"
            target.mkdir(parents=True)
            with tarfile.open(fileobj=io.BytesIO(skill_tar)) as tar:
                tar.extractall(target, filter="data")
        prompt = body.replace("$ARGUMENTS", request) if variant == "deep-mode" else request
        run_dir = t.runs / str(number)
        run_dir.mkdir(parents=True)
        (run_dir / "prompt.txt").write_text(prompt + "\n", encoding="utf-8")
        key["candidates"][str(number)] = {"variant": variant, "folder": str(folder),
                                          "base": git("rev-parse", "HEAD", cwd=folder)}
        print(f"{folder.relative_to(ROOT)}  {variant}")
    t.key.write_text(json.dumps(key, indent=2) + "\n", encoding="utf-8")


def omp_command(omp, run_dir, args, model, extra):
    cmd = [omp, "-p", "--no-title", "--mode", "json", "--max-cost", str(args.max_cost), "--max-time", args.max_time,
           "--session-dir", str(run_dir / "sessions"), "--no-rules", "--no-context-files", "--no-extensions", *extra]
    return cmd + (["--model", model] if model else [])


def run_all(jobs):
    """Start every (name, cmd, cwd, run_dir) at once; return {name: (exit code, wall seconds)}."""
    procs = {}
    for name, cmd, cwd, run_dir in jobs:
        out = open(run_dir / "events.jsonl", "w", encoding="utf-8")
        err = open(run_dir / "stderr.txt", "w", encoding="utf-8")
        procs[name] = (subprocess.Popen(cmd, cwd=cwd, env=child_env(), stdout=out, stderr=err), out, err, time.monotonic())
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
    t = task_paths(args.task)
    key = json.loads(t.key.read_text(encoding="utf-8"))
    omp = shutil.which("omp") or sys.exit("omp is not on PATH")
    jobs = []
    for number, info in key["candidates"].items():
        run_dir = t.runs / number
        skills = ["--skills", "deep-mode"] if info["variant"] == "deep-mode" else ["--no-skills"]
        cmd = omp_command(omp, run_dir, args, args.model, skills)
        jobs.append((number, cmd + [(run_dir / "prompt.txt").read_text(encoding="utf-8").strip()], info["folder"], run_dir))
    for number, (code, seconds) in run_all(jobs).items():
        key["candidates"][number].update({"exit": code, "wall_seconds": seconds, "model": args.model or "default"})
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


def outside_paths(calls, folder):
    inside = {str(folder).lower().replace("\\", "/"), str(folder).lower()}
    pattern = re.compile(r"(?:(?<![A-Za-z])[A-Za-z]:[\\/]|(?<![\w.])/tmp\b|\$TMPDIR|%TEMP%|\$TEMP|~/|/c/Users)[^\s'\"`]*")
    hits = []
    for call in calls:
        blob = json.dumps(call["args"]) if call["name"] not in ("bash",) else str(call["args"].get("command", ""))
        blob = blob.replace("\\\\", "\\")
        for match in pattern.findall(blob):
            if not any(match.lower().replace("\\", "/").startswith(p.replace("\\", "/")) for p in inside):
                hits.append(f"{call.get('helper', 'main')} {call['name']}: {match}")
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
    t = task_paths(args.task)
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
            "label": label, "variant": info["variant"], "cost": cost, "models": models, "exit": info.get("exit"),
            "wall_seconds": info.get("wall_seconds"), "tool_calls": len(calls), "files_changed": changed,
            "diff_lines": lines, "hidden": hidden_checks(t, folder, run_dir / "scored"),
            "specs_after": run_specs(folder), "specs_on_old_code": run_specs(before),
            "new_or_changed_specs": [name for name in changed if is_spec(name)], "git": git_state(folder),
            "outside_paths": outside_paths(calls, folder),
            "files_read": sorted({str(c["args"].get("path")) for c in calls if c["name"] == "read"}),
        }
        target = t.pack / label
        shutil.copytree(folder, target / "repo", ignore=shutil.ignore_patterns(*SKIP_DIRS))
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
              f"  on old code {m['specs_on_old_code']}  diff {m['diff_lines']} lines  outside {len(m['outside_paths'])}")
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
    blocks = re.findall(r"```json\s*(\{.*?\})\s*```", reply, re.S)
    if not blocks:
        return None
    data = json.loads(blocks[-1])
    scores = {}
    for letter in letters:
        row = data.get(letter, {}).get("scores")
        if not isinstance(row, list) or len(row) != count:
            return None
        scores[letter] = {"scores": [int(s) for s in row], "total": sum(int(s) for s in row),
                          "notes": data[letter].get("notes", "")}
    return scores


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
    t = task_paths(args.task)
    rubric = (t.home / "rubric.md").read_text(encoding="utf-8")
    letters = sorted(p.name for p in t.pack.iterdir() if p.is_dir() and p.name != "base")
    prompt = judge_prompt(t, letters, rubric)
    (t.runs / "judge-prompt.txt").write_text(prompt, encoding="utf-8")
    if args.dry_run:
        print(prompt)
        return
    omp = shutil.which("omp") or sys.exit("omp is not on PATH")
    jobs, packs = [], {}
    for index, model in enumerate(JUDGES, 1):
        # Each judge gets its own copy, so one judge's trial runs never show up in the other's folders.
        pack = SCRATCH / f"{t.name}-review-{index}"
        if pack.exists():
            shutil.rmtree(pack)
        shutil.copytree(t.pack, pack)
        run_dir = t.runs / f"judge-{index}"
        if run_dir.exists():
            shutil.rmtree(run_dir)
        run_dir.mkdir(parents=True)
        packs[model] = (pack, run_dir)
        jobs.append((model, omp_command(omp, run_dir, args, model, ["--no-skills"]) + [prompt], pack, run_dir))
    run_all(jobs)
    count = criteria_count(rubric)
    verdicts = {}
    for model, (pack, run_dir) in packs.items():
        reply, cost, models, calls = read_run(run_dir)
        (run_dir / "reply.md").write_text(reply + "\n", encoding="utf-8")
        verdicts[model] = {"cost": cost, "models": models, "scores": parse_scores(reply, letters, count),
                           "outside_paths": outside_paths(calls, pack)}
    result = {"letters": letters, "judges": verdicts}
    first, second = (verdicts[m]["scores"] for m in JUDGES)
    if first and second:
        result["agreement"] = agreement(first, second, letters)
    (t.runs / "judges.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    report(t, result)


def report(t, result):
    measurements = json.loads((t.runs / "measurements.json").read_text(encoding="utf-8"))
    by_label = {m["label"]: m for m in measurements.values()}
    for model, verdict in result["judges"].items():
        print(f"{model}: ${verdict['cost']}  scores {'parsed' if verdict['scores'] else 'MISSING'}"
              f"  outside {len(verdict['outside_paths'])}")
    print("letter variant   hidden  cost     calls  wall   " + "  ".join(m.split("/")[1] for m in JUDGES))
    for letter in result["letters"]:
        m = by_label[letter]
        totals = [str(v["scores"][letter]["total"]) if v["scores"] else "-" for v in result["judges"].values()]
        print(f"{letter}      {m['variant']:9} {m['hidden']['passed']:>2}/{m['hidden']['total']:<3} ${m['cost']:<7}"
              f" {m['tool_calls']:>5}  {m['wall_seconds'] or '-'}s  " + "  ".join(totals))
    if "agreement" in result:
        print(f"agreement: {result['agreement']}")


def selftest(args):
    t = task_paths(args.task)
    if not (t.home / "reference").is_dir():
        sys.exit(f"{t.home.relative_to(ROOT)}/reference is missing")
    work = SCRATCH / f"{t.name}-selftest"
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
        if step == "setup":
            p.add_argument("--ref", default="HEAD", help="commit whose deep-mode skill and /deep command are installed")
            p.add_argument("--per-variant", type=int, default=2)
            p.add_argument("--seed", type=int, default=7)
        if step in ("run", "judge"):
            p.add_argument("--max-cost", type=float, default=3.0, help="omp --max-cost per process, in USD")
            p.add_argument("--max-time", default="45m")
        if step == "run":
            p.add_argument("--model", help="omp --model for every candidate (default: omp's default model)")
        if step == "judge":
            p.add_argument("--dry-run", action="store_true", help="write and print the judge prompt; call no model")
    args = parser.parse_args()
    steps[args.step](args)


if __name__ == "__main__":
    main()
