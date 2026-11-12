#!/usr/bin/env python3
"""Run and score sealed, JSON-only review-quality evaluations."""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
CORPUS = HERE / "cases-v2.json"
SCRATCH = ROOT / ".scratch" / "review-runs"
SETTINGS = ("--no-tools", "--no-rules", "--no-context-files", "--no-skills", "--no-extensions", "--no-lsp")


def load_reviewer():
    import importlib.util
    source = ROOT / "plugins/deepmodebot/skills/deepmodebot/assets/github-app/bot.py"
    spec = importlib.util.spec_from_file_location("deepmodebot_review_prompt", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def context_coverage(packet):
    files = re.findall(r"^--- (.+?) \(head [0-9a-f]+, blob [0-9a-f]+, \d+ bytes,", packet, re.M)
    omitted = []
    marker = "\nOMISSIONS:\n"
    if marker in packet:
        omitted = packet.split(marker, 1)[1].splitlines()
    return files, omitted


def build_prompt(case, packet, reviewer):
    conversation = SimpleNamespace(
        pr={"title": "Review evaluator case", "body": ""},
        comments=[], head="pinned evaluation head", base="pinned evaluation base",
        own=False, repo="local/review-evaluation", n=1,
    )
    return reviewer.review_prompt(conversation, 1, case["diff"], None, packet)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def json_digest(value):
    data = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def finding_digest(finding):
    return json_digest(finding)




def parse_events(stdout):
    text, observed_model, credential_id, stop_reason, cost = "", None, None, None, 0.0
    usage = {"input": 0, "output": 0}
    unsafe = None
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if not isinstance(event, dict):
            continue
        message = event.get("message") if isinstance(event.get("message"), dict) else {}
        if event.get("type") == "tool_execution_start":
            unsafe = f"tool execution started: {message.get('toolName') or event.get('toolName')}"
        if message.get("role") == "fileMention":
            unsafe = "omp attached a file mention to the prompt"
        if event.get("type") != "message_end" or message.get("role") != "assistant":
            continue
        observed_model = f"{message.get('provider')}/{message.get('model')}"
        credential_id = message.get("credentialId")
        stop_reason = message.get("stopReason")
        metering = message.get("usage") or {}
        cost += float((metering.get("cost") or {}).get("total") or 0)
        usage["input"] += (metering.get("input") or 0) + (metering.get("cacheRead") or 0) + (metering.get("cacheWrite") or 0)
        usage["output"] += metering.get("output") or 0
        text = "".join(part.get("text", "") for part in message.get("content", [])
                       if isinstance(part, dict) and part.get("type") == "text")
    return text, observed_model, credential_id, stop_reason, round(cost, 6), usage, unsafe


def build_context(repo, base, head):
    import importlib.util
    source = ROOT / "plugins/deepmodebot/skills/deepmodebot/assets/github-app/review_context.py"
    spec = importlib.util.spec_from_file_location("review_context", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.build_context(repo, base, head)


def load_seal():
    import importlib.util
    source = ROOT / "plugins/deepmodebot/skills/deepmodebot/assets/pr-agent/pr_agent_local.py"
    spec = importlib.util.spec_from_file_location("pr_agent_local", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def version_info(omp):
    try:
        p = subprocess.run([omp, "--version"], capture_output=True, text=True, timeout=10)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("timed out determining omp version") from exc
    if p.returncode:
        raise RuntimeError(f"cannot determine omp version: {p.returncode}")
    return {"executable": str(Path(omp).resolve()), "version": (p.stdout or p.stderr).strip(),
            "sha256": digest(Path(omp).resolve())}



def load_corpus(path=CORPUS):
    corpus = json.loads(path.read_text(encoding="utf-8"))
    if corpus.get("schema") != 1 or not isinstance(corpus.get("cases"), list):
        raise ValueError("unsupported corpus schema")
    ids = [c["id"] for c in corpus["cases"]]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate case id")
    project_splits = {}
    pairs = {}
    expected_ids = set()
    bug_count = 0
    for c in corpus["cases"]:
        if c.get("split") not in {"calibration", "holdout"} or c.get("kind") not in {"bug", "clean"}:
            raise ValueError(f"invalid case classification: {c['id']}")
        if not c.get("diff") or not c.get("source_url") or not c.get("commit"):
            raise ValueError(f"incomplete case: {c['id']}")
        if not re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", c["commit"]):
            raise ValueError(f"case commit must be a full object ID: {c['id']}")
        if c["kind"] == "bug":
            if not c.get("expected_bugs"):
                raise ValueError(f"bug case has no expected label: {c['id']}")
            bug_count += 1
            if expected_ids.intersection(c["expected_bugs"]):
                raise ValueError(f"expected bug labels must be globally unique: {c['id']}")
            expected_ids.update(c["expected_bugs"])
        elif c.get("expected_bugs"):
            raise ValueError(f"clean control has expected bug labels: {c['id']}")
        old_split = project_splits.setdefault(c["project"], c["split"])
        if old_split != c["split"]:
            raise ValueError(f"project {c['project']} crosses calibration and holdout")
        pair = c.get("pair")
        if not isinstance(pair, str) or not pair:
            raise ValueError(f"case has no matched-patch pair: {c['id']}")
        pairs.setdefault(pair, []).append(c)
        context = c.get("context")
        if not isinstance(context, dict) or not all(
            isinstance(context.get(k), str) for k in ("repository", "base", "head")
        ):
            raise ValueError(f"missing case-pinned context metadata: {c['id']}")
        if any(not re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", context[k]) for k in ("base", "head")):
            raise ValueError(f"context commits must be full object IDs: {c['id']}")
    projects = {c["project"] for c in corpus["cases"]}
    if bug_count < 4 or len(projects) < 2 or not {"calibration", "holdout"} <= {c["split"] for c in corpus["cases"]}:
        raise ValueError("corpus requires at least four bugs across two projects and project-separated splits")
    if any(len(members) != 2
           or {m.get("input_direction") for m in members} != {"reverse-repair", "forward-repair"}
           or len({(m["project"], m["split"]) for m in members}) != 1 for members in pairs.values()):
        raise ValueError("each pair must contain forward and reverse patches from the same project split")
    for pair, members in pairs.items():
        reverse = next(m for m in members if m["input_direction"] == "reverse-repair")
        forward = next(m for m in members if m["input_direction"] == "forward-repair")
        before, after = reverse["context"], forward["context"]
        if (before["repository"] != after["repository"] or before["base"] != reverse["commit"]
                or after["head"] != forward["commit"] or before["head"] != after["base"]
                or reverse["commit"] != forward["commit"]):
            raise ValueError(f"paired context must match immutable forward and reverse patch heads: {pair}")
    return corpus


def parse_findings(response):
    text = response.strip()
    blocks = re.findall(r"```json\s*(.*?)\s*```", text, re.I | re.S)
    if blocks:
        if len(blocks) != 1:
            raise ValueError("expected exactly one fenced JSON block")
        text = blocks[0]
    obj = json.loads(text)
    if not isinstance(obj, dict) or set(obj) != {"findings"} or not isinstance(obj["findings"], list):
        raise ValueError("expected object with only a findings array")
    for finding in obj["findings"]:
        if not isinstance(finding, dict) or not all(k in finding for k in ("id", "file", "line", "severity", "claim", "evidence")):
            raise ValueError("finding is missing required fields")
        if not isinstance(finding["line"], int) or finding["severity"] not in {"P0", "P1", "P2"}:
            raise ValueError("invalid finding line or severity")
        if not all(isinstance(finding[k], str) for k in ("id", "file", "claim", "evidence")):
            raise ValueError("finding fields must be strings")
    return obj["findings"]


def prepare(args):
    corpus = load_corpus(Path(args.corpus))
    count = len(corpus["cases"])
    print(f"validated {count} cases; canonical corpus sha256 {json_digest(corpus)}")
    print("No downloads or target code execution performed.")
    return 0


def run_case(case, mode, packet, model, max_cost, timeout, omp, run_dir, overlay, seal, credentials, reviewer):
    case_dir = run_dir / case["id"]
    case_dir.mkdir(parents=True, exist_ok=True)
    context_files, context_omissions = context_coverage(packet) if packet else ([], [])
    prompt = seal.flatten([{"role": "user", "content": build_prompt(case, packet, reviewer)}])
    prompt_path = case_dir / "prompt.txt"
    prompt_path.write_text(prompt, encoding="utf-8")
    cmd = [omp, "-p", "--no-session", "--no-title", "--mode", "json", "--model", model,
           "--max-cost", str(max_cost), "--config", str(overlay), "--system-prompt", seal.SYSTEM,
           *SETTINGS, f"@{prompt_path}"]
    env = seal.scrubbed_env()
    tmp = run_dir / "tmp"
    tmp.mkdir(exist_ok=True)
    env.update(TMPDIR=str(tmp), TMP=str(tmp), TEMP=str(tmp))
    started = time.monotonic()
    record = {"case_id": case["id"], "model_requested": model, "command": cmd[:-1] + ["@<prompt>"],
              "mode": mode, "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
              "context_sha256": hashlib.sha256(packet.encode()).hexdigest() if packet else None,
              "context_files": context_files, "context_omissions": context_omissions,
              "settings": [*SETTINGS, "--config <no-discovery-overlay>"], "status": "failed", "findings": [], "usage": None}
    try:
        proc = subprocess.run(cmd, cwd=case_dir, env=env, capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=timeout,
                              creationflags=seal.NO_WINDOW)
        (case_dir / "stdout.txt").write_text(proc.stdout, encoding="utf-8")
        (case_dir / "stderr.txt").write_text(proc.stderr, encoding="utf-8")
        record["exit_code"] = proc.returncode
        record["raw_stdout"] = proc.stdout
        record["raw_stderr"] = proc.stderr
        parsed_text, observed_model, credential_id, stop_reason, cost, usage, unsafe = parse_events(proc.stdout)
        record.update(model_observed=observed_model, credential_id=credential_id, stop_reason=stop_reason,
                      usage_cost=cost, usage_tokens=usage)
        if unsafe:
            record["error"] = unsafe
        elif observed_model != model or not credential_id:
            record["error"] = f"observed model {observed_model} or credential identity missing/mismatched"
        elif credential_id not in credentials:
            record["error"] = "model response did not use an approved OAuth credential"
        elif proc.returncode:
            record["error"] = f"omp exited {proc.returncode}"
        elif stop_reason != "stop":
            record["error"] = f"omp stopped with {stop_reason}; partial output rejected"
        else:
            try:
                record["findings"] = parse_findings(parsed_text or proc.stdout)
                record["status"] = "valid"
            except (ValueError, json.JSONDecodeError) as e:
                record["error"] = f"malformed JSON: {e}"
    except subprocess.TimeoutExpired as e:
        record["error"] = f"timeout after {timeout}s"
        for key, value in (("stdout.txt", e.stdout), ("stderr.txt", e.stderr)):
            if value:
                (case_dir / key).write_bytes(value if isinstance(value, bytes) else value.encode())
    record["elapsed_seconds"] = round(time.monotonic() - started, 3)
    return record


def run(args):
    corpus_path = Path(args.corpus).resolve()
    corpus = load_corpus(corpus_path)
    selected = [c for c in corpus["cases"] if c["split"] == args.split and (not args.only or c["id"] in args.only)]
    if args.only and set(args.only) != {c["id"] for c in selected}:
        raise ValueError("--only includes unknown or other-split case ids")
    if args.timeout <= 0 or not 0 < args.max_cost < float("inf"):
        raise ValueError("--timeout and --max-cost must be positive and finite")
    context_root = Path(args.context_repos_dir).resolve() if args.context_repos_dir else None
    scratch_root = ROOT / ".scratch"
    if context_root and not context_root.is_relative_to(scratch_root.resolve()):
        raise ValueError("context repositories must be under .scratch")
    if args.mode == "enriched" and not context_root:
        raise ValueError("enriched mode requires --context-repos-dir containing the case-pinned repositories")
    omp = shutil.which("omp")
    if not omp:
        raise RuntimeError("omp is unavailable; no alternate model or API fallback is permitted")
    run_dir = SCRATCH / dt.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    run_dir.mkdir(parents=True)
    out = Path(args.out).resolve() if args.out else run_dir / "run.json"
    if not out.is_relative_to(SCRATCH.resolve()):
        raise ValueError("run output must be under .scratch/review-runs")
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        raise ValueError(f"run output already exists: {out}")
    tmp = run_dir / "tmp"
    tmp.mkdir()
    os.environ.update(TMPDIR=str(tmp), TMP=str(tmp), TEMP=str(tmp))
    cli = version_info(omp)
    seal = load_seal()
    credentials = seal.omp_oauth_credentials(args.model)
    reviewer = load_reviewer()
    cli["no_discovery_overlay_sha256"] = hashlib.sha256(seal.NO_DISCOVERY.encode()).hexdigest()
    cli["system_prompt_sha256"] = hashlib.sha256(seal.SYSTEM.encode()).hexdigest()
    overlay = run_dir / "no-discovery.yml"
    overlay.write_text(seal.NO_DISCOVERY, encoding="utf-8")
    records = []
    for case in selected:
        packet, context_files, context_omissions = "", [], []
        if args.mode == "enriched":
            context_info = case.get("context")
            try:
                if not isinstance(context_info, dict):
                    raise ValueError("case has no pinned context source")
                repo_dir = (context_root / context_info["repository"]).resolve()
                if not repo_dir.is_relative_to(context_root):
                    raise ValueError("unsafe context repository path")
                packet = build_context(repo_dir, context_info["base"], context_info["head"])
                if "OMITTED: source context unavailable" in packet:
                    raise ValueError("pinned Git objects unavailable")
                context_files, context_omissions = context_coverage(packet)
                if not context_files:
                    raise ValueError("pinned packet contains no source blobs")
                context_error = None
            except (OSError, RuntimeError, ValueError, KeyError) as exc:
                context_error = f"pinned context unavailable: {exc}"
            if context_error:
                records.append({"case_id": case["id"], "status": "failed", "findings": [],
                                "model_requested": args.model, "model_observed": None, "error": context_error,
                                "context_sha256": hashlib.sha256(packet.encode()).hexdigest() if packet else None,
                                "context_files": context_files, "context_omissions": context_omissions,
                                "settings": [*SETTINGS, "--config <no-discovery-overlay>" ]})
                continue
        records.append(run_case(case, args.mode, packet, args.model, args.max_cost, args.timeout,
                                omp, run_dir, overlay, seal, credentials, reviewer))
    report = {"schema": 1, "created_at": dt.datetime.now(dt.timezone.utc).isoformat(), "corpus_sha256": json_digest(corpus),
              "corpus_path": str(corpus_path), "artifact_directory": str(run_dir),
              "model_requested": args.model, "mode": args.mode,
              "model_observed": sorted({r.get("model_observed") for r in records if r.get("model_observed")}),
              "cli": cli, "context_sources": {r["case_id"]: r.get("context_sha256") for r in records},
              "context_bindings": {c["id"]: c.get("context") for c in selected},
              "context_coverage": {r["case_id"]: {"files": r.get("context_files", []),
                                                  "omissions": r.get("context_omissions", [])} for r in records},
              "settings": [*SETTINGS, "--config <no-discovery-overlay>"],
              "timeout_seconds": args.timeout, "max_cost_per_case": args.max_cost,
              "split": args.split, "results": records}
    with out.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(report, indent=2) + "\n")
    print(out)
    return 1 if any(r["status"] != "valid" for r in records) else 0


def adjudicate(args):
    run_path = Path(args.run)
    report = json.loads(run_path.read_text(encoding="utf-8"))
    corpus = load_corpus(Path(report["corpus_path"]))
    by_id = {c["id"]: c for c in corpus["cases"]}
    output = {"schema": 1, "run_sha256": digest(run_path), "corpus_sha256": report["corpus_sha256"],
              "model_requested": report["model_requested"],
              "model_observed": sorted({r.get("model_observed") for r in report["results"] if r.get("model_observed")}),
              "cli": report.get("cli"), "mode": report["mode"], "settings": report["settings"], "cases": []}
    for result in report["results"]:
        c = by_id[result["case_id"]]
        findings = result.get("findings", [])
        output["cases"].append({"case_id": c["id"], "status": result["status"], "error": result.get("error"),
                                "expected_bugs": c.get("expected_bugs", []),
                                "findings": [{"finding_sha256": finding_digest(f), "finding": f,
                                              "maps_to": None, "adjudication": "", "rationale": ""}
                                             for f in findings]})
    out = Path(args.out).resolve()
    if not out.is_relative_to(SCRATCH.resolve()):
        raise ValueError("adjudication output must be under .scratch/review-runs")
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        raise ValueError(f"adjudication output already exists: {out}")
    with out.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(output, indent=2) + "\n")
    print(out)
    return 0


def score_data(run_data, adj, corpus, run_digest):
    identity = ("model_requested", "model_observed", "cli", "mode", "settings", "corpus_sha256")
    if adj.get("run_sha256") != run_digest or any(adj.get(k) != run_data.get(k) for k in identity):
        raise ValueError("adjudication does not match exact run/corpus/model/CLI version/mode/settings")
    if json_digest(corpus) != run_data.get("corpus_sha256"):
        raise ValueError("current corpus differs from the corpus bound to the run")
    results = run_data.get("results", [])
    worksheets = adj.get("cases")
    if not isinstance(worksheets, list) or [w.get("case_id") for w in worksheets] != [r.get("case_id") for r in results]:
        raise ValueError("adjudication must contain exactly one row for every run case in order")
    cases = {c["id"]: c for c in corpus["cases"]}
    tp = fp = total_expected = total_clean = clean_fp_cases = 0
    valid_expected = valid_clean = valid_tp = failed_bug_cases = failed_clean_cases = 0
    errors = []
    for item, result in zip(worksheets, results):
        case_id = result["case_id"]
        c = cases[case_id]
        expected_bugs = c.get("expected_bugs", [])
        if item.get("status") != result["status"] or item.get("error") != result.get("error"):
            raise ValueError(f"adjudication changed run status or error for {case_id}")
        if item.get("expected_bugs") != expected_bugs:
            raise ValueError(f"adjudication changed expected labels for {case_id}")
        original_findings = result.get("findings", [])
        rows = item.get("findings")
        if not isinstance(rows, list) or len(rows) != len(original_findings):
            raise ValueError(f"adjudication changed finding count for {case_id}")
        for row, original in zip(rows, original_findings):
            if row.get("finding") != original or row.get("finding_sha256") != finding_digest(original):
                raise ValueError(f"adjudication changed model finding for {case_id}")
        is_bug = c["kind"] == "bug"
        if is_bug:
            total_expected += len(expected_bugs)
        else:
            total_clean += 1
        if result["status"] != "valid":
            errors.append({"case_id": case_id, "error": result.get("error") or result["status"]})
            if is_bug:
                failed_bug_cases += 1
            else:
                failed_clean_cases += 1
            if rows:
                raise ValueError(f"failed case {case_id} must not contain findings")
            continue
        if is_bug:
            valid_expected += len(expected_bugs)
        else:
            valid_clean += 1
        mapped = set()
        case_fp = False
        for row in rows:
            decision = row.get("adjudication")
            target = row.get("maps_to")
            rationale = row.get("rationale")
            if decision not in {"true_positive", "false_positive"} or not isinstance(rationale, str) or not rationale.strip():
                raise ValueError(f"pending or unsupported adjudication for {case_id}")
            if decision == "true_positive" and target not in expected_bugs:
                raise ValueError(f"true positive must map to an expected bug in {case_id}")
            if decision == "false_positive" and target is not None:
                raise ValueError(f"false positive must not map to an expected bug in {case_id}")
            if decision == "true_positive" and target in mapped:
                fp += 1
                case_fp = True
            elif decision == "true_positive":
                tp += 1
                valid_tp += 1
                mapped.add(target)
            else:
                fp += 1
                case_fp = True
        if not is_bug and case_fp:
            clean_fp_cases += 1
    return {"true_positives": tp, "false_positives": fp, "missed_expected_bugs": total_expected - tp,
            "precision": tp / (tp + fp) if tp + fp else None,
            "bug_recall": tp / total_expected if total_expected else None,
            "clean_case_false_positive_rate": clean_fp_cases / valid_clean if valid_clean else None,
            "expected_bug_denominator_including_failures": total_expected,
            "valid_expected_bug_denominator": valid_expected, "valid_true_positives": valid_tp,
            "clean_case_attempts": total_clean, "valid_clean_cases": valid_clean,
            "failed_bug_cases": failed_bug_cases, "failed_clean_cases": failed_clean_cases,
            "invalid_cases": errors}


def score(args):
    run_path, adj_path = Path(args.run), Path(args.adjudication)
    run_data, adj = json.loads(run_path.read_text()), json.loads(adj_path.read_text())
    corpus = load_corpus(Path(run_data["corpus_path"]))
    metrics = score_data(run_data, adj, corpus, digest(run_path))
    print(json.dumps(metrics, indent=2))
    return 0


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="action", required=True)
    prep = sub.add_parser("prepare"); prep.add_argument("--corpus", default=str(CORPUS)); prep.set_defaults(func=prepare)
    r = sub.add_parser("run"); r.add_argument("--corpus", default=str(CORPUS)); r.add_argument("--model", required=True)
    r.add_argument("--mode", choices=("diff-only", "enriched"), default="diff-only"); r.add_argument("--split", choices=("calibration", "holdout"), default="calibration")
    r.add_argument("--only", action="append", default=[]); r.add_argument("--max-cost", type=float, default=0.25); r.add_argument("--timeout", type=int, default=180)
    r.add_argument("--context-repos-dir", help="directory under .scratch with project repositories named as in cases.json")
    r.add_argument("--out"); r.set_defaults(func=run)
    a = sub.add_parser("adjudicate"); a.add_argument("run"); a.add_argument("--out", required=True); a.set_defaults(func=adjudicate)
    s = sub.add_parser("score"); s.add_argument("run"); s.add_argument("adjudication"); s.set_defaults(func=score)
    args = p.parse_args()
    try:
        return args.func(args)
    except (OSError, ValueError, RuntimeError, KeyError, json.JSONDecodeError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
