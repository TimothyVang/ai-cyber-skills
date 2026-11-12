"""Unit tests for run.py's contamination scan and judge-reply parsing. No model calls, no files written."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run  # noqa: E402

FOLDER = Path(r"C:\work\.scratch\kitty-1")

# (tool, arguments, whether the call reaches outside FOLDER)
CASES = [
    ("read", {"path": "src/ledger.js:10-20"}, False),
    ("read", {"path": "../../evals/outcome/tasks/kitty/hidden/kitty.checks.mjs"}, True),
    ("read", {"path": "C:/work/.scratch/kitty-1/src/x.js"}, False),
    ("read", {"path": "/c/work/.scratch/kitty-2/src/x.js"}, True),
    ("read", {"path": "skill://deepmodebot/references/playbooks/feature.md"}, False),
    ("grep", {"pattern": "x", "path": "src;../kitty-runs"}, True),
    ("edit", {"input": "[src/a.js#1A2B]\nPUT 1.=1:\n+x\n[../kitty-2/b.js#3C4D]\nCUT 1.=1"}, True),
    ("bash", {"command": "node --test spec/*.spec.js 2>/dev/null && git status"}, False),
    ("bash", {"command": "cd src && ls .. && cat ../README.md"}, False),
    ("bash", {"command": "cd .. && ls"}, True),
    ("bash", {"command": "ls ../kitty-runs/key.json"}, True),
    ("bash", {"command": "cat > spec/x.spec.js <<'EOF'\nimport { a } from '../src/money.js';\nEOF\nnode --test"}, False),
    ("bash", {"command": "python - <<'EOF'\nopen('../kitty-runs/key.json').read()\nEOF"}, True),
    ("bash", {"command": "echo hi > $TEMP/x"}, True),
    ("bash", {"command": "ls ~/.omp"}, True),
    ("bash", {"command": "grep -E '/^\\d+/' src/money.js; sed -i 's/a/b/' src/x.js"}, False),
    ("bash", {"command": "ls", "cwd": ".."}, True),
    ("bash", {"command": "KITTY_FILE=.work/k.json node bin/kitty.js balances --file=../x.json"}, True),
    ("eval", {"code": "open('/tmp/x','w')"}, True),
    ("eval", {"code": "print(open('src/money.js').read())"}, False),
    ("bash", {"command": "curl https://example.com/a/b"}, False),
    # A cd target is judged from where the cd starts, never again from where it lands.
    ("bash", {"command": "cd .worktrees/split && npm test && cd ../.."}, False),
    ("bash", {"command": "cd spec && node --test x.spec.js && cd .."}, False),
    ("bash", {"command": "cd .. && cat kitty-3/x"}, True),
    ("bash", {"command": "cd src && cd ../.. && ls"}, True),
    # Relative paths inside quoted code are left alone; a quoted path argument is still judged.
    ("bash", {"command": "node -e \"import('../src/money.js').then(m => console.log(m))\""}, False),
    ("bash", {"command": "node --input-type=module -e 'import { a } from \"../src/a.js\"; a()'"}, False),
    ("bash", {"command": "cat \"../kitty-runs/key.json\""}, True),
    ("bash", {"command": "node -e \"require('fs').readFileSync('C:/work/.scratch/kitty-runs/key.json')\""}, True),
    # mktemp writes to the system temp folder unless told where.
    ("bash", {"command": "export KITTY_FILE=$(mktemp -d)/k.json; node bin/kitty.js balances"}, True),
    ("bash", {"command": "cd \"$(mktemp -d)\" && ls"}, True),
    ("bash", {"command": "D=$(mktemp -d -p .scratch/tmp); export KITTY_FILE=$D/k.json"}, False),
    ("bash", {"command": "export TMPDIR=$PWD/.scratch/tmp; f=$(mktemp)"}, False),
    ("bash", {"command": "f=$(mktemp .scratch/tmp/k.XXXX)"}, False),
]


class OutsidePaths(unittest.TestCase):
    def test_cases(self):
        for name, args, outside in CASES:
            with self.subTest(tool=name, args=args):
                hits = run.outside_paths([{"name": name, "args": args}], FOLDER)
                self.assertEqual(bool(hits), outside, hits)


class ParseScores(unittest.TestCase):
    def test_reads_the_last_json_block(self):
        reply = "notes\n```json\n{\"A\": {\"scores\": [2, 1, 0], \"notes\": \"ok\"}}\n```\n"
        scores, error = run.parse_scores(reply, ["A"], 3)
        self.assertIsNone(error)
        self.assertEqual(scores["A"]["total"], 3)

    def test_reports_bad_replies(self):
        for reply in ("no block", "```json\n{\"A\": {\"scores\": [2, 1]},}\n```",
                      "```json\n{\"A\": {\"scores\": [2, \"two\", 1]}}\n```", "```json\n{\"A\": {\"scores\": [2, 1.5, 1]}}\n```",
                      "```json\n{\"B\": {\"scores\": [2, 1, 1]}}\n```"):
            with self.subTest(reply=reply):
                scores, error = run.parse_scores(reply, ["A"], 3)
                self.assertIsNone(scores)
                self.assertTrue(error)


if __name__ == "__main__":
    unittest.main()
