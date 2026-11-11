#!/usr/bin/env python3
"""Structural checks for the skills in this repo. Prints OK or a list of problems and exits non-zero."""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAX_LINE_BYTES = 760  # omp read truncates lines at 768 characters
problems = []


def frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return None
    fields = {}
    for line in m.group(1).splitlines():
        if ":" in line and not line.startswith(" "):
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip().strip('"')
    return fields


for manifest in [ROOT / ".omp-plugin/marketplace.json", ROOT / ".claude-plugin/marketplace.json"]:
    try:
        catalog = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, ValueError) as err:
        problems.append(f"{manifest.relative_to(ROOT)}: {err}")
        continue
    for plugin in catalog.get("plugins", []):
        source = plugin.get("source")
        if isinstance(source, str) and not (ROOT / source).is_dir():
            problems.append(f"{manifest.relative_to(ROOT)}: plugin {plugin.get('name')} source {source} is missing")

for plugin_json in [*ROOT.glob("plugins/*/.claude-plugin/plugin.json"), *ROOT.glob("plugins/*/hooks/hooks.json")]:
    try:
        json.loads(plugin_json.read_text(encoding="utf-8"))
    except ValueError as err:
        problems.append(f"{plugin_json.relative_to(ROOT)}: {err}")

for skill_md in ROOT.glob("plugins/*/skills/*/SKILL.md"):
    fields = frontmatter(skill_md.read_text(encoding="utf-8"))
    rel = skill_md.relative_to(ROOT)
    if fields is None:
        problems.append(f"{rel}: missing frontmatter")
    elif not fields.get("name") or not fields.get("description"):
        problems.append(f"{rel}: frontmatter needs name and description")
    elif fields["name"] != skill_md.parent.name:
        problems.append(f"{rel}: name {fields['name']!r} does not match folder {skill_md.parent.name!r}")

for md in ROOT.rglob("*.md"):
    if {".git", ".scratch", ".worktrees"} & set(md.parts):
        continue
    rel = md.relative_to(ROOT)
    text = md.read_text(encoding="utf-8")
    for number, line in enumerate(text.splitlines(), 1):
        if len(line.encode("utf-8")) > MAX_LINE_BYTES:
            problems.append(f"{rel}:{number}: line is {len(line.encode('utf-8'))} bytes (max {MAX_LINE_BYTES})")
    skill_dir = next((p for p in md.parents if (p / "SKILL.md").is_file()), None)
    if skill_dir is None:
        continue
    sibling_skills = [p.parent for p in skill_dir.parent.glob("*/SKILL.md")]
    for link in re.findall(r"references/[\w\-/]+\.md", text):
        if not any((d / link).is_file() for d in [md.parent, skill_dir, *sibling_skills]):
            problems.append(f"{rel}: broken link {link}")
    for anchor in re.findall(r"[\w\-]+\.md#[\w\-]+", text):
        problems.append(f"{rel}: anchor link {anchor} (omp can't read anchors; link the file)")

if problems:
    print("\n".join(problems))
    sys.exit(1)
print("OK")
