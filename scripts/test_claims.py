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


def claim(login, expires):
    return login, f"{overlap.CLAIM_MARKER}\nClaimed by @{login} via /contribute\nPlan: p\nFiles: a.py\nExpires: {expires}"


def unclaim(login):
    return login, f"{overlap.UNCLAIM_MARKER}\nReleased by @{login}: no time"


def holders(board):
    """board maps issue number -> (assignees, [(login, comment body), ...]). Returns each script's issue -> claimants."""
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
    from_overlap = {c.issue: c.author.split(", ") for c in overlap.fetch_active_claims(REPO)}
    from_roadmap = {r["number"]: r["claimants"] for r in roadmap.collect(REPO, TODAY) if r["claimants"]}
    return from_overlap, from_roadmap


class AssigneeClaims(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
