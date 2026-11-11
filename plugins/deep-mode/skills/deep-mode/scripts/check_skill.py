"""Validate a skill folder: frontmatter, referenced files, and skill:// links.

Usage: python check_skill.py <skill dir> [<skill dir> ...]
Exits 1 and lists every problem when any check fails.
"""

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

REF = re.compile(r"(?<![\w/])((?:references|scripts)/[\w./-]+\.(?:md|py|sh|json|txt))")
LINK = re.compile(r"skill://([\w-]+(?:/[\w-]+)?)(?![\w<-])")


def installed_skills(skill_dir: Path) -> dict[str, Path]:
    found = {p.parent.name: p.parent for p in skill_dir.parent.glob("*/SKILL.md")}
    omp = shutil.which("omp")
    if omp:
        try:
            out = subprocess.run([omp, "skill", "list", "--json"], capture_output=True, text=True, timeout=60).stdout
            data = json.loads(out)
            for skill in data if isinstance(data, list) else data.get("skills", []):
                path = skill.get("path") or skill.get("filePath") or ""
                found.setdefault(skill["name"], Path(path).parent if path else Path())
        except (OSError, ValueError, subprocess.SubprocessError):
            pass
    return found


def check(skill_dir: Path, skills: dict[str, Path]) -> list[str]:
    problems = []
    entry = skill_dir / "SKILL.md"
    if not entry.exists():
        return [f"{skill_dir}: no SKILL.md"]
    text = entry.read_text(encoding="utf-8")
    head = text.split("---", 2) if text.startswith("---") else []
    if len(head) < 3 or not re.search(r"^name:[ \t]*\S", head[1], re.M) or not re.search(r"^description:[ \t]*\S", head[1], re.M):
        problems.append(f"{entry}: frontmatter needs name and description")
    for doc in sorted(skill_dir.rglob("*.md")):
        for n, line in enumerate(doc.read_text(encoding="utf-8").splitlines(), 1):
            links = LINK.findall(line)
            for link in links:
                if link.split("/")[0] not in skills:
                    problems.append(f"{doc.relative_to(skill_dir)}:{n}: skill://{link} is not installed")
            for ref in REF.findall(line):
                # A path resolves from the skill root, the citing file's folder, or a skill named on the line.
                roots = [skill_dir, doc.parent] + [skills[l.split("/")[0]] for l in links if l.split("/")[0] in skills]
                if any((root / ref).exists() for root in roots):
                    continue
                # scripts/<name> may be where a skill copies a shipped asset into the user's repo.
                if ref.startswith("scripts/") and any(skill_dir.parent.rglob(Path(ref).name)):
                    continue
                problems.append(f"{doc.relative_to(skill_dir)}:{n}: {ref} does not exist")
    return problems


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    problems = []
    for arg in sys.argv[1:]:
        skill_dir = Path(arg).expanduser().resolve()
        problems += check(skill_dir, installed_skills(skill_dir))
    for problem in problems:
        print(problem)
    print("ok" if not problems else f"{len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
