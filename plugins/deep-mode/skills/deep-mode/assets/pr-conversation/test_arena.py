"""Pure-function tests for show_thread.py and arena.py (no network). Run: python -m unittest test_arena"""

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import arena  # noqa: E402
import show_thread as st  # noqa: E402


def comment(body, cid=1):
    return {"id": cid, "html_url": f"https://github.com/o/r/pull/1#issuecomment-{cid}",
            "created_at": "2026-11-11T21:56:00Z", "body": body}


def fenced(data):
    return "```json\n" + json.dumps(data) + "\n```"


def turn(body, cid=1):
    return st.voice(comment(body, cid), limit=None)


class ThreadUrl(unittest.TestCase):
    def test_pull_and_issue(self):
        self.assertEqual(st.parse_url("https://github.com/o/r/pull/12"), ("o/r", 12, "pr"))
        self.assertEqual(st.parse_url("https://github.com/o/r.js/issues/7"), ("o/r.js", 7, "issue"))

    def test_suffixes(self):
        self.assertEqual(st.parse_url("https://github.com/o/r/pull/12/files"), ("o/r", 12, "pr"))
        self.assertEqual(st.parse_url("https://github.com/o/r/issues/3#issuecomment-9"), ("o/r", 3, "issue"))

    def test_not_a_thread(self):
        for url in ("https://example.com/o/r/pull/1", "https://github.com/o/r/commit/abc",
                    "https://github.com/o/r/pull/x", "https://github.com/o/r/pull/12x", "o/r#12"):
            self.assertIsNone(st.parse_url(url), url)


class Signature(unittest.TestCase):
    def test_lens_signature(self):
        sig = st.parse_signature("**deep-mode reviewer · UI/UX** · head `e840ec3e`")
        self.assertEqual((sig["role"], sig["kind"], sig["lens"], sig["agent"], sig["head"]),
                         ("reviewer", "reviewer", "UI/UX", None, "e840ec3e"))

    def test_agent_and_model(self):
        sig = st.parse_signature("**deep-mode reviewer · omp (m/x)** · head `abcdef1`")
        self.assertEqual((sig["agent"], sig["model"], sig["lens"]), ("omp", "m/x", None))
        self.assertEqual(st.parse_signature("**hunt panel · bot.py** · head `abc1234`")["agent"], "bot.py")

    def test_verifier_number_and_trunk_check(self):
        sig = st.parse_signature("**deep-mode verifier 2 · edges** · head `0330d961`")
        self.assertEqual((sig["kind"], sig["number"], sig["lens"]), ("verifier", 2, "edges"))
        sig = st.parse_signature("**deep-mode trunk check · claude** · head `1234567`")
        self.assertEqual((sig["role"], sig["kind"], sig["number"], sig["agent"]), ("trunk check", "verifier", None, "claude"))

    def test_heads(self):
        self.assertEqual(st.parse_signature("**deep-mode author** · merge note")["head"], "merge note")
        self.assertEqual(st.parse_signature("**deep-mode coordinator · bot.py** · head ``")["head"], "")

    def test_not_a_signature(self):
        self.assertIsNone(st.parse_signature("**[Persistent review](https://x)** updated to latest commit"))
        self.assertIsNone(st.parse_signature("**deep-mode reviewers** · head `abc1234`"))
        self.assertIsNone(st.parse_signature("deep-mode reviewer · head `abc1234`"))

    def test_voice(self):
        self.assertIsNone(st.voice(comment("LGTM, thanks!")))
        agent = st.voice(comment("## PR Reviewer Guide 🔍\n\nNo major issues detected"))
        self.assertEqual((agent["kind"], agent["gist"]), ("pr-agent", ["No major issues detected"]))
        v = st.voice(comment("**deep-mode verifier 1 · omp** · head `abc1234`\n\n" + fenced({"vote": "PASS", "evidence": "ok"})))
        self.assertEqual((v["kind"], v["number"], v["gist"]), ("verifier", 1, ["vote: PASS — ok"]))


class ProseAnswers(unittest.TestCase):
    def test_forms(self):
        body = ("**deep-mode author** · head `ed506edb`\n\nAnswers to round 1:\n\n"
                "1. **P1 clipped text: fixed.** Show more toggles.\n"
                "| security P2: install source | **fixed**: the URL comes from the identity. |\n"
                "| build P2: shared checkout | **fixed in `47d46cf1`**. Only fresh installs get the fork. |\n"
                "The one new P2 is **dismissed**: it is intended. Done.\n")
        self.assertEqual(st.gist(body, "author"), [
            "Answers to round 1:",
            "fixed P1 clipped text — Show more toggles.",
            "fixed security P2: install source — the URL comes from the identity.",
            "fixed build P2: shared checkout — Only fresh installs get the fork.",
            "dismissed — The one new P2 is dismissed: it is intended.",
        ])

    def test_only_for_the_author(self):
        body = "**deep-mode reviewer** · head `abc1234`\n\nNo findings. All three are **fixed** now."
        self.assertEqual(st.gist(body, "reviewer"), ["No findings. All three are fixed now."])


class Dialog(unittest.TestCase):
    def test_review_findings_and_effectiveness(self):
        v = turn("**deep-mode reviewer · security** · head `964653e3`\n\n" + fenced({"findings": [
            {"id": "F1", "severity": "P1", "file": "write-build-stamp.mjs", "line": 255, "claim": "hands updates off"},
            {"id": "F2", "severity": "P0", "file": "a.py", "line": 3, "claim": "drops data"},
            {"id": "F3", "severity": "P2", "file": "b.py", "line": 9, "claim": "naming"}]}))
        self.assertEqual(arena.turn_lines(v, True), [
            "REVIEWER (security) appeared!",
            "It found a P1: write-build-stamp.mjs:255 - hands updates off",
            "It's super effective!",
            "It found a P0: a.py:3 - drops data",
            "A critical hit!",
            "It found a P2: b.py:9 - naming",
        ])
        self.assertEqual(arena.turn_lines(v, False)[0], "REVIEWER (security) returns!")

    def test_author_fixes_grouped_by_commit(self):
        v = turn("**deep-mode author · omp** · head `1a2b3c4`\n\n" + fenced({"responses": [
            {"id": "F1", "action": "fixed", "sha": "1a2b3c4d5e", "reason": "stamped external"},
            {"id": "F2", "action": "fixed", "sha": "1a2b3c4d5e", "reason": "repo from identity"},
            {"id": "F3", "action": "dismissed", "reason": "intended, see a.py:3"}]}))
        self.assertEqual(arena.turn_lines(v, False, "964653e3"), [
            "AUTHOR returns!",
            "The head moved to 1a2b3c4.",
            "AUTHOR used FIX! x2 (in 1a2b3c4d)",
            "F1 - stamped external",
            "F2 - repo from identity",
            "AUTHOR used DISMISS!",
            "F3 - intended, see a.py:3",
        ])

    def test_prose_fix_lands_at_the_turn_head(self):
        v = turn("**deep-mode author** · head `0330d961`\n\nRound 2. The P2 is **fixed**: the rail reads “1 step · 1 dropped”.")
        self.assertEqual(arena.turn_lines(v, False, "0330d961")[1:], [
            "Round 2.", "AUTHOR used FIX! (in 0330d961)", 'The P2 is fixed: the rail reads "1 step - 1 dropped".'])

    def test_votes_panel_and_pr_agent(self):
        vote = turn("**deep-mode verifier 2 · omp** · head `abc1234`\n\n" + fenced({"vote": "PASS", "evidence": "tests pass"}))
        self.assertEqual(arena.turn_lines(vote, True), ["VERIFIER 2 appeared!", "VERIFIER 2 voted PASS!", "tests pass"])
        old = turn("**deep-mode verifier 3 · design** · head `abc1234`\n\nVERDICT: DONE (criteria 1)")
        self.assertEqual(arena.turn_lines(old, True)[1], "VERIFIER 3 voted DONE!")
        panel = turn("**deep-mode panel · bot.py** · head `abc1234`\n\nPanel PASS at `abc1234`: 3/3 PASS.\n\n- verifier 1 (omp): PASS")
        self.assertEqual(arena.turn_lines(panel, True)[:2], ["PANEL appeared!", "The panel: 3/3 PASS."])
        agent = turn("## PR Reviewer Guide\n\nRecommended focus areas\n<strong>Build Contamination</strong>")
        self.assertEqual(arena.turn_lines(agent, True), ["PR-AGENT appeared!", "It points at: Build Contamination"])

    def test_fold(self):
        self.assertEqual(arena.fold("`a` — b · c… “d” café ×2 →\n🔍"), 'a - b - c... "d" cafe x2 ->')


class Battle(unittest.TestCase):
    def test_score_votes_and_merge(self):
        sig = "**deep-mode {}** · head `{}`\n\n"
        found = [
            turn(sig.format("reviewer · omp", "aaaaaaa") + fenced({"findings": [
                {"severity": "P1", "file": "a", "line": 1, "claim": "x"}, {"severity": "P2", "file": "b", "line": 2, "claim": "y"}]}), 1),
            turn(sig.format("author · omp", "bbbbbbb") + fenced({"responses": [
                {"id": "F1", "action": "fixed", "sha": "bbbbbbb", "reason": "done"}]}), 2),
            turn(sig.format("verifier 1 · omp", "bbbbbbb") + fenced({"vote": "PASS", "evidence": "ok"}), 3),
            turn(sig.format("verifier 2 · omp", "bbbbbbb") + fenced({"vote": "FAIL", "evidence": "no"}), 4),
            turn(sig.format("panel · bot.py", "bbbbbbb") + "Panel not done at `bbbbbbb`: 1/2 PASS.", 5),
            turn(sig.format("verifier 1 · omp", "ccccccc") + fenced({"vote": "PASS", "evidence": "ok"}), 6),
            turn(sig.format("coordinator · bot.py", "ccccccc") + "Merged `ccccccc` (squash). Panel 3/3.", 7),
        ]
        meta = {"url": "https://github.com/o/r/pull/9", "repo": "o/r", "number": 9, "kind": "pr", "title": "Add x", "state": "merged"}
        b = arena.battle(meta, found)
        after = [t["after"] for t in b["turns"]]
        self.assertEqual([(a["open"], a["peak"]) for a in after], [(2, 2), (1, 2), (1, 2), (1, 2), (1, 2), (1, 2), (1, 2)])
        self.assertEqual(after[4]["votes"], ["PASS", "FAIL", None])
        self.assertEqual(after[5]["votes"], ["PASS", None, None])  # a new round after the panel
        self.assertEqual(b["turns"][-1]["lines"][-1], "PR #9 was merged!")
        self.assertTrue(after[-1]["merged"] and not after[-2]["merged"])
        self.assertEqual((b["intro"], b["outro"]), (["PR #9 wants to merge!", '"Add x"'], []))

    def test_open_issue_outro(self):
        meta = {"url": "u", "repo": "o/r", "number": 4, "kind": "issue", "title": "Bug", "state": "open"}
        b = arena.battle(meta, [turn("**deep-mode author** · head `abc1234`\n\nPlan: fix it.")])
        self.assertEqual((b["label"], b["intro"][0], b["outro"]), ("Issue #4", "Issue #4 was opened!", ["The conversation goes on..."]))

    def test_sprites_are_16_by_16_in_palette(self):
        for name, rows in arena.SPRITES.items():
            self.assertEqual(len(rows), 16, name)
            for row in rows:
                self.assertEqual(len(row), 16, (name, row))
                self.assertTrue(set(row) <= set(".0123"), (name, row))
        self.assertTrue({"author", "reviewer", "verifier", "panel", "coordinator", "pr-agent", "pr", "issue"} <= set(arena.SPRITES))

    def test_page_escapes_comment_text(self):
        html = arena.page(arena.payload([], ["</script><!--"], live=False))
        self.assertNotIn("</script><!--", html)
        self.assertNotIn("__ARENA_DATA__", html)
        self.assertNotIn("__FONT_HEX__", html)


if __name__ == "__main__":
    unittest.main()
