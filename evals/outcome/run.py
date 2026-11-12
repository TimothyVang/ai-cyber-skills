#!/usr/bin/env python3
"""Outcome eval: the same organic bug report, with deep-mode installed and without, scored by a blinded judge.

  python evals/outcome/run.py setup [--ref HEAD] [--per-variant 2] [--seed N]
  python evals/outcome/run.py run [--max-cost 3] [--model ID]
  python evals/outcome/run.py collect

setup builds one project folder per candidate under .scratch/billsplit-<n>/ and keeps the variant key in
.scratch/billsplit-runs/. run starts every candidate at once as its own `omp -p` process. collect measures each
result and writes a judge pack under .scratch/billsplit-review/ with candidates behind shuffled letters.
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
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
TEMPLATE = HERE / "project"
SCRATCH = ROOT / ".scratch"
NAME = "billsplit"
RUNS = SCRATCH / f"{NAME}-runs"
PACK = SCRATCH / f"{NAME}-review"
KEY = RUNS / "key.json"
API_KEYS = ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "CODEX_API_KEY")
SKIP_DIRS = {".git", ".omp", ".scratch", ".worktrees", "node_modules"}
# (amount, people, tip): every share list must add up to the total, each share within one cent of the others.
SPLITS = [("100", 3, 0), ("200", 3, 0), ("0.10", 3, 0), ("1", 7, 0), ("75", 3, 20), ("84.50", 3, 18),
          ("$1,250.00", 4, 0), ("10", 1, 0), ("90", 3, 0)]


def git(*args, cwd):
    return subprocess.run(["git", "-c", "user.name=Sam Rivera", "-c", "user.email=sam@example.com", *args],
                          cwd=cwd, check=True, capture_output=True, text=True, encoding="utf-8").stdout.strip()


def candidate_dir(number):
    return SCRATCH / f"{NAME}-{number}"


def setup(args):
    if KEY.exists():
        sys.exit(f"{KEY.relative_to(ROOT)} exists; remove .scratch/{NAME}-* first for a fresh run")
    ref_sha = git("rev-parse", args.ref, cwd=ROOT)
    skill_tar = subprocess.run(["git", "archive", f"{ref_sha}:plugins/deep-mode/skills/deep-mode"],
                               cwd=ROOT, check=True, capture_output=True).stdout
    command = git("show", f"{ref_sha}:plugins/deep-mode/commands/deep.md", cwd=ROOT)
    body = re.sub(r"^---\n.*?\n---\n", "", command, flags=re.S).strip()
    request = (HERE / "prompt.txt").read_text(encoding="utf-8").strip()
    variants = ["deep-mode"] * args.per_variant + ["plain"] * args.per_variant
    random.Random(args.seed).shuffle(variants)
    key = {"ref": ref_sha, "seed": args.seed, "candidates": {}}
    for number, variant in enumerate(variants, 1):
        folder = candidate_dir(number)
        if folder.exists():
            sys.exit(f"{folder} exists")
        shutil.copytree(TEMPLATE, folder)
        git("init", "-q", "-b", "main", cwd=folder)
        git("add", "-A", cwd=folder)
        git("commit", "-q", "-m", "billsplit 0.3.1", cwd=folder)
        (folder / ".git/info/exclude").write_text(".omp/\n", encoding="utf-8")
        if variant == "deep-mode":
            target = folder / ".omp/skills/deep-mode"
            target.mkdir(parents=True)
            with tarfile.open(fileobj=io.BytesIO(skill_tar)) as tar:
                tar.extractall(target, filter="data")
        prompt = body.replace("$ARGUMENTS", request) if variant == "deep-mode" else request
        run_dir = RUNS / str(number)
        run_dir.mkdir(parents=True)
        (run_dir / "prompt.txt").write_text(prompt + "\n", encoding="utf-8")
        key["candidates"][str(number)] = {"variant": variant, "folder": str(folder),
                                          "base": git("rev-parse", "HEAD", cwd=folder)}
        print(f"{folder.relative_to(ROOT)}  {variant}")
    KEY.write_text(json.dumps(key, indent=2) + "\n", encoding="utf-8")


def run(args):
    key = json.loads(KEY.read_text(encoding="utf-8"))
    omp = shutil.which("omp") or sys.exit("omp is not on PATH")
    env = {name: value for name, value in os.environ.items() if name not in API_KEYS}
    procs = []
    for number, info in key["candidates"].items():
        run_dir = RUNS / number
        cmd = [omp, "-p", "--no-title", "--mode", "json", "--max-cost", str(args.max_cost), "--max-time", args.max_time,
               "--session-dir", str(run_dir / "sessions"), "--no-rules", "--no-context-files", "--no-extensions"]
        cmd += ["--skills", "deep-mode"] if info["variant"] == "deep-mode" else ["--no-skills"]
        if args.model:
            cmd += ["--model", args.model]
        cmd.append((run_dir / "prompt.txt").read_text(encoding="utf-8").strip())
        out = open(run_dir / "events.jsonl", "w", encoding="utf-8")
        err = open(run_dir / "stderr.txt", "w", encoding="utf-8")
        procs.append((number, subprocess.Popen(cmd, cwd=info["folder"], env=env, stdout=out, stderr=err), out, err))
        print(f"started {number}")
    for number, proc, out, err in procs:
        code = proc.wait()
        out.close()
        err.close()
        key["candidates"][number]["exit"] = code
        print(f"finished {number} exit {code}")
    KEY.write_text(json.dumps(key, indent=2) + "\n", encoding="utf-8")


def read_events(path):
    reply, cost, models, calls = "", 0.0, set(), []
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


def check_splits(folder):
    results = []
    for amount, people, tip in SPLITS:
        proc = subprocess.run(["node", "bin/billsplit.js", amount, "--people", str(people), "--tip", str(tip)],
                              cwd=folder, capture_output=True, text=True)
        total = re.search(r"Total:\s+\$([\d,]+\.\d\d)", proc.stdout)
        shares = [round(float(s.replace(",", "")) * 100) for s in re.findall(r"Person \d+:\s+\$([\d,]+\.\d\d)", proc.stdout)]
        ok = bool(total) and len(shares) == people and sum(shares) == round(float(total.group(1).replace(",", "")) * 100) \
            and max(shares) - min(shares) <= 1
        results.append({"args": [amount, people, tip], "ok": ok, "stdout": proc.stdout.strip()})
    return results


def run_specs(folder):
    proc = subprocess.run(["node", "--test", "spec/*.spec.js"], cwd=folder, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    counts = dict(re.findall(r"ℹ (pass|fail) (\d+)", proc.stdout))
    return {"exit": proc.returncode, "pass": int(counts.get("pass", 0)), "fail": int(counts.get("fail", 0))}


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


def sanitize(text, folder):
    for form in {str(folder), str(folder).replace("\\", "/"), str(folder).replace("\\", "\\\\")}:
        text = re.sub(re.escape(form), "<project>", text, flags=re.I)
    text = re.sub(rf"{NAME}-\d+", "<project>", text)
    return re.sub(r"light[ -]?panel[ -]?", "", text, flags=re.I)


def describe(call):
    args = call["args"]
    main = args.get("command") or args.get("path") or args.get("pattern") or args.get("input") or json.dumps(args)
    return f"{call['name']}: {str(main)[:400]}".replace("\n", " ")


def collect(args):
    key = json.loads(KEY.read_text(encoding="utf-8"))
    if PACK.exists():
        shutil.rmtree(PACK)
    base_files = tree_files(TEMPLATE)
    shutil.copytree(TEMPLATE, PACK / "base")
    numbers = sorted(key["candidates"])
    labels = [chr(ord("A") + i) for i in range(len(numbers))]
    random.Random(key["seed"] + 1).shuffle(labels)
    measurements = {}
    for number, label in zip(numbers, labels):
        info = key["candidates"][number]
        folder = Path(info["folder"])
        reply, cost, models, calls = read_events(RUNS / number / "events.jsonl")
        for helper in sorted((RUNS / number / "sessions").glob("*/*.jsonl")):
            _, helper_cost, helper_models, helper_calls = read_events(helper)
            cost = round(cost + helper_cost, 4)
            models = sorted(set(models) | set(helper_models))
            calls += [{**call, "helper": helper.stem} for call in helper_calls]
        files = tree_files(folder)
        patch = unified_diff(base_files, files)
        changed = [name for name in sorted(set(base_files) | set(files)) if base_files.get(name) != files.get(name)]
        lines = sum(1 for line in patch.splitlines() if line[:1] in "+-" and line[:3] not in ("+++", "---"))
        before = RUNS / number / "before"
        if before.exists():
            shutil.rmtree(before)
        shutil.copytree(folder, before, ignore=shutil.ignore_patterns(*SKIP_DIRS))
        for name in ("src/split.js", "src/money.js", "bin/billsplit.js"):
            (before / name).write_text(base_files[name], encoding="utf-8")
        new_specs = [n for n in changed if n.startswith("spec/") or ".spec." in n or ".test." in n]
        measurements[number] = {
            "label": label, "variant": info["variant"], "cost": cost, "models": models, "exit": info.get("exit"),
            "tool_calls": len(calls), "files_changed": changed, "diff_lines": lines,
            "splits": check_splits(folder), "specs_after": run_specs(folder), "specs_on_old_code": run_specs(before),
            "new_or_changed_specs": new_specs, "outside_paths": outside_paths(calls, folder),
            "files_read": sorted({str(c["args"].get("path")) for c in calls if c["name"] == "read"}),
        }
        target = PACK / label
        shutil.copytree(folder, target / "repo", ignore=shutil.ignore_patterns(*SKIP_DIRS))
        (target / "reply.md").write_text(sanitize(reply, folder) + "\n", encoding="utf-8")
        (target / "diff.patch").write_text(patch, encoding="utf-8")
        actions = [("[helper] " if "helper" in c else "") + sanitize(describe(c), folder) for c in calls]
        actions = [a for a in actions if ".omp/skills" not in a and ".omp\\skills" not in a and "skill://" not in a]
        (target / "actions.txt").write_text("\n".join(actions) + "\n", encoding="utf-8")
    (RUNS / "measurements.json").write_text(json.dumps(measurements, indent=2) + "\n", encoding="utf-8")
    for number, m in measurements.items():
        print(f"{number} {m['label']} {m['variant']:9} ${m['cost']:<6} splits {sum(s['ok'] for s in m['splits'])}/{len(SPLITS)}"
              f"  specs after {m['specs_after']}  on old code {m['specs_on_old_code']}  diff {m['diff_lines']} lines"
              f"  outside {len(m['outside_paths'])}")
    print(f"judge pack: {PACK.relative_to(ROOT)}")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="step", required=True)
    p = sub.add_parser("setup")
    p.add_argument("--ref", default="HEAD", help="commit whose deep-mode skill and /deep command are installed")
    p.add_argument("--per-variant", type=int, default=2)
    p.add_argument("--seed", type=int, default=7)
    p = sub.add_parser("run")
    p.add_argument("--max-cost", type=float, default=3.0, help="omp --max-cost per candidate, in USD")
    p.add_argument("--max-time", default="45m")
    p.add_argument("--model", help="omp --model for every candidate (default: omp's default model)")
    sub.add_parser("collect")
    args = parser.parse_args()
    {"setup": setup, "run": run, "collect": collect}[args.step](args)


if __name__ == "__main__":
    main()
