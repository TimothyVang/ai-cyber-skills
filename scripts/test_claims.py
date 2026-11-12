"""Who holds an issue: the claim rule that pr-overlap.py and sync-roadmap.py share.

Both scripts read the same fake GitHub data here. No network and no gh calls.
"""
import datetime as dt
import importlib.util
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = "owner/name"
TODAY = dt.date(2026, 11, 12)
PAST, FUTURE = "2026-11-01", "2026-11-19"


def load(filename):
    name = filename.replace("-", "_").removesuffix(".py")
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module  # dataclasses look the module up by name
    spec.loader.exec_module(module)
    return module


overlap = load("pr-overlap.py")
roadmap = load("sync-roadmap.py")


def claim(login, expires, files="a.py"):
    return login, f"{overlap.CLAIM_MARKER}\nClaimed by @{login} via /contribute\nPlan: p\nFiles: {files}\nExpires: {expires}"


def unclaim(login):
    return login, f"{overlap.UNCLAIM_MARKER}\nReleased by @{login}: no time"


def serve(board):
    """Point both scripts at a fake board: issue number -> (assignees, [(login, comment body), ...])."""
    def gh(path):
        if "/comments" in path:
            number = int(path.split("/issues/")[1].split("/")[0])
            return [{"id": i, "created_at": f"2026-10-{i + 1:02d}T00:00:00Z", "user": {"login": login}, "body": body}
                    for i, (login, body) in enumerate(board[number][1])]
        if "/pulls" in path:
            return []
        return [{"number": n, "title": f"task {n}", "html_url": f"https://example.test/{n}",
                 "labels": [{"name": roadmap.LABEL}], "assignees": [{"login": a} for a in assignees],
                 "comments": len(comments)}
                for n, (assignees, comments) in board.items()]

    overlap.gh_api_list, overlap._today, roadmap.gh_api = gh, lambda: TODAY, gh
    overlap.open_prs = lambda repo, exclude_pr=None: []


def holders(board):
    """Each script's issue -> claimants for the board."""
    serve(board)
    from_overlap = {}
    for c in overlap.fetch_active_claims(REPO):
        from_overlap.setdefault(c.issue, []).extend(c.author.split(", "))
    from_roadmap = {r["number"]: r["claimants"] for r in roadmap.collect(REPO, TODAY) if r["claimants"]}
    return from_overlap, from_roadmap


class Claims(unittest.TestCase):
    def assert_holders(self, board, expected):
        from_overlap, from_roadmap = holders(board)
        self.assertEqual(from_overlap, expected, "pr-overlap.py")
        self.assertEqual(from_roadmap, expected, "sync-roadmap.py")

    def test_expired_claim_frees_the_issue_though_the_claimant_is_still_assigned(self):
        self.assert_holders({7: (["ann"], [claim("ann", PAST)])}, {})

    def test_released_claim_frees_the_issue_though_the_claimant_is_still_assigned(self):
        self.assert_holders({7: (["ann"], [claim("ann", FUTURE), unclaim("ann")])}, {})

    def test_active_claim_with_self_assign_lists_the_claimant_once(self):
        self.assert_holders({7: (["ann"], [claim("ann", FUTURE)])}, {7: ["ann"]})

    def test_assignee_who_never_posted_a_claim_holds_the_issue(self):
        self.assert_holders({7: (["max"], []), 8: (["max"], [claim("ann", PAST)])}, {7: ["max"], 8: ["max"]})

    def test_newer_active_claim_drops_an_earlier_claimant_left_assigned(self):
        self.assert_holders({7: (["ann"], [claim("ann", PAST), claim("bob", FUTURE)])}, {7: ["bob"]})

    def test_later_claimant_who_withdraws_leaves_the_earlier_claim_standing(self):
        self.assert_holders({7: ([], [claim("ann", FUTURE), claim("bob", FUTURE), unclaim("bob")])}, {7: ["ann"]})

    def test_two_live_claims_both_hold_and_both_guard_their_files(self):
        board = {7: ([], [claim("ann", FUTURE, "src/a.py"), claim("bob", FUTURE, "docs/")])}
        self.assert_holders(board, {7: ["ann", "bob"]})
        hits = overlap.find_overlaps(REPO, ["src/a.py"])
        self.assertEqual([(h["author"], h["overlapping"]) for h in hits], [("ann", ["src/a.py"])])
        self.assertEqual(roadmap.collect(REPO, TODAY)[0]["files"], ["docs/", "src/a.py"])

    def test_an_authors_newest_claim_replaces_their_earlier_ones(self):
        self.assert_holders({7: ([], [claim("ann", FUTURE), claim("ann", PAST)])}, {})
        self.assert_holders({7: ([], [claim("ann", FUTURE), claim("ann", FUTURE), unclaim("ann")])}, {})
        self.assert_holders({7: ([], [claim("ann", FUTURE), unclaim("ann"), claim("ann", FUTURE)])}, {7: ["ann"]})

    def test_active_claim_keeps_an_assignee_who_never_posted_a_claim(self):
        self.assert_holders({7: (["max"], [claim("ann", FUTURE)])}, {7: ["ann", "max"]})


if __name__ == "__main__":
    unittest.main()
