"""Rebuild docs/llms-full.txt: the README, the flow map and the bot techniques concatenated as plain markdown.

    py -3 scripts/media/llms_full.py [--brand brand/brand.json]
"""
import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import brandlib  # noqa: E402

ROOT = HERE.parent.parent


def build(root: Path, brand: dict) -> Path:
    refs = f"plugins/{brand['slug']}/skills/{brand['mainSkillName']}/references"
    files = ["README.md", f"{refs}/flows.md", f"{refs}/techniques/github-app.md", f"{refs}/techniques/pr-conversation.md",
             f"{refs}/techniques/issue-conversation.md"]
    repo = f"https://github.com/{brand['repo']}"
    parts = [f"# {brand['name']}: full docs\n\n> The key {brand['name']} docs concatenated as plain markdown. "
             f"Source: {repo}. Site: {brand['homepage']}\n"]
    for f in files:
        text = (root / f).read_text(encoding="utf-8").strip()
        parts.append(f"\n\n---\n\nSource: {repo}/blob/main/{f}\n\n{text}\n")
    out = root / "docs/llms-full.txt"
    out.write_text("".join(parts), encoding="utf-8", newline="\n")
    return out


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--brand", default=str(ROOT / "brand/brand.json"))
    print(build(ROOT, brandlib.load(parser.parse_args().brand)))
