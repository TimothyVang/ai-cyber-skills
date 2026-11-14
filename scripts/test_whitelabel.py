"""Edge cases of the white-label build. Run: py -3 scripts/test_whitelabel.py"""
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import whitelabel  # noqa: E402
from brandlib import MAX_BYTES, load, to_json  # noqa: E402

SRC = to_json(load(ROOT / "brand/brand.json"))  # the names the build replaces; the literals below spell them out
# The main skill differs from the slug here, so a path that mixes them shows which rule fired.
DST = dict(SRC, name="Zeta Review", displayName="Zeta Review", slug="zeta-review", commandName="z", mainSkillName="zeta",
           stackSkillName="zeta-stack", envPrefix="ZETA", botTrigger="/zeta-bot", description="Zeta Review bots.",
           author={"name": "Zeta Inc.", "url": "https://zeta.example"}, homepage="https://zeta.example/",
           repo="zeta-co/zeta-review", supportUrl="https://zeta.example/help")
LINE_LIMIT = 760  # MAX_LINE_BYTES in scripts/check.py, which the built copy has to pass


def normalized(data: dict) -> dict:
    return dict(data, owner=data["repo"].split("/")[0])


def write_brand(folder: Path, data: dict) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    for name in ("logo.svg", "favicon.svg"):
        (folder / name).write_text(f'<svg xmlns="http://www.w3.org/2000/svg"><title>{data["name"]}</title></svg>\n', encoding="utf-8")
    (folder / "brand.json").write_text(json.dumps(data), encoding="utf-8")
    return folder / "brand.json"


def longest_brand() -> dict:
    """Every name at its limit. The names start with a vowel, so an "a" before them grows to "an" as well."""
    def run(head, letter, size):
        return head + letter * (size - len(head))
    return dict(DST, name=run("A", "n", MAX_BYTES["name"]), displayName=run("A", "d", MAX_BYTES["displayName"]),
                slug=run("a", "s", 23), commandName="c" * MAX_BYTES["commandName"], mainSkillName="m" * MAX_BYTES["mainSkillName"],
                stackSkillName="k" * MAX_BYTES["stackSkillName"], envPrefix="E" * MAX_BYTES["envPrefix"],
                botTrigger=run("/", "t", MAX_BYTES["botTrigger"]),
                repo="o" * MAX_BYTES["repo owner"] + "/" + "r" * MAX_BYTES["repo name"],
                homepage=run("https://", "h", MAX_BYTES["homepage"]), supportUrl=run("https://", "u", MAX_BYTES["supportUrl"]),
                author={"name": "U" * MAX_BYTES["author name"], "url": run("https://", "w", MAX_BYTES["author url"])})


class TokenOrder(unittest.TestCase):
    rb = whitelabel.Rebrand(normalized(SRC), normalized(DST))

    def test_overlapping_names_take_the_longest_match(self):
        cases = {
            "/deepmodebot:deep fix it": "/zeta-review:z fix it",
            "/deepmodebot:review-pr 42": "/zeta-review:review-pr 42",
            "$deepmodebot:deepmodebot go": "$zeta-review:zeta go",
            "`$deepmodebot`": "`$zeta`",
            "run `/deep` or /deep.": "run `/z` or /z.",
            "comment `@deepmodebot continue`": "comment `/zeta-bot continue`",
            '"mention": "@deepmodebot"': '"mention": "/zeta-bot"',
            "skill://deepmodebot and skill://deep-stack": "skill://zeta and skill://zeta-stack",
            "deep-stack/SKILL.md": "zeta-stack/SKILL.md",
            "~/.config/deepmodebot/bot.json": "~/.config/zeta-review/bot.json",
            "DEEPMODEBOT_CONFIG_DIR and export_deepmodebot.py": "ZETA_CONFIG_DIR and export_zeta_review.py",
            "omp plugin install deepmodebot@deepmodebot": "omp plugin install zeta-review@zeta-review",
            "https://github.com/TimothyVang/deepmodebot/blob/main/README.md": "https://github.com/zeta-co/zeta-review/blob/main/README.md",
            "https://timothyvang.github.io/deepmodebot/llms.txt": "https://zeta.example/llms.txt",
            "TimothyVang/frontend": "zeta-co/frontend",
            "deepmodebot-timothyvang[bot]": "zeta-review-zeta-co[bot]",
        }
        for before, after in cases.items():
            self.assertEqual(self.rb.text(before), after, before)

    def test_prose_names_the_product_and_leaves_ordinary_words(self):
        text = "deepmodebot is a plugin. Deepmodebot's gates win. Say \"Deepmodebot\". A deep model goes deep. a deepmodebot PR"
        self.assertEqual(self.rb.text(text, prose=True),
                         "Zeta Review is a plugin. Zeta Review's gates win. Say \"Zeta Review\". A deep model goes deep. "
                         "a Zeta Review PR")

    def test_frontmatter_name_follows_its_folder(self):
        # From SRC, not spelled out: in a copy whose main skill is not named after its slug, a literal here
        # would be rewritten to the slug, which is not a skill's name.
        self.assertEqual(self.rb.text(f"---\nname: {SRC['mainSkillName']}\n---\n"), "---\nname: zeta\n---\n")
        self.assertEqual(self.rb.text(f"---\nname: {SRC['stackSkillName']}\n---\n"), "---\nname: zeta-stack\n---\n")


class PathRenames(unittest.TestCase):
    rb = whitelabel.Rebrand(normalized(SRC), normalized(DST))

    def test_plugin_skill_and_command_paths(self):
        self.assertEqual(self.rb.path("plugins/deepmodebot/skills/deepmodebot/assets/github-app/install.py"),
                         "plugins/zeta-review/skills/zeta/assets/github-app/install.py")
        self.assertEqual(self.rb.path("plugins/deepmodebot/skills/deep-stack/SKILL.md"), "plugins/zeta-review/skills/zeta-stack/SKILL.md")
        self.assertEqual(self.rb.path("plugins/deepmodebot/commands/deep.md"), "plugins/zeta-review/commands/z.md")
        self.assertEqual(self.rb.path("plugins/deepmodebot/commands/deep-dive.md"), "plugins/zeta-review/commands/deep-dive.md")
        self.assertEqual(self.rb.path("docs/images/how-it-works.svg"), "docs/images/how-it-works.svg")


class Escaping(unittest.TestCase):
    """A name is plain text; each file type gets it in that type's own escaping."""
    rb = whitelabel.Rebrand(normalized(SRC), normalized(dict(DST, name='Zeta "Review" & <Co>')))

    def test_a_name_with_quotes_stays_valid_in_json_ld_and_in_markup(self):
        page = ('<script type="application/ld+json">\n{"name": "What is deepmodebot?"}\n</script>\n'
                '<img alt="How deepmodebot works">\n<p>deepmodebot is a plugin.</p>\n')
        script, markup = self.rb.file_text("docs/index.html", page).split("</script>\n")
        self.assertEqual(json.loads(script.split(">", 1)[1]), {"name": 'What is Zeta "Review" & <Co>?'})
        self.assertNotIn("<Co>", script)  # nothing in a JSON-LD value may read as markup and end the script
        self.assertEqual(markup, '<img alt="How Zeta &quot;Review&quot; &amp; &lt;Co&gt; works">\n'
                                 "<p>Zeta &quot;Review&quot; &amp; &lt;Co&gt; is a plugin.</p>\n")

    def test_json_ld_that_does_not_parse_stops_the_build(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "docs").mkdir()
            page = Path(tmp) / "docs/index.html"
            page.write_text('<script type="application/ld+json">{"name": "Zeta "Review""}</script>\n', encoding="utf-8")
            with self.assertRaises(whitelabel.BrandError):
                whitelabel.check_json_ld(Path(tmp))
            page.write_text('<script type="application/ld+json">{"name": "Zeta"}</script>\n', encoding="utf-8")
            whitelabel.check_json_ld(Path(tmp))


class Build(unittest.TestCase):
    """A small source tree, built for real without the images or the copy's check.py."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.src, self.out = base / "src", base / "out"
        write_brand(self.src / "brand", SRC)
        self.dst_file = write_brand(base / "zeta", DST)
        self.license = b"MIT License\r\n\r\nCopyright (c) 2026 Timothy Vang and deepmodebot contributors"  # no final newline
        self.skill_license = b"Copyright (c) 2026 deepmodebot upstream\n"
        files = {
            "LICENSE": self.license,
            "NOTICE.md": b"# Notices\n\n| `plugins/deepmodebot/skills/deepmodebot/` | MIT |\n",
            "plugins/deepmodebot/skills/deepmodebot/LICENSE": self.skill_license,
            "plugins/deepmodebot/skills/deepmodebot/SKILL.md": b"---\nname: deepmodebot\ndescription: x\n---\n# Deepmodebot\n",
            "plugins/deepmodebot/commands/deep.md": b"Read `skill://deepmodebot`.\n",
            "README.md": b"# deepmodebot\n\nRun `/deep`. By TimothyVang.\n",
        }
        for rel, data in files.items():
            (self.src / rel).parent.mkdir(parents=True, exist_ok=True)
            (self.src / rel).write_bytes(data)

    def tearDown(self):
        self.tmp.cleanup()

    def build(self, brand_file=None):
        return whitelabel.build(brand_file or self.dst_file, self.out, src_root=self.src, media=False, check=False,
                                log=lambda *_: None)

    def test_recorded_evidence_keeps_paths_bytes_and_digest_after_rebranding(self):
        refs = Path("plugins") / SRC["slug"] / "skills" / SRC["mainSkillName"] / "references"
        for name in ("flows.md", "techniques/github-app.md", "techniques/pr-conversation.md",
                     "techniques/issue-conversation.md"):
            target = self.src / refs / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((ROOT / refs / name).read_bytes())
        rel = "docs/evidence/deepmodebot-pilot/observed.txt"
        payload = b"deepmodebot: PR #19, original observation\r\n"
        source = self.src / rel
        source.parent.mkdir(parents=True)
        source.write_bytes(payload)
        digest = hashlib.sha256(payload).hexdigest().encode()
        source.with_suffix(".sha256").write_bytes(digest + b"\r\n")
        adjacent = self.src / "docs/evidenceology/deepmodebot.txt"
        adjacent.parent.mkdir(parents=True)
        adjacent.write_bytes(b"deepmodebot")

        self.assertEqual(self.build(), [])
        copied = self.out / rel
        self.assertEqual(copied.read_bytes(), payload)
        self.assertEqual(copied.with_suffix(".sha256").read_bytes(), digest + b"\r\n")
        self.assertEqual(hashlib.sha256(copied.read_bytes()).hexdigest().encode(), digest)
        self.assertEqual((self.out / "docs/evidenceology/zeta-review.txt").read_bytes(), b"Zeta Review")

    def test_license_bytes_stay_and_the_copyright_line_is_appended_once(self):
        self.assertEqual(self.build(), [])
        self.assertEqual(self.build(), [])  # a rebuild into the same folder appends nothing twice
        self.assertEqual((self.out / "plugins/zeta-review/skills/zeta/LICENSE").read_bytes(), self.skill_license)
        root = (self.out / "LICENSE").read_bytes()
        self.assertTrue(root.startswith(self.license))
        self.assertEqual(root.count(b"Zeta Inc."), 1)
        self.assertIn(b"`plugins/deepmodebot/skills/deepmodebot/` is `plugins/zeta-review/skills/zeta/` here.",
                      (self.out / "NOTICE.md").read_bytes())

    def test_renamed_tree_and_rewritten_text(self):
        self.build()
        self.assertTrue((self.out / "plugins/zeta-review/commands/z.md").is_file())
        self.assertFalse((self.out / "plugins/deepmodebot").exists())
        self.assertEqual((self.out / "README.md").read_text(encoding="utf-8"), "# Zeta Review\n\nRun `/z`. By zeta-co.\n")
        self.assertEqual(json.loads((self.out / "brand/brand.json").read_text(encoding="utf-8"))["slug"], "zeta-review")

    def test_verification_catches_a_planted_leftover(self):
        self.build()
        pattern = whitelabel.leftover_regex(normalized(SRC))
        (self.out / "README.md").write_text("# Zeta Review\n\nSee the Deepmodebot docs.\n", encoding="utf-8")
        (self.out / "notes").mkdir()
        (self.out / "notes/deepmodebot.txt").write_text("clean\n", encoding="utf-8")
        (self.out / "LICENSE-THIRD-PARTY").write_text("deepmodebot by TimothyVang\n", encoding="utf-8")
        self.assertEqual(whitelabel.find_leftovers(self.out, pattern),
                         ["README.md:3: 'Deepmodebot'", "notes/deepmodebot.txt: name in path"])

    def test_a_folder_the_build_did_not_write_is_refused_and_left_alone(self):
        write_brand(self.out / "brand", SRC)  # another project can hold a brand/brand.json too
        (self.out / "work.txt").write_text("uncommitted\n", encoding="utf-8")
        with self.assertRaises(whitelabel.BrandError):
            self.build()
        self.assertEqual((self.out / "work.txt").read_text(encoding="utf-8"), "uncommitted\n")
        self.assertEqual(json.loads((self.out / "brand/brand.json").read_text(encoding="utf-8"))["slug"], SRC["slug"])

    def test_a_failed_build_can_be_rebuilt_into_the_same_folder(self):
        (self.src / "docs").mkdir()
        (self.src / "docs/index.html").write_text("<html></html>\n", encoding="utf-8")  # nothing to retheme: the build stops
        with self.assertRaises(whitelabel.BrandError):
            self.build()
        (self.src / "docs/index.html").unlink()
        self.assertEqual(self.build(), [])

    def test_rebuild_from_the_copys_own_brand_file(self):
        self.build()
        logo = (self.out / "brand/logo.svg").read_bytes()
        self.assertEqual(self.build(self.out / "brand/brand.json"), [])
        self.assertEqual((self.out / "brand/logo.svg").read_bytes(), logo)
        self.assertEqual((self.out / "brand/favicon.svg").read_bytes(), logo)

    def test_the_install_recording_becomes_example_output_with_no_account_names(self):
        lines = [{"version": 2, "width": 92, "height": 22, "title": "install.py --check (real run)"},
                 [0.0, "o", "~/deepmodebot $ "],
                 [3.4, "o", "  [ok] gh logged in as TimothyVang\r\n"],
                 [12.7, "o", "  [ok] app deepmodebot-timothyvang already configured\r\n"],
                 [13.0, "o", "  [ok] installed on TimothyVang, some-org\r\n"]]
        (self.src / "docs/images").mkdir(parents=True)
        (self.src / "docs/images/install.cast").write_text("".join(json.dumps(line) + "\n" for line in lines), encoding="utf-8")
        (self.src / "README.md").unlink()  # no README: the build skips llms-full.txt, which needs the full docs
        self.assertEqual(self.build(), [])
        text = (self.out / "docs/images/install.cast").read_text(encoding="utf-8")
        built = [json.loads(line) for line in text.splitlines()]
        self.assertEqual(built[0]["title"], "install.py --check (example output)")
        self.assertEqual([event[2] for event in built[1:]],
                         ["~/zeta-review $ ", "  [ok] gh logged in as <login>\r\n",
                          "  [ok] app zeta-review-<login> already configured\r\n", "  [ok] installed on <login>\r\n"])
        self.assertEqual(whitelabel.example_cast(text, "zeta-review"), text)  # a copy of a copy: already an example

    def test_the_install_caption_stops_claiming_a_real_run(self):
        (self.src / "README.md").write_bytes(b"# deepmodebot\n\n![A real run of install.py --check](docs/images/install.gif)\n")
        self.assertEqual(self.build(), [])
        self.assertEqual((self.out / "README.md").read_text(encoding="utf-8"),
                         "# Zeta Review\n\n![Example output of install.py --check](docs/images/install.gif)\n")

    def test_a_real_run_claim_left_in_the_copy_fails_verification(self):
        self.build()
        (self.out / "README.md").write_text("# Zeta Review\n\nA real run of install.py --check.\n", encoding="utf-8")
        self.assertEqual(whitelabel.find_leftovers(self.out, whitelabel.leftover_regex(normalized(SRC))),
                         ["README.md:3: claims a real run this copy has not made"])

    def test_the_github_app_gets_the_brand_files_description(self):
        runtime = "skills/deepmodebot/assets/github-app/brand.json"
        (self.src / "plugins/deepmodebot" / runtime).parent.mkdir(parents=True)
        (self.src / "plugins/deepmodebot" / runtime).write_text(json.dumps({
            "name": "deepmodebot", "description": "deepmodebot bots: review, fix, verify and merge.",
            "homepage": "https://github.com/TimothyVang/deepmodebot"}), encoding="utf-8")
        self.assertEqual(self.build(), [])
        built = json.loads((self.out / "plugins/zeta-review/skills/zeta/assets/github-app/brand.json").read_text(encoding="utf-8"))
        self.assertEqual((built["name"], built["description"], built["homepage"]),
                         ("zeta-review", "Zeta Review bots.", "https://zeta.example/"))


class Limits(unittest.TestCase):
    """A brand file that loads must not fail the build on line length. A Markdown line that names the product
    grows with the brand, so the names have limits and this repo keeps room for them."""

    @unittest.skipIf((ROOT / whitelabel.BUILD_MARK).is_file(),
                     "a built copy: its own names also stand where the upstream wrote them as examples, so only the upstream is measured")
    def test_the_longest_valid_brand_builds_this_repo_within_the_line_limit(self):
        # A failure names the lines to split: ones added here without room for the longest names.
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out"
            brand = write_brand(Path(tmp) / "brand", longest_brand())
            self.assertEqual(whitelabel.build(brand, out, media=False, check=False, log=lambda *_: None), [])
            too_long = [f"{path.relative_to(out).as_posix()}:{number}: {len(line.encode('utf-8'))} bytes"
                        for path in sorted(out.rglob("*.md"))
                        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
                        if len(line.encode("utf-8")) > LINE_LIMIT]
            self.assertEqual(too_long, [])
            load(out / "brand/brand.json")  # the brand file the build wrote is within the limits too

    def test_a_name_past_its_limit_is_refused_when_the_brand_file_loads(self):
        with tempfile.TemporaryDirectory() as tmp:
            brand = write_brand(Path(tmp), dict(longest_brand(), name="A" * (MAX_BYTES["name"] + 1)))
            with self.assertRaisesRegex(whitelabel.BrandError, f"name .*at most {MAX_BYTES['name']} bytes"):
                load(brand)


if __name__ == "__main__":
    unittest.main()
