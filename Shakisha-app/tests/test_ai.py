from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch


class TestInterpretQuery(unittest.TestCase):
    def _make_message(self, text: str):
        content = MagicMock()
        content.text = text
        message = MagicMock()
        message.content = [content]
        return message

    @patch("src.ai._get_client")
    def test_returns_expected_keys(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.messages.create.return_value = self._make_message(
            '{"keywords": ["women", "labour"], "year_min": 2018, "year_max": null, "explanation": "Searching for women labour data."}'
        )

        from src.ai import interpret_query

        result = interpret_query("women labour force after 2018")
        self.assertIn("keywords", result)
        self.assertIn("year_min", result)
        self.assertIn("year_max", result)
        self.assertIn("explanation", result)
        self.assertIsInstance(result["keywords"], list)

    @patch("src.ai._get_client")
    def test_fallback_on_bad_json(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.messages.create.return_value = self._make_message("not valid json at all")

        from src.ai import interpret_query

        result = interpret_query("some query")
        self.assertIn("keywords", result)
        self.assertIsInstance(result["keywords"], list)

    @patch("src.ai._get_client")
    def test_empty_query_skips_api(self, mock_get_client):
        from src.ai import interpret_query

        result = interpret_query("   ")
        mock_get_client.assert_not_called()
        self.assertEqual(result["keywords"], [])
        self.assertIsNone(result["year_min"])


class TestExplainStudy(unittest.TestCase):
    def _make_message(self, text: str):
        content = MagicMock()
        content.text = text
        message = MagicMock()
        message.content = [content]
        return message

    @patch("src.ai._get_client")
    def test_returns_string(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.messages.create.return_value = self._make_message(
            "This survey covers gender employment gaps. It is directly relevant to the query."
        )

        from src.ai import explain_study

        result = explain_study(
            {"title": "DHS 2014", "year": 2014, "organization": "NISR", "abstract": "Survey data..."},
            "women employment",
        )
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)


class TestAdvocacyBrief(unittest.TestCase):
    def _make_message(self, text: str):
        content = MagicMock()
        content.text = text
        message = MagicMock()
        message.content = [content]
        return message

    @patch("src.ai._get_client")
    def test_returns_all_required_sections(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.messages.create.return_value = self._make_message(
            '{"policy_context": "Context here.", "key_findings": "• Finding 1\\n• Finding 2\\n• Finding 3", '
            '"data_gaps": "Some gaps.", "recommended_action": "Take this action.", "citation": "NISR, DHS, 2014."}'
        )

        from src.ai import advocacy_brief

        result = advocacy_brief(
            {"title": "DHS 2014", "year": 2014, "organization": "NISR", "abstract": "..."},
            [],
        )
        for key in ("policy_context", "key_findings", "data_gaps", "recommended_action", "citation"):
            self.assertIn(key, result)
            self.assertIsInstance(result[key], str)

    @patch("src.ai._get_client")
    def test_fallback_on_bad_json(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.messages.create.return_value = self._make_message("Some non-JSON response from Claude.")

        from src.ai import advocacy_brief

        result = advocacy_brief({"title": "Test", "year": 2020, "organization": "NISR"}, [])
        self.assertIn("citation", result)


if __name__ == "__main__":
    unittest.main()
