import unittest
from unittest.mock import MagicMock, patch

import pandas as pd

from zindi import utils

# Sample data needed for API helper tests
SAMPLE_CHALLENGES_DATA = pd.DataFrame(
    [
        {
            "id": "challenge-1-long-id-string-that-needs-truncating",
            "kind": "competition",
            "subtitle": "Challenge 1 Subtitle",
            "reward": "prize",
            "type_of_problem": ["Classification"],
            "data_type": ["Tabular"],
            "secret_code_required": False,
            "sealed": False,
        },
        {
            "id": "challenge-2",
            "kind": "hackathon",
            "subtitle": "Challenge 2 Subtitle",
            "reward": "points",
            "type_of_problem": [],  # Empty problem type
            "data_type": ["Image"],
            "secret_code_required": True,  # Private
            "sealed": False,
        },
    ]
)


# --- Test Class for API Helper Functions (join_challenge, get_challenges) ---
class TestApiHelpers(unittest.TestCase):
    @patch("zindi.utils.requests.post")
    @patch("builtins.print")
    def test_join_challenge_success(self, mock_print, mock_post):
        """Test joining a challenge successfully."""
        mock_post.return_value.json.return_value = {"data": {"ids": [123]}}
        headers = {"auth_token": "token"}
        url = "http://example.com/participations"
        utils.join_challenge(url=url, headers=headers)
        mock_post.assert_called_once_with(
            url=url, headers=headers, data={"auth_token": "token"}
        )
        mock_print.assert_any_call(
            "\n[ 🟢 ] Welcome for the first time to this challenge.\n"
        )

    @patch("zindi.utils.requests.post")
    @patch("builtins.print")
    def test_join_challenge_already_in(self, mock_print, mock_post):
        """Test joining a challenge when already participating."""
        mock_post.return_value.json.return_value = {
            "data": {"errors": {"message": "already in"}}
        }
        headers = {"auth_token": "token"}
        url = "http://example.com/participations"
        utils.join_challenge(url=url, headers=headers)
        mock_post.assert_called_once_with(
            url=url, headers=headers, data={"auth_token": "token"}
        )
        # Should not print success or raise error

    @patch("zindi.utils.requests.post")
    @patch("builtins.input", return_value="secretcode123")
    @patch("builtins.print")
    def test_join_challenge_requires_code(self, mock_print, mock_input, mock_post):
        """Test joining a challenge that requires a secret code."""
        # First call response indicates code needed, second call response is success
        mock_post.side_effect = [
            MagicMock(
                json=lambda: {
                    "data": {
                        "errors": {
                            "message": "This competition requires a secret code to join."
                        }
                    }
                }
            ),
            MagicMock(json=lambda: {"data": {"ids": [456]}}),
        ]
        headers = {"auth_token": "token"}
        url = "http://example.com/participations"

        utils.join_challenge(url=url, headers=headers)

        self.assertEqual(mock_post.call_count, 2)
        # First call (no code)
        mock_post.assert_any_call(
            url=url, headers=headers, data={"auth_token": "token"}
        )
        # Second call (with code)
        mock_post.assert_any_call(
            url=url, headers=headers, params={"secret_code": "secretcode123"}
        )
        mock_input.assert_called_once()
        mock_print.assert_any_call(
            "\n[ 🟢 ] Welcome for the first time to this challenge.\n"
        )

    @patch("zindi.utils.requests.post")
    def test_join_challenge_other_error(self, mock_post):
        """Test joining a challenge with an unexpected error."""
        mock_post.return_value.json.return_value = {
            "data": {"errors": {"message": "Some other error"}}
        }
        headers = {"auth_token": "token"}
        url = "http://example.com/participations"
        with self.assertRaises(Exception) as cm:
            utils.join_challenge(url=url, headers=headers)
        self.assertIn("Some other error", str(cm.exception))
        mock_post.assert_called_once()

    @patch("zindi.utils.requests.get")
    def test_get_challenges_success(self, mock_get):
        """Test getting challenges successfully with filters."""
        mock_get.return_value.json.return_value = {
            "data": SAMPLE_CHALLENGES_DATA.to_dict("records")
        }
        headers = {"User-Agent": "Test"}
        url = "http://base.api/competitions"

        df = utils.get_challenges(
            reward="prize", kind="competition", active=True, url=url, headers=headers
        )

        expected_params = {
            "page": 0,
            "per_page": 800,
            "prize": "prize",
            "kind": "competition",
            "active": 1,
        }
        mock_get.assert_called_once_with(url, headers=headers, params=expected_params)
        pd.testing.assert_frame_equal(df, SAMPLE_CHALLENGES_DATA)

    @patch("zindi.utils.requests.get")
    def test_get_challenges_invalid_filters(self, mock_get):
        """Test getting challenges with invalid filter values (should default)."""
        mock_get.return_value.json.return_value = {
            "data": SAMPLE_CHALLENGES_DATA.to_dict("records")
        }
        headers = {"User-Agent": "Test"}
        url = "http://base.api/competitions"

        utils.get_challenges(
            reward="invalid_reward",
            kind="invalid_kind",
            active="invalid_active",
            url=url,
            headers=headers,
        )

        # Expect default/empty filters for invalid values
        expected_params = {
            "page": 0,
            "per_page": 800,
            "prize": "",
            "kind": "competition",
            "active": "",
        }
        mock_get.assert_called_once_with(url, headers=headers, params=expected_params)


if __name__ == "__main__":
    unittest.main()
