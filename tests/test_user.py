import os
import sys
import unittest
from unittest.mock import patch, MagicMock, mock_open
import pandas as pd
import datetime

from zindi.user import Zindian
from zindi.utils import download, upload

# Mock API responses
MOCK_SIGNIN_SUCCESS = {
    "data": {
        "auth_token": "mock_token",
        "user": {"username": "testuser", "id": 123},
    }
}
MOCK_SIGNIN_FAILURE = {"data": {"errors": {"message": "Wrong username or password"}}}
MOCK_CHALLENGES_DATA = pd.DataFrame(
    [
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
)
MOCK_PARTICIPATION_SUCCESS = {"data": {"ids": [1]}}
MOCK_PARTICIPATION_ALREADY_IN = {"data": {"errors": {"message": "already in"}}}
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
            "created_at": (datetime.datetime.utcnow() - datetime.timedelta(hours=2)).isoformat() + "Z",
            "filename": "submission1.csv",
            "public_score": 0.92,
            "private_score": 0.91,
            "comment": "First attempt",
            "status_description": None,
        },
        {
            "id": "sub-2",
            "status": "failed",
            "created_at": (datetime.datetime.utcnow() - datetime.timedelta(hours=1)).isoformat() + "Z",
            "filename": "submission2.csv",
            "public_score": None,
            "private_score": None,
            "comment": "Second attempt",
            "status_description": "Invalid format",
        },
         {
            "id": "sub-3",
            "status": "successful",
            "created_at": (datetime.datetime.utcnow() - datetime.timedelta(days=1, hours=5)).isoformat() + "Z",
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
            {"title": "Rules", "content_html": "Blah blah You may make a maximum of 5 submissions per day. Blah blah"},
        ]
    }
}
MOCK_SUBMIT_SUCCESS = {"data": {"id": "sub-new-123"}}
MOCK_SUBMIT_FAILURE = {"data": {"errors": {"base": "Submission failed"}}}
MOCK_CREATE_TEAM_SUCCESS = {"data": {"title": "New Team"}}
MOCK_CREATE_TEAM_ALREADY_LEADER = {"data": {"errors": {"base": "Leader can only be part of one team per competition."}}}
MOCK_TEAM_UP_SUCCESS = {"data": {"message": "Invitation sent"}}
MOCK_TEAM_UP_ALREADY_INVITED = {"data": {"errors": {"base": "User is already invited"}}}
MOCK_DISBAND_SUCCESS = {"data": "Team disbanded successfully"}


class TestZindian(unittest.TestCase):

    @patch("zindi.user.requests.post")
    @patch("zindi.user.getpass")
    def test_init_signin_success(self, mock_getpass, mock_post):
        mock_getpass.return_value = "password"
        mock_post.return_value.json.return_value = MOCK_SIGNIN_SUCCESS
        user = Zindian(username="testuser")
        mock_getpass.assert_called_once()
        mock_post.assert_called_once_with(
            "https://api.zindi.africa/v1/auth/signin",
            data={"username": "testuser", "password": "password"},
            headers=user._Zindian__headers,
        )
        self.assertEqual(user._Zindian__auth_data, MOCK_SIGNIN_SUCCESS["data"])
        self.assertFalse(user._Zindian__challenge_selected)

    @patch("zindi.user.requests.post")
    @patch("zindi.user.getpass")
    def test_init_signin_failure(self, mock_getpass, mock_post):
        mock_getpass.return_value = "wrongpassword"
        mock_post.return_value.json.return_value = MOCK_SIGNIN_FAILURE
        with self.assertRaises(Exception) as cm:
            Zindian(username="testuser")
        self.assertIn("Wrong username or password", str(cm.exception))
        mock_getpass.assert_called_once()

    @patch("zindi.user.requests.post")
    @patch("zindi.user.getpass")
    def setUp(self, mock_getpass, mock_post):
        mock_getpass.return_value = "password"
        mock_post.return_value.json.return_value = MOCK_SIGNIN_SUCCESS
        self.user = Zindian(username="testuser")
        mock_getpass.reset_mock()
        mock_post.reset_mock()

    def test_which_challenge_not_selected(self):
        self.assertIsNone(self.user.which_challenge)

    @patch("zindi.user.requests.get")
    @patch("zindi.user.requests.post")
    @patch("builtins.input", return_value="1")
    def test_select_a_challenge_success(self, mock_input, mock_post, mock_get):
        mock_get.return_value.json.return_value = {"data": MOCK_CHALLENGES_DATA.to_dict('records')}
        mock_post.return_value.json.return_value = MOCK_PARTICIPATION_SUCCESS

        self.user.select_a_challenge(kind="all")

        mock_get.assert_called_once()
        mock_post.assert_called_once()
        self.assertTrue(self.user._Zindian__challenge_selected)
        self.assertEqual(self.user._Zindian__challenge_data["id"], "challenge-2")
        self.assertEqual(self.user.which_challenge, "challenge-2")

    @patch("zindi.user.requests.get")
    @patch("zindi.user.requests.post")
    def test_select_a_challenge_fixed_index(self, mock_post, mock_get):
        mock_get.return_value.json.return_value = {"data": MOCK_CHALLENGES_DATA.to_dict('records')}
        mock_post.return_value.json.return_value = MOCK_PARTICIPATION_ALREADY_IN

        self.user.select_a_challenge(fixed_index=2)

        self.assertTrue(self.user._Zindian__challenge_selected)
        self.assertEqual(self.user._Zindian__challenge_data["id"], "challenge-3")
        mock_post.assert_called_once()

    @patch("zindi.user.requests.get")
    def test_select_a_challenge_invalid_fixed_index(self, mock_get):
        mock_get.return_value.json.return_value = {"data": MOCK_CHALLENGES_DATA.to_dict('records')}
        with self.assertRaises(Exception) as cm:
            self.user.select_a_challenge(fixed_index=10)
        self.assertIn("must be an integer in range", str(cm.exception))

        with self.assertRaises(Exception) as cm:
            self.user.select_a_challenge(fixed_index=-1)
        self.assertIn("must be an integer in range", str(cm.exception))

    def test_download_dataset_not_selected(self):
        with self.assertRaises(Exception) as cm:
            self.user.download_dataset()
        self.assertIn("select a challenge before", str(cm.exception))

    @patch("zindi.user.os.makedirs")
    @patch("zindi.user.os.path.isdir", return_value=False)
    @patch("zindi.user.requests.get")
    @patch("zindi.user.download")
    def test_download_dataset_success(self, mock_util_download, mock_get, mock_isdir, mock_makedirs):
        self.user._Zindian__challenge_selected = True
        self.user._Zindian__challenge_data = pd.Series({"id": "challenge-2"})
        self.user._Zindian__api = f"{self.user._Zindian__base_api}/challenge-2"

        mock_get.return_value.json.return_value = MOCK_CHALLENGE_DETAILS_DATA

        dest_folder = "./mock_dataset"
        self.user.download_dataset(destination=dest_folder)

        mock_isdir.assert_called_once_with(dest_folder)
        mock_makedirs.assert_called_once_with(dest_folder, exist_ok=True)
        mock_get.assert_called_once_with(
            self.user._Zindian__api,
            headers={'User-Agent': unittest.mock.ANY, 'auth_token': 'mock_token'},
            data={'auth_token': 'mock_token'}
        )
        self.assertEqual(mock_util_download.call_count, 3)
        expected_calls = [
            unittest.mock.call(
                url=f"{self.user._Zindian__api}/files/Train.csv",
                filename=os.path.join(dest_folder, "Train.csv"),
                headers={'User-Agent': unittest.mock.ANY, 'auth_token': 'mock_token'}
            ),
            unittest.mock.call(
                url=f"{self.user._Zindian__api}/files/Test.csv",
                filename=os.path.join(dest_folder, "Test.csv"),
                headers={'User-Agent': unittest.mock.ANY, 'auth_token': 'mock_token'}
            ),
            unittest.mock.call(
                url=f"{self.user._Zindian__api}/files/SampleSubmission.csv",
                filename=os.path.join(dest_folder, "SampleSubmission.csv"),
                headers={'User-Agent': unittest.mock.ANY, 'auth_token': 'mock_token'}
            ),
        ]
        mock_util_download.assert_has_calls(expected_calls, any_order=True)

    def test_submit_not_selected(self):
        with self.assertRaises(Exception) as cm:
            self.user.submit(filepaths=["./dummy.csv"])
        self.assertIn("select a challenge before", str(cm.exception))

    @patch("zindi.user.os.path.isfile", return_value=True)
    @patch("zindi.user.upload")
    def test_submit_success(self, mock_util_upload, mock_isfile):
        self.user._Zindian__challenge_selected = True
        self.user._Zindian__challenge_data = pd.Series({"id": "challenge-2"})
        self.user._Zindian__api = f"{self.user._Zindian__base_api}/challenge-2"

        mock_util_upload.return_value.json.return_value = MOCK_SUBMIT_SUCCESS
        filepath = "./submission.csv"
        comment = "Test submission"
        self.user.submit(filepaths=[filepath], comments=[comment])

        mock_isfile.assert_called_once_with(filepath)
        mock_util_upload.assert_called_once_with(
            filepath=filepath,
            comment=comment,
            url=f"{self.user._Zindian__api}/submissions",
            headers={'User-Agent': unittest.mock.ANY, 'auth_token': 'mock_token'}
        )

    @patch("zindi.user.os.path.isfile", return_value=False)
    def test_submit_file_not_exist(self, mock_isfile):
        self.user._Zindian__challenge_selected = True
        self.user._Zindian__challenge_data = pd.Series({"id": "challenge-2"})
        self.user._Zindian__api = f"{self.user._Zindian__base_api}/challenge-2"
        filepath = "./nonexistent.csv"
        self.user.submit(filepaths=[filepath])
        mock_isfile.assert_called_once_with(filepath)

    def test_submit_invalid_extension(self):
        self.user._Zindian__challenge_selected = True
        self.user._Zindian__challenge_data = pd.Series({"id": "challenge-2"})
        self.user._Zindian__api = f"{self.user._Zindian__base_api}/challenge-2"
        filepath = "./submission.txt"
        self.user.submit(filepaths=[filepath])

    @patch("zindi.user.requests.get")
    @patch("zindi.user.participations", return_value=None)
    def test_leaderboard_success(self, mock_participations, mock_get):
        self.user._Zindian__challenge_selected = True
        self.user._Zindian__challenge_data = pd.Series({"id": "challenge-2"})
        self.user._Zindian__api = f"{self.user._Zindian__base_api}/challenge-2"
        mock_get.return_value.json.return_value = MOCK_LEADERBOARD_DATA

        self.user.leaderboard(to_print=False)

        mock_get.assert_called_once()
        self.assertEqual(len(self.user._Zindian__challengers_data), 3)
        self.assertEqual(self.user._Zindian__rank, 2)

    def test_leaderboard_not_selected(self):
        with self.assertRaises(Exception) as cm:
            self.user.leaderboard()
        self.assertIn("select a challenge before", str(cm.exception))

    @patch("zindi.user.requests.get")
    def test_submission_board_success(self, mock_get):
        self.user._Zindian__challenge_selected = True
        self.user._Zindian__challenge_data = pd.Series({"id": "challenge-2"})
        self.user._Zindian__api = f"{self.user._Zindian__base_api}/challenge-2"
        mock_get.return_value.json.return_value = MOCK_SUBMISSION_BOARD_DATA

        self.user.submission_board(to_print=False)

        mock_get.assert_called_once()
        self.assertEqual(len(self.user._Zindian__sb_data), 3)

    def test_submission_board_not_selected(self):
        with self.assertRaises(Exception) as cm:
            self.user.submission_board()
        self.assertIn("select a challenge before", str(cm.exception))

    @patch("zindi.user.requests.get")
    @patch("zindi.user.participations", return_value=None)
    def test_my_rank_success(self, mock_participations, mock_get):
        self.user._Zindian__challenge_selected = True
        self.user._Zindian__challenge_data = pd.Series({"id": "challenge-2"})
        self.user._Zindian__api = f"{self.user._Zindian__base_api}/challenge-2"
        mock_get.return_value.json.return_value = MOCK_LEADERBOARD_DATA

        rank = self.user.my_rank
        self.assertEqual(rank, 2)
        self.assertEqual(self.user._Zindian__rank, 2)

    def test_my_rank_not_selected(self):
        rank = self.user.my_rank
        self.assertEqual(rank, 0)

    @patch("zindi.user.requests.get")
    @patch("zindi.user.n_subimissions_per_day", return_value=5)
    def test_remaining_submissions_success(self, mock_n_sub, mock_get_sb):
        self.user._Zindian__challenge_selected = True
        self.user._Zindian__challenge_data = pd.Series({"id": "challenge-2"})
        self.user._Zindian__api = f"{self.user._Zindian__base_api}/challenge-2"
        mock_get_sb.return_value.json.return_value = MOCK_SUBMISSION_BOARD_DATA

        remaining = self.user.remaining_subimissions

        self.assertEqual(remaining, 4)
        mock_n_sub.assert_called_once()
        mock_get_sb.assert_called_once()

    def test_remaining_submissions_not_selected(self):
        remaining = self.user.remaining_subimissions
        self.assertIsNone(remaining)

    @patch("zindi.user.requests.post")
    def test_create_team_success(self, mock_post):
        self.user._Zindian__challenge_selected = True
        self.user._Zindian__challenge_data = pd.Series({"id": "challenge-2"})
        self.user._Zindian__api = f"{self.user._Zindian__base_api}/challenge-2"
        mock_post.return_value.json.return_value = MOCK_CREATE_TEAM_SUCCESS

        self.user.create_team(team_name="New Team")
        mock_post.assert_called_once_with(
            f"{self.user._Zindian__api}/my_team",
            headers={'User-Agent': unittest.mock.ANY},
            data={'title': 'New Team', 'auth_token': 'mock_token'}
        )

    @patch("zindi.user.requests.post")
    def test_create_team_already_leader(self, mock_post):
        self.user._Zindian__challenge_selected = True
        self.user._Zindian__challenge_data = pd.Series({"id": "challenge-2"})
        self.user._Zindian__api = f"{self.user._Zindian__base_api}/challenge-2"
        mock_post.return_value.json.return_value = MOCK_CREATE_TEAM_ALREADY_LEADER

        self.user.create_team(team_name="Another Team")
        mock_post.assert_called_once()

    @patch("zindi.user.requests.post")
    def test_team_up_success(self, mock_post):
        self.user._Zindian__challenge_selected = True
        self.user._Zindian__challenge_data = pd.Series({"id": "challenge-2"})
        self.user._Zindian__api = f"{self.user._Zindian__base_api}/challenge-2"
        mock_post.return_value.json.return_value = MOCK_TEAM_UP_SUCCESS

        teammates = ["friend1", "friend2"]
        self.user.team_up(zindians=teammates)

        self.assertEqual(mock_post.call_count, 2)
        expected_calls = [
            unittest.mock.call(
                f"{self.user._Zindian__api}/my_team/invite",
                headers={'User-Agent': unittest.mock.ANY},
                data={'username': 'friend1'}
            ),
             unittest.mock.call(
                f"{self.user._Zindian__api}/my_team/invite",
                headers={'User-Agent': unittest.mock.ANY},
                data={'username': 'friend2'}
            ),
        ]

    @patch("zindi.user.requests.delete")
    def test_disband_team_success(self, mock_delete):
        self.user._Zindian__challenge_selected = True
        self.user._Zindian__challenge_data = pd.Series({"id": "challenge-2"})
        self.user._Zindian__api = f"{self.user._Zindian__base_api}/challenge-2"
        mock_delete.return_value.json.return_value = MOCK_DISBAND_SUCCESS

        self.user.disband_team()
        mock_delete.assert_called_once_with(
            f"{self.user._Zindian__api}/my_team",
            headers={'User-Agent': unittest.mock.ANY},
            data={'auth_token': 'mock_token'}
        )


if __name__ == "__main__":
    unittest.main()
