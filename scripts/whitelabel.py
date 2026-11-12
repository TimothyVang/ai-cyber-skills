#!/usr/bin/env python3
"""Build a complete white-label copy of this repo under another brand.

    py -3 scripts/whitelabel.py --brand brand/examples/acme.json --out ../acme-review

The source brand is `brand/brand.json`. The build copies every file, replaces the source brand's names with
the new brand's (longest token first) in text and in paths, rethemes the site, re-renders the images, and
rewrites the plugin, marketplace, bot and SEO metadata. LICENSE and NOTICE files keep their bytes; the root
LICENSE and NOTICE.md get the new brand's copyright line appended. A last pass fails the build if any source
name is left anywhere outside LICENSE* and NOTICE*, then runs the copy's own scripts/check.py.

Re-running into the same --out rebuilds it from scratch, so the result is the same each time. Needs Python 3.10+,
Pillow, and agg and gifski on PATH for the images.
"""
import argparse
import datetime
import html
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts/media"))
import brandlib  # noqa: E402
from brandlib import BrandError  # noqa: E402

PROSE = {".md", ".html", ".txt"}
SKIP_DIRS = {".git", "__pycache__", ".scratch", ".worktrees", "node_modules"}
OWN_RUN_CLAIM = re.compile(r"pull/19\b|pr-19-thread|PR #19\b|PR 19\b")
OWN_RUN_FILES = {".md", ".html", ".txt", ".json", ".xml", ".svg"}
# The upstream's own artifacts: the capture of its real PR thread, the script that composes it, and the
# screenshots of its site in the rebrand guide. A branded copy drops them.
UPSTREAM_ONLY = ("docs/images/pr-19-thread.gif", "scripts/media/pr19_thread.py", "docs/images/rebrand-")
DEMO_ALT = ("Illustrated walk-through of a PR conversation: kickoff, conflict merge, review, answer, re-review, "
            "a three-verifier panel, and the merge gate.")
DEMO_CAPTION = "How a PR moves through the bots. Every turn is a comment in the PR thread, and only a panel pass merges it."
# The build writes this file first and refuses to empty a folder without it, so --out can never wipe a
# project the build did not write. It names no brand, so it survives a rebrand of a rebrand unchanged.
BUILD_MARK = "brand/.whitelabel-build"
BUILD_MARK_TEXT = "Built by scripts/whitelabel.py. A rebuild into this folder replaces everything in it except .git.\n"


def is_legal(rel: str) -> bool:
    return rel.rsplit("/", 1)[-1].upper().startswith(("LICENSE", "NOTICE"))


def words(text: str) -> list:
    return [w for w in re.split(r"[^A-Za-z0-9]+", text) if w]


class Rebrand:
    """Maps the source brand's names to the target's. One regex pass, longest token first, so a replaced
    name is never replaced again and `/deep-mode:deep` wins over `/deep-mode` and `/deep`."""

    def __init__(self, src: dict, dst: dict):
        self.src, self.dst = src, dst
        edge_b, edge_a = r"(?<![A-Za-z0-9])", r"(?![A-Za-z0-9])"
        rules = []  # (literal, replacement, before, after, prose_only)

        def add(old, new, before=edge_b, after=edge_a, prose=False):
            if old and old != new or prose:
                rules.append((old, new, before, after, prose))

        s, d = src, dst
        bare = lambda url: url.split("://", 1)[1].rstrip("/")  # noqa: E731
        add(s["homepage"].rstrip("/"), d["homepage"].rstrip("/"), "", "")
        add(bare(s["homepage"]), bare(d["homepage"]), "", "")
        add(s["supportUrl"], d["supportUrl"], "", r"(?![\w/-])")
        add(s["author"]["url"], d["author"]["url"], "", r"(?![\w/-])")
        add(s["repo"], d["repo"], edge_b, r"(?![\w-])")
        add(s["owner"], d["owner"])
        add(s["owner"].lower(), d["owner"].lower())
        add(s["author"]["name"], d["author"]["name"])
        add(f"/{s['slug']}:{s['commandName']}", f"/{d['slug']}:{d['commandName']}", "", r"(?![\w-])")
        add(f"{s['slug']}:{s['mainSkillName']}", f"{d['slug']}:{d['mainSkillName']}", edge_b, r"(?![\w-])")
        add(f"{s['slug']}:{s['stackSkillName']}", f"{d['slug']}:{d['stackSkillName']}", edge_b, r"(?![\w-])")
        add(f"/{s['slug']}:", f"/{d['slug']}:", "", "")
        add(s["botTrigger"], d["botTrigger"], r"(?<![\w.~/-])", r"(?![\w:/-])")
        add("@" + s["slug"], d["botTrigger"], r"(?<![\w.-])", r"(?![\w/-])")
        add(f"skill://{s['mainSkillName']}", f"skill://{d['mainSkillName']}", "", r"(?![\w-])")
        add(f"skills/{s['mainSkillName']}", f"skills/{d['mainSkillName']}", edge_b, r"(?![\w-])")
        add(f"${s['mainSkillName']}", f"${d['mainSkillName']}", "", r"(?![\w:-])")
        add(f"name: {s['mainSkillName']}", f"name: {d['mainSkillName']}", "^", "$")
        add(f"commands/{s['commandName']}.md", f"commands/{d['commandName']}.md", edge_b, "")
        add(f"/{s['commandName']}", f"/{d['commandName']}", r"(?<![\w.~/:-])", r"(?![\w-])")
        add(s["stackSkillName"], d["stackSkillName"], edge_b, r"(?![\w])")
        add(s["envPrefix"], d["envPrefix"], edge_b, r"(?![A-Za-z0-9])")
        add(s["slug"].replace("-", "_"), d["slug"].replace("-", "_"))
        add(s["slug"].replace("-", ""), d["slug"].replace("-", ""))
        parts = s["slug"].split("-")
        for sep in ("-", " ", "_"):
            for form in (sep.join(parts), sep.join(p.capitalize() for p in parts), sep.join(parts).capitalize(),
                         sep.join(parts).upper()):
                if form not in (s["slug"], s["slug"].replace("-", "_"), s["envPrefix"]):
                    add(form, d["displayName"].upper() if form.isupper() else d["displayName"])
        for display in {s["name"], s["displayName"]} - {s["slug"]}:
            add(display, d["displayName"] if display == s["displayName"] else d["name"])
        # In prose, the slug standing alone as a word is the product's name: "deep-mode is ...", "**deep-mode**".
        add(s["slug"], d["name"], r"(?<![^\s(*>|])", r"(?=[\s'’,;)*<?!|]|[.:](?:\s|$)|$)", prose=True)
        add(s["slug"], d["slug"])
        rules.sort(key=lambda r: (-len(r[0]), not (r[2] or r[3]), not r[4]))
        self.rules = rules
        self.code = self._compile([r for r in rules if not r[4]])
        self.prose = self._compile(rules)
        # "a <old name> PR" becomes "an <new name> PR" when the new name starts with a vowel.
        vowel_names = sorted({n for n in (d["name"], d["displayName"], d["slug"]) if n[0].lower() in "aeiou"})
        self.article = (re.compile(r"(?<![A-Za-z0-9])([Aa]) (?=(?:" + "|".join(map(re.escape, vowel_names)) + r")(?![A-Za-z0-9]))")
                        if vowel_names and s["slug"][0].lower() not in "aeiou" else None)

    @staticmethod
    def _compile(rules):
        alternatives = [f"(?P<r{i}>{before}{re.escape(old)}{after})" for i, (old, _, before, after, _) in enumerate(rules)]
        return re.compile("|".join(alternatives), re.M), [r[1] for r in rules]

    def text(self, text: str, prose: bool = False, escape=None) -> str:
        regex, news = self.prose if prose else self.code
        esc = escape or (lambda x: x)
        text = regex.sub(lambda m: esc(news[int(m.lastgroup[1:])]), text)
        return self.article.sub(lambda m: m.group(1) + "n ", text) if prose and self.article else text

    def path(self, rel: str) -> str:
        return self.text(rel)

    def file_text(self, rel: str, text: str) -> str:
        suffix = Path(rel).suffix.lower()
        escape = None
        if suffix in (".html", ".svg"):
            escape = lambda x: html.escape(x, quote=False)  # noqa: E731
        elif suffix == ".json":
            escape = lambda x: json.dumps(x)[1:-1]  # noqa: E731
        return self.text(text, prose=suffix in PROSE, escape=escape)


def leftover_regex(src: dict) -> re.Pattern:
    """Every way the source brand's names can be written: any case, `-`, `_`, space or nothing between words."""
    names = {src["slug"], src["name"], src["displayName"], src["stackSkillName"], src["owner"], src["author"]["name"]}
    forms = sorted({"[-_ ]?".join(map(re.escape, words(n))) for n in names if words(n)}, key=len, reverse=True)
    return re.compile(r"(?<![a-z0-9])(?:" + "|".join(forms) + r")(?![a-z0-9])", re.I)


def find_leftovers(root: Path, pattern: re.Pattern) -> list:
    found = []
    for path in sorted(root.rglob("*"), key=lambda p: p.relative_to(root).as_posix()):
        rel = path.relative_to(root).as_posix()
        if SKIP_DIRS & set(rel.split("/")):
            continue
        if pattern.search(rel):
            found.append(f"{rel}: name in path")
        if not path.is_file() or is_legal(rel):
            continue
        text = path.read_bytes().decode("utf-8", errors="ignore")
        for number, line in enumerate(text.splitlines(), 1):
            for m in pattern.finditer(line):
                found.append(f"{rel}:{number}: {m.group(0)!r}")
        if Path(rel).suffix.lower() in OWN_RUN_FILES:
            for number, line in enumerate(text.splitlines(), 1):
                if OWN_RUN_CLAIM.search(line):
                    found.append(f"{rel}:{number}: claims the upstream's own PR #19 run")
    return found


def append_line(data: bytes, line: str) -> bytes:
    """The original bytes, untouched, then one more line."""
    sep = b"" if data.endswith(b"\n") else b"\n"
    return data + sep + b"\n" + line.encode("utf-8") + b"\n"


def source_files(root: Path, out: Path) -> list:
    if (root / ".git").exists() and shutil.which("git"):
        listed = subprocess.run(["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"], cwd=root,
                                capture_output=True, check=True).stdout.decode("utf-8").split("\0")
        files = [f for f in listed if f and (root / f).is_file()]
    else:
        files = [p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()]
    out_rel = None
    try:
        out_rel = out.resolve().relative_to(root.resolve()).as_posix() + "/"
    except ValueError:
        pass
    return sorted(f for f in files if not (SKIP_DIRS & set(f.split("/"))) and not (out_rel and f.startswith(out_rel)))


def prepare_out(out: Path, root: Path) -> None:
    """Empty --out for a fresh build, keeping its .git, and mark it as a build. Refuses folders that would hold
    or eat the source, and any non-empty folder without the mark: only what an earlier build wrote is deleted."""
    out, root = out.resolve(), root.resolve()
    if out == root or out in root.parents or (root in out.parents and out.relative_to(root).parts[0] != ".scratch"):
        raise BrandError(f"--out {out}: pick a folder outside the source repo (or under its .scratch/)")
    if out.exists():
        entries = [p for p in out.iterdir() if p.name != ".git"]
        if entries and not (out / BUILD_MARK).is_file():
            raise BrandError(f"--out {out}: not empty and not an earlier build (no {BUILD_MARK}); pick an empty folder")
        for p in entries:
            shutil.rmtree(p) if p.is_dir() and not p.is_symlink() else p.unlink()
    (out / BUILD_MARK).parent.mkdir(parents=True, exist_ok=True)
    (out / BUILD_MARK).write_text(BUILD_MARK_TEXT, encoding="utf-8", newline="\n")


def sub(text: str, pattern: str, repl, where: str, count: int = 0, flags=re.M) -> str:
    """re.sub that fails when the pattern no longer matches, so a drifted source is caught, not shipped."""
    new, n = re.subn(pattern, repl if callable(repl) else (lambda m: repl), text, count=count, flags=flags)
    if not n:
        raise BrandError(f"{where}: expected text not found for /{pattern}/; update scripts/whitelabel.py")
    return new


def own_run_rewrites(out: Path) -> None:
    """Drop the upstream's claims about its own merged PR, and show the illustrated demo GIF instead. A claim
    these patterns miss is still caught: the verification pass fails on any mention of that PR."""
    edits = {
        "README.md": [
            (r"^!\[[^\]\n]*\]\(docs/images/pr-19-thread\.gif\)$", f"![{DEMO_ALT}](docs/images/how-it-works.gif)"),
            (r"^A real run, not a mock-up:[^\n]*$", DEMO_CAPTION),
            (r"^\*\*Has it merged a real PR on its own\?\*\*[^\n]*\n\n", ""),
        ],
        "docs/index.html": [
            (r'("screenshot": "[^"]*/)pr-19-thread\.gif"', lambda m: m.group(1) + 'how-it-works.gif"'),
            (r'^    \{"@type": "Question", "name": "Has [^\n]*\n[^\n]*\n', ""),
            (r'^<a class="btn" href="[^"]*/pull/19">[^<]*</a>\n', ""),
            (r'<img src="images/pr-19-thread\.gif"[^>]*>\n<figcaption>[^\n]*</figcaption>',
             f'<img src="images/how-it-works.gif" width="960" height="540" alt="{html.escape(DEMO_ALT)}">\n'
             f"<figcaption>{html.escape(DEMO_CAPTION)}</figcaption>"),
            (r"^<h3>Has [^<]*real PR[^<]*</h3>\n<p>[^\n]*</p>\n", ""),
            (r"from real screenshots and a real terminal recording", "from rendered frames and a real terminal recording"),
        ],
        "docs/llms.txt": [
            (r"^- Real run: [^\n]*\n", ""),
            (r", the real PR #19 run", ", an illustrated PR walk-through"),
        ],
        "docs/rebrand.md": [(r"<!-- screenshots -->.*?<!-- /screenshots -->\n*", "")],
    }
    for rel, pairs in edits.items():
        path = out / rel
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for pattern, repl in pairs:
            text = re.sub(pattern, repl if callable(repl) else (lambda m, r=repl: r), text,
                          flags=re.M | re.S if "<!--" in pattern else re.M)
        path.write_text(text, encoding="utf-8", newline="\n")


def theme_site(out: Path, d: dict) -> None:
    path = out / "docs/index.html"
    if not path.is_file():
        return
    a = lambda x: html.escape(x, quote=True)  # noqa: E731
    title = f"{d['name']}: {d['tagline']}"
    c = d["colors"]
    t = path.read_text(encoding="utf-8")
    rel = "docs/index.html"
    t = sub(t, r"<title>[^<]*</title>", f"<title>{html.escape(title)}</title>", rel, 1)
    for prop, value in [('name="description"', d["description"]), ('name="author"', d["author"]["name"]),
                        ('name="theme-color"', c["background"]), ('property="og:site_name"', d["name"]),
                        ('property="og:title"', title), ('property="og:description"', d["description"]),
                        ('property="og:image:alt"', title + "."), ('name="twitter:title"', title),
                        ('name="twitter:description"', d["description"]), ('name="twitter:image:alt"', title + ".")]:
        t = sub(t, rf'(<meta {re.escape(prop)} content=")[^"]*(">)', lambda m, v=value: m.group(1) + a(v) + m.group(2), rel, 1)
    app = sub(t, r'("@type": "SoftwareApplication",\n  "name": )"[^"\n]*"',
              lambda m: m.group(1) + json.dumps(d["name"]), rel, 1)
    app = sub(app, r'(  "@type": "SoftwareApplication",(?:\n[^\n]*)*?\n  "description": )"[^"\n]*"',
              lambda m: m.group(1) + json.dumps(d["description"]), rel, 1)
    t = sub(app, r'"author": \{[^}\n]*\}',
            lambda m: '"author": ' + json.dumps({"@type": "Organization", "name": d["author"]["name"], "url": d["author"]["url"]}), rel, 1)
    t = sub(t, r":root\{--brand-primary:[^}]*\}",
            f":root{{--brand-primary:{c['primary']};--brand-accent:{c['accent']};--brand-bg:{c['background']};"
            f"--brand-surface:{c['surface']};--brand-text:{c['text']};--brand-muted:{c['muted']}}}", rel, 1)
    t = sub(t, r'(<a class="brand" href="#top"><img src="images/logo\.svg" alt=")[^"]*(")',
            lambda m: m.group(1) + a(d["name"]) + m.group(2), rel, 1)
    t = sub(t, r'(<footer>.*?by )<a href="[^"]*">[^<]*</a>',
            lambda m: m.group(1) + f'<a href="{a(d["author"]["url"])}">{html.escape(d["author"]["name"])}</a>', rel, 1, re.S)
    path.write_text(t, encoding="utf-8", newline="\n")


def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def update_manifests(out: Path, d: dict) -> None:
    repo_url = f"https://github.com/{d['repo']}"
    plugin = out / "plugins" / d["slug"] / ".claude-plugin/plugin.json"
    if plugin.is_file():
        data = json.loads(plugin.read_text(encoding="utf-8"))
        data.update(name=d["slug"], description=d["description"], homepage=d["homepage"], repository=repo_url,
                    author={"name": d["author"]["name"], "url": d["author"]["url"]})
        write_json(plugin, data)
    for manifest in (out / ".omp-plugin/marketplace.json", out / ".claude-plugin/marketplace.json"):
        if not manifest.is_file():
            continue
        data = json.loads(manifest.read_text(encoding="utf-8"))
        data["name"] = d["slug"]
        data["owner"] = {"name": d["author"]["name"]}
        data.setdefault("metadata", {})["description"] = f"{d['name']}: {d['tagline']}"
        for entry in data.get("plugins", []):
            entry.update(name=d["slug"], source=f"./plugins/{d['slug']}", description=d["description"],
                         homepage=d["homepage"], repository=repo_url)
        write_json(manifest, data)
    runtime = out / "plugins" / d["slug"] / "skills" / d["mainSkillName"] / "assets/github-app/brand.json"
    if runtime.is_file():
        data = json.loads(runtime.read_text(encoding="utf-8"))
        data.update(name=d["slug"], homepage=d["homepage"], mention=d["botTrigger"], branchPrefix=d["slug"],
                    repoConfigFile=f".{d['slug']}.json", configDirName=d["slug"], autostartId=f"{d['slug']}-bot")
        write_json(runtime, data)


def write_brand(out: Path, d: dict, assets: dict) -> None:
    write_json(out / "brand/brand.json", brandlib.to_json(d))
    for key, targets in (("logo", ("brand/logo.svg", "docs/images/logo.svg")), ("favicon", ("brand/favicon.svg", "docs/favicon.svg"))):
        for rel in targets:
            if (out / rel).parent.is_dir():
                (out / rel).write_bytes(assets[key])


def legal_notes(rb: Rebrand, notice_src: str, year: int) -> tuple:
    s, d = rb.src, rb.dst
    copyright_line = f"Copyright (c) {year} {d['author']['name']} (the {d['name']} rebrand of this software)"
    moved = {}
    for path in re.findall(r"`(plugins/[^`]+)`", notice_src):
        segs = path.rstrip("/").split("/")
        for i in range(1, len(segs) + path.endswith("/")):  # each renamed folder once
            old = "/".join(segs[:i])
            new = rb.path(old)
            if new.rsplit("/", 1)[-1] != segs[i - 1]:
                moved[old] = f"- `{old}/` is `{new}/` here."
    moved = [moved[k] for k in sorted(moved)]
    notice = "\n".join([f"## {d['name']}", "",
                        f"{d['name']} is a rebranded copy of {s['name']} ({'https://github.com/' + s['repo']}), "
                        f"built with its brand kit. {copyright_line}.",
                        "", "The paths above are the upstream layout. In this copy:", "", *moved])
    return copyright_line, notice


def build(brand_file, out, src_root: Path = ROOT, media: bool = True, check: bool = True, log=print) -> list:
    src_root = Path(src_root)
    src = brandlib.load(src_root / "brand/brand.json")
    dst = brandlib.load(brand_file)
    leftover = leftover_regex(src)
    for key in ("name", "displayName", "slug", "commandName", "mainSkillName", "stackSkillName", "envPrefix",
                "botTrigger", "repo", "homepage", "supportUrl"):
        if leftover.search(dst[key]):
            raise BrandError(f"{key} {dst[key]!r} still contains the source name")
    if leftover.search(dst["author"]["name"]) or leftover.search(dst["author"]["url"]):
        raise BrandError("author still contains the source name")
    rb = Rebrand(src, dst)
    out = Path(out)
    files = source_files(src_root, out)
    # Read before --out is emptied: the brand file may be the built copy's own brand/brand.json.
    assets = {key: dst[key + "Path"].read_bytes() for key in ("logo", "favicon")}
    prepare_out(out, src_root)
    targets = {}
    for rel in files:
        if rel.startswith(UPSTREAM_ONLY):
            continue
        new_rel = rb.path(rel)
        if new_rel in targets:
            raise BrandError(f"{rel} and {targets[new_rel]} both become {new_rel}")
        targets[new_rel] = rel
        data = (src_root / rel).read_bytes()
        if not is_legal(rel) and b"\0" not in data:
            try:
                data = rb.file_text(rel, data.decode("utf-8")).encode("utf-8")
            except UnicodeDecodeError:
                pass
        dest = out / new_rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        if os.name != "nt":
            os.chmod(dest, (src_root / rel).stat().st_mode & 0o777)
    year = datetime.date.today().year
    if (out / "LICENSE").is_file() and (out / "NOTICE.md").is_file():
        line, notice = legal_notes(rb, (src_root / "NOTICE.md").read_text(encoding="utf-8"), year)
        (out / "LICENSE").write_bytes(append_line((src_root / "LICENSE").read_bytes(), line))
        (out / "NOTICE.md").write_bytes(append_line((src_root / "NOTICE.md").read_bytes(), notice))
    write_brand(out, dst, assets)
    update_manifests(out, dst)
    theme_site(out, dst)
    own_run_rewrites(out)
    if (out / "README.md").is_file() and (out / "docs").is_dir():
        import llms_full
        llms_full.build(out, dst)
    if media:
        import render
        for path in render.render(dst, out):
            log(f"rendered {path}")
    found = find_leftovers(out, leftover)
    if found:
        return found
    if check and (out / "scripts/check.py").is_file():
        result = subprocess.run([sys.executable, str(out / "scripts/check.py")], capture_output=True, text=True)
        log(f"{out / 'scripts/check.py'}: {result.stdout.strip()}")
        if result.returncode:
            raise BrandError(f"the built copy's scripts/check.py failed:\n{result.stdout}{result.stderr}")
    return []


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--brand", required=True, help="brand file, like brand/examples/acme.json")
    parser.add_argument("--out", required=True, help="folder for the branded copy (rebuilt from scratch)")
    args = parser.parse_args()
    try:
        found = build(args.brand, args.out)
    except (BrandError, subprocess.CalledProcessError) as err:
        print(f"error: {err}", file=sys.stderr)
        return 2
    if found:
        print("\n".join(found))
        print(f"FAILED: {len(found)} leftover(s) of the source brand", file=sys.stderr)
        return 1
    print(f"OK: built {args.out}, 0 leftovers")
    return 0


if __name__ == "__main__":
    sys.exit(main())
