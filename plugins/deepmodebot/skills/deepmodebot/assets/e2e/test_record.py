"""Narrow synthetic boundary regressions; live browser proof is a separate pilot."""
import copy
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import record
from evidence import assertion_passes, load_bundle, validate_scenario
from test_evidence import PNG, make_bundle


class StepBoundary:
    """Only the browser boundary is simulated to force capture-error branches."""
    def __init__(self, actual, screenshot_error=False):
        self.actual = actual
        self.screenshot_error = screenshot_error
        self.calls = []

    def action(self, action):
        self.calls.append(action)

    def verify_target(self):
        return "synthetic-target"

    def observe(self, expected):
        spec = {"kind": "url", "equals": expected["url"]}
        return {"url": self.actual, "target_id": "synthetic-target", "errors": [], "assertions": [
            {"expected": spec, "actual": self.actual, "passed": assertion_passes(spec, self.actual)}]}

    def call(self, command, *args):
        self.calls.append(command)
        if command == "screenshot":
            if self.screenshot_error:
                raise record.CaptureError("synthetic screenshot failure")
            Path(args[0]).write_bytes(PNG)
            return {}
        return {"snapshot": "synthetic snapshot"}


class RecordTests(unittest.TestCase):
    def setUp(self):
        scratch = Path(__file__).resolve().parents[6] / ".scratch" / "tmp"
        scratch.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=scratch)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "source"
        make_bundle(self.source)
        self.scenario = json.loads((self.source / "scenario.json").read_bytes())

    def test_assertion_failure_retains_screenshot_and_snapshot(self):
        (self.root / "steps").mkdir()
        browser = StepBoundary("https://example.com/wrong")
        result = record.capture_step(browser, self.root, self.scenario["steps"][0], lambda: 10)
        self.assertEqual(result["status"], "failed")
        self.assertFalse(result["observations"]["assertions"][0]["passed"])
        self.assertIsNotNone(result["screenshot"])
        self.assertIsNotNone(result["snapshot"])

    def test_failed_screenshot_does_not_invent_image(self):
        (self.root / "steps").mkdir()
        browser = StepBoundary("https://example.com/", screenshot_error=True)
        result = record.capture_step(browser, self.root, self.scenario["steps"][0], lambda: 10)
        self.assertEqual(result["status"], "failed")
        self.assertIsNone(result["screenshot"])
        self.assertIsNotNone(result["snapshot"])
        self.assertIn("synthetic screenshot failure", result["observations"]["errors"][0])

    def test_replay_pins_intent_scenario_and_fresh_session_without_launch(self):
        first = self.root / "first"
        second = self.root / "second"
        options = {"executable": "deepmode-definitely-missing-browser-executable"}
        original, digest = load_bundle(self.source)
        a, _ = record.replay(self.source, first, **options)
        b, _ = record.replay(self.source, second, **options)
        self.assertEqual(a["state"], "unavailable")
        self.assertEqual(a["intent"], original["intent"])
        self.assertEqual(a["scenario"]["sha256"], original["scenario"]["sha256"])
        self.assertEqual(a["replay"]["source_bundle_sha256"], digest)
        self.assertNotEqual(a["session"], b["session"])
        self.assertEqual((first / "scenario.json").read_bytes(), (self.source / "scenario.json").read_bytes())
        load_bundle(first, require_success=False)
        with self.assertRaises(FileExistsError):
            record.replay(self.source, first, **options)

    def test_replay_refuses_tampered_source_before_output(self):
        (self.source / "step.png").write_bytes(b"tampered")
        output = self.root / "unused"
        with self.assertRaises(ValueError):
            record.replay(self.source, output, executable="unused")
        self.assertFalse(output.exists())

    def test_replay_cannot_write_inside_original_bundle(self):
        output = self.source / "nested-replay"
        with self.assertRaisesRegex(ValueError, "disjoint"):
            record.replay(self.source, output, executable="unused")
        self.assertFalse(output.exists())

    def test_personal_browser_environment_is_removed(self):
        with patch.dict(os.environ, {"AGENT_BROWSER_CDP": "9222", "AGENT_BROWSER_PROFILE": "personal",
                                     "AGENT_BROWSER_STATE": "secrets.json", "NODE_OPTIONS": "--require evil.js",
                                     "OPENAI_API_KEY": "synthetic"}):
            env = record.clean_environment()
        self.assertFalse(any(key.upper().startswith("AGENT_BROWSER_") for key in env))
        self.assertNotIn("NODE_OPTIONS", env)
        self.assertNotIn("OPENAI_API_KEY", env)

    def test_inspection_rejects_known_unfiltered_recording_version(self):
        class Inspection:
            def run(self, argv):
                return "agent-browser 0.15.0"
        with patch.object(record, "browser_command", return_value=["browser"]):
            with self.assertRaisesRegex(record.CaptureError, "unfiltered recording context"):
                record.inspect_browser(Inspection(), "browser")

    def test_origin_scheme_port_and_credentials_are_not_interchangeable(self):
        for url in ("http://example.com/", "https://example.com:8443/", "https://user:pass@example.com/"):
            candidate = copy.deepcopy(self.scenario)
            candidate["steps"][0]["action"]["url"] = url
            with self.subTest(url=url), self.assertRaises(ValueError):
                validate_scenario(candidate)

    def test_boolean_state_not_coerced_from_text(self):
        spec = {"kind": "state", "property": "visible", "selector": "h1", "equals": True}
        self.assertFalse(assertion_passes(spec, "true"))
        self.assertFalse(assertion_passes(spec, 1))
        self.assertTrue(assertion_passes(spec, True))

    def test_popup_or_changed_target_refuses_same_origin_observations(self):
        original = {"active": True, "targetId": "original"}
        for tabs in ([{"active": True, "targetId": "replacement"}],
                     [original, {"active": False, "targetId": "popup"}]):
            with self.subTest(tabs=tabs):
                replies = iter([[original], tabs])

                class Boundary:
                    def run(self, *args, **kwargs):
                        return json.dumps({"success": True, "data": {"tabs": next(replies)}})

                browser = record.Browser(Boundary(), ["fixture-browser"], self.root, self.scenario, "fixture")
                browser.verify_target()
                with self.assertRaises(record.CaptureError):
                    browser.observe(self.scenario["steps"][0]["expected"])

    def test_interrupt_during_finalization_still_closes_and_seals_failure(self):
        for interrupted in ("stop", "close"):
            with self.subTest(interrupted=interrupted):
                output = self.root / interrupted
                seen = []

                class InterruptedBrowser(StepBoundary):
                    def call(self, command, *args, cleanup=False):
                        seen.append(command)
                        if command == "record" and args[0] == "stop":
                            if interrupted == "stop":
                                raise KeyboardInterrupt()
                            (output / "video.webm").write_bytes(b"synthetic fixture, not a playable video")
                        if command == "close" and interrupted == "close":
                            raise KeyboardInterrupt()
                        return super().call(command, *args)

                boundary = InterruptedBrowser("https://example.com/")
                with patch.object(record, "Browser", return_value=boundary), \
                        patch.object(record, "inspect_browser", return_value=(["fixture-browser"], "0.43.0")), \
                        patch.object(record.shutil, "which", return_value="fixture"), \
                        patch.object(record, "sample_video"):
                    manifest, digest = record.record(self.scenario, (self.source / "scenario.json").read_bytes(), output)
                self.assertIn("close", seen)
                self.assertEqual(manifest["state"], "failed")
                self.assertTrue(any("KeyboardInterrupt" in item for item in manifest["limitations"]))
                self.assertEqual(load_bundle(output, require_success=False)[1], digest)
                with self.assertRaises(ValueError):
                    load_bundle(output)


if __name__ == "__main__":
    unittest.main()
