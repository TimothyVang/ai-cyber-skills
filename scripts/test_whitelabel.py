"""Edge cases of the white-label build. Run: py -3 scripts/test_whitelabel.py"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import whitelabel  # noqa: E402
from brandlib import load, to_json  # noqa: E402

SRC = to_json(load(ROOT / "brand/brand.json"))  # the names the build replaces; the literals below spell them out
# The main skill differs from the slug here, so a path that mixes them shows which rule fired.
DST = dict(SRC, name="Zeta Review", displayName="Zeta Review", slug="zeta-review", commandName="z", mainSkillName="zeta",
           stackSkillName="zeta-stack", envPrefix="ZETA", botTrigger="/zeta-bot", description="Zeta Review bots.",
           author={"name": "Zeta Inc.", "url": "https://zeta.example"}, homepage="https://zeta.example/",
           repo="zeta-co/zeta-review", supportUrl="https://zeta.example/help")


def normalized(data: dict) -> dict:
    return dict(data, owner=data["repo"].split("/")[0])


def write_brand(folder: Path, data: dict) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    for name in ("logo.svg", "favicon.svg"):
        (folder / name).write_text(f'<svg xmlns="http://www.w3.org/2000/svg"><title>{data["name"]}</title></svg>\n', encoding="utf-8")
    (folder / "brand.json").write_text(json.dumps(data), encoding="utf-8")
    return folder / "brand.json"


class TokenOrder(unittest.TestCase):
    rb = whitelabel.Rebrand(normalized(SRC), normalized(DST))

    def test_overlapping_names_take_the_longest_match(self):
        cases = {
            "/deep-mode:deep fix it": "/zeta-review:z fix it",
            "/deep-mode:review-pr 42": "/zeta-review:review-pr 42",
            "$deep-mode:deep-mode go": "$zeta-review:zeta go",
            "`$deep-mode`": "`$zeta`",
            "run `/deep` or /deep.": "run `/z` or /z.",
            "comment `/deep-mode continue`": "comment `/zeta-bot continue`",
            '"mention": "@deep-mode"': '"mention": "/zeta-bot"',
            "skill://deep-mode and skill://deep-stack": "skill://zeta and skill://zeta-stack",
            "deep-stack/SKILL.md": "zeta-stack/SKILL.md",
            "~/.config/deep-mode/bot.json": "~/.config/zeta-review/bot.json",
            "DEEP_MODE_CONFIG_DIR and export_deep_mode.py": "ZETA_CONFIG_DIR and export_zeta_review.py",
            "omp plugin install deep-mode@deep-mode": "omp plugin install zeta-review@zeta-review",
            "https://github.com/TimothyVang/deep-mode/blob/main/README.md": "https://github.com/zeta-co/zeta-review/blob/main/README.md",
            "https://timothyvang.github.io/deep-mode/llms.txt": "https://zeta.example/llms.txt",
            "TimothyVang/frontend": "zeta-co/frontend",
            "deep-mode-timothyvang[bot]": "zeta-review-zeta-co[bot]",
        }
        for before, after in cases.items():
            self.assertEqual(self.rb.text(before), after, before)

    def test_prose_names_the_product_and_leaves_ordinary_words(self):
        text = "deep-mode is a plugin. Deep-mode's gates win. Say \"deep mode\". A deep model goes deep. a deep-mode PR"
        self.assertEqual(self.rb.text(text, prose=True),
                         "Zeta Review is a plugin. Zeta Review's gates win. Say \"Zeta Review\". A deep model goes deep. "
                         "a Zeta Review PR")

    def test_frontmatter_name_follows_its_folder(self):
        self.assertEqual(self.rb.text("---\nname: deep-mode\n---\n"), "---\nname: zeta\n---\n")
        self.assertEqual(self.rb.text("---\nname: deep-stack\n---\n"), "---\nname: zeta-stack\n---\n")


class PathRenames(unittest.TestCase):
    rb = whitelabel.Rebrand(normalized(SRC), normalized(DST))

    def test_plugin_skill_and_command_paths(self):
        self.assertEqual(self.rb.path("plugins/deep-mode/skills/deep-mode/assets/github-app/install.py"),
                         "plugins/zeta-review/skills/zeta/assets/github-app/install.py")
        self.assertEqual(self.rb.path("plugins/deep-mode/skills/deep-stack/SKILL.md"), "plugins/zeta-review/skills/zeta-stack/SKILL.md")
        self.assertEqual(self.rb.path("plugins/deep-mode/commands/deep.md"), "plugins/zeta-review/commands/z.md")
        self.assertEqual(self.rb.path("plugins/deep-mode/commands/deep-dive.md"), "plugins/zeta-review/commands/deep-dive.md")
        self.assertEqual(self.rb.path("docs/images/how-it-works.svg"), "docs/images/how-it-works.svg")


class Build(unittest.TestCase):
    """A small source tree, built for real without the images or the copy's check.py."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.src, self.out = base / "src", base / "out"
        write_brand(self.src / "brand", SRC)
        self.dst_file = write_brand(base / "zeta", DST)
        self.license = b"MIT License\r\n\r\nCopyright (c) 2026 Timothy Vang and deep-mode contributors"  # no final newline
        self.skill_license = b"Copyright (c) 2026 deep-mode upstream\n"
        files = {
            "LICENSE": self.license,
            "NOTICE.md": b"# Notices\n\n| `plugins/deep-mode/skills/deep-mode/` | MIT |\n",
            "plugins/deep-mode/skills/deep-mode/LICENSE": self.skill_license,
            "plugins/deep-mode/skills/deep-mode/SKILL.md": b"---\nname: deep-mode\ndescription: x\n---\n# Deep mode\n",
            "plugins/deep-mode/commands/deep.md": b"Read `skill://deep-mode`.\n",
            "README.md": b"# deep-mode\n\nRun `/deep`. By TimothyVang.\n",
        }
        for rel, data in files.items():
            (self.src / rel).parent.mkdir(parents=True, exist_ok=True)
            (self.src / rel).write_bytes(data)

    def tearDown(self):
        self.tmp.cleanup()

    def build(self):
        return whitelabel.build(self.dst_file, self.out, src_root=self.src, media=False, check=False, log=lambda *_: None)

    def test_license_bytes_stay_and_the_copyright_line_is_appended_once(self):
        self.assertEqual(self.build(), [])
        self.assertEqual(self.build(), [])  # a rebuild into the same folder appends nothing twice
        self.assertEqual((self.out / "plugins/zeta-review/skills/zeta/LICENSE").read_bytes(), self.skill_license)
        root = (self.out / "LICENSE").read_bytes()
        self.assertTrue(root.startswith(self.license))
        self.assertEqual(root.count(b"Zeta Inc."), 1)
        self.assertIn(b"`plugins/deep-mode/skills/deep-mode/` is `plugins/zeta-review/skills/zeta/` here.",
                      (self.out / "NOTICE.md").read_bytes())

    def test_renamed_tree_and_rewritten_text(self):
        self.build()
        self.assertTrue((self.out / "plugins/zeta-review/commands/z.md").is_file())
        self.assertFalse((self.out / "plugins/deep-mode").exists())
        self.assertEqual((self.out / "README.md").read_text(encoding="utf-8"), "# Zeta Review\n\nRun `/z`. By zeta-co.\n")
        self.assertEqual(json.loads((self.out / "brand/brand.json").read_text(encoding="utf-8"))["slug"], "zeta-review")

    def test_verification_catches_a_planted_leftover(self):
        self.build()
        pattern = whitelabel.leftover_regex(normalized(SRC))
        (self.out / "README.md").write_text("# Zeta Review\n\nSee the Deep Mode docs.\n", encoding="utf-8")
        (self.out / "notes").mkdir()
        (self.out / "notes/deep_mode.txt").write_text("clean\n", encoding="utf-8")
        (self.out / "LICENSE-THIRD-PARTY").write_text("deep-mode by TimothyVang\n", encoding="utf-8")
        self.assertEqual(whitelabel.find_leftovers(self.out, pattern),
                         ["README.md:3: 'Deep Mode'", "notes/deep_mode.txt: name in path"])


if __name__ == "__main__":
    unittest.main()
