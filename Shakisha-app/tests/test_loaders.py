import os
import unittest
from pathlib import Path

from src.loaders import load_all_data


class TestLoaders(unittest.TestCase):
    def setUp(self):
        self.data_dir = Path("data/sample")
        os.environ["HACKATHON_DATA_DIR"] = str(self.data_dir)

    def tearDown(self):
        os.environ.pop("HACKATHON_DATA_DIR", None)

    def test_loads_expected_columns(self):
        studies, resources, quality = load_all_data()
        self.assertIn("study_id", studies.columns)
        self.assertIn("title", studies.columns)
        self.assertIn("study_id", resources.columns)
        self.assertIn("type", resources.columns)
        self.assertIn("missing_field_count", quality.columns)
        self.assertGreaterEqual(len(studies), 1)


if __name__ == "__main__":
    unittest.main()

