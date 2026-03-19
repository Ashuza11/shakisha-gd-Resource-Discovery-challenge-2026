import unittest

from src.quality_badges import parse_quality_flags, quality_level


class TestQualityBadges(unittest.TestCase):
    def test_parse_quality_flags(self):
        raw = "missing_study_type;missing_scope_notes"
        parsed = parse_quality_flags(raw)
        self.assertEqual(parsed, ["missing_study_type", "missing_scope_notes"])

    def test_quality_level(self):
        self.assertEqual(quality_level(0), "good")
        self.assertEqual(quality_level(2), "warning")
        self.assertEqual(quality_level(3), "critical")


if __name__ == "__main__":
    unittest.main()

