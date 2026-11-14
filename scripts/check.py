#!/usr/bin/env python3
"""Structural checks for the skills in this repo. Prints OK or a list of problems and exits non-zero."""
import ast
import datetime as dt
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAX_LINE_BYTES = 760  # omp read truncates lines at 768 characters
BANNED = re.compile(
    r"(?<![a-z0-9])[pr]stack(?![a-z0-9])|poteto|lauren\s+tan|cursor/plugins|pocock|ras\s*mic"
    r"|cloud\s*x\s*berry|greptile|code\s*rabbit|james\s+clements",
    re.I,
)
# Source citations retain real third-party identities; they are not this product's branding.
WHITE_LABEL_EXEMPT = {
    Path("scripts/check.py"), Path("trending"), Path("evals/workflows"),
    Path("plugins/deepmodebot/skills/deepmodebot/assets/repo-references.json"),
    Path("docs/research/youtube-learning/history-recovery.md"),
}
LOCAL_ONLY = {".git", ".scratch", ".worktrees", "__pycache__"}  # self-ignored work folders and caches, never shipped
RULES_WINDOW_BYTES = 20_000  # about 5,000 tokens at 4 bytes each: what Claude Code keeps of a skill after compaction
CORE_LINE_BYTES = 600  # deepmodebot's SKILL.md, playbooks and techniques: one instruction per line
# Reference skills hold cited facts that go stale; each SKILL.md states the date they were true as of.
LIBRARY_SKILLS = ("agent-harnesses", "cloud-devsecops", "domain-rules", "frontend-ui", "secrets-and-auth",
                  "software-architecture")
STALE_AFTER_DAYS = 120
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
    if LOCAL_ONLY & set(md.relative_to(ROOT).parts):
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

for path in ROOT.rglob("*"):
    rel = path.relative_to(ROOT)
    if not path.is_file() or LOCAL_ONLY & set(rel.parts) or rel.name.upper().startswith(("LICENSE", "NOTICE")):
        continue
    if any(rel == exempt or exempt in rel.parents for exempt in WHITE_LABEL_EXEMPT):
        continue
    text = path.read_bytes().decode("utf-8", errors="ignore")
    for number, line in enumerate(text.splitlines(), 1):
        for match in BANNED.finditer(line):
            problems.append(f"{rel}:{number}: banned name {match.group(0)!r}")
    if BANNED.search(str(rel)):
        problems.append(f"{rel}: banned name in path")

skill_root = ROOT / "plugins/deepmodebot/skills/deepmodebot"

# README counts must match the folders.
counts = re.search(r"(\d+) playbooks, (\d+) principles and (\d+) techniques", (ROOT / "README.md").read_text(encoding="utf-8"))
actual = tuple(len(list((skill_root / "references" / kind).glob("*.md"))) for kind in ("playbooks", "principles", "techniques"))
if not counts or tuple(map(int, counts.groups())) != actual:
    problems.append(f"README.md: says {counts.groups() if counts else 'no'} playbooks, principles, techniques; the folders hold {actual}")

# Process files: every playbook and technique says when it is done, and core lines stay one instruction long.
for kind in ("playbooks", "techniques"):
    for md in sorted((skill_root / "references" / kind).glob("*.md")):
        if "Done when" not in md.read_text(encoding="utf-8"):
            problems.append(f"{md.relative_to(ROOT)}: no 'Done when' completion criterion")
for md in [skill_root / "SKILL.md", *(skill_root / "references").glob("playbooks/*.md"),
           *(skill_root / "references").glob("techniques/*.md")]:
    text = md.read_text(encoding="utf-8")
    body_start = text.find("\n---\n", 4) + 5 if text.startswith("---\n") else 0  # the frontmatter hook is one line
    for number, line in enumerate(text[body_start:].splitlines(), text[:body_start].count("\n") + 1):
        if len(line.encode("utf-8")) > CORE_LINE_BYTES:
            problems.append(f"{md.relative_to(ROOT)}:{number}: line is {len(line.encode('utf-8'))} bytes "
                            f"(max {CORE_LINE_BYTES} in core files; split it)")

# Library skills carry the date their facts were checked; an old one is reported, not failed.
for name in LIBRARY_SKILLS:
    head = (ROOT / "plugins/deepmodebot/skills" / name / "SKILL.md").read_text(encoding="utf-8").split("\n---\n", 1)[0]
    stamp = re.search(r'^\s+as-of:\s*"?(\d{4}-\d{2}-\d{2})"?\s*$', head, re.M)
    if not stamp:
        problems.append(f"plugins/deepmodebot/skills/{name}/SKILL.md: frontmatter needs metadata.as-of: YYYY-MM-DD")
    elif (dt.date.today() - dt.date.fromisoformat(stamp.group(1))).days > STALE_AFTER_DAYS:
        print(f"note: {name} facts are as of {stamp.group(1)}, over {STALE_AFTER_DAYS} days old; recheck and restamp")

# docs/llms-full.txt embeds whole files; each embedded copy must match its source. --fix rewrites it.
llms = ROOT / "docs/llms-full.txt"
blob_base = "https://github.com/TimothyVang/deepmodebot/blob/main/"
pieces = re.split(r"\n\n---\n\nSource: (\S+)\n\n", llms.read_text(encoding="utf-8"))
fresh = pieces[0] + "".join(
    f"\n\n---\n\nSource: {url}\n\n" + (ROOT / url.removeprefix(blob_base)).read_text(encoding="utf-8") for url in pieces[1::2])
if fresh != llms.read_text(encoding="utf-8"):
    if "--fix" in sys.argv:
        llms.write_text(fresh, encoding="utf-8", newline="\n")
        print("fixed: docs/llms-full.txt")
    else:
        problems.append("docs/llms-full.txt: embedded files are stale; run `python scripts/check.py --fix`")

# SKILL.md puts the rules that must survive compaction first; the lookup tables start at "## Routes".
skill_bytes = (skill_root / "SKILL.md").read_bytes()
window = skill_bytes.find(b"\n## Routes\n")
if window < 0 or window > RULES_WINDOW_BYTES:
    problems.append(f"plugins/deepmodebot/skills/deepmodebot/SKILL.md: '## Routes' starts at byte {window}; the rules before it must fit in {RULES_WINDOW_BYTES} bytes")

# Every skill's own references and skill:// links resolve (check_skill.py, the per-skill checker).
skill_dirs = sorted(str(p.parent) for p in ROOT.glob("plugins/*/skills/*/SKILL.md"))
run = subprocess.run([sys.executable, str(skill_root / "scripts/check_skill.py"), *skill_dirs],
                     capture_output=True, text=True, encoding="utf-8", errors="replace")
if run.returncode:
    problems.append(f"check_skill.py found problems:\n{(run.stdout + run.stderr).strip()[-3000:]}")

# Every shipped Python file parses, and every test folder passes.
test_dirs = set()
for py in ROOT.rglob("*.py"):
    if LOCAL_ONLY & set(py.relative_to(ROOT).parts):
        continue
    try:
        ast.parse(py.read_text(encoding="utf-8"), filename=str(py))
    except SyntaxError as err:
        problems.append(f"{py.relative_to(ROOT)}:{err.lineno}: {err.msg}")
    if py.name.startswith("test_"):
        test_dirs.add(py.parent)
for test_dir in sorted(test_dirs):
    run = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", str(test_dir), "-p", "test_*.py"],
                         capture_output=True, text=True, encoding="utf-8", errors="replace")
    if run.returncode:
        problems.append(f"{test_dir.relative_to(ROOT)}: tests failed\n{run.stderr[-3000:]}")
    elif "skipped" in run.stderr.splitlines()[-1]:
        print(f"note: {test_dir.relative_to(ROOT)}: {run.stderr.splitlines()[-1]} ({'bun' if shutil.which('bun') else 'no bun'} on PATH)")

if problems:
    print("\n".join(problems))
    sys.exit(1)
print("OK")
