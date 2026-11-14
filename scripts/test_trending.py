"""Consumer-visible reference discovery and cache migration regressions."""
import argparse
import contextlib
import datetime as dt
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location(
    "reference_catalog_test", ROOT / "plugins/deepmodebot/skills/deepmodebot/scripts/trending.py")
catalog = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(catalog)


class ReferenceDiscoveryTests(unittest.TestCase):
    def setUp(self):
        scratch = ROOT / ".scratch/tmp"
        scratch.mkdir(parents=True, exist_ok=True)
        temporary = tempfile.TemporaryDirectory(dir=scratch)
        self.addCleanup(temporary.cleanup)
        self.out = Path(temporary.name)
        clock = patch.object(catalog, "today", return_value=dt.date(2026, 11, 14))
        clock.start()
        self.addCleanup(clock.stop)
        self.reference = {
            "reviewed": "2026-11-14", "archive": "https://example.test/archive",
            "topics": ["doctor admin prototype"], "sources": ["https://example.test/source"],
            "caution": "Separate enterprise terms apply. " + "Check the intended use. " * 12
                       + "Do not use patient data in this prototype.",
        }

    def repository(self, name):
        return {"full_name": name, "html_url": "https://github.com/" + name,
                "description": "A generic workflow component", "language": "Python",
                "license": {"spdx_id": "Apache-2.0"}, "stargazers_count": 10,
                "created_at": "2026-01-01T00:00:00Z", "pushed_at": "2026-11-14T00:00:00Z"}

    def entry(self, name):
        return {**catalog.entry_from(self.repository(name)), "first_seen": "2026-11-01",
                "stars_first_seen": 2, "last_seen": "2026-11-14", "seen_in": ["earlier-source"]}

    def write_catalog(self, value):
        (self.out / "catalog.json").write_text(json.dumps(value), encoding="utf-8")

    def test_same_day_published_revision_exposes_reference_only_match(self):
        previous = {"updated": "2026-11-14", "sources": {}, "repos": {}}
        self.write_catalog(previous)
        entry = self.entry("example/component")
        entry["reference"] = self.reference
        published = {**previous, "reference_revision": catalog.REFERENCE_REVISION,
                     "repos": {"example/component": entry}}
        output = io.StringIO()
        with patch.object(catalog, "PUBLISHED", "https://example.test/catalog.json"), \
                patch.object(catalog, "fetch", return_value=json.dumps(published)), \
                patch.object(catalog, "update", side_effect=AssertionError("unnecessary rebuild")), \
                contextlib.redirect_stdout(output):
            catalog.find(argparse.Namespace(out=self.out, terms=["doctor admin"], limit=20, no_refresh=False))
        self.assertIn("example/component", output.getvalue())
        self.assertIn(self.reference["caution"], output.getvalue())
        self.assertEqual(catalog.load_catalog(self.out / "catalog.json"), published)

    def test_redirected_alias_preserves_reference_cautions_and_observation_history(self):
        self.write_catalog({"updated": "2026-11-14", "sources": {},
                            "repos": {"old-owner/component": self.entry("old-owner/component")}})

        def source(found, token):
            repo = self.repository("new-owner/component")
            catalog.add(found, "new-owner/component", "reference-library", repo)
            found["new-owner/component"]["reference"] = self.reference
            catalog.add(found, "old-owner/component", "other-source", repo)

        with patch.object(catalog, "SOURCES", [("reference-library", source)]), \
                patch.object(catalog, "github_token", return_value=None), \
                contextlib.redirect_stdout(io.StringIO()):
            catalog.update(argparse.Namespace(out=self.out))
        result = catalog.load_catalog(self.out / "catalog.json")
        self.assertNotIn("old-owner/component", result["repos"])
        entry = result["repos"]["new-owner/component"]
        self.assertEqual(entry["reference"], self.reference)
        self.assertEqual(entry["first_seen"], "2026-11-01")
        self.assertEqual(entry["stars_first_seen"], 2)
        self.assertEqual(entry["seen_in"], ["earlier-source", "other-source", "reference-library"])
        self.assertIn(self.reference["caution"], (self.out / "README.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
