"""Real bundle/coverage checks; only remote model replies are simulated. No live provider calls."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

import review
from test_evidence import make_bundle, replace_manifest_for_test


def response(data, choice="approve"):
    return {"schema_version": 1, "bundle_sha256": data["bundle_sha256"], "lens": data["lens"],
            "vision_available": True, "vote": choice,
            "steps": [{"id": step["id"], "verdict": choice,
                       "findings": ["The captured page has a visible heading and an unclipped content area."],
                       "evidence_refs": ["step:" + step["id"]]} for step in data["steps"]],
            "images": [{"ref": item["ref"], "finding": "The page background and heading remain visible."}
                       for item in data["images"]],
            "limitations": ["Uniform samples cannot establish behavior between captured frames."]}


class Remote:
    def __init__(self, choices=None, mutate=None, unavailable=None):
        self.choices = choices or {}
        self.mutate = mutate
        self.unavailable = unavailable
        self.calls = []

    def __call__(self, prompt, images, directory):
        data = json.loads(prompt.split("\nINPUT DATA:\n", 1)[1])
        self.calls.append({"prompt": prompt, "data": data, "directory": directory,
                           "images": [path.read_bytes() for path in images]})
        if data["lens"] == self.unavailable:
            raise RuntimeError("provider deadline exceeded")
        vote = response(data, self.choices.get(data["lens"], "approve"))
        if self.mutate:
            self.mutate(vote, images, directory)
        return json.dumps(vote)


class ReviewCase(unittest.TestCase):
    def setUp(self):
        scratch = Path(__file__).resolve().parents[6] / ".scratch" / "visual-review-tests"
        scratch.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=scratch)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.bundle = self.root / "bundle"
        self.manifest = make_bundle(self.bundle)
        self.output = self.root / "review"

    def run_review(self, remote):
        return review.review_bundle(self.bundle, self.output, remote)

    def reseal_fixture(self):
        replace_manifest_for_test(self.bundle, self.manifest)

    def test_three_fresh_contexts_receive_identical_actual_images_and_original_intent(self):
        remote = Remote({review.LENSES[2]: "revise"})
        result = self.run_review(remote)
        self.assertTrue(result["accepted"])
        self.assertEqual(result["state"], "approved")
        self.assertEqual(result["valid_reviewers"], 3)
        self.assertEqual(len(result["minority_report"]), 1)
        self.assertEqual(result["minority_report"][0]["lens"], review.LENSES[2])
        self.assertFalse(result["vcs_actions"])
        self.assertFalse(result["executed_remediations"])
        self.assertEqual(len({call["directory"] for call in remote.calls}), 3)
        self.assertEqual(len(remote.calls), 3)
        inventory = review.image_inventory(self.bundle.resolve(), self.manifest)
        expected = [(self.bundle / item["artifact"]["path"]).read_bytes() for item in inventory]
        for call in remote.calls:
            self.assertEqual(call["images"], expected)
            self.assertEqual(call["data"]["original_intent"], self.manifest["intent"])
            self.assertNotIn("reviews", call["data"])
            self.assertNotIn("minority_report", call["data"])
            self.assertTrue((call["directory"] / "vote.json").is_file())
        self.assertEqual(json.loads((self.output / "review.json").read_text())["minority_report"], result["minority_report"])

    def test_revision_majority_is_not_acceptance(self):
        result = self.run_review(Remote(dict.fromkeys(review.LENSES[:2], "revise")))
        self.assertEqual(result["state"], "revise")
        self.assertFalse(result["accepted"])
        self.assertEqual(result["minority_report"][0]["vote"], "approve")

    def test_two_approvals_cannot_replace_third_response(self):
        remote = Remote(unavailable=review.LENSES[2])
        result = self.run_review(remote)
        self.assertEqual(result["state"], "incomplete_panel")
        self.assertFalse(result["accepted"])
        self.assertEqual(len(remote.calls), 3)
        self.assertTrue((self.output / review.LENSES[2] / "error.json").exists())

    def test_unavailable_first_reviewer_does_not_prevent_other_independent_attempts(self):
        remote = Remote(unavailable=review.LENSES[0])
        result = self.run_review(remote)
        self.assertEqual(len(remote.calls), 3)
        self.assertFalse(result["accepted"])

    def test_failed_capture_never_calls_model(self):
        self.manifest["state"] = "failed"
        self.reseal_fixture()
        remote = Remote()
        result = self.run_review(remote)
        self.assertEqual(result["state"], "invalid")
        self.assertEqual(remote.calls, [])
        self.assertFalse(result["accepted"])

    def test_artifact_changed_before_review_is_rejected(self):
        path = self.bundle / self.manifest["steps"][0]["screenshot"]["path"]
        path.write_bytes(path.read_bytes() + b"changed")
        remote = Remote()
        result = self.run_review(remote)
        self.assertEqual(remote.calls, [])
        self.assertFalse(result["accepted"])

    def test_artifact_changed_after_third_vote_invalidates_entire_panel(self):
        def mutate(vote, images, directory):
            if vote["lens"] == review.LENSES[2]:
                path = self.bundle / self.manifest["video"]["path"]
                path.write_bytes(path.read_bytes() + b"changed")
        result = self.run_review(Remote(mutate=mutate))
        self.assertEqual(result["state"], "invalid")
        self.assertFalse(result["accepted"])

    def test_resealed_manifest_change_is_still_detected(self):
        def mutate(vote, images, directory):
            if vote["lens"] == review.LENSES[2]:
                self.manifest["limitations"].append("Evidence changed during voting")
                self.reseal_fixture()
        result = self.run_review(Remote(mutate=mutate))
        self.assertEqual(result["state"], "invalid")
        self.assertFalse(result["accepted"])

    def test_attachment_changed_by_later_context_invalidates_panel(self):
        def mutate(vote, images, directory):
            if vote["lens"] == review.LENSES[2]:
                (self.output / review.LENSES[0] / "image-000.png").unlink()
        result = self.run_review(Remote(mutate=mutate))
        self.assertEqual(result["state"], "invalid")
        self.assertFalse(result["accepted"])

    def test_incomplete_sampling_does_not_call_remote(self):
        self.manifest["sampling"]["coverage"] = "incomplete"
        self.reseal_fixture()
        remote = Remote()
        result = self.run_review(remote)
        self.assertFalse(result["accepted"])
        self.assertEqual(remote.calls, [])

    def test_payload_cap_rejects_instead_of_omitting_frames(self):
        frame = self.manifest["frames"][0]["image"]
        self.manifest["frames"] = [{"at_ms": index, "image": frame} for index in range(review.MAX_IMAGES)]
        self.manifest["sampling"].update(interval_ms=1, duration_ms=review.MAX_IMAGES, max_frames=review.MAX_IMAGES)
        self.reseal_fixture()
        remote = Remote()
        result = self.run_review(remote)
        self.assertFalse(result["accepted"])
        self.assertIn("none omitted", result["error"])
        self.assertEqual(remote.calls, [])

    def test_individual_image_cap_rejects_real_bytes_before_remote(self):
        artifact = self.manifest["steps"][0]["screenshot"]
        path = self.bundle / artifact["path"]
        data = path.read_bytes() + b"x" * review.MAX_IMAGE_BYTES
        path.write_bytes(data)
        for step in self.manifest["steps"]:
            if step["screenshot"]["path"] == artifact["path"]:
                step["screenshot"]["sha256"] = review.sha(data)
        for frame in self.manifest["frames"]:
            if frame["image"]["path"] == artifact["path"]:
                frame["image"]["sha256"] = review.sha(data)
        self.reseal_fixture()
        remote = Remote()
        result = self.run_review(remote)
        self.assertFalse(result["accepted"])
        self.assertEqual(remote.calls, [])

    def test_existing_output_and_bundle_output_are_rejected_without_overwrite(self):
        self.output.mkdir()
        marker = self.output / "keep.txt"
        marker.write_text("retain")
        with self.assertRaises(FileExistsError):
            self.run_review(Remote())
        self.assertEqual(marker.read_text(), "retain")
        with self.assertRaises(ValueError):
            review.review_bundle(self.bundle, self.bundle / "reviews", Remote())

    def test_invalid_third_vote_cannot_be_outvoted(self):
        changes = {
            "wrong hash": lambda vote: vote.update(bundle_sha256="0" * 64),
            "wrong lens": lambda vote: vote.update(lens=review.LENSES[0]),
            "vision unavailable": lambda vote: vote.update(vision_available=False),
            "frame omitted": lambda vote: vote["images"].pop(),
            "step omitted": lambda vote: vote["steps"].pop(),
            "invented evidence": lambda vote: vote["steps"][0]["evidence_refs"].append("frame:999"),
            "missing screenshot": lambda vote: vote["steps"][0].update(evidence_refs=["frame:0"]),
            "duplicate image": lambda vote: vote["images"].append(copy.deepcopy(vote["images"][0])),
            "contradictory approval": lambda vote: vote["steps"][0].update(verdict="revise"),
            "missing limitations": lambda vote: vote.update(limitations=[]),
        }
        for index, (name, change) in enumerate(changes.items()):
            with self.subTest(name=name):
                self.output = self.root / f"invalid-{index}"
                def mutate(vote, images, directory):
                    if vote["lens"] == review.LENSES[2]:
                        change(vote)
                remote = Remote(mutate=mutate)
                result = self.run_review(remote)
                self.assertFalse(result["accepted"])
                self.assertEqual(result["state"], "incomplete_panel")
                self.assertEqual(len(remote.calls), 3)


class NativeBoundaryCase(unittest.TestCase):
    def message(self):
        return {"role": "assistant", "provider": "openai-codex", "model": "gpt-6-astra", "credentialId": 7,
                "stopReason": "stop", "content": [{"type": "text", "text": '{"vote":"approve"}'}]}

    def stream(self, message, extra=None):
        return "\n".join(json.dumps(event) for event in [*(extra or []), {"type": "message_end", "message": message}])

    def test_exact_model_and_oauth_reply_is_extracted(self):
        self.assertEqual(review.native_reply(self.stream(self.message()), review.MODEL, {7}), '{"vote":"approve"}')

    def test_tool_calls_fallbacks_bad_credentials_and_partial_replies_fail(self):
        for change in ({"provider": "openai"}, {"model": "different"}, {"credentialId": 8},
                       {"stopReason": "length"}, {"content": [{"type": "toolCall", "name": "bash"}]}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                review.native_reply(self.stream({**self.message(), **change}), review.MODEL, {7})
        with self.assertRaises(ValueError):
            review.native_reply(self.stream(self.message(), [{"type": "tool_execution_start", "toolName": "bash"}]), review.MODEL, {7})

    def test_multiple_assistant_contexts_cannot_be_combined(self):
        raw = self.stream(self.message())
        with self.assertRaises(ValueError):
            review.native_reply(raw + "\n" + raw, review.MODEL, {7})

    def test_duplicate_schema_keys_are_rejected(self):
        with self.assertRaises(ValueError):
            review.strict_json('{"vote":"revise","vote":"approve"}')
        with self.assertRaises(ValueError):
            review.strict_json('{"value":NaN}')

    def test_unauthorized_model_and_invalid_caps_are_rejected_without_launch(self):
        with self.assertRaises(ValueError):
            review.NativeOMP("openai-codex/another-model", 1, 1)
        for minutes, cost in ((0, 1), (float("nan"), 1), (1, float("inf")), (31, 1), (1, 0)):
            with self.subTest(minutes=minutes, cost=cost), self.assertRaises(ValueError):
                review.NativeOMP(review.MODEL, minutes, cost)


if __name__ == "__main__":
    unittest.main()
