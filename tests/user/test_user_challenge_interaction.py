import datetime
import os
import unittest
from unittest.mock import patch

import pandas as pd

from zindi.user import Zindian

# Mock API responses (Copied from original file)
MOCK_SIGNIN_SUCCESS = {
    "auth_token": "mock_token",
    "user": {"username": "testuser", "id": 123},
}
MOCK_LEADERBOARD_DATA = {
    "data": [
        {
            "public_rank": 1,
            "best_public_score": 0.95,
            "user": {"username": "leader"},
            "submission_count": 5,
            "best_public_submitted_at": "2023-01-10T10:00:00Z",
        },
        {
            "public_rank": 2,
            "best_public_score": 0.92,
            "user": {"username": "testuser"},
            "submission_count": 3,
            "best_public_submitted_at": "2023-01-09T15:30:00Z",
        },
        {
            "public_rank": 3,
            "best_public_score": 0.90,
            "team": {"title": "Team Awesome", "id": "team-123"},
            "submission_count": 8,
            "best_public_submitted_at": "2023-01-11T08:00:00Z",
        },
    ]
}
MOCK_SUBMISSION_BOARD_DATA = {
    "data": [
        {
            "id": "sub-1",
            "status": "successful",
            "created_at": (
                datetime.datetime.now() - datetime.timedelta(hours=2)
            ).isoformat()
            + "Z",
            "filename": "submission1.csv",
            "public_score": 0.92,
            "private_score": 0.91,
            "comment": "First attempt",
            "status_description": None,
        },
        {
            "id": "sub-2",
            "status": "failed",
            "created_at": (
                datetime.datetime.now() - datetime.timedelta(hours=1)
            ).isoformat()
            + "Z",
            "filename": "submission2.csv",
            "public_score": None,
            "private_score": None,
            "comment": "Second attempt",
            "status_description": "Invalid format",
        },
        {
            "id": "sub-3",
            "status": "successful",
            "created_at": (
                datetime.datetime.now() - datetime.timedelta(days=1, hours=5)
            ).isoformat()
            + "Z",
            "filename": "submission_old.csv",
            "public_score": 0.90,
            "private_score": 0.89,
            "comment": "Old one",
            "status_description": None,
        },
    ]
}
MOCK_CHALLENGE_DETAILS_DATA = {
    "data": {
        "id": "challenge-2",
        "subtitle": "Challenge 2 Subtitle",
        "datafiles": [
            {"filename": "Train.csv", "id": "df-1"},
            {"filename": "Test.csv", "id": "df-2"},
            {"filename": "SampleSubmission.csv", "id": "df-3"},
        ],
        "pages": [
            {"title": "Overview", "content_html": "Some content"},
            {
                "title": "Rules",
                "content_html": "Blah blah You may make a maximum of 5 submissions per day. Blah blah",
            },
        ],
    }
}
MOCK_SUBMIT_SUCCESS = {"data": {"id": "sub-new-123"}}
MOCK_SUBMIT_FAILURE = {"data": {"errors": {"base": "Submission failed"}}}


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


# --- Test Class for Challenge Interaction (Download, Submit, Boards, Rank) ---
class TestUserChallengeInteraction(AuthenticatedUserTestCase):
    def setUp(self):
        """Extend setUp to also select a challenge."""
        super().setUp()
        # Pre-select a challenge for these tests
        self.user._Zindian__challenge_selected = True
        self.user._Zindian__challenge_data = pd.Series(
            {"id": "challenge-2", "subtitle": "Challenge 2 Subtitle"}
        )
        self.user._Zindian__api = f"{self.user._Zindian__base_api}/challenge-2"

    def test_download_dataset_not_selected_error(self):
        """Test downloading dataset before selecting a challenge (edge case)."""
        self.user._Zindian__challenge_selected = False  # Override setup
        with self.assertRaises(Exception) as cm:
            self.user.download_dataset()
        self.assertIn("select a challenge before", str(cm.exception))

    @patch("zindi.user.os.makedirs")
    @patch("zindi.user.os.path.isdir", return_value=False)
    @patch("zindi.user.ZindiPlatformAPI.get_competition")
    @patch("zindi.user.download")
    def test_download_dataset_success(
        self, mock_util_download, mock_get_competition, mock_isdir, mock_makedirs
    ):
        """Test successful dataset download."""
        mock_get_competition.return_value = MOCK_CHALLENGE_DETAILS_DATA["data"]
        dest_folder = "./mock_dataset"
        self.user.download_dataset(destination=dest_folder)

        mock_isdir.assert_called_once_with(dest_folder)
        mock_makedirs.assert_called_once_with(dest_folder, exist_ok=True)
        mock_get_competition.assert_called_once_with(
            auth_token="mock_token",
            challenge_id="challenge-2",
        )
        self.assertEqual(mock_util_download.call_count, 3)
        called_urls = [kwargs["url"] for _, kwargs in mock_util_download.call_args_list]
        self.assertIn(f"{self.user._Zindian__base_api}/challenge-2/files/Train.csv", called_urls)
        self.assertIn(f"{self.user._Zindian__base_api}/challenge-2/files/Test.csv", called_urls)
        self.assertIn(
            f"{self.user._Zindian__base_api}/challenge-2/files/SampleSubmission.csv",
            called_urls,
        )

    def test_submit_not_selected_error(self):
        """Test submitting before selecting a challenge (edge case)."""
        self.user._Zindian__challenge_selected = False  # Override setup
        with self.assertRaises(Exception) as cm:
            self.user.submit(filepaths=["./dummy.csv"])
        self.assertIn("select a challenge before", str(cm.exception))

    @patch("zindi.user.os.path.isfile", return_value=True)
    @patch("zindi.user.ZindiPlatformAPI.submit_file")
    def test_submit_success(self, mock_submit_file, mock_isfile):
        """Test successful submission."""
        mock_submit_file.return_value = MOCK_SUBMIT_SUCCESS["data"]
        filepath = "./submission.csv"
        comment = "Test submission"
        response = self.user.submit(filepaths=[filepath], comments=[comment])

        mock_isfile.assert_called_once_with(filepath)
        mock_submit_file.assert_called_once_with(
            auth_token="mock_token",
            challenge_id="challenge-2",
            filepath=filepath,
            comment=comment,
        )
        self.assertEqual(response[0]["status"], "success")
        self.assertEqual(response[0]["submission_id"], "sub-new-123")

    @patch("zindi.user.os.path.isfile", return_value=False)
    @patch("builtins.print")  # Mock print to check output
    def test_submit_file_not_exist(self, mock_print, mock_isfile):
        """Test submission when file does not exist."""
        filepath = "./nonexistent.csv"
        self.user.submit(filepaths=[filepath])
        mock_isfile.assert_called_once_with(filepath)
        mock_print.assert_any_call(
            f"\n[ 🔴 ] File doesn't exists, please verify this filepath : {filepath}\n"
        )

    @patch("builtins.print")  # Mock print to check output
    def test_submit_invalid_extension(self, mock_print):
        """Test submission with an invalid file extension."""
        filepath = "./submission.txt"
        response = self.user.submit(filepaths=[filepath])
        mock_print.assert_any_call(
            f"\n[ 🔴 ] Submission file must be a CSV file ( .csv ),\n\tplease verify this filepath : {filepath}\n"
        )
        self.assertEqual(response[0]["status"], "error")
        self.assertEqual(response[0]["errors"], "invalid_extension")

    @patch("zindi.user.ZindiPlatformAPI.get_leaderboard")
    @patch("zindi.user.user_on_lb", return_value=2)
    def _leaderboard_success(self, mock_user_on_lb, mock_get):
        """Test fetching the leaderboard successfully."""
        mock_get.return_value = MOCK_LEADERBOARD_DATA["data"]
        self.user.leaderboard(to_print=False)
        mock_get.assert_called_once()
        self.assertEqual(len(self.user._Zindian__challengers_data), 3)
        self.assertEqual(self.user._Zindian__rank, 2)
        mock_user_on_lb.assert_called_once()

    def test_leaderboard_not_selected_error(self):
        """Test fetching leaderboard before selecting a challenge (edge case)."""
        self.user._Zindian__challenge_selected = False  # Override setup
        with self.assertRaises(Exception) as cm:
            self.user.leaderboard()
        self.assertIn("select a challenge before", str(cm.exception))

    @patch("zindi.user.ZindiPlatformAPI.get_submission_history")
    def test_submission_board_success(self, mock_get):
        """Test fetching the submission board successfully."""
        mock_get.return_value = MOCK_SUBMISSION_BOARD_DATA["data"]
        response = self.user.submission_board(to_print=False)
        mock_get.assert_called_once()
        self.assertEqual(len(self.user._Zindian__sb_data), 3)
        self.assertEqual(len(response), 3)

    @patch("zindi.user.ZindiPlatformAPI.get_leaderboard")
    @patch("zindi.user.user_on_lb", return_value=2)
    def test_leaderboard_success_return(self, mock_user_on_lb, mock_get):
        """Test leaderboard returns rank and rows."""
        mock_get.return_value = MOCK_LEADERBOARD_DATA["data"]
        response = self.user.leaderboard(to_print=False)

        self.assertEqual(response["rank"], 2)
        self.assertEqual(len(response["leaderboard"]), 3)
        mock_user_on_lb.assert_called_once()

    def test_submission_board_not_selected_error(self):
        """Test fetching submission board before selecting a challenge (edge case)."""
        self.user._Zindian__challenge_selected = False  # Override setup
        with self.assertRaises(Exception) as cm:
            self.user.submission_board()
        self.assertIn("select a challenge before", str(cm.exception))

    @patch("zindi.user.ZindiPlatformAPI.get_my_participation")
    def _my_rank_success(self, mock_get):
        """Test getting user rank."""
        mock_get.return_value = {"public_rank": 2}
        rank = self.user.my_rank
        self.assertEqual(rank, 2)
        self.assertEqual(self.user._Zindian__rank, 2)

    def test_my_rank_not_selected(self):
        """Test getting rank before selecting a challenge."""
        self.user._Zindian__challenge_selected = False  # Override setup
        rank = self.user.my_rank
        self.assertEqual(rank, 0)

    def test_remaining_submissions_not_selected(self):
        """Test remaining submissions before selecting a challenge."""
        self.user._Zindian__challenge_selected = False  # Override setup
        remaining = self.user.remaining_subimissions
        self.assertIsNone(remaining)


if __name__ == "__main__":
    unittest.main()
