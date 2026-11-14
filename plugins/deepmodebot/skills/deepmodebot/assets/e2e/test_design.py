"""Focused regressions for untrusted recording text in portable design formats."""
import base64
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET

import design
from test_evidence import PNG, make_bundle


class DesignRenderingTests(unittest.TestCase):
    def manifest(self):
        return {"intent": 'Keep <script>alert("intent")</script> literal\x00', "state": "failed",
                "limitations": ["Capture interrupted"], "steps": [
                    {"id": '</text><script>alert("step")</script>',
                     "action": {"type": "click", "selector": '[data-name="save"]'},
                     "expected": {"text": "Saved"}, "status": "failed",
                     "started_ms": 0, "ended_ms": 123,
                     "observations": {"error": '</pre><img src=x onerror="alert(1)">',
                                      "detail": "The button remained disabled."}}]}

    def test_svg_keeps_untrusted_text_as_text_and_uses_generated_ids(self):
        root = ET.fromstring(design._svg(self.manifest(), "a" * 64, [{"screenshot": None}], Path(".")))
        allowed = {"svg", "title", "desc", "rect", "text", "g", "a", "path"}
        self.assertTrue(all(node.tag.rsplit("}", 1)[-1] in allowed for node in root.iter()))
        self.assertIn("Screenshot unavailable", "".join(root.itertext()))
        self.assertIn("\\u0000", "".join(root.itertext()))
        self.assertEqual([n.attrib["id"] for n in root.iter() if "id" in n.attrib], ["step-1"])
        self.assertEqual([n.attrib["href"] for n in root.iter() if "href" in n.attrib],
                         ["index.html#step-1"])

    def test_index_retains_full_observations_without_active_markup(self):
        manifest = self.manifest()
        manifest["steps"][0]["observations"]["detail"] = "full observation " * 100
        result = design._index(manifest, "a" * 64, [{}], None, [])
        self.assertNotIn("<script>", result)
        self.assertNotIn("<img src=x", result)
        self.assertIn("&lt;script&gt;", result)
        self.assertIn("full observation " * 100, result)
        self.assertIn("incomplete visual evidence", result)
        self.assertIn("Video unavailable", result)

    def test_mermaid_cannot_inject_directives_or_click_targets(self):
        manifest = self.manifest()
        manifest["steps"][0]["id"] = '\"]\n%%{init: {securityLevel: "loose"}}%%\nclick evil "https://evil.test"'
        result = design._mmd(manifest)
        self.assertNotIn("%%{", result)
        self.assertNotIn("https://", result)
        self.assertEqual([line for line in result.splitlines() if line.strip().startswith("click")],
                         ['  click step1 "index.html#step-1" "Full recorded evidence"'])

    def test_exported_svg_embeds_verified_step_images_for_portable_import(self):
        scratch = Path(__file__).resolve().parents[6] / ".scratch" / "tmp"
        scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as temp:
            root = Path(temp)
            make_bundle(root / "capture")
            design.export_bundle(root / "capture", root / "design")
            document = ET.parse(root / "design/workflow.svg")
            images = document.findall(".//{http://www.w3.org/2000/svg}image")
            self.assertEqual(len(images), 1)
            mime, encoded = images[0].attrib["href"].split(",", 1)
            self.assertEqual(mime, "data:image/png;base64")
            self.assertEqual(base64.b64decode(encoded, validate=True), PNG)


if __name__ == "__main__":
    unittest.main()
