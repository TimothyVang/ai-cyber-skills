#!/usr/bin/env python3
"""Routing eval: ask a headless omp which route and size the skill picks for each case, then score the answers.

Each case runs one `omp -p` process from its own empty folder under .scratch/, with tools, skills, rules,
context files and extensions off, so the answer comes from the skill text in the prompt alone.
"""
import argparse
import datetime
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SKILL = ROOT / "plugins/deep-mode/skills/deep-mode/SKILL.md"
DEFAULT_CASES = ROOT / "evals/routing/cases.json"
SCRATCH = ROOT / ".scratch/routing-runs"
API_KEYS = ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "CODEX_API_KEY")
SIZES = {"S", "M", "L", "none"}

PROMPT = """You are routing a request with the deep-mode skill below. Do not do the work.
Answer which route the skill picks and what size it gives the work.

<skill file="SKILL.md">
{skill}
</skill>

Repo context: {context}

Request: /deep {request}

Reply with one JSON line and nothing else: {{"route": "<name>", "size": "<S|M|L|none>"}}
- route: the name the first matching row of the Routes table names first.
  For a playbook, its file name without `.md` (for example `bug-fix`).
  For a technique, its name (for example `pr-review`). For a sibling skill, its name (for example `contribute`).
  When the Routes table sends you to the Playbooks table, the matching playbook's file name.
- size: S, M or L from the Size table, or none for read-only work (a review, an investigation, a question).
"""


def build_prompt(skill_text, context, case):
    return PROMPT.format(skill=skill_text.strip(), context=case.get("context", context), request=case["request"])


def normalize_route(value):
    route = str(value or "").strip().strip("`*").lower()
    route = re.sub(r"^skill://", "", route)
    route = route.rsplit("/", 1)[-1].removesuffix(".md")
    return route.replace(" ", "-")


def normalize_size(value):
    size = str(value if value is not None else "none").strip().strip("`*")
    return size.upper() if size.upper() in {"S", "M", "L"} else size.lower()


def parse_events(stdout):
    """Return (final assistant text, model id, summed cost) from omp --mode json output."""
    text, model, cost = "", None, 0.0
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        message = event.get("message") if event.get("type") == "message_end" else None
        if not message or message.get("role") != "assistant":
            continue
        model = f"{message.get('provider')}/{message.get('model')}"
        cost += float(message.get("usage", {}).get("cost", {}).get("total") or 0)
        text = "".join(part.get("text", "") for part in message.get("content", []) if part.get("type") == "text")
    return text, model, round(cost, 6)


def parse_answer(text):
    for blob in reversed(re.findall(r"\{[^{}]*\}", text)):
        try:
            answer = json.loads(blob)
        except ValueError:
            continue
        if isinstance(answer, dict) and "route" in answer:
            return {"route": normalize_route(answer.get("route")), "size": normalize_size(answer.get("size"))}
    return None


def run_case(case, prompt, run_dir, args, omp):
    case_dir = run_dir / case["id"]
    case_dir.mkdir(parents=True)
    prompt_file = run_dir / "prompts" / f"{case['id']}.md"
    prompt_file.write_text(prompt, encoding="utf-8")
    cmd = [omp, "-p", "--no-session", "--no-title", "--max-cost", str(args.max_cost), "--mode", "json",
           "--no-tools", "--no-skills", "--no-rules", "--no-context-files", "--no-extensions"]
    if args.model:
        cmd += ["--model", args.model]
    cmd.append(f"@{prompt_file}")
    env = {key: value for key, value in os.environ.items() if key not in API_KEYS}
    tmp = run_dir / "tmp"
    env.update(TMPDIR=str(tmp), TMP=str(tmp), TEMP=str(tmp))
    result = {"id": case["id"], "request": case["request"], "expected": {"route": case["route"], "size": case["size"]}}
    try:
        proc = subprocess.run(cmd, cwd=case_dir, env=env, capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=args.timeout)
    except subprocess.TimeoutExpired:
        return {**result, "answer": None, "raw": "", "model": None, "cost": None, "error": f"timeout after {args.timeout}s"}
    text, model, cost = parse_events(proc.stdout)
    answer = parse_answer(text)
    error = None if answer else f"no JSON answer (exit {proc.returncode}): {(text or proc.stderr)[-300:]}"
    result.update(answer=answer, raw=text.strip(), model=model, cost=cost, error=error)
    result["route_ok"] = bool(answer) and answer["route"] == case["route"]
    result["size_ok"] = bool(answer) and answer["size"] == case["size"]
    return result


def print_table(results):
    rows = [("case", "expected", "answer", "route", "size")]
    for r in results:
        got = r["answer"] or {}
        rows.append((r["id"], f"{r['expected']['route']} {r['expected']['size']}",
                     f"{got.get('route', '-')} {got.get('size', '-')}" if got else f"ERROR {r['error'][:40]}",
                     "ok" if r.get("route_ok") else "MISS", "ok" if r.get("size_ok") else "MISS"))
    widths = [max(len(row[i]) for row in rows) for i in range(5)]
    for row in rows:
        print("  ".join(cell.ljust(width) for cell, width in zip(row, widths)).rstrip())


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("skill", nargs="?", default=str(DEFAULT_SKILL), help="SKILL.md under test")
    parser.add_argument("--cases", default=str(DEFAULT_CASES), help="cases JSON file")
    parser.add_argument("--model", help="omp --model for every case (default: omp's default model)")
    parser.add_argument("--max-cost", type=float, default=0.5, help="omp --max-cost per case, in USD")
    parser.add_argument("--only", action="append", default=[], metavar="ID", help="run only this case id (repeatable)")
    parser.add_argument("--jobs", type=int, default=4, help="cases run at the same time")
    parser.add_argument("--timeout", type=int, default=300, help="seconds per case")
    parser.add_argument("--dry-run", action="store_true", help="print the prompts; make no model calls")
    parser.add_argument("--out", help="results file (default evals/results/routing-<date>.json; .scratch/ with --only)")
    args = parser.parse_args()

    skill_path = Path(args.skill).resolve()
    skill_bytes = skill_path.read_bytes()
    spec = json.loads(Path(args.cases).read_text(encoding="utf-8"))
    cases = spec["cases"]
    if args.only:
        unknown = set(args.only) - {case["id"] for case in cases}
        if unknown:
            sys.exit(f"unknown case id: {', '.join(sorted(unknown))}")
        cases = [case for case in cases if case["id"] in args.only]
    bad = [case["id"] for case in cases if case["size"] not in SIZES]
    if bad:
        sys.exit(f"cases with a size outside {sorted(SIZES)}: {bad}")
    prompts = {case["id"]: build_prompt(skill_bytes.decode("utf-8"), spec["context"], case) for case in cases}

    if args.dry_run:
        for case in cases:
            print(f"===== {case['id']} (expect {case['route']} {case['size']}) =====")
            print(prompts[case["id"]])
        return 0

    omp = shutil.which("omp")
    if not omp:
        sys.exit("omp is not on PATH")
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir = SCRATCH / stamp
    (run_dir / "prompts").mkdir(parents=True)
    (run_dir / "tmp").mkdir()
    with ThreadPoolExecutor(max_workers=max(1, args.jobs)) as pool:
        results = list(pool.map(lambda case: run_case(case, prompts[case["id"]], run_dir, args, omp), cases))
    shutil.rmtree(run_dir / "tmp", ignore_errors=True)

    print_table(results)
    total = len(results)
    route_ok = sum(bool(r.get("route_ok")) for r in results)
    size_ok = sum(bool(r.get("size_ok")) for r in results)
    both_ok = sum(bool(r.get("route_ok") and r.get("size_ok")) for r in results)
    cost = round(sum(r["cost"] or 0 for r in results), 4)
    print(f"\nroute {route_ok}/{total}  size {size_ok}/{total}  both {both_ok}/{total}  cost ${cost}")

    today = datetime.date.today().isoformat()
    default_out = (run_dir / "results.json") if args.only else ROOT / f"evals/results/routing-{today}.json"
    out = Path(args.out) if args.out else default_out
    out.parent.mkdir(parents=True, exist_ok=True)
    models = sorted({r["model"] for r in results if r["model"]})
    report = {
        "date": today,
        "skill": skill_path.relative_to(ROOT).as_posix() if skill_path.is_relative_to(ROOT) else str(skill_path),
        "skill_sha256": hashlib.sha256(skill_bytes).hexdigest(),
        "cases_file": Path(args.cases).resolve().relative_to(ROOT).as_posix(),
        "model_requested": args.model,
        "models_observed": models,
        "max_cost_per_case": args.max_cost,
        "scores": {"cases": total, "route": route_ok, "size": size_ok, "both": both_ok, "cost_usd": cost},
        "results": results,
    }
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out.relative_to(ROOT) if out.is_relative_to(ROOT) else out}")
    return 1 if any(r["error"] for r in results) else 0


if __name__ == "__main__":
    sys.exit(main())
