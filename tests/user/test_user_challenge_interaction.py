import datetime
import os
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
    @patch("zindi.user.requests.get")
    @patch("zindi.user.download")
    def test_download_dataset_success(
        self, mock_util_download, mock_get, mock_isdir, mock_makedirs
    ):
        """Test successful dataset download."""
        mock_get.return_value.json.return_value = MOCK_CHALLENGE_DETAILS_DATA
        dest_folder = "./mock_dataset"
        self.user.download_dataset(destination=dest_folder)

        mock_isdir.assert_called_once_with(dest_folder)
        mock_makedirs.assert_called_once_with(dest_folder, exist_ok=True)
        mock_get.assert_called_once_with(
            self.user._Zindian__api,
            headers={"User-Agent": unittest.mock.ANY, "auth_token": "mock_token"},
            data={"auth_token": "mock_token"},
        )
        self.assertEqual(mock_util_download.call_count, 3)
        expected_calls = [
            call(  # Use call() for assert_has_calls
                url=f"{self.user._Zindian__api}/files/Train.csv",
                filename=os.path.join(dest_folder, "Train.csv"),
                headers={"User-Agent": unittest.mock.ANY, "auth_token": "mock_token"},
            ),
            call(
                url=f"{self.user._Zindian__api}/files/Test.csv",
                filename=os.path.join(dest_folder, "Test.csv"),
                headers={"User-Agent": unittest.mock.ANY, "auth_token": "mock_token"},
            ),
            call(
                url=f"{self.user._Zindian__api}/files/SampleSubmission.csv",
                filename=os.path.join(dest_folder, "SampleSubmission.csv"),
                headers={"User-Agent": unittest.mock.ANY, "auth_token": "mock_token"},
            ),
        ]
        mock_util_download.assert_has_calls(expected_calls, any_order=True)

    def test_submit_not_selected_error(self):
        """Test submitting before selecting a challenge (edge case)."""
        self.user._Zindian__challenge_selected = False  # Override setup
        with self.assertRaises(Exception) as cm:
            self.user.submit(filepaths=["./dummy.csv"])
        self.assertIn("select a challenge before", str(cm.exception))

    @patch("zindi.user.os.path.isfile", return_value=True)
    @patch("zindi.user.upload")
    def test_submit_success(self, mock_util_upload, mock_isfile):
        """Test successful submission."""
        mock_util_upload.return_value.json.return_value = MOCK_SUBMIT_SUCCESS
        filepath = "./submission.csv"
        comment = "Test submission"
        self.user.submit(filepaths=[filepath], comments=[comment])

        mock_isfile.assert_called_once_with(filepath)
        mock_util_upload.assert_called_once_with(
            filepath=filepath,
            comment=comment,
            url=f"{self.user._Zindian__api}/submissions",
            headers={"User-Agent": unittest.mock.ANY, "auth_token": "mock_token"},
        )

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
        self.user.submit(filepaths=[filepath])
        mock_print.assert_any_call(
            f"\n[ 🔴 ] Submission file must be a CSV file ( .csv ),\n\tplease verify this filepath : {filepath}\n"
        )

    @patch("zindi.user.requests.get")
    @patch("zindi.user.participations", return_value=None)
    def _leaderboard_success(self, mock_participations, mock_get):
        """Test fetching the leaderboard successfully."""
        mock_get.return_value.json.return_value = MOCK_LEADERBOARD_DATA
        self.user.leaderboard(to_print=False)
        mock_get.assert_called_once()
        self.assertEqual(len(self.user._Zindian__challengers_data), 3)
        self.assertEqual(self.user._Zindian__rank, 2)

    def test_leaderboard_not_selected_error(self):
        """Test fetching leaderboard before selecting a challenge (edge case)."""
        self.user._Zindian__challenge_selected = False  # Override setup
        with self.assertRaises(Exception) as cm:
            self.user.leaderboard()
        self.assertIn("select a challenge before", str(cm.exception))

    @patch("zindi.user.requests.get")
    def test_submission_board_success(self, mock_get):
        """Test fetching the submission board successfully."""
        mock_get.return_value.json.return_value = MOCK_SUBMISSION_BOARD_DATA
        self.user.submission_board(to_print=False)
        mock_get.assert_called_once()
        self.assertEqual(len(self.user._Zindian__sb_data), 3)

    def test_submission_board_not_selected_error(self):
        """Test fetching submission board before selecting a challenge (edge case)."""
        self.user._Zindian__challenge_selected = False  # Override setup
        with self.assertRaises(Exception) as cm:
            self.user.submission_board()
        self.assertIn("select a challenge before", str(cm.exception))

    @patch("zindi.user.requests.get")
    @patch("zindi.user.participations", return_value=None)
    def _my_rank_success(self, mock_participations, mock_get):
        """Test getting user rank."""
        mock_get.return_value.json.return_value = MOCK_LEADERBOARD_DATA
        rank = self.user.my_rank
        self.assertEqual(rank, 2)
        self.assertEqual(self.user._Zindian__rank, 2)

    def test_my_rank_not_selected(self):
        """Test getting rank before selecting a challenge."""
        self.user._Zindian__challenge_selected = False  # Override setup
        rank = self.user.my_rank
        self.assertEqual(rank, 0)

    @patch("zindi.user.requests.get")
    @patch("zindi.user.n_subimissions_per_day", return_value=5)
    def test_remaining_submissions_success(self, mock_n_sub, mock_get_sb):
        """Test calculating remaining submissions."""
        mock_get_sb.return_value.json.return_value = MOCK_SUBMISSION_BOARD_DATA
        remaining = self.user.remaining_subimissions
        self.assertEqual(remaining, 4)
        mock_n_sub.assert_called_once()
        mock_get_sb.assert_called_once()

    def test_remaining_submissions_not_selected(self):
        """Test remaining submissions before selecting a challenge."""
        self.user._Zindian__challenge_selected = False  # Override setup
        remaining = self.user.remaining_subimissions
        self.assertIsNone(remaining)


if __name__ == "__main__":
    unittest.main()
