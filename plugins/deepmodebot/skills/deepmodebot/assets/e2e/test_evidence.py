"""Synthetic boundary fixtures, not browser execution or visual-quality evidence."""
import base64
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from evidence import artifact, canonical, contained_path, load_bundle, seal_bundle, validate_scenario

PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII=")


def make_bundle(directory, *, state="passed"):
    root = Path(directory)
    root.mkdir(parents=True, exist_ok=True)
    scenario = {"schema_version": 1, "intent": "Open the explicitly authorized example page.",
                "allowed_origins": ["https://example.com"],
                "steps": [{"id": "home", "action": {"type": "open", "url": "https://example.com/"},
                           "expected": {"url": "https://example.com/"}}]}
    (root / "scenario.json").write_bytes(canonical(scenario))
    (root / "step.png").write_bytes(PNG)
    (root / "frame.png").write_bytes(PNG)
    (root / "snapshot.json").write_bytes(canonical({"snapshot": "heading Example Domain"}))
    (root / "video.webm").write_bytes(b"synthetic unit fixture, not a playable recording")
    row = {**copy.deepcopy(scenario["steps"][0]), "started_ms": 0, "ended_ms": 1,
           "status": "passed" if state == "passed" else "failed", "screenshot": artifact(root, "step.png"),
           "snapshot": artifact(root, "snapshot.json"),
           "observations": {"url": "https://example.com/", "target_id": "synthetic-target", "errors": [],
                            "assertions": [{"expected": {"kind": "url", "equals": "https://example.com/"},
                                            "actual": "https://example.com/", "passed": True}]}}
    manifest = {"schema_version": 1, "intent": scenario["intent"], "scenario": artifact(root, "scenario.json"),
                "capture_tool": {"sha256": "0" * 64, "browser_version": "synthetic fixture"},
                "state": state, "recorded_target_id": "synthetic-target", "steps": [row], "video": artifact(root, "video.webm"),
                "frames": [{"at_ms": 0, "image": artifact(root, "frame.png")}],
                "sampling": {"method": "uniform", "interval_ms": 1000, "max_frames": 1,
                             "duration_ms": 1000, "coverage": "complete"},
                "limitations": ["Synthetic unit fixture; not runtime proof."]}
    seal_bundle(root, manifest)
    return manifest


def replace_manifest_for_test(root, manifest):
    """Simulate an adversary who can rewrite the untrusted seal too."""
    payload = canonical(manifest)
    (root / "manifest.json").write_bytes(payload)
    (root / "manifest.sha256").write_text(hashlib.sha256(payload).hexdigest(), encoding="ascii")


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        scratch = Path(__file__).resolve().parents[6] / ".scratch" / "tmp"
        scratch.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=scratch)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.manifest = make_bundle(self.root)

    def test_load_returns_pinned_manifest_digest(self):
        manifest, digest = load_bundle(self.root)
        self.assertEqual(manifest, self.manifest)
        self.assertEqual(digest, hashlib.sha256(canonical(manifest)).hexdigest())

    def test_changed_image_is_rejected(self):
        (self.root / "step.png").write_bytes(PNG + b"tamper")
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            load_bundle(self.root)

    def test_changed_manifest_without_seal_is_rejected(self):
        (self.root / "manifest.json").write_bytes(canonical({**self.manifest, "intent": "changed"}))
        with self.assertRaisesRegex(ValueError, "seal mismatch"):
            load_bundle(self.root)

    def test_unsafe_cross_platform_paths(self):
        for path in ("../step.png", "/step.png", "C:/step.png", "steps\\step.png", "steps//step.png",
                     "steps/./step.png", "step.png:stream", "CON.png", "step.png.", "step%2epng", "step.png#x"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                contained_path(self.root, path)

    def test_symlink_escape_is_rejected(self):
        link = self.root / "linked.png"
        try:
            link.symlink_to(self.root / "step.png")
        except OSError:
            self.skipTest("host does not permit creating symlinks")
        with self.assertRaisesRegex(ValueError, "linked"):
            contained_path(self.root, "linked.png")

    def test_failed_capture_never_passes_default_admission(self):
        self.manifest["state"] = "failed"
        self.manifest["steps"][0]["status"] = "failed"
        self.manifest["steps"][0]["screenshot"] = None
        replace_manifest_for_test(self.root, self.manifest)
        with self.assertRaisesRegex(ValueError, "did not pass"):
            load_bundle(self.root)
        self.assertEqual(load_bundle(self.root, require_success=False)[0]["state"], "failed")

    def test_forged_pass_with_false_assertion_is_rejected(self):
        self.manifest["steps"][0]["observations"]["assertions"][0]["actual"] = "https://example.com/wrong"
        replace_manifest_for_test(self.root, self.manifest)
        with self.assertRaisesRegex(ValueError, "failed assertion"):
            load_bundle(self.root)

    def test_missing_timeline_frame_is_rejected(self):
        self.manifest["frames"] = []
        replace_manifest_for_test(self.root, self.manifest)
        with self.assertRaisesRegex(ValueError, "incomplete timeline"):
            load_bundle(self.root)

    def test_scenario_expectation_cannot_be_changed_in_manifest(self):
        self.manifest["steps"][0]["expected"]["url"] = "https://example.com/wrong"
        replace_manifest_for_test(self.root, self.manifest)
        with self.assertRaisesRegex(ValueError, "pinned scenario"):
            load_bundle(self.root)

    def test_duplicate_json_keys_rejected(self):
        (self.root / "manifest.json").write_text('{"state":"passed","state":"failed"}', encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "duplicate"):
            load_bundle(self.root)

    def test_step_from_another_tab_cannot_pass_even_at_the_same_origin(self):
        self.manifest["steps"][0]["observations"]["target_id"] = "different-target"
        replace_manifest_for_test(self.root, self.manifest)
        with self.assertRaises(ValueError):
            load_bundle(self.root)

    def test_scenario_ids_cannot_overwrite_or_name_reserved_artifacts(self):
        scenario = json.loads((self.root / "scenario.json").read_bytes())
        for reserved in ("CON", "nul", "Com1", "LPT9"):
            candidate = copy.deepcopy(scenario)
            candidate["steps"][0]["id"] = reserved
            with self.subTest(id=reserved), self.assertRaises(ValueError):
                validate_scenario(candidate)
        candidate = copy.deepcopy(scenario)
        candidate["steps"].append({**copy.deepcopy(candidate["steps"][0]), "id": "HOME"})
        with self.assertRaises(ValueError):
            validate_scenario(candidate)

    def test_reject_unbounded_or_shell_actions(self):
        import json
        scenario = json.loads((self.root / "scenario.json").read_bytes())
        for action in ({"type": "eval", "script": "alert(1)"}, {"type": "open", "url": "file:///etc/passwd"},
                       {"type": "click", "selector": "--cdp"}, {"type": "pause", "ms": 5001}):
            candidate = copy.deepcopy(scenario)
            candidate["steps"].append({"id": "bad", "action": action, "expected": {"url": "https://example.com/"}})
            with self.subTest(action=action), self.assertRaises(ValueError):
                validate_scenario(candidate)


if __name__ == "__main__":
    unittest.main()
