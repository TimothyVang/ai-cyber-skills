"""Deterministic tests at planning, consensus, compiler and ACP transcript boundaries.

Run: python -m unittest discover -s <this folder> -p test_plan.py
Remote responses alone are stubbed; the planner, validators and compiler are real.
"""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import loop
import plan

MODEL = "openai-codex/gpt-6-astra"


def measurement():
    return {"metric": "passing fixed cases", "target": 10, "direction": "equals", "unit": "cases",
            "measurement": "Count successful cases in fixed-check.json; any missing case fails",
            "evidence_source": "fixed-check.json", "denominator": "10 frozen cases",
            "workload": "fixtures/v1.json", "sample_count": 10,
            "anti_gaming": "Keep all ten case IDs and protected checker unchanged"}


def candidate(contract):
    return {"goal": "All ten consumer cases pass", "status": "ready", "contract_sha256": plan.digest(contract),
            "criteria": [{"id": "cases", **measurement(), "baseline": 8,
                          "baseline_evidence": "context: fixed-check.json reports 8/10",
                          "baseline_milestone": None}],
            "milestones": [{"id": "fix", "title": "Fix both failing cases", "depends_on": [],
                            "criteria": ["cases"], "establishes_baseline": [], "acceptance": measurement(),
                            "iterations": 1, "cost_usd": 0.5, "minutes": 5}],
            "questions": [], "evidence_requests": []}


def vote(draft, contract, lens, choice="approve"):
    return {"candidate_sha256": plan.digest(draft), "contract_sha256": plan.digest(contract),
            "lens": lens, "vote": choice, "reasons": ["The fixed ten-case check measures the requested outcome"],
            "questions": ([{"question": "Which consumer is primary?", "recommendation": "Existing API clients"}]
                          if choice == "needs_context" else []), "evidence_requests": []}


class Remote:
    def __init__(self, drafts, votes=None, unavailable=None):
        self.drafts, self.votes, self.unavailable = drafts, votes or {}, unavailable
        self.calls = []
        self.round = 0

    def __call__(self, prompt, directory):
        self.calls.append((prompt, directory))
        data = json.loads(prompt.split("\nINPUT DATA:\n", 1)[1])
        if "lens" not in data:
            self.round += 1
            return json.dumps({"candidate": self.drafts[min(self.round - 1, len(self.drafts) - 1)],
                               "self_grill": {key: "Concise author-only conclusion" for key in plan.GRILL_KEYS}})
        if data["lens"] == self.unavailable:
            raise plan.Unavailable("reviewer unavailable")
        choice = self.votes.get(self.round, {}).get(data["lens"], "approve")
        return json.dumps(vote(data["candidate"], data["contract"], data["lens"], choice))


class PlanningCase(unittest.TestCase):
    def setUp(self):
        scratch = Path(__file__).resolve().parents[6] / ".scratch" / "planner-tests"
        scratch.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=scratch)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        (self.root / "check.sh").write_text("exit 37\n", encoding="utf-8")
        self.contract = {"check": "bash check.sh", "protect": ["check.sh", "absent:conftest.py"],
                         "constraints": "Only repair implementation; no network, installs or nested loops",
                         "max_iterations": 3, "max_cost_usd": 1, "iteration_minutes": 10, "check_minutes": 2}
        self.draft = candidate(self.contract)
        self.output = self.root / "out"

    def run_plan(self, remote, rounds=2):
        return plan.plan("Make all ten cases pass", "Fixed checker measures 8 of 10 passing cases",
                         self.contract, self.root, self.output, MODEL, remote, rounds)

    def test_two_of_three_approves_and_retains_minority(self):
        remote = Remote([self.draft], {1: {plan.LENSES[2]: "revise"}})
        result = self.run_plan(remote)
        self.assertEqual(result["state"], "approved_draft")
        self.assertEqual(result["goal_sha256"], hashlib.sha256((self.output / "goal.md").read_bytes()).hexdigest())
        self.assertFalse(result["executed"])
        self.assertTrue(result["draft"])
        self.assertEqual(len(result["rounds"][0]["minority_report"]), 1)
        self.assertEqual(len(remote.calls), 4)
        self.assertEqual(len({directory for _, directory in remote.calls}), 4)
        for prompt, _ in remote.calls[1:]:
            self.assertNotIn("Concise author-only conclusion", prompt)
            data = json.loads(prompt.split("\nINPUT DATA:\n", 1)[1])
            self.assertNotIn("reviews", data)
            self.assertNotIn("revision_feedback", data)
            self.assertEqual(data["original_request"], "Make all ten cases pass")
        self.assertEqual((self.root / "check.sh").read_text(), "exit 37\n")
        self.assertFalse((self.root / "conftest.py").exists())

    def test_tie_fails_closed_without_revision(self):
        remote = Remote([self.draft], {1: dict(zip(plan.LENSES, ("approve", "revise", "needs_context")))})
        result = self.run_plan(remote)
        self.assertEqual(result["state"], "no_consensus")
        self.assertEqual(len(remote.calls), 4)
        self.assertFalse((self.output / "goal.md").exists())

    def test_unavailable_reviewer_still_attempts_all_three(self):
        remote = Remote([self.draft], unavailable=plan.LENSES[0])
        result = self.run_plan(remote)
        self.assertEqual(result["state"], "unavailable")
        self.assertEqual(len(remote.calls), 4)
        self.assertFalse((self.output / "goal.md").exists())

    def test_missing_vote_and_duplicate_lens_fail_closed(self):
        votes = [vote(self.draft, self.contract, lens) for lens in plan.LENSES]
        with self.assertRaises(plan.Invalid):
            plan.consensus(self.draft, self.contract, votes[:2])
        votes[2] = votes[1]
        with self.assertRaises(plan.Invalid):
            plan.consensus(self.draft, self.contract, votes)

    def test_changed_candidate_invalidates_votes(self):
        votes = [vote(self.draft, self.contract, lens) for lens in plan.LENSES]
        changed = copy.deepcopy(self.draft)
        changed["goal"] = "Another goal"
        with self.assertRaisesRegex(plan.Invalid, "stale"):
            plan.consensus(changed, self.contract, votes)

    def test_contract_cannot_be_rewritten_by_candidate(self):
        for mutation in ({"contract_sha256": "0" * 64}, {"check": "exit 0"}, {"protect": "none"}):
            with self.subTest(mutation=mutation):
                changed = {**self.draft, **mutation}
                with self.assertRaises(plan.Invalid):
                    plan.compile_goal(changed, self.contract, MODEL, self.root)

    def test_mutated_operator_contract_is_rejected(self):
        remote = Remote([self.draft])
        def mutate(prompt, directory):
            result = remote(prompt, directory)
            if directory.name == plan.LENSES[-1]:
                self.contract["check"] = "exit 0"
            return result
        result = self.run_plan(mutate)
        self.assertEqual(result["state"], "invalid")
        self.assertFalse((self.output / "goal.md").exists())

    def test_material_preference_questions_are_not_guessed(self):
        self.draft.update(status="needs_context", criteria=[], milestones=[],
                          questions=[{"question": "Which clients need support?", "recommendation": "Current API clients"}])
        remote = Remote([self.draft])
        result = self.run_plan(remote)
        self.assertEqual(result["state"], "needs_context")
        self.assertEqual(len(remote.calls), 4)
        self.assertEqual(result["questions"][0]["recommendation"], "Current API clients")
        self.assertFalse((self.output / "goal.md").exists())

    def test_factual_gaps_are_host_evidence_requests(self):
        self.draft.update(status="needs_context", criteria=[], milestones=[],
                          evidence_requests=[{"request": "Find supported API versions", "source": "project API schema"}])
        result = self.run_plan(Remote([self.draft]))
        self.assertEqual(result["state"], "needs_context")
        self.assertEqual(result["questions"], [])
        self.assertEqual(result["evidence_requests"][0]["source"], "project API schema")

    def test_majority_needs_context_blocks_ready_author(self):
        choices = {1: {plan.LENSES[0]: "needs_context", plan.LENSES[1]: "needs_context"}}
        result = self.run_plan(Remote([self.draft], choices))
        self.assertEqual(result["state"], "needs_context")
        self.assertFalse((self.output / "goal.md").exists())

    def test_invalid_metrics_rejected(self):
        for field, value in (("target", "better"), ("target", float("nan")), ("target", True),
                             ("direction", "improve"), ("unit", ""), ("sample_count", 0),
                             ("sample_count", 1.2), ("denominator", ""), ("anti_gaming", "")):
            with self.subTest(field=field, value=value):
                draft = copy.deepcopy(self.draft)
                draft["criteria"][0][field] = value
                with self.assertRaises(plan.Invalid):
                    plan.validate_candidate(draft, self.contract)

    def test_overflowing_model_number_retains_invalid_receipt_without_goal(self):
        remote = Remote([self.draft])
        def overflow(prompt, directory):
            return remote(prompt, directory).replace('"target": 10', '"target": 1e309', 1)
        result = self.run_plan(overflow)
        self.assertEqual(result["state"], "invalid")
        self.assertIn("nonfinite JSON number", result["error"])
        self.assertEqual(json.loads((self.output / "receipt.json").read_text()), result)
        self.assertFalse((self.output / "goal.md").exists())

    def test_unmeasured_baseline_requires_first_measurement_and_dependency(self):
        draft = copy.deepcopy(self.draft)
        draft["criteria"][0].update(baseline=None, baseline_evidence=None, baseline_milestone="measure")
        with self.assertRaises(plan.Invalid):
            plan.validate_candidate(draft, self.contract)
        first = copy.deepcopy(draft["milestones"][0])
        first.update(id="measure", title="Measure baseline", establishes_baseline=["cases"])
        first["acceptance"].update(metric="baseline samples recorded", target=10)
        draft["milestones"].insert(0, first)
        with self.assertRaises(plan.Invalid):
            plan.validate_candidate(draft, self.contract)
        draft["milestones"][1]["depends_on"] = ["measure"]
        plan.validate_candidate(draft, self.contract)
        compiled, _ = plan.compile_goal(draft, self.contract, MODEL, self.root)
        self.assertIn("Baseline: unmeasured", compiled)

    def test_compiler_round_trips_flat_frontmatter(self):
        (self.root / "check with spaces.sh").write_text("exit 37\n")
        self.contract["protect"].append("check with spaces.sh")
        self.contract["constraints"] = "Keep user's 'quoted' rules: fixed; no extra authority"
        self.draft["contract_sha256"] = plan.digest(self.contract)
        goal, expected = plan.compile_goal(self.draft, self.contract, MODEL, self.root)
        path = self.root / "goal.md"
        path.write_text(goal, encoding="utf-8")
        fields, _, body = loop.parse(path)
        self.assertEqual(fields, expected)
        self.assertEqual(fields["constraints"], self.contract["constraints"])
        self.assertEqual(loop.protected_paths(fields, str(self.root), str(path)),
                         ["check.sh", "conftest.py", "check with spaces.sh"])
        self.assertEqual(loop.cost_cap(fields, "omp", path), "1")
        self.assertIn("## Milestones", body)
        frontmatter = goal.split("---\n")[1]
        self.assertTrue(all(line and not line.startswith((" ", "-")) and ": " in line
                            for line in frontmatter.splitlines()))

    def test_frontmatter_injection_and_invalid_paths_are_rejected(self):
        for goal in ("Goal\ncheck: exit 0", "Goal\u2028check: exit 0"):
            with self.assertRaises(plan.Invalid):
                plan.compile_goal({**self.draft, "goal": goal}, self.contract, MODEL, self.root)
        for protect in (["../escape"], ["absent:../escape"], [], "tests", ["missing.py"]):
            with self.subTest(protect=protect), self.assertRaises(plan.Invalid):
                plan.validate_contract({**self.contract, "protect": protect}, self.root)

    def test_missing_contract_and_unknown_authority_fail_before_remote(self):
        remote = Remote([self.draft])
        for contract in (None, {}, {**self.contract, "harness_args": "--tools bash"}):
            with self.subTest(contract=contract), self.assertRaises(plan.Invalid):
                plan.plan("request", "evidence", contract, self.root, self.output, MODEL, remote)
        self.assertEqual(remote.calls, [])

    def test_bounded_revision_replaces_votes(self):
        revised = copy.deepcopy(self.draft)
        revised["goal"] = "All ten existing consumer cases pass"
        choices = {1: dict.fromkeys(plan.LENSES, "revise")}
        remote = Remote([self.draft, revised], choices)
        result = self.run_plan(remote)
        self.assertEqual(result["state"], "approved_draft")
        self.assertEqual(len(remote.calls), 8)
        self.assertNotEqual(result["rounds"][0]["candidate_sha256"], result["rounds"][1]["candidate_sha256"])
        self.assertTrue(all(v["candidate_sha256"] == plan.digest(revised) for v in result["rounds"][1]["votes"]))

    def test_revision_cap_has_no_nested_repair(self):
        choices = {number: dict.fromkeys(plan.LENSES, "revise") for number in (1, 2)}
        remote = Remote([self.draft], choices)
        result = self.run_plan(remote)
        self.assertEqual(result["state"], "no_consensus")
        self.assertEqual(len(remote.calls), 8)
        self.assertFalse((self.output / "goal.md").exists())
        self.assertTrue((self.output / "round-2" / "author-response.txt").exists())

    def test_milestone_caps_and_forward_dependencies_rejected(self):
        for key, value in (("iterations", 4), ("cost_usd", 2), ("minutes", 11), ("depends_on", ["later"])):
            with self.subTest(key=key):
                draft = copy.deepcopy(self.draft)
                draft["milestones"][0][key] = value
                with self.assertRaises(plan.Invalid):
                    plan.validate_candidate(draft, self.contract)

    def test_output_cannot_overlap_protection_or_be_reused(self):
        self.contract["protect"].append("absent:out/forbidden.py")
        self.draft["contract_sha256"] = plan.digest(self.contract)
        with self.assertRaises(plan.Invalid):
            self.run_plan(Remote([self.draft]))
        self.contract["protect"].pop()
        self.output.mkdir()
        with self.assertRaises(FileExistsError):
            self.run_plan(Remote([self.draft]))

    def test_acp_transcript_requires_completion_and_no_tools(self):
        events = [{"jsonrpc": "2.0", "id": 1, "method": "session/prompt", "params": {}},
                  {"jsonrpc": "2.0", "method": "session/update", "params": {"update": {
                      "sessionUpdate": "agent_message_chunk", "content": {"type": "text", "text": "{}"}}}},
                  {"jsonrpc": "2.0", "id": 1, "result": {"stopReason": "end_turn"}}]
        encode = lambda rows: "\n".join(json.dumps(row) for row in rows)
        self.assertEqual(plan.acp_text(encode(events)), "{}")
        with self.assertRaises(plan.Unavailable):
            plan.acp_text(encode(events[:-1]))
        tool = {"jsonrpc": "2.0", "method": "session/update", "params": {"update": {"sessionUpdate": "tool_call"}}}
        with self.assertRaises(plan.Unavailable):
            plan.acp_text(encode([*events, tool]))


if __name__ == "__main__":
    unittest.main()
