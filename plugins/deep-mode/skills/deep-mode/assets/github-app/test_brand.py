"""Brand derivation and explicit trigger overrides."""
import unittest

import brand


class BrandTriggers(unittest.TestCase):
    def test_reseller_derives_its_own_mention(self):
        self.assertEqual(brand.derive("acme-review")["mention"], "@acme-review")

    def test_explicit_trigger_overrides_derived_mention(self):
        for name in ("deep-mode", "acme-review"):
            for mention in ("@custom-bot", "/custom-review"):
                with self.subTest(name=name, mention=mention):
                    self.assertEqual(brand.derive(name, {"mention": mention})["mention"], mention)


if __name__ == "__main__":
    unittest.main()
