"""Pure-function tests for show_thread.py and arena.py (no network). Run: python -m unittest test_arena"""

import contextlib
import io
import json
import sys
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import arena  # noqa: E402
import arena_tui as tui  # noqa: E402
import show_thread as st  # noqa: E402


def comment(body, cid=1, user=("o", "User", "OWNER")):
    login, kind, association = user
    return {"id": cid, "html_url": f"https://github.com/o/r/pull/1#issuecomment-{cid}",
            "created_at": "2026-11-11T21:56:00Z", "body": body,
            "user": {"login": login, "type": kind}, "author_association": association}


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


class Voices(unittest.TestCase):
    def test_pr_agent_by_its_own_headings_only(self):
        self.assertEqual(st.voice(comment("## PR Reviewer Guide 🔍\n\nNo major issues detected"))["kind"], "pr-agent")
        self.assertIsNone(st.voice(comment("Please address what pr-agent flagged.\nP1: a.py:3 — wrong")))

    def test_only_bots_and_writers_speak_as_bots(self):
        signed = "**deep-mode reviewer** · head `abc1234`\n\nP1: a.py:3 — wrong"
        self.assertEqual(st.voice(comment(signed, user=("app[bot]", "Bot", "NONE")))["kind"], "reviewer")
        self.assertEqual(st.voice(comment(signed, user=("m", "User", "MEMBER")))["kind"], "reviewer")
        for outsider in (("x", "User", "NONE"), ("x", "User", "CONTRIBUTOR")):
            self.assertIsNone(st.voice(comment(signed, user=outsider)))
            self.assertIsNone(st.voice(comment("## PR Reviewer Guide 🔍\n\nNo major issues detected", user=outsider)))

    def test_odd_content_never_raises(self):
        signed = lambda body: comment("**deep-mode author · omp** · head `abc1234`\n\n" + body)
        for payload in ('{"findings": null}', '{"findings": "none"}', '{"responses": {"a": 1}}'):
            st.voice(signed(fenced(json.loads(payload))))
        mixed = st.voice(signed(fenced({"findings": ["x", {"severity": "P1", "file": "a.py", "line": 3, "claim": "c"}]})))
        self.assertEqual(mixed["gist"], ["P1: a.py:3 — c"])
        # Comments near GitHub's 65,536-character limit that defeat a backtracking pattern.
        for hostile in ("1. **" + " " * 65000, "<!--" * 16000, "```{x" * 13000):
            started = time.perf_counter()
            st.voice(signed(hostile))
            self.assertLess(time.perf_counter() - started, 1.0)
        self.assertEqual(st.clean("Suggestion&nbsp;&amp; <b>x</b>"), "Suggestion\xa0&  x ")

    def test_backticks_inside_json_strings_keep_the_block(self):
        v = st.voice(comment("**deep-mode reviewer** · head `abc1234`\n\nSummary.\n\n" + fenced({"findings": [
            {"id": "F5", "severity": "P1", "file": "a.py", "line": 3, "claim": "a ``` fence ends it", "evidence": "```json\n{"}]})))
        self.assertEqual((v["gist"], v["findings"]), (["P1: a.py:3 — a ``` fence ends it"], {"F5": "a.py a ``` fence ends it"}))

    def test_only_pr_agent_gets_the_pr_agent_gist(self):
        v = st.voice(comment("**deep-mode reviewer** · head `abc1234`\n\n" + fenced({"findings": [
            {"id": "F1", "severity": "P2", "file": "s.py", "line": 9, "claim": "a `PR Reviewer Guide` mention is misread"}]})))
        self.assertEqual(v["gist"], ["P2: s.py:9 — a `PR Reviewer Guide` mention is misread"])


class PrAgentGist(unittest.TestCase):
    GUIDE = ("## PR Reviewer Guide 🔍\n\n<table>\n"
             "<tr><td>⏱️&nbsp;<strong>Estimated effort to review</strong>: 4</td></tr>\n"
             "<tr><td>🧪&nbsp;<strong>PR contains tests</strong></td></tr>\n"
             "<tr><td>🔒&nbsp;<strong>No security concerns identified</strong></td></tr>\n{}</table>\n"
             "<details><summary>Resolved</summary><strong>Old finding</strong></details>")

    def test_no_focus_section_is_its_all_clear_line(self):
        body = self.GUIDE.format("<tr><td>⚡&nbsp;<strong>No major issues detected</strong></td></tr>\n")
        self.assertEqual(st.gist(body, "pr-agent"), ["No major issues detected"])
        self.assertEqual(st.gist(self.GUIDE.format(""), "pr-agent"), ["No major issues detected"])

    def test_focus_titles_come_from_the_focus_section_only(self):
        body = self.GUIDE.format("<tr><td>⚡&nbsp;<strong>Recommended focus areas for review</strong><br>"
                                 "<a href='x'><strong>Shared Checkout</strong></a><br>text<br>"
                                 "<a href='y'><strong>Unreviewed Binary</strong></a></td></tr>\n")
        self.assertEqual(st.gist(body, "pr-agent"), ["focus: Shared Checkout; Unreviewed Binary"])


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

    def test_re_reported_findings_count_once(self):
        sig = "**deep-mode {}** · head `{}`\n\n"
        f = lambda i, sev="P1": {"id": i, "severity": sev, "file": "a", "line": 1, "claim": i}
        answer = lambda *ids: fenced({"responses": [{"id": i, "action": "fixed", "reason": f"r{n}"} for n, i in enumerate(ids)]})
        found = [
            turn(sig.format("reviewer · security", "aaaaaaa") + fenced({"findings": [f("F1"), f("F2", "P2")]}), 1),
            turn(sig.format("reviewer · UI", "aaaaaaa") + fenced({"findings": [f("F1")]}), 2),  # another lens's own F1
            turn(sig.format("author", "bbbbbbb") + answer("F2", "V1"), 3),  # V1: a panel failure, never a review finding
            # The re-review lists only what is still open: F1 again, and a new F3.
            turn(sig.format("reviewer · security", "bbbbbbb") + fenced({"findings": [f("F1"), f("F3")]}), 4),
            turn(sig.format("author", "ccccccc") + answer("F1", "F1"), 5),
            turn(sig.format("reviewer · security", "ccccccc") + fenced({"findings": []}), 6),
        ]
        meta = {"url": "u", "repo": "o/r", "number": 9, "kind": "pr", "title": "x", "state": "open"}
        after = [t["after"] for t in arena.battle(meta, found)["turns"]]
        self.assertEqual([(a["open"], a["peak"]) for a in after], [(2, 2), (3, 3), (2, 3), (3, 3), (1, 3), (0, 3)])

    def test_prose_answer_closes_the_finding_it_names(self):
        sig = "**deep-mode {}** · head `{}`\n\n"
        found = [
            turn(sig.format("reviewer", "aaaaaaa") + fenced({"findings": [
                {"id": "F1", "severity": "P1", "file": "a.py", "line": 1, "claim": "Windows encoding crash"},
                {"id": "F2", "severity": "P2", "file": "b.py", "line": 2, "claim": "Empty pane after reload"}]}), 1),
            turn(sig.format("author", "bbbbbbb") + "Answers:\n\n1. **Empty pane: fixed.** Reload keeps it.", 2),
            turn(sig.format("author", "ccccccc") + fenced({"responses": [{"id": "F1", "action": "fixed", "reason": "utf-8"}]}), 3),
        ]
        meta = {"url": "u", "repo": "o/r", "number": 9, "kind": "pr", "title": "x", "state": "open"}
        self.assertEqual([t["after"]["open"] for t in arena.battle(meta, found)["turns"]], [2, 1, 0])

    def test_prose_answer_sharing_no_words_closes_nothing(self):
        sig = "**deep-mode {}** · head `{}`\n\n"
        found = [
            turn(sig.format("reviewer", "aaaaaaa") + fenced({"findings": [
                {"id": "F1", "severity": "P1", "file": "a.py", "line": 1, "claim": "Windows encoding crash"}]}), 1),
            turn(sig.format("author", "bbbbbbb") + "Answers:\n\n1. **Telemetry: fixed.** Removed.", 2),
        ]
        meta = {"url": "u", "repo": "o/r", "number": 9, "kind": "pr", "title": "x", "state": "open"}
        self.assertEqual([t["after"]["open"] for t in arena.battle(meta, found)["turns"]], [1, 1])

    def test_digest_of_drawn_turns_without_bodies(self):
        meta = {"url": "u", "repo": "o/r", "number": 9, "kind": "pr", "title": "x", "state": "open"}
        drawn = arena.battle(meta, [turn("**deep-mode author** · head `abc1234`\n\nPlan: fix it.")])["turns"]
        self.assertIn("    Plan: fix it.", st.digest(drawn))

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


class TerminalStatus(unittest.TestCase):
    def test_live_time_on_the_dialog_border_and_the_error_below(self):
        ui = tui.UI(two_threads(), live=True)
        ui.status, ui.error = tui.status_of({"generated": "2026-11-11T21:56:00+00:00", "errors": []}, tui.glyphs("mono"))
        lines = plain(screen(ui, 80, 24, "mono"))
        self.assertIn("live · updated", lines[-4])
        self.assertIn("q quit", lines[-1])
        live, ui.error = tui.status_of({"generated": "x", "errors": ["gh api failed: HTTP 502"]}, tui.glyphs("mono"))
        lines = plain(screen(ui, 60, 20, "mono"))
        self.assertIn("error: gh api failed: HTTP 502", lines[-1])
        self.assertIn("live · updated", lines[-4])  # the last good time stays

    def test_partial_refetch_moves_the_time_and_a_failed_one_keeps_it(self):
        ui, g = tui.UI(two_threads(), live=True), tui.glyphs("mono")
        ui.status = "refreshing..."
        tui.took(ui, {"threads": [], "generated": "2026-11-11T21:56:00+00:00", "errors": ["o/r#3: HTTP 502"]}, g)
        self.assertIn("updated", ui.status)
        self.assertIn("HTTP 502", ui.error)
        kept = ui.status
        tui.took(ui, {"errors": ["gh not found"]}, g)
        self.assertEqual((ui.status, ui.error), (kept, "error: gh not found"))

    def test_a_failed_gh_fetch_serves_the_old_threads_at_their_old_time(self):
        source = arena.Source([], "o/r", 5)
        source.data = {**arena.payload(two_threads(), [], live=True), "generated": "2026-11-11T21:56:00+00:00"}
        original = arena.gather
        def offline(*_):
            raise st.GhError("error connecting to api.github.com")
        arena.gather = offline
        try:
            got = source.get(force=True)
        finally:
            arena.gather = original
        self.assertEqual((len(got["threads"]), got["generated"]), (2, "2026-11-11T21:56:00+00:00"))
        self.assertIn("error connecting", got["errors"][0])

    def test_code_spans_keep_their_markup(self):
        body = "Round 2: an unclosed `<!--` runs to `\\Z`; run `arena.py <url>`.\n<!-- hidden -->Next <b>line</b>."
        self.assertEqual(st.clean(body), "Round 2: an unclosed `<!--` runs to `\\Z`; run `arena.py <url>`.\nNext  line .")

    def test_hostile_bodies_never_reach_the_terminal_or_raise(self):
        comment = lambda body: {"id": 1, "html_url": "", "created_at": "2026-11-11T00:00:00Z", "body": body,
                                "user": {"login": "me", "type": "User"}, "author_association": "OWNER"}
        sig = "**deep-mode reviewer** · head `abc1234`\n\n"
        osc = st.voice(comment(sig + fenced({"findings": [{"severity": "P1", "file": "a", "line": 1,
                                                          "claim": "\x1b]52;c;aGk=\x07\x9b2J ok"}]})))
        printed = "\n".join(st.digest([osc]) + st.digest([osc], full=True))
        self.assertNotRegex(printed, r"[\x00-\x08\x0b-\x1f\x7f-\x9f]")
        self.assertIn("ok", printed)
        st.voice(comment(sig + "```json\n" + "[" * 5000 + "\n```"))  # deeper than json parses
        st.voice(comment(sig + "&#" + "9" * 5000 + ";"))  # longer than int() takes
        st.voice(comment(sig + "`&#" + "9" * 5000 + ";`"))  # the same inside a code span
        started = time.perf_counter()
        arena.turn_lines(st.voice(comment("**deep-mode panel** · head `abc1234`\n\n" + "7" * 65000)), False)
        self.assertLess(time.perf_counter() - started, 1.0)

    def test_missing_gh_is_a_plain_error(self):
        original = st.subprocess.run
        def missing(*_, **__):
            raise FileNotFoundError("gh")
        st.subprocess.run = missing
        try:
            with self.assertRaisesRegex(st.GhError, "not installed"):
                st.gh_json("repos/o/r/issues/1")
        finally:
            st.subprocess.run = original


def two_threads():
    sig = "**deep-mode {}** · head `{}`\n\n"
    review = turn(sig.format("reviewer · omp (openai/gpt-x)", "aaaaaaa") + fenced({"findings": [
        {"severity": "P1", "file": "src/very/long/path/to/a/module/file_name.py", "line": 12,
         "claim": "the bar drops “too early” when \x1b[31mred\x1b[0m text arrives"}]}), 1)
    fix = turn(sig.format("author · omp", "bbbbbbb") + fenced({"responses": [
        {"id": "F1", "action": "fixed", "sha": "bbbbbbb", "reason": "done"}]}), 2)
    pr = arena.battle({"url": "https://github.com/o/r/pull/12345", "repo": "o/r", "number": 12345, "kind": "pr",
                       "title": "A pull request", "state": "merged"}, [review, fix])
    issue = arena.battle({"url": "https://github.com/o/r/issues/7", "repo": "o/r", "number": 7, "kind": "issue",
                          "title": "An issue", "state": "open"}, [turn(sig.format("author · omp", "ccccccc") + "Plan: x.", 3)])
    return [pr, issue]


def screen(ui, w, h, mode="truecolor"):
    ui.layout(tui.text_cols(w))
    return tui.frame(ui, w, h, mode, arena.SPRITES)


def plain(lines):
    return [tui.ANSI.sub("", line) for line in lines]


class TerminalFrame(unittest.TestCase):
    SIZES = [(60, 20), (80, 24), (100, 30), (120, 40), (200, 60)]

    def battle_ui(self):
        ui = tui.UI(two_threads(), live=True)
        ui.key("enter")
        return ui

    def test_every_line_fits_the_width_in_every_mode(self):
        for mode in ("truecolor", "256", "mono", "ascii"):
            for w, h in self.SIZES:
                for ui in (tui.UI(two_threads()), self.battle_ui()):
                    for _ in range(6):
                        lines = screen(ui, w, h, mode)
                        self.assertEqual(len(lines), h)
                        for line in plain(lines):
                            self.assertEqual(len(line), w, (mode, w, h, ui.mode, line))
                        ui.key("enter")
                        ui.tick(ui.now + 10)

    def test_dialog_text_is_shown_and_typed(self):
        ui = self.battle_ui()
        lines = plain(screen(ui, 80, 24))
        self.assertFalse(any("wants to merge" in line for line in lines))  # nothing typed yet
        ui.tick(5.0)
        lines = plain(screen(ui, 80, 24))
        self.assertTrue(any("PR #12345 wants to merge!" in line for line in lines))
        self.assertTrue(any("TURN 0/2" in line for line in lines))

    def test_finding_reaches_the_dialog_without_escape_codes_from_the_comment(self):
        ui = self.battle_ui()
        ui.key("l")  # latest turn is the author's; step back into the review
        ui.key("home")
        text = []
        for _ in range(12):
            ui.tick(ui.now + 10)
            text += plain(screen(ui, 80, 24, "mono"))
            ui.key("enter")
        joined = "\n".join(text)
        self.assertIn("It found a P1:", joined)
        self.assertIn("It's super effective!", joined)
        self.assertNotIn("\x1b", joined)

    def test_menu_cursor_marks_the_selected_thread(self):
        ui = tui.UI(two_threads())
        ui.key("down")
        lines = plain(screen(ui, 80, 24, "mono"))
        cursor = [line for line in lines if "►" in line]
        self.assertEqual(len(cursor), 1)
        self.assertIn("ISSUE #7", cursor[0])
        ui.key("up")
        self.assertIn("PR #12345", next(line for line in plain(screen(ui, 80, 24, "mono")) if "►" in line))

    def test_ascii_and_mono_have_no_escape_codes(self):
        for mode in ("ascii", "mono"):
            for ui in (tui.UI(two_threads()), self.battle_ui()):
                ui.tick(10)
                for line in screen(ui, 80, 24, mode):
                    self.assertNotIn("\x1b", line)
                    if mode == "ascii":
                        self.assertTrue(all(" " <= ch < "\x7f" for ch in line), line)

    def test_too_small(self):
        lines = screen(self.battle_ui(), 59, 20)
        self.assertIn("make the window larger", lines[0])
        self.assertTrue(all(len(line) == 59 for line in lines))

    def test_resize_keeps_the_reader_on_the_same_turn(self):
        ui = self.battle_ui()
        screen(ui, 120, 40)
        ui.key("l")
        turn_before = ui.shown_turn()
        screen(ui, 60, 20)
        self.assertEqual(ui.shown_turn(), turn_before)

    def test_live_turn_moves_a_reader_waiting_at_the_end(self):
        threads = two_threads()
        pr = threads[0]
        ui = tui.UI([{**pr, "outro": ["The conversation goes on..."]}])
        screen(ui, 80, 24)
        ui.go(len(ui.boxes) - 1, full=True)
        grown = {**pr, "turns": pr["turns"] + [{**pr["turns"][-1], "id": 99, "lines": ["AUTHOR returns!"]}],
                 "outro": ["The conversation goes on..."]}
        ui.apply([grown])
        self.assertEqual(ui.shown_turn(), 2)
        self.assertEqual(ui.boxes[ui.bi]["lines"][0], "AUTHOR returns!")

    def test_keys_and_colour_modes(self):
        self.assertEqual(tui.parse_posix("\x1b[A\x1b[B\x1b[C\x1b[D\r \x7f\x1bq"),
                         ["up", "down", "right", "left", "enter", "space", "backspace", "esc", "q"])
        self.assertEqual(tui.parse_windows(["\xe0", "H", "\x00", "P", "\xe0", "M", "\r", "\x08", "\x1b", "a"]),
                         ["up", "down", "right", "enter", "backspace", "esc", "a"])
        self.assertEqual(tui.colour_mode({"COLORTERM": "truecolor"}), "truecolor")
        self.assertEqual(tui.colour_mode({"WT_SESSION": "x"}), "truecolor")
        self.assertEqual(tui.colour_mode({}), "256")
        self.assertEqual(tui.colour_mode({"NO_COLOR": "1", "WT_SESSION": "x"}), "mono")
        self.assertEqual(tui.colour_mode({"COLORTERM": "truecolor"}, ascii_flag=True), "ascii")
        self.assertEqual(tui.fold("a\x1b[31mb\x07c"), "a [31mb c")

    def test_quit_keys(self):
        ui = tui.UI(two_threads())
        self.assertEqual(ui.key("esc"), "quit")  # Esc on the menu quits
        ui.key("enter")
        self.assertIsNone(ui.key("esc"))         # Esc in a battle goes back to the menu
        self.assertEqual(ui.mode, "menu")
        ui.key("enter")
        self.assertEqual(ui.key("q"), "quit")


class InlineFrames(unittest.TestCase):
    LONG = ("the findings bar drops before the author answers, because the score counts each answer line "
            "rather than each finding id; a turn that answers one finding twice empties the bar too early, "
            "and the vote pips then reset on a second panel round even when nothing changed at the head")

    def threads(self):
        """PR #12345 with turns 1 (review), 2 (fix), 4 (a long review), and issue #7 with turn 3."""
        sig = "**deep-mode {}** · head `{}`\n\n"
        review = turn(sig.format("reviewer · omp", "aaaaaaa") + fenced({"findings": [
            {"severity": "P1", "file": "a.py", "line": 1, "claim": "x"}]}), 1)
        fix = turn(sig.format("author · omp", "bbbbbbb") + fenced({"responses": [
            {"id": "F1", "action": "fixed", "sha": "bbbbbbb", "reason": "done"}]}), 2)
        long = turn(sig.format("reviewer · omp", "ddddddd") + fenced({"findings": [
            {"severity": "P2", "file": "arena.py", "line": 7, "claim": self.LONG}]}), 4)
        pr = arena.battle({"url": "https://github.com/o/r/pull/12345", "repo": "o/r", "number": 12345, "kind": "pr",
                           "title": "A pull request", "state": "open"}, [review, fix, long])
        return [pr, two_threads()[1]]

    def test_lines_fit_and_no_escape_codes(self):
        for mode in ("mono", "ascii"):
            for width in (60, 80, 120):
                for line in tui.frames(self.threads(), last=10, width=width, mode=mode, sprites=arena.SPRITES):
                    self.assertLessEqual(len(line), width, (mode, width, line))
                    self.assertNotIn("\x1b", line)
                    if mode == "ascii":
                        self.assertTrue(all(" " <= ch < "\x7f" for ch in line), line)
        coloured = tui.frames(self.threads(), last=1, width=80, mode="truecolor", sprites=arena.SPRITES)
        self.assertTrue(any("\x1b[" in line for line in coloured))
        self.assertTrue(all(len(line) <= 80 for line in plain(coloured)))

    def test_dialog_boxes_close_at_the_width(self):
        out = tui.frames(self.threads(), last=1, width=80, mode="mono", sprites=arena.SPRITES)
        dialog = [line for line in out if line.startswith(("╔", "║", "╚"))]
        self.assertTrue(dialog)
        self.assertTrue(all(len(line) == 80 and line.endswith(("╗", "║", "╝")) for line in dialog))

    def test_since_takes_only_newer_turns(self):
        out = "\n".join(tui.frames(self.threads(), since=2, width=80, sprites=arena.SPRITES))
        self.assertEqual(out.count("TURN "), 2)
        self.assertIn("TURN 3/3", out)                 # the PR's comment 4
        self.assertIn("TURN 1/1", out)                 # the issue's comment 3
        self.assertNotIn("TURN 1/3", out)
        self.assertNotIn("TURN 2/3", out)
        none = tui.frames(self.threads(), since=4, width=80, sprites=arena.SPRITES)
        self.assertEqual(none, ["arena: no bot turns since 4", "arena: newest comment 4 (next: --since 4)"])

    def test_default_and_last(self):
        out = "\n".join(tui.frames(self.threads(), width=80, sprites=arena.SPRITES))
        self.assertEqual(out.count("TURN "), 4)  # the PR's 3 turns (the default is the newest 3) and the issue's 1
        out = "\n".join(tui.frames(self.threads(), last=1, width=80, sprites=arena.SPRITES))
        self.assertEqual(out.count("TURN "), 2)

    def test_long_finding_in_full(self):
        out = tui.frames(self.threads(), last=1, width=60, mode="mono", sprites=arena.SPRITES)
        text = " ".join(line.strip("║ ") for line in out if line.startswith("║"))
        self.assertIn(self.LONG, " ".join(text.split()))
        self.assertNotIn("...", text)

    def test_trailing_id_line(self):
        self.assertEqual(tui.frames(self.threads(), width=80, sprites=arena.SPRITES)[-1],
                         "arena: newest comment 4 (next: --since 4)")

    def run_frames(self, threads, errors):
        original_gather, original_argv = arena.gather, sys.argv
        arena.gather = lambda *_: (threads, errors)
        sys.argv = ["arena.py", "https://github.com/o/r/pull/9", "--frames"]
        out = io.StringIO()
        try:
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
                try:
                    code = arena.main()
                except SystemExit as stop:
                    code = stop.code
        finally:
            arena.gather, sys.argv = original_gather, original_argv
        return code, out.getvalue()

    def test_a_failed_fetch_is_not_a_quiet_thread(self):
        code, out = self.run_frames([], ["o/r#9: gh: Not Found (HTTP 404)"])
        self.assertNotIn(code, (0, None))
        self.assertNotIn("no bot turns", out)

    def test_a_partial_failure_keeps_the_cursor(self):
        code, out = self.run_frames(self.threads(), ["o/r#8: HTTP 502"])
        self.assertEqual(code, 1)
        self.assertIn("TURN", out)
        self.assertNotIn("--since 4)", out)
        self.assertIn("run again with the same --since", out.strip().splitlines()[-1])


if __name__ == "__main__":
    unittest.main()
