import unittest
from unittest.mock import patch

from zindi.user import Zindian

# Mock API responses (Copied from original file)
MOCK_SIGNIN_SUCCESS = {
    "auth_token": "mock_token",
    "user": {"username": "testuser", "id": 123},
}
MOCK_CHALLENGES_DATA = [
    {
        "id": "challenge-1",
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
        "type_of_problem": ["Regression"],
        "data_type": ["Image"],
        "secret_code_required": False,
        "sealed": False,
    },
    {
        "id": "challenge-3",
        "kind": "competition",
        "subtitle": "Challenge 3 Subtitle",
        "reward": "knowledge",
        "type_of_problem": ["NLP"],
        "data_type": ["Text"],
        "secret_code_required": False,
        "sealed": False,
    },
]


# --- Base Class for Tests Requiring Authenticated User ---
class AuthenticatedUserTestCase(unittest.TestCase):
    @patch("zindi.user.ZindiPlatformAPI.signin")
    @patch("zindi.user.getpass")
    def setUp(self, mock_getpass, mock_signin):
        """Set up a mocked Zindian instance for tests."""
        mock_getpass.return_value = "password"
        mock_signin.return_value = MOCK_SIGNIN_SUCCESS
        self.user = Zindian(username="testuser")
        # Prevent setUp mocks from interfering with test-specific mocks
        mock_getpass.reset_mock()
        mock_signin.reset_mock()


# --- Test Class for Challenge Selection ---
class TestUserChallengeSelection(AuthenticatedUserTestCase):
    def test_which_challenge_not_selected(self):
        """Test which_challenge when no challenge is selected."""
        self.assertIsNone(self.user.which_challenge)

    @patch("zindi.user.ZindiPlatformAPI.join_competition")
    @patch("zindi.user.ZindiPlatformAPI.search_competitions")
    @patch("builtins.input", return_value="1")
    def test_select_a_challenge_success(self, mock_input, mock_search, mock_join):
        """Test successfully selecting a challenge via input."""
        mock_search.return_value = MOCK_CHALLENGES_DATA
        mock_join.return_value = {"joined": True, "message": "already in"}

        self.user.select_a_challenge(kind="all")

        mock_search.assert_called_once()
        mock_join.assert_called_once()
        self.assertTrue(self.user._Zindian__challenge_selected)
        self.assertEqual(self.user._Zindian__challenge_data["id"], "challenge-2")
        self.assertEqual(self.user.which_challenge, "challenge-2")

    @patch("zindi.user.ZindiPlatformAPI.join_competition")
    @patch("zindi.user.ZindiPlatformAPI.search_competitions")
    def test_select_a_challenge_fixed_index(self, mock_search, mock_join):
        """Test selecting a challenge using fixed_index."""
        mock_search.return_value = MOCK_CHALLENGES_DATA
        mock_join.return_value = {"joined": True, "message": "already in"}

        response = self.user.select_a_challenge(fixed_index=2)

        self.assertTrue(self.user._Zindian__challenge_selected)
        self.assertEqual(self.user._Zindian__challenge_data["id"], "challenge-3")
        self.assertEqual(response["challenge"]["id"], "challenge-3")
        self.assertTrue(response["joined"]["joined"])
        mock_join.assert_called_once()

    @patch("zindi.user.ZindiPlatformAPI.search_competitions")
    def test_select_a_challenge_invalid_fixed_index(self, mock_search):
        """Test selecting a challenge with an invalid fixed_index."""
        mock_search.return_value = MOCK_CHALLENGES_DATA
        with self.assertRaises(Exception) as cm:
            self.user.select_a_challenge(fixed_index=10)
        self.assertIn("must be an integer in range", str(cm.exception))

        with self.assertRaises(Exception) as cm:
            self.user.select_a_challenge(fixed_index=-1)
        self.assertIn("must be an integer in range", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
