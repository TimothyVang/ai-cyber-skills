"""Strict, dependency-free recording bundle boundary shared by all consumers."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urlsplit

MAX_JSON_BYTES = 4 * 1024 * 1024
HEX = re.compile(r"[0-9a-f]{64}\Z")
ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}\Z")
RESERVED_NAMES = frozenset({"CON", "PRN", "AUX", "NUL", *[f"COM{i}" for i in range(10)],
                            *[f"LPT{i}" for i in range(10)]})


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                      allow_nan=False).encode("utf-8")


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def parse_json(data):
    if len(data) > MAX_JSON_BYTES:
        raise ValueError("JSON exceeds 4 MiB")
    return json.loads(data.decode("utf-8"), object_pairs_hook=_pairs,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))


def read_json(path):
    try:
        with Path(path).open("rb") as handle:
            data = handle.read(MAX_JSON_BYTES + 1)
        return parse_json(data)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read JSON {path}: {exc}") from exc


def require(condition, message):
    if not condition:
        raise ValueError(message)


def integer(value, minimum, maximum):
    return type(value) is int and minimum <= value <= maximum


def text(value, limit=8192):
    return isinstance(value, str) and 0 < len(value) <= limit and "\0" not in value


def origin(url):
    require(text(url), "URL must be nonempty text")
    try:
        parts = urlsplit(url)
        port = parts.port
    except ValueError as exc:
        raise ValueError("invalid URL") from exc
    require(parts.scheme in ("http", "https") and parts.hostname and not parts.username
            and not parts.password and not any(c.isspace() for c in url) and "\\" not in url,
            "only credential-free HTTP(S) URLs are allowed")
    host = parts.hostname.lower()
    require(re.fullmatch(r"[a-z0-9.-]+", host) is not None, "use an ASCII DNS name or IPv4 host")
    return f"{parts.scheme}://{host}" + (f":{port}" if port and port != (443 if parts.scheme == "https" else 80) else "")


def validate_scenario(value):
    require(isinstance(value, dict), "scenario must be an object")
    require(set(value) <= {"schema_version", "intent", "allowed_origins", "steps"}, "unknown scenario fields")
    require(type(value.get("schema_version")) is int and value["schema_version"] == 1, "scenario version must be 1")
    require(text(value.get("intent"), 32768), "operator intent is required verbatim")
    origins = value.get("allowed_origins")
    require(isinstance(origins, list) and 1 <= len(origins) <= 20, "allow 1..20 explicit origins")
    require(all(isinstance(item, str) and origin(item) == item for item in origins), "origins must be canonical, without paths")
    require(len(set(origins)) == len(origins), "duplicate origins")
    steps = value.get("steps")
    require(isinstance(steps, list) and 1 <= len(steps) <= 40, "scenario needs 1..40 steps")
    ids = set()
    for step in steps:
        require(isinstance(step, dict) and set(step) == {"id", "action", "expected"}, "invalid step fields")
        sid = step["id"]
        require(isinstance(sid, str) and ID.fullmatch(sid) and sid.casefold() not in ids
                and sid.upper() not in RESERVED_NAMES, "invalid, reserved, or repeated step id")
        ids.add(sid.casefold())
        action = step["action"]
        require(isinstance(action, dict), "action must be an object")
        kind = action.get("type")
        require(isinstance(kind, str), "action type must be text")
        fields = {"open": {"url"}, "click": {"selector"}, "fill": {"selector", "text"},
                  "check": {"selector"}, "uncheck": {"selector"}, "press": {"key"},
                  "wait": {"selector"}, "pause": {"ms"}, "scroll": {"direction", "pixels"}}
        require(kind in fields and set(action) == fields[kind] | {"type"}, "unsupported action or fields")
        for key in fields[kind] - {"ms", "pixels"}:
            require(text(action[key]) or (key == "text" and action[key] == ""), f"invalid {key}")
            require(not action[key].startswith("-"), f"option-like {key} is not allowed")
        if "selector" in action:
            require(not action["selector"].startswith("@"), "replay needs stable selectors, not transient snapshot refs")
        if kind == "open":
            require(origin(action["url"]) in origins, "navigation origin is not allowlisted")
        if kind == "pause":
            require(integer(action["ms"], 1, 5000), "pause must be 1..5000 ms")
        if kind == "scroll":
            require(action["direction"] in ("up", "down", "left", "right") and integer(action["pixels"], 1, 2000), "invalid scroll")
        expected = step["expected"]
        require(isinstance(expected, dict) and expected and set(expected) <= {"url", "text", "state"}, "expectations are required")
        count = 0
        if "url" in expected:
            require(origin(expected["url"]) in origins, "expected URL is not allowlisted")
            count += 1
        for key in ("text", "state"):
            if key not in expected:
                continue
            entries = expected[key]
            require(isinstance(entries, list) and 1 <= len(entries) <= 8, "expectation list needs 1..8 entries")
            for item in entries:
                require(isinstance(item, dict) and text(item.get("selector")), "expectation selector required")
                require(not item["selector"].startswith(("-", "@")), "expectation needs a stable selector")
                if key == "text":
                    require(set(item) in ({"selector", "equals"}, {"selector", "contains"}), "invalid text expectation")
                    term = item.get("equals", item.get("contains"))
                    require(isinstance(term, str) and len(term) <= 8192 and "\0" not in term, "invalid expected text")
                else:
                    require(set(item) == {"selector", "property", "equals"} and item["property"] in ("visible", "enabled", "checked")
                            and type(item["equals"]) is bool, "invalid state expectation")
                count += 1
        require(count > 0, "at least one assertion required")
    require(steps[0]["action"]["type"] == "open", "first step must open an allowlisted URL")
    return value


def assertion_specs(expected):
    specs = []
    if "url" in expected:
        specs.append({"kind": "url", "equals": expected["url"]})
    for kind in ("text", "state"):
        specs.extend({"kind": kind, **item} for item in expected.get(kind, []))
    return specs


def assertion_passes(spec, actual):
    if spec["kind"] == "state":
        return type(actual) is bool and actual is spec["equals"]
    if not isinstance(actual, str):
        return False
    return spec["contains"] in actual if "contains" in spec else actual == spec["equals"]


def contained_path(directory, relative):
    require(isinstance(relative, str) and relative and "\\" not in relative and ":" not in relative,
            "artifact path must be a literal relative POSIX path")
    parts = relative.split("/")
    require(all(part not in ("", ".", "..") and not part.endswith((".", " "))
                and not any(ord(c) < 32 or c in '<>\"|?*#%' for c in part) for part in parts), "unsafe artifact path")
    require(not any(part.split(".")[0].upper() in RESERVED_NAMES for part in parts), "reserved artifact path")
    root = Path(directory).resolve()
    path = root
    for part in parts:
        path = path / part
        require(not path.is_symlink() and not getattr(path, "is_junction", lambda: False)(), "linked artifact paths are forbidden")
    require(path.resolve().is_relative_to(root) and path.is_file(), "artifact is missing or escapes bundle")
    return path


def artifact(directory, relative):
    path = contained_path(directory, relative)
    return {"path": relative, "sha256": sha256(path)}


def seal_bundle(directory, manifest):
    """Create once; never overwrite or reseal an existing recording."""
    root = Path(directory)
    payload = canonical(manifest)
    digest = hashlib.sha256(payload).hexdigest()
    with (root / "manifest.json").open("xb") as handle:
        handle.write(payload + b"\n")
    with (root / "manifest.sha256").open("x", encoding="ascii") as handle:
        handle.write(digest + "\n")
    return digest


def load_bundle(directory, *, require_success=True):
    try:
        return _load_bundle(directory, require_success=require_success)
    except (OSError, TypeError, KeyError, OverflowError, RecursionError) as exc:
        raise ValueError(f"invalid evidence bundle: {exc}") from exc


def _load_bundle(directory, *, require_success):
    root = Path(directory).resolve()
    manifest = read_json(contained_path(root, "manifest.json"))
    require(isinstance(manifest, dict), "manifest must be an object")
    digest = hashlib.sha256(canonical(manifest)).hexdigest()
    seal = contained_path(root, "manifest.sha256").read_text(encoding="ascii").strip()
    require(seal == digest, "manifest seal mismatch")
    require(type(manifest.get("schema_version")) is int and manifest["schema_version"] == 1, "unsupported manifest schema")
    require(manifest.get("state") in ("passed", "failed", "unavailable"), "invalid capture state")
    require(isinstance(manifest.get("limitations"), list) and all(isinstance(x, str) for x in manifest["limitations"]), "limitations required")
    seen = {}

    def check(item, *, nullable=False, png=False):
        if nullable and item is None:
            return None
        require(isinstance(item, dict) and set(item) == {"path", "sha256"}, "invalid artifact descriptor")
        require(isinstance(item["sha256"], str) and HEX.fullmatch(item["sha256"]), "invalid artifact digest")
        path = contained_path(root, item["path"])
        folded = item["path"].casefold()
        require(folded not in seen or seen[folded] == item, "aliased artifact path")
        seen[folded] = item
        require(sha256(path) == item["sha256"], f"artifact hash mismatch: {item['path']}")
        if png:
            with path.open("rb") as handle:
                require(handle.read(8) == b"\x89PNG\r\n\x1a\n", "screenshot/frame is not PNG")
        return path

    scenario_path = check(manifest.get("scenario"))
    scenario = validate_scenario(read_json(scenario_path))
    require(manifest.get("intent") == scenario["intent"], "intent differs from pinned scenario")
    tool = manifest.get("capture_tool")
    require(isinstance(tool, dict) and isinstance(tool.get("sha256"), str) and HEX.fullmatch(tool["sha256"])
            and text(tool.get("browser_version")), "capture tool provenance required")
    if "source" in tool:
        check(tool["source"])
        require(tool["source"]["sha256"] == tool["sha256"], "capture source hash mismatch")
    for item in manifest.get("artifacts", []):
        check(item)
    state = manifest["state"]
    target = manifest.get("recorded_target_id")
    require(target is None or text(target, 256), "invalid recorded tab identity")
    steps = manifest.get("steps")
    require(isinstance(steps, list) and len(steps) <= len(scenario["steps"]), "invalid recorded steps")
    last_end = 0
    for step, original in zip(steps, scenario["steps"]):
        require(isinstance(step, dict) and all(step.get(k) == original[k] for k in ("id", "action", "expected")), "step differs from pinned scenario")
        require(step.get("status") in ("passed", "failed"), "invalid step status")
        require(integer(step.get("started_ms"), last_end, 3_600_000)
                and integer(step.get("ended_ms"), step["started_ms"], 3_600_000), "invalid step timing")
        last_end = step["ended_ms"]
        complete = step["status"] == "passed"
        check(step.get("screenshot"), nullable=not complete, png=True)
        check(step.get("snapshot"), nullable=not complete)
        obs = step.get("observations")
        require(isinstance(obs, dict), "step observations required")
        if complete:
            require(text(target, 256) and obs.get("target_id") == target, "step differs from recorded tab")
            require(not obs.get("errors") and origin(obs.get("url")) in scenario["allowed_origins"], "passed step has errors or disallowed URL")
            assertions = obs.get("assertions")
            specs = assertion_specs(original["expected"])
            require(isinstance(assertions, list) and len(assertions) == len(specs), "incomplete assertions")
            for row, spec in zip(assertions, specs):
                require(isinstance(row, dict) and row.get("expected") == spec and row.get("passed") is True
                        and assertion_passes(spec, row.get("actual")), "passed step contains a failed assertion")
    video = check(manifest.get("video"), nullable=state != "passed")
    if video is not None:
        require(video.stat().st_size > 0, "empty video")
    frames = manifest.get("frames")
    sampling = manifest.get("sampling")
    require(isinstance(frames, list) and len(frames) <= 60 and isinstance(sampling, dict), "invalid timeline")
    require(sampling.get("method") == "uniform" and sampling.get("coverage") in ("complete", "incomplete"), "invalid sampling method")
    require(integer(sampling.get("interval_ms"), 1, 3_600_000) and integer(sampling.get("duration_ms"), 0, 3_600_000)
            and integer(sampling.get("max_frames"), 1, 60), "invalid sampling bounds")
    times = []
    for frame in frames:
        require(isinstance(frame, dict) and integer(frame.get("at_ms"), 0, sampling["duration_ms"]), "invalid frame timestamp")
        check(frame.get("image"), png=True)
        times.append(frame["at_ms"])
    require(times == sorted(set(times)) and len(times) <= sampling["max_frames"], "duplicate or excessive frames")
    if sampling["coverage"] == "complete":
        planned_count = (sampling["duration_ms"] + sampling["interval_ms"] - 1) // sampling["interval_ms"]
        require(planned_count <= sampling["max_frames"], "sampling schedule exceeds frame cap")
        require(video is not None and sampling["duration_ms"] > 0 and times == list(range(0, sampling["duration_ms"], sampling["interval_ms"])), "incomplete timeline sampling")
    if state == "passed":
        require(len(steps) == len(scenario["steps"]) and all(s["status"] == "passed" for s in steps)
                and sampling["coverage"] == "complete" and frames, "passed bundle is incomplete")
    if require_success:
        require(state == "passed", f"capture did not pass: {state}")
    return manifest, digest
