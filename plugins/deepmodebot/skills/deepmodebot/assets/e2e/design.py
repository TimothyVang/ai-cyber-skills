#!/usr/bin/env python3
"""Export a verified recording as an editable, offline workflow evidence index."""
from __future__ import annotations

import argparse
import base64
import hashlib
import html
import json
from pathlib import Path
import shutil
import textwrap
import xml.etree.ElementTree as ET

from evidence import load_bundle

SVG = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG)


def _text(value: object) -> str:
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, sort_keys=True)
    return "".join(c if c in "\t\n\r" or 32 <= ord(c) <= 0xD7FF or 0xE000 <= ord(c) <= 0xFFFD
                   or 0x10000 <= ord(c) <= 0x10FFFF else f"\\u{ord(c):04x}" for c in text)


def _brief(value: object, limit: int = 170) -> str:
    text = " ".join(_text(value).split())
    return text if len(text) <= limit else text[:limit - 3] + "..."


def _mermaid(value: object) -> str:
    return "".join(c if c.isascii() and (c.isalnum() or c == " ") else f"#{ord(c)};"
                   for c in _brief(value))


def _svg(manifest: dict, digest: str, links: list[dict], assets: Path) -> str:
    intent = textwrap.wrap("Intent: " + _text(manifest["intent"]), width=95) or ["Intent:"]
    top = 140 + 22 * len(intent)
    height = top + 380 * len(manifest["steps"]) + 60
    root = ET.Element(f"{{{SVG}}}svg", {"width": "1080", "height": str(height),
                                     "viewBox": f"0 0 1080 {height}", "role": "img"})
    ET.SubElement(root, "title").text = "Recorded workflow evidence index"
    ET.SubElement(root, "desc").text = (
        "Observed recorder results, not a prospective design or a Penpot-authored file. "
        "Cards contain abbreviated previews; index.html preserves full intent and observations.")
    ET.SubElement(root, "rect", {"width": "1080", "height": str(height), "fill": "#f5f7fa"})

    def text(parent: ET.Element, x: int, y: int, value: object, size: int = 16,
             color: str = "#243247") -> None:
        ET.SubElement(parent, "text", {"x": str(x), "y": str(y), "font-family": "sans-serif",
                                     "font-size": str(size), "fill": color}).text = _text(value)

    text(root, 48, 44, "Recorded workflow", 28)
    text(root, 48, 72, f"Recorder state: {manifest['state']} | Evidence index, not a design proposal")
    text(root, 48, 99, f"Bundle SHA-256: {digest}", 13)
    for row, line in enumerate(intent):
        text(root, 48, 130 + row * 22, line)
    for index, (step, artifacts) in enumerate(zip(manifest["steps"], links)):
        y = top + index * 380
        group = ET.SubElement(root, "g", {"id": f"step-{index + 1}"})
        ET.SubElement(group, "rect", {"x": "48", "y": str(y), "width": "984", "height": "350",
                                     "rx": "8", "fill": "#ffffff", "stroke": "#8290a3"})
        text(group, 68, y + 30, f"{index + 1}. {_brief(step['id'], 70)} | {step['status']}", 20)
        row = y + 59
        for label, value in (("Action", step["action"]), ("Expected", step["expected"]),
                             ("Recorded observation", step.get("observations", {}))):
            for line in textwrap.wrap(f"{label}: {_brief(value)}", width=48):
                text(group, 68, row, line, 14)
                row += 19
            row += 6
        text(group, 68, y + 312, f"Recorded interval: {step['started_ms']} to {step['ended_ms']} ms", 14)
        anchor = ET.SubElement(group, "a", {"href": f"index.html#step-{index + 1}"})
        text(anchor, 68, y + 336, "Full observation and evidence", 16, "#174ea6")
        if artifacts.get("screenshot"):
            image = base64.b64encode((assets / artifacts["screenshot"]).read_bytes()).decode("ascii")
            text(group, 548, y + 57, "Observed screenshot", 14)
            ET.SubElement(group, "image", {"x": "548", "y": str(y + 68), "width": "464", "height": "261",
                                         "preserveAspectRatio": "xMidYMid meet", "href": "data:image/png;base64," + image})
        else:
            text(group, 548, y + 80, "Screenshot unavailable", 16, "#8b241c")
        if index + 1 < len(links):
            ET.SubElement(root, "path", {"d": f"M 540 {y + 350} v 24 m -5 -6 l 5 6 l 5 -6",
                                         "stroke": "#53647c", "fill": "none", "stroke-width": "2"})
    text(root, 48, height - 20, "Previews abbreviated. Arrows show recording order, not proven causality.", 14)
    return ET.tostring(root, encoding="unicode", xml_declaration=False) + "\n"


def _mmd(manifest: dict) -> str:
    lines = ["flowchart TD", "  accTitle: Recorded workflow evidence index",
             "  accDescr: Recording order, not a prospective design or proof of causality.",
             f'  intent["Intent: {_mermaid(manifest["intent"])}"]']
    for index, step in enumerate(manifest["steps"], 1):
        label = f"{index}. {step['id']} | {step['status']} | Action: {_brief(step['action'], 60)}"
        lines.append(f'  step{index}["{_mermaid(label)}"]')
        lines.append(f"  {'intent' if index == 1 else 'step' + str(index - 1)} --> step{index}")
        lines.append(f'  click step{index} "index.html#step-{index}" "Full recorded evidence"')
    return "\n".join(lines) + "\n"


def _index(manifest: dict, digest: str, links: list[dict], video: str | None,
           frames: list[dict]) -> str:
    esc = lambda value: html.escape(_text(value), quote=True)
    parts = ["<!doctype html><html lang=\"en\"><meta charset=\"utf-8\">",
             '<meta name="viewport" content="width=device-width,initial-scale=1">',
             '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; '
             'img-src \'self\'; media-src \'self\'; style-src \'unsafe-inline\'; base-uri \'none\'">',
             "<title>Recorded workflow evidence</title><style>",
             "body{font:17px/1.5 system-ui,sans-serif;color:#243247;background:#f5f7fa;"
             "max-width:1080px;margin:auto;padding:24px}a{color:#174ea6}"
             "section{background:white;border:1px solid #8290a3;margin:24px 0;padding:24px}"
             "pre{white-space:pre-wrap;overflow-wrap:anywhere}img,video{max-width:100%;height:auto}"
             "a:focus-visible{outline:3px solid #174ea6}code{overflow-wrap:anywhere}",
             "</style><main><h1>Recorded workflow evidence</h1>",
             "<p>This is an index of recorder observations, not a prospective design, "
             "independent acceptance, or proof that Penpot imported anything.</p>",
             f"<p>Recorder state: <strong>{esc(manifest['state'])}</strong></p>",
             f"<p>Source bundle SHA-256: <code>{digest}</code></p>",
             f"<h2>Original user intent</h2><pre>{esc(manifest['intent'])}</pre>",
             '<p><a href="workflow.svg">Editable SVG</a> | <a href="workflow.mmd">Mermaid source</a> | '
             '<a href="design.json">Export provenance and hashes</a></p>',
             f"<h2>Capture limitations</h2><pre>{esc(manifest.get('limitations', []))}</pre>",
             f"<h2>Frame sampling</h2><pre>{esc(manifest.get('sampling', {}))}</pre>"]
    if video:
        parts.append(f'<h2>Recorded video</h2><video controls preload="metadata" src="{video}"></video>'
                     f'<p><a href="{video}">Original video bytes</a></p>')
    else:
        parts.append("<p>Video unavailable in the source capture.</p>")
    for index, (step, artifacts) in enumerate(zip(manifest["steps"], links), 1):
        parts.append(f'<section id="step-{index}"><h2>{index}. {esc(step["id"])} '
                     f'({esc(step["status"])})</h2>')
        for label, field in (("Operator action", "action"), ("Operator expectation", "expected"),
                             ("Actual recorder observations", "observations")):
            parts.append(f"<h3>{label}</h3><pre>{esc(step.get(field, {}))}</pre>")
        parts.append(f'<p>Recorded interval: {esc(step["started_ms"])} to {esc(step["ended_ms"])} ms.</p>')
        if artifacts.get("screenshot"):
            path = artifacts["screenshot"]
            parts.append(f'<a href="{path}"><img loading="lazy" src="{path}" '
                         f'alt="Recorded screenshot for step {index}"></a>')
        else:
            parts.append("<p>Screenshot unavailable. This step has incomplete visual evidence.</p>")
        if artifacts.get("snapshot"):
            parts.append(f'<p><a href="{artifacts["snapshot"]}">Recorded textual snapshot</a></p>')
        parts.append("</section>")
    parts.append("<h2>Sampled video frames</h2><p>Samples are not continuous semantic video review.</p>")
    for frame in frames:
        parts.append(f'<figure><a href="{frame["path"]}"><img loading="lazy" '
                     f'src="{frame["path"]}" alt="Video frame at {esc(frame["at_ms"])} ms"></a>'
                     f'<figcaption>{esc(frame["at_ms"])} ms</figcaption></figure>')
    parts.append("</main></html>\n")
    return "\n".join(parts)


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def export_bundle(directory: Path | str, output: Path | str) -> dict:
    """Copy verified media unchanged into a new, disjoint, portable export directory."""
    source, target = Path(directory).resolve(), Path(output).resolve()
    if source == target or source in target.parents or target in source.parents:
        raise ValueError("design output must be outside and disjoint from the source bundle")
    if target.exists():
        raise ValueError("design output must be a new directory")
    manifest, digest = load_bundle(source, require_success=False)
    target.mkdir(parents=True, exist_ok=False)
    try:
        (target / "assets").mkdir()
        copies: dict[str, dict] = {}

        def copy(artifact: dict | None, kind: str) -> str | None:
            if artifact is None:
                return None
            suffix = Path(artifact["path"]).suffix.lower()
            if kind == "image" and suffix not in {".png", ".jpg", ".jpeg", ".webp"}:
                raise ValueError("design images must be inert raster artifacts")
            if kind == "video" and suffix not in {".webm", ".mp4"}:
                raise ValueError("design video must be webm or mp4")
            if kind == "snapshot":
                suffix = ".txt"
            relative = f"assets/{artifact['sha256']}{suffix}"
            original = (source / artifact["path"]).resolve()
            if source not in original.parents:
                raise ValueError("source artifact escapes bundle")
            if relative not in copies:
                shutil.copyfile(original, target / relative)
                if _sha(target / relative) != artifact["sha256"]:
                    raise ValueError("source artifact changed during export")
                copies[relative] = {"path": relative, "sha256": artifact["sha256"]}
            return relative

        links = [{"screenshot": copy(step.get("screenshot"), "image"),
                  "snapshot": copy(step.get("snapshot"), "snapshot")} for step in manifest["steps"]]
        video = copy(manifest.get("video"), "video")
        frames = [{"at_ms": frame["at_ms"], "path": copy(frame["image"], "image")}
                  for frame in manifest.get("frames", [])]
        outputs = {"workflow.svg": _svg(manifest, digest, links, target), "workflow.mmd": _mmd(manifest),
                   "index.html": _index(manifest, digest, links, video, frames)}
        for name, content in outputs.items():
            (target / name).write_text(content, encoding="utf-8", newline="\n")
        _, after = load_bundle(source, require_success=False)
        if after != digest:
            raise ValueError("source bundle changed during export")
        report = {"schema_version": 1, "kind": "recorded-workflow-index",
                  "source_bundle_sha256": digest, "source_state": manifest["state"],
                  "intent": manifest["intent"], "penpot_import": "not-attempted",
                  "steps": [{"id": step["id"], "index": f"index.html#step-{i}", **link}
                            for i, (step, link) in enumerate(zip(manifest["steps"], links), 1)],
                  "artifacts": [*copies.values(), *({"path": name, "sha256": _sha(target / name)}
                                                   for name in outputs)],
                  "limitations": ["Diagram previews are abbreviated; index.html retains full text.",
                                  "Diagram arrows show recorded order, not proven causality.",
                                  "SVG links and Mermaid click links depend on the importing renderer.",
                                  "No Penpot creation, import, round-trip, or visual acceptance is claimed."]}
        (target / "design.json").write_text(json.dumps(report, indent=2, ensure_ascii=True) + "\n",
                                            encoding="utf-8")
        return report
    except BaseException:
        shutil.rmtree(target)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    try:
        report = export_bundle(args.bundle, args.out)
    except (ValueError, OSError) as exc:
        parser.exit(2, f"design export failed: {exc}\n")
    print(json.dumps({"output": str(args.out), "source_bundle_sha256": report["source_bundle_sha256"],
                      "kind": report["kind"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
