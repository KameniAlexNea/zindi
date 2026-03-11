import unittest
from unittest.mock import call, patch

import pandas as pd

from zindi.user import Zindian

# Mock API responses (Copied from original file)
MOCK_SIGNIN_SUCCESS = {
    "auth_token": "mock_token",
    "user": {"username": "testuser", "id": 123},
}
MOCK_CREATE_TEAM_SUCCESS = {"title": "New Team"}
MOCK_CREATE_TEAM_ALREADY_LEADER = {
    "errors": {"base": "Leader can only be part of one team per competition."}
}
MOCK_TEAM_UP_SUCCESS = {"message": "Invitation sent"}
MOCK_TEAM_UP_ALREADY_INVITED = {"errors": {"base": "User is already invited"}}
MOCK_DISBAND_SUCCESS = "Team disbanded successfully"


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

    @patch("zindi.user.ZindiPlatformAPI.create_team")
    def test_create_team_success(self, mock_create_team):
        """Test creating a team successfully."""
        mock_create_team.return_value = MOCK_CREATE_TEAM_SUCCESS
        response = self.user.create_team(team_name="New Team")
        mock_create_team.assert_called_once_with(
            auth_token="mock_token",
            challenge_id="challenge-team",
            team_name="New Team",
        )
        self.assertFalse(response["already_leader"])
        self.assertEqual(response["team"]["title"], "New Team")

    @patch("zindi.user.ZindiPlatformAPI.create_team")
    @patch("builtins.print")  # Mock print
    def test_create_team_already_leader(self, mock_print, mock_create_team):
        """Test creating a team when already a leader."""
        mock_create_team.return_value = MOCK_CREATE_TEAM_ALREADY_LEADER
        self.user.create_team(team_name="Another Team")
        mock_create_team.assert_called_once()
        mock_print.assert_any_call(f"\n[ 🟢 ] You are already the leader of a team.\n")

    @patch("zindi.user.ZindiPlatformAPI.invite_to_team")
    def test_team_up_success(self, mock_invite):
        """Test inviting teammates successfully."""
        mock_invite.return_value = MOCK_TEAM_UP_SUCCESS
        teammates = ["friend1", "friend2"]
        response = self.user.team_up(zindians=teammates)

        self.assertEqual(mock_invite.call_count, 2)
        expected_calls = [
            call(
                auth_token="mock_token",
                challenge_id="challenge-team",
                username="friend1",
            ),
            call(
                auth_token="mock_token",
                challenge_id="challenge-team",
                username="friend2",
            ),
        ]
        mock_invite.assert_has_calls(expected_calls, any_order=True)
        self.assertEqual(len(response), 2)
        self.assertEqual(response[0]["status"], "invited")

    @patch("zindi.user.ZindiPlatformAPI.disband_team")
    def test_disband_team_success(self, mock_disband):
        """Test disbanding a team successfully."""
        mock_disband.return_value = MOCK_DISBAND_SUCCESS
        response = self.user.disband_team()
        mock_disband.assert_called_once_with(
            auth_token="mock_token",
            challenge_id="challenge-team",
        )
        self.assertEqual(response, "Team disbanded successfully")


if __name__ == "__main__":
    unittest.main()
