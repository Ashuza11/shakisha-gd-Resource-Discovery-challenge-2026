import unittest

import pandas as pd

from src.filters import apply_study_filters, filter_resources_by_type


class TestFilters(unittest.TestCase):
    def test_apply_study_filters_query_and_year(self):
        df = pd.DataFrame(
            [
                {"study_id": 1, "title": "Labour report", "abstract": "jobs", "year": 2020},
                {"study_id": 2, "title": "Health report", "abstract": "maternal", "year": 2015},
            ]
        )
        out = apply_study_filters(df, query="labour", year_min=2019, year_max=2025)
        self.assertEqual(len(out), 1)
        self.assertEqual(int(out.iloc[0]["study_id"]), 1)

    def test_filter_resources_by_type(self):
        resources = pd.DataFrame(
            [
                {"study_id": 1, "type": "pdf", "url": "a"},
                {"study_id": 1, "type": "doc", "url": "b"},
            ]
        )
        out = filter_resources_by_type(resources, "pdf")
        self.assertEqual(len(out), 1)
        self.assertEqual(out.iloc[0]["type"], "pdf")


if __name__ == "__main__":
    unittest.main()

