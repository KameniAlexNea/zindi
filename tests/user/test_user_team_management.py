import unittest
from unittest.mock import call, patch

import pandas as pd

from zindi.user import Zindian

# Mock API responses (Copied from original file)
MOCK_SIGNIN_SUCCESS = {
    "data": {
        "auth_token": "mock_token",
        "user": {"username": "testuser", "id": 123},
    }
}
MOCK_CREATE_TEAM_SUCCESS = {"data": {"title": "New Team"}}
MOCK_CREATE_TEAM_ALREADY_LEADER = {
    "data": {"errors": {"base": "Leader can only be part of one team per competition."}}
}
MOCK_TEAM_UP_SUCCESS = {"data": {"message": "Invitation sent"}}
MOCK_TEAM_UP_ALREADY_INVITED = {"data": {"errors": {"base": "User is already invited"}}}
MOCK_DISBAND_SUCCESS = {"data": "Team disbanded successfully"}


# --- Base Class for Tests Requiring Authenticated User ---
class AuthenticatedUserTestCase(unittest.TestCase):
    @patch("zindi.user.requests.post")
    @patch("zindi.user.getpass")
    def setUp(self, mock_getpass, mock_post):
        """Set up a mocked Zindian instance for tests."""
        mock_getpass.return_value = "password"
        mock_post.return_value.json.return_value = MOCK_SIGNIN_SUCCESS
        self.user = Zindian(username="testuser")
        # Prevent setUp mocks from interfering with test-specific mocks
        mock_getpass.reset_mock()
        mock_post.reset_mock()


# --- Test Class for Team Management ---
class TestUserTeamManagement(AuthenticatedUserTestCase):
    def setUp(self):
        """Extend setUp to also select a challenge."""
        super().setUp()
        # Pre-select a challenge for these tests
        self.user._Zindian__challenge_selected = True
        self.user._Zindian__challenge_data = pd.Series(
            {"id": "challenge-team", "subtitle": "Team Challenge"}
        )
        self.user._Zindian__api = f"{self.user._Zindian__base_api}/challenge-team"

    def test_team_action_not_selected_error(self):
        """Test team actions before selecting a challenge (edge case)."""
        self.user._Zindian__challenge_selected = False  # Override setup
        with self.assertRaises(Exception) as cm_create:
            self.user.create_team(team_name="Fail")
        self.assertIn("select a challenge before", str(cm_create.exception))

        with self.assertRaises(Exception) as cm_up:
            self.user.team_up(zindians=["user"])
        self.assertIn("select a challenge before", str(cm_up.exception))

        with self.assertRaises(Exception) as cm_disband:
            self.user.disband_team()
        self.assertIn("select a challenge before", str(cm_disband.exception))

    @patch("zindi.user.requests.post")
    def test_create_team_success(self, mock_post):
        """Test creating a team successfully."""
        mock_post.return_value.json.return_value = MOCK_CREATE_TEAM_SUCCESS
        self.user.create_team(team_name="New Team")
        mock_post.assert_called_once_with(
            f"{self.user._Zindian__api}/my_team",
            headers={"User-Agent": unittest.mock.ANY},
            data={"title": "New Team", "auth_token": "mock_token"},
        )

    @patch("zindi.user.requests.post")
    @patch("builtins.print")  # Mock print
    def test_create_team_already_leader(self, mock_print, mock_post):
        """Test creating a team when already a leader."""
        mock_post.return_value.json.return_value = MOCK_CREATE_TEAM_ALREADY_LEADER
        self.user.create_team(team_name="Another Team")
        mock_post.assert_called_once()
        mock_print.assert_any_call(f"\n[ 🟢 ] You are already the leader of a team.\n")

    @patch("zindi.user.requests.post")
    def test_team_up_success(self, mock_post):
        """Test inviting teammates successfully."""
        mock_post.return_value.json.return_value = MOCK_TEAM_UP_SUCCESS
        teammates = ["friend1", "friend2"]
        self.user.team_up(zindians=teammates)

        self.assertEqual(mock_post.call_count, 2)
        # Check calls carefully - original code needs auth_token in data for invite POST
        expected_calls = [
            call(
                f"{self.user._Zindian__api}/my_team/invite",
                headers={"User-Agent": unittest.mock.ANY},
                # data={"username": "friend1", "auth_token": "mock_token"} # Assuming auth_token should be here
                data={"username": "friend1"},  # Based on original code
            ),
            call(
                f"{self.user._Zindian__api}/my_team/invite",
                headers={"User-Agent": unittest.mock.ANY},
                # data={"username": "friend2", "auth_token": "mock_token"} # Assuming auth_token should be here
                data={"username": "friend2"},  # Based on original code
            ),
        ]
        mock_post.assert_has_calls(expected_calls, any_order=True)

    @patch("zindi.user.requests.delete")
    def test_disband_team_success(self, mock_delete):
        """Test disbanding a team successfully."""
        mock_delete.return_value.json.return_value = MOCK_DISBAND_SUCCESS
        self.user.disband_team()
        mock_delete.assert_called_once_with(
            f"{self.user._Zindian__api}/my_team",
            headers={"User-Agent": unittest.mock.ANY},
            data={"auth_token": "mock_token"},
        )


if __name__ == "__main__":
    unittest.main()
