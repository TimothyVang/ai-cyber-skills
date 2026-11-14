#!/usr/bin/env python3
"""Record an explicit operator scenario, or replay its sealed assertions in isolation."""
from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import time
import uuid
import hashlib

from evidence import (artifact, assertion_passes, assertion_specs, canonical, load_bundle,
                      origin, parse_json, seal_bundle, sha256, validate_scenario)

MIN_BROWSER = (0, 43, 0)


class CaptureError(RuntimeError):
    pass


def browser_command(executable):
    found = shutil.which(str(executable))
    if not found:
        raise CaptureError(f"missing executable: {executable}; install explicitly, never automatically")
    path = Path(found).resolve()
    if path.suffix.lower() in (".cmd", ".bat"):
        launcher = path.parent / "node_modules" / "agent-browser" / "bin" / "agent-browser.js"
        node = shutil.which("node")
        if not launcher.is_file() or not node:
            raise CaptureError("select a native agent-browser executable with --browser; shell launchers are not accepted")
        return [node, str(launcher)]
    return [str(path)]


def clean_environment():
    forbidden = {"NODE_OPTIONS", "NODE_PATH", "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "CODEX_API_KEY",
                 "BROWSERBASE_API_KEY", "BROWSERBASE_PROJECT_ID", "BROWSER_USE_API_KEY"}
    return {key: value for key, value in os.environ.items()
            if not key.upper().startswith("AGENT_BROWSER_") and key.upper() not in forbidden}


class Commands:
    def __init__(self, output, seconds, command_seconds, env):
        self.output = Path(output)
        self.deadline = time.monotonic() + seconds
        self.command_seconds = command_seconds
        self.env = env
        self.count = 0
        self.logs = []

    def run(self, argv, *, cleanup=False):
        if self.count >= 1000:
            raise CaptureError("command count limit reached")
        remaining = self.deadline - time.monotonic()
        timeout = min(self.command_seconds, remaining) if not cleanup else 15
        if timeout <= 0:
            raise CaptureError("capture wall-clock limit reached")
        self.count += 1
        prefix = f"commands/{self.count:04d}"
        stdout = self.output / (prefix + ".stdout.txt")
        stderr = self.output / (prefix + ".stderr.txt")
        stdout.parent.mkdir(exist_ok=True)
        started = time.monotonic()
        code = None
        timed_out = False
        try:
            with stdout.open("xb") as out, stderr.open("xb") as err:
                proc = subprocess.Popen(argv, cwd=self.output, env=self.env, stdin=subprocess.DEVNULL,
                                        stdout=out, stderr=err, start_new_session=os.name != "nt")
                try:
                    code = proc.wait(timeout=timeout)
                except BaseException:
                    timed_out = True
                    if os.name == "nt":
                        subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                                       stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                       stderr=subprocess.DEVNULL, timeout=5, check=False)
                    else:
                        try:
                            os.killpg(proc.pid, signal.SIGKILL)
                        except ProcessLookupError:
                            pass
                    proc.wait(timeout=5)
                    raise
        except subprocess.TimeoutExpired as exc:
            raise CaptureError(f"command timed out after {timeout:.1f}s; see {prefix}") from exc
        except OSError as exc:
            raise CaptureError(f"could not execute {argv[0]}: {exc}") from exc
        finally:
            row = {"argv": argv, "exit_code": code, "timed_out": timed_out,
                   "elapsed_ms": round((time.monotonic() - started) * 1000),
                   "stdout": prefix + ".stdout.txt", "stderr": prefix + ".stderr.txt"}
            self.logs.append(row)
        if stdout.stat().st_size > 4 * 1024 * 1024 or stderr.stat().st_size > 4 * 1024 * 1024:
            raise CaptureError(f"command output exceeds 4 MiB; retained at {prefix}")
        result = stdout.read_text(encoding="utf-8", errors="replace")
        if code != 0:
            detail = stderr.read_text(encoding="utf-8", errors="replace")[-2000:]
            raise CaptureError(f"command exited {code}: {detail or result[-2000:]}; see {prefix}")
        return result


def inspect_browser(commands, executable, provenance=None):
    argv = browser_command(executable)
    version = commands.run([*argv, "--version"]).strip()
    if provenance is not None:
        provenance["agent_browser_version"] = version
    matched = re.search(r"\b(\d+)\.(\d+)\.(\d+)\b", version)
    if not matched or tuple(map(int, matched.groups())) < MIN_BROWSER:
        raise CaptureError(f"{version}: recording containment verified only from 0.43.0; installed 0.15.0 creates an unfiltered recording context")
    help_text = commands.run([*argv, "--help"])
    for option in ("record", "--allowed-domains", "--config", "--session", "--action-policy", "--pin-tab"):
        if option not in help_text:
            raise CaptureError(f"browser lacks required capability {option}")
    commands.run([*argv, "skills", "get", "core"])
    recording_help = commands.run([*argv, "record", "--help"])
    if "--fps" not in recording_help or "fresh browser context" in recording_help:
        raise CaptureError("required in-place native recording capability is unavailable")
    return argv, version


class Browser:
    def __init__(self, commands, argv, output, scenario, session):
        self.commands = commands
        self.output = output
        self.scenario = scenario
        self.target_id = None
        hosts = sorted({origin(item).split("://", 1)[1].split(":", 1)[0] for item in scenario["allowed_origins"]})
        self.argv = [*argv, "--config", str(output / "browser-config.json"), "--session", session,
                     "--allowed-domains", ",".join(hosts), "--action-policy", str(output / "action-policy.json"),
                     "--pin-tab", "--json"]

    def call(self, *args, cleanup=False):
        raw = self.commands.run([*self.argv, *map(str, args)], cleanup=cleanup)
        try:
            response = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise CaptureError("browser did not return structured JSON; inspect command logs") from exc
        if not isinstance(response, dict) or response.get("success") is not True or not isinstance(response.get("data"), dict):
            raise CaptureError(f"browser command failed: {raw[:2000]}")
        data = response["data"]
        if data.get("error"):
            raise CaptureError(f"browser reported error: {data['error']}")
        return data

    def verify_target(self):
        tabs = self.call("tab", "list").get("tabs")
        if not isinstance(tabs, list) or len(tabs) != 1 or not isinstance(tabs[0], dict) or tabs[0].get("active") is not True:
            raise CaptureError("recording requires one pinned tab; popups and tab transitions are unsupported")
        target = tabs[0].get("targetId")
        if not isinstance(target, str) or not target or (self.target_id is not None and target != self.target_id):
            raise CaptureError("observed tab differs from the recorded target")
        self.target_id = target
        return target

    def action(self, action):
        kind = action["type"]
        if kind == "open":
            return self.call("open", action["url"])
        if kind in ("click", "check", "uncheck", "wait"):
            return self.call(kind, action["selector"])
        if kind == "fill":
            return self.call("fill", action["selector"], action["text"])
        if kind == "press":
            return self.call("press", action["key"])
        if kind == "pause":
            return self.call("wait", action["ms"])
        if kind == "scroll":
            return self.call("scroll", action["direction"], action["pixels"])
        raise CaptureError("unsupported action")

    def observe(self, expected):
        target = self.verify_target()
        url = self.call("get", "url").get("url")
        if origin(url) not in self.scenario["allowed_origins"]:
            raise CaptureError(f"observed top-level origin outside scenario allowlist: {url}")
        result = {"url": url, "target_id": target, "assertions": [], "errors": []}
        for spec in assertion_specs(expected):
            if spec["kind"] == "url":
                actual = url
            elif spec["kind"] == "text":
                actual = self.call("get", "text", spec["selector"]).get("text")
            else:
                actual = self.call("is", spec["property"], spec["selector"]).get(spec["property"])
            result["assertions"].append({"expected": spec, "actual": actual, "passed": assertion_passes(spec, actual)})
        page_errors = self.call("errors").get("errors")
        if not isinstance(page_errors, list):
            raise CaptureError("browser error inventory is unavailable")
        result["errors"] = [f"browser page error: {item}" for item in page_errors]
        return result


def capture_step(browser, root, step, elapsed):
    row = {**step, "started_ms": elapsed(), "ended_ms": elapsed(), "status": "failed",
           "screenshot": None, "snapshot": None, "observations": {"errors": [], "assertions": []}}
    errors = []
    try:
        browser.action(step["action"])
        row["observations"] = browser.observe(step["expected"])
        errors.extend(row["observations"]["errors"])
    except (CaptureError, ValueError) as exc:
        errors.append(str(exc))
    for kind in ("screenshot", "snapshot"):
        relative = f"steps/{step['id']}.{'png' if kind == 'screenshot' else 'snapshot.json'}"
        try:
            if kind == "screenshot":
                browser.call("screenshot", str(root / relative))
            else:
                data = browser.call("snapshot")
                (root / relative).write_bytes(canonical(data) + b"\n")
            row[kind] = artifact(root, relative)
        except (CaptureError, ValueError, OSError) as exc:
            errors.append(f"{kind}: {exc}")
    row["observations"]["errors"] = errors
    row["ended_ms"] = elapsed()
    if not errors and row["observations"]["assertions"] and all(item["passed"] for item in row["observations"]["assertions"]):
        row["status"] = "passed"
    return row


def sample_video(commands, root, manifest, max_frames):
    raw = commands.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(root / "video.webm")])
    (root / "video-probe.json").write_text(raw, encoding="utf-8")
    try:
        duration = float(json.loads(raw)["format"]["duration"])
    except (ValueError, KeyError, TypeError) as exc:
        raise CaptureError("video has no finite observed duration") from exc
    if not math.isfinite(duration) or not 0 < duration <= 3600:
        raise CaptureError("video duration is outside 0..3600 seconds")
    duration_ms = math.ceil(duration * 1000)
    interval = max(1000, math.ceil(duration_ms / max_frames))
    manifest["sampling"].update(interval_ms=interval, duration_ms=duration_ms)
    for at_ms in range(0, duration_ms, interval):
        relative = f"frames/{at_ms:08d}.png"
        commands.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-n",
                      "-ss", f"{at_ms / 1000:.3f}", "-i", str(root / "video.webm"),
                      "-frames:v", "1", "-vf", "scale=1280:-2", str(root / relative)])
        manifest["frames"].append({"at_ms": at_ms, "image": artifact(root, relative)})
    manifest["sampling"]["coverage"] = "complete"


def record(scenario, scenario_bytes, output, *, executable="agent-browser", seconds=300,
           command_seconds=30, max_frames=12, replay_of=None, browser_skills_dir=None):
    validate_scenario(scenario)
    if parse_json(scenario_bytes) != scenario:
        raise ValueError("scenario object differs from its pinned bytes")
    if not 10 <= seconds <= 1800 or not 1 <= command_seconds <= 120 or not 1 <= max_frames <= 60:
        raise ValueError("caps: seconds 10..1800, command-seconds 1..120, max-frames 1..60")
    root = Path(output).absolute()
    root.mkdir(parents=True, exist_ok=False)
    root = root.resolve()
    for name in ("steps", "frames", "tmp"):
        (root / name).mkdir()
    (root / "scenario.json").write_bytes(scenario_bytes)
    (root / "capture-tool.py").write_bytes(Path(__file__).read_bytes())
    (root / "evidence-source.py").write_bytes(Path(__file__).with_name("evidence.py").read_bytes())
    (root / "browser-config.json").write_bytes(b"{}\n")
    (root / "action-policy.json").write_bytes(canonical({"default": "allow", "deny": ["eval", "download", "upload", "state"]}))
    session = "deepmode-e2e-" + uuid.uuid4().hex
    env = clean_environment()
    if browser_skills_dir is not None:
        env["AGENT_BROWSER_SKILLS_DIR"] = str(Path(browser_skills_dir).resolve())
    env.update({"TMP": str(root / "tmp"), "TEMP": str(root / "tmp"), "TMPDIR": str(root / "tmp"),
                "AGENT_BROWSER_DEFAULT_TIMEOUT": str(int(command_seconds * 1000))})
    commands = Commands(root, seconds, command_seconds, env)
    started = time.monotonic()
    elapsed = lambda: round((time.monotonic() - started) * 1000)
    manifest = {"schema_version": 1, "intent": scenario["intent"], "scenario": artifact(root, "scenario.json"),
                "capture_tool": {"sha256": sha256(__file__), "source": artifact(root, "capture-tool.py"),
                                 "browser_version": "unavailable: CLI does not expose actual Chrome version",
                                 "agent_browser_version": "unavailable"},
                "state": "unavailable", "session": session, "recorded_target_id": None,
                "steps": [], "video": None, "frames": [],
                "sampling": {"method": "uniform", "interval_ms": 1000, "duration_ms": 0,
                             "max_frames": max_frames, "coverage": "incomplete"},
                "limits": {"seconds": seconds, "command_seconds": command_seconds, "cleanup_seconds": 30,
                           "max_steps": 40, "max_commands": 1000},
                "limitations": ["Uniform timeline frames are samples, not continuous semantic video understanding.",
                                "Only one pinned tab is recorded; popup and tab transitions fail rather than imply coverage.",
                                "Browser allowlist is domain-based, not a firewall; top-level exact origins are checked after steps.",
                                "No source/application revision is inferred from recorder provenance.",
                                "Hashes detect changed artifacts relative to the seal, not forgery by someone who can rewrite the entire bundle.",
                                "Actual Chrome version is not exposed by this command contract."]}
    if replay_of:
        manifest["replay"] = {"source_bundle_sha256": replay_of, "comparison": "same pinned scenario and assertions; no pixel-identity requirement"}
    browser = None
    recording = False
    try:
        for tool in ("ffmpeg", "ffprobe"):
            if not shutil.which(tool):
                raise CaptureError(f"{tool} unavailable on PATH; explicit installation required")
        argv, version = inspect_browser(commands, executable, manifest["capture_tool"])
        browser = Browser(commands, argv, root, scenario, session)
        browser.call("open")
        browser.call("set", "viewport", "1280", "720")
        manifest["recorded_target_id"] = browser.verify_target()
        browser.call("record", "start", str(root / "video.webm"), "--fps", "10")
        recording = True
        manifest["state"] = "failed"
        for step in scenario["steps"]:
            row = capture_step(browser, root, step, elapsed)
            manifest["steps"].append(row)
            if row["status"] != "passed":
                break
        browser.verify_target()
    except (CaptureError, ValueError, OSError, KeyboardInterrupt) as exc:
        manifest["limitations"].append(f"Capture failure: {type(exc).__name__}: {exc}")
    finally:
        if browser is not None:
            if recording:
                try:
                    browser.call("record", "stop", cleanup=True)
                    manifest["video"] = artifact(root, "video.webm")
                except (CaptureError, ValueError, OSError, KeyboardInterrupt) as exc:
                    manifest["limitations"].append(f"Video finalization failure: {type(exc).__name__}: {exc}")
            try:
                browser.call("close", cleanup=True)
            except (CaptureError, ValueError, OSError, KeyboardInterrupt) as exc:
                manifest["limitations"].append(f"Session cleanup failed ({session}); explicitly close this session: {type(exc).__name__}: {exc}")
                manifest["state"] = "failed"
    if manifest["video"] is not None:
        try:
            sample_video(commands, root, manifest, max_frames)
        except (CaptureError, ValueError, OSError, KeyboardInterrupt) as exc:
            manifest["limitations"].append(f"Frame extraction failure: {exc}")
    if (len(manifest["steps"]) == len(scenario["steps"]) and all(s["status"] == "passed" for s in manifest["steps"])
            and manifest["sampling"]["coverage"] == "complete"
            and not any("failure:" in x.lower() or "cleanup failed" in x.lower() for x in manifest["limitations"])):
        manifest["state"] = "passed"
    (root / "commands.json").write_bytes(canonical(commands.logs) + b"\n")
    manifest["artifacts"] = [artifact(root, path.relative_to(root).as_posix()) for path in sorted(root.rglob("*"))
                             if path.is_file() and "tmp" not in path.relative_to(root).parts]
    digest = seal_bundle(root, manifest)
    return manifest, digest


def replay(bundle, output, **kwargs):
    if Path(output).resolve().is_relative_to(Path(bundle).resolve()):
        raise ValueError("replay output must be disjoint from the source bundle")
    manifest, digest = load_bundle(bundle, require_success=False)
    source = Path(bundle) / manifest["scenario"]["path"]
    data = source.read_bytes()
    scenario = validate_scenario(parse_json(data))
    if hashlib.sha256(data).hexdigest() != manifest["scenario"]["sha256"]:
        raise ValueError("scenario changed during replay admission")
    return record(scenario, data, output, replay_of=digest, **kwargs)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("record", "replay"):
        child = sub.add_parser(name)
        child.add_argument("source", type=Path, help="operator scenario JSON" if name == "record" else "sealed bundle directory")
        child.add_argument("--output", required=True, type=Path, help="new directory; never reused")
        child.add_argument("--browser", default="agent-browser", help="installed 0.43.0+ executable")
        child.add_argument("--browser-skills-dir", type=Path, help="matching installed skill-data directory for standalone native binaries")
        child.add_argument("--seconds", type=int, default=300)
        child.add_argument("--command-seconds", type=int, default=30)
        child.add_argument("--max-frames", type=int, default=12)
    args = parser.parse_args(argv)
    options = {"executable": args.browser, "seconds": args.seconds, "command_seconds": args.command_seconds,
               "max_frames": args.max_frames, "browser_skills_dir": args.browser_skills_dir}
    try:
        if args.command == "replay":
            manifest, digest = replay(args.source, args.output, **options)
        else:
            raw = args.source.read_bytes()
            scenario = validate_scenario(parse_json(raw))
            manifest, digest = record(scenario, raw, args.output, **options)
        print(json.dumps({"state": manifest["state"], "bundle": str(args.output.resolve()), "bundle_sha256": digest}))
        return 0 if manifest["state"] == "passed" else 2
    except (ValueError, OSError, CaptureError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
