import copy
import importlib.util
import json
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("review_eval", Path(__file__).with_name("run.py"))
review_eval = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(review_eval)


def finding(fid, file="src/a.py", line=12):
    return {"id": fid, "file": file, "line": line, "severity": "P1",
            "claim": "a behavior is wrong", "evidence": "specific source evidence"}


def worksheet(case_id, status, error, findings, expected, decisions):
    return {"case_id": case_id, "status": status, "error": error, "expected_bugs": expected,
            "findings": [{"finding": f, "finding_sha256": review_eval.finding_digest(f), **d}
                         for f, d in zip(findings, decisions)]}


class ScoringBehaviorTests(unittest.TestCase):
    def setUp(self):
        self.corpus = {"cases": [
            {"id": "bug", "kind": "bug", "expected_bugs": ["b1", "b2"]},
            {"id": "clean", "kind": "clean", "expected_bugs": []},
            {"id": "failed", "kind": "bug", "expected_bugs": ["b3"]},
            {"id": "failed-clean", "kind": "clean", "expected_bugs": []},
        ]}
        self.run = {"model_requested": "model-a", "model_observed": ["provider/model-a"],
                    "cli": {"version": "18.19.0", "sha256": "cli-hash"}, "mode": "diff-only",
                    "settings": ["--no-tools"], "corpus_sha256": review_eval.json_digest(self.corpus),
                    "results": [
                        {"case_id": "bug", "status": "valid", "findings": [finding("F1"), finding("F2", line=30), finding("F3", line=40)]},
                        {"case_id": "clean", "status": "valid", "findings": [finding("F1", "src/clean.py")]},
                        {"case_id": "failed", "status": "failed", "error": "timeout", "findings": []},
                        {"case_id": "failed-clean", "status": "failed", "error": "malformed JSON", "findings": []},
                    ]}
        self.adj = {"run_sha256": "run-hash", "corpus_sha256": self.run["corpus_sha256"],
                    "model_requested": self.run["model_requested"], "model_observed": self.run["model_observed"],
                    "cli": self.run["cli"], "mode": self.run["mode"], "settings": self.run["settings"],
                    "cases": [
                        worksheet("bug", "valid", None, self.run["results"][0]["findings"], ["b1", "b2"], [
                            {"maps_to": "b1", "adjudication": "true_positive", "rationale": "maps to distinct bug"},
                            {"maps_to": None, "adjudication": "false_positive", "rationale": "duplicate claim"},
                            {"maps_to": None, "adjudication": "false_positive", "rationale": "unmapped unsupported claim"}]),
                        worksheet("clean", "valid", None, self.run["results"][1]["findings"], [], [
                            {"maps_to": None, "adjudication": "false_positive", "rationale": "clean control has no defect"}]),
                        worksheet("failed", "failed", "timeout", [], ["b3"], []),
                        worksheet("failed-clean", "failed", "malformed JSON", [], [], []),
                    ]}

    def score(self, run=None, adj=None, corpus=None):
        return review_eval.score_data(run or self.run, adj or self.adj, corpus or self.corpus, "run-hash")

    def test_duplicate_unmapped_and_clean_findings_are_false_positives(self):
        score = self.score()
        self.assertEqual((score["true_positives"], score["false_positives"]), (1, 3))
        self.assertEqual(score["missed_expected_bugs"], 2)
        self.assertEqual(score["bug_recall"], 1 / 3)
        self.assertEqual(score["clean_case_false_positive_rate"], 1.0)

    def test_duplicate_true_positive_mapping_is_false_positive_not_another_true_positive(self):
        adj = copy.deepcopy(self.adj)
        adj["cases"][0]["findings"][1].update(
            maps_to="b1", adjudication="true_positive", rationale="repeats b1")
        score = self.score(adj=adj)
        self.assertEqual((score["true_positives"], score["false_positives"]), (1, 3))

    def test_failed_bug_remains_a_miss_and_failed_clean_is_not_clean_success(self):
        score = self.score()
        self.assertEqual(score["expected_bug_denominator_including_failures"], 3)
        self.assertEqual(score["failed_bug_cases"], 1)
        self.assertEqual(score["failed_clean_cases"], 1)
        self.assertEqual(score["invalid_cases"], [
            {"case_id": "failed", "error": "timeout"},
            {"case_id": "failed-clean", "error": "malformed JSON"},
        ])

    def test_pending_adjudication_cannot_be_scored(self):
        adj = copy.deepcopy(self.adj)
        adj["cases"][0]["findings"][0]["adjudication"] = ""
        with self.assertRaises(ValueError):
            self.score(adj=adj)

    def test_missing_case_or_finding_cannot_inflate_score(self):
        adj = copy.deepcopy(self.adj)
        adj["cases"].pop(0)
        with self.assertRaises(ValueError):
            self.score(adj=adj)
        adj = copy.deepcopy(self.adj)
        adj["cases"][0]["findings"].pop()
        with self.assertRaises(ValueError):
            self.score(adj=adj)
        adj = copy.deepcopy(self.adj)
        added = finding("invented")
        adj["cases"][0]["findings"].append(
            {"finding": added, "finding_sha256": review_eval.finding_digest(added),
             "maps_to": None, "adjudication": "false_positive", "rationale": "unsupported"})
        with self.assertRaises(ValueError):
            self.score(adj=adj)

    def test_mutated_finding_status_or_expected_labels_are_rejected(self):
        for mutate in ("finding", "status", "labels"):
            adj = copy.deepcopy(self.adj)
            if mutate == "finding":
                adj["cases"][0]["findings"][0]["finding"]["claim"] = "changed"
            elif mutate == "status":
                adj["cases"][0]["status"] = "failed"
            else:
                adj["cases"][0]["expected_bugs"].clear()
            with self.subTest(mutate=mutate), self.assertRaises(ValueError):
                self.score(adj=adj)

    def test_model_cli_version_settings_and_corpus_digest_must_match(self):
        for key, value in (("model_requested", "other"), ("cli", {"sha256": "other"}),
                           ("settings", ["--no-tools", "--no-lsp"]), ("corpus_sha256", "other")):
            adj = copy.deepcopy(self.adj)
            adj[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.score(adj=adj)
        changed_corpus = copy.deepcopy(self.corpus)
        changed_corpus["cases"][0]["expected_bugs"].append("extra")
        with self.assertRaises(ValueError):
            self.score(corpus=changed_corpus)

    def test_zero_denominators_are_unavailable(self):
        corpus = {"cases": [{"id": "bug", "kind": "bug", "expected_bugs": ["b"]}]}
        run = {**self.run, "corpus_sha256": review_eval.json_digest(corpus),
               "results": [{"case_id": "bug", "status": "valid", "findings": []}]}
        adj = {**self.adj, "corpus_sha256": run["corpus_sha256"],
               "cases": [worksheet("bug", "valid", None, [], ["b"], [])]}
        score = self.score(run=run, adj=adj, corpus=corpus)
        self.assertIsNone(score["precision"])
        self.assertIsNone(score["clean_case_false_positive_rate"])
        self.assertEqual(score["bug_recall"], 0.0)

    def test_production_fenced_response_and_malformed_json(self):
        self.assertEqual(review_eval.parse_findings('Summary.\n```json\n{"findings": []}\n```'), [])
        with self.assertRaises(json.JSONDecodeError):
            review_eval.parse_findings("not json")
        with self.assertRaises(ValueError):
            review_eval.parse_findings('{"findings":[{"file":"a.py"}]}')


class BudgetBoundaryTests(unittest.TestCase):
    def test_nonfinite_and_nonpositive_caps_fail_before_launch(self):
        for cap in (float("nan"), float("inf"), float("-inf"), 0, -1):
            args = SimpleNamespace(corpus=review_eval.CORPUS, split="calibration", only=[],
                                   timeout=30, max_cost=cap)
            with self.subTest(cap=cap), self.assertRaisesRegex(ValueError, "positive and finite"):
                review_eval.run(args)


class CorpusContextTests(unittest.TestCase):
    def test_forward_patch_can_have_bugs_but_cannot_use_unrelated_context(self):
        corpus = review_eval.load_corpus()
        forward = next(c for c in corpus["cases"]
                       if c["input_direction"] == "forward-repair" and c["kind"] == "bug")
        self.assertTrue(forward["expected_bugs"])
        forward["context"]["head"] = "0" * 40
        with patch.object(Path, "read_text", return_value=json.dumps(corpus)):
            with self.assertRaisesRegex(ValueError, "immutable forward and reverse"):
                review_eval.load_corpus()

    def test_context_coverage_exposes_included_files_and_omissions(self):
        packet = ("--- src/module.py (head " + "a" * 40 + ", blob " + "b" * 40
                  + ", 3 bytes, changed) ---\nsource\n\nOMISSIONS:\n- src/large.py: byte limit")
        files, omissions = review_eval.context_coverage(packet)
        self.assertEqual(files, ["src/module.py"])
        self.assertEqual(omissions, ["- src/large.py: byte limit"])
        self.assertEqual(review_eval.context_coverage("OMISSIONS: none")[0], [])

if __name__ == "__main__":
    unittest.main()
