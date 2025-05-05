import os
import sys
import unittest
from unittest.mock import MagicMock, call, mock_open, patch

import pandas as pd
import requests  # Import requests for exception testing

# Ensure the zindi package is importable
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

from zindi import utils

# Sample data for testing print functions and others
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

SAMPLE_LEADERBOARD_DATA = [
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
        "user": {"username": "testuser"},  # The user we might be testing for
        "submission_count": 3,
        "best_public_submitted_at": "2023-01-09T15:30:00Z",
    },
    {
        "public_rank": 3,
        "best_public_score": 0.90,
        "team": {"title": "Team Awesome", "id": "team-123"},  # A team entry
        "submission_count": 8,
        "best_public_submitted_at": None,  # No submission time
    },
    {  # Entry with private scores
        "private_rank": 4,
        "best_private_score": 0.88,
        "user": {"username": "anotheruser"},
        "submission_count": 2,
        "best_private_submitted_at": "2023-01-12T11:00:00Z",
    },
    {  # Entry with no rank (should be skipped in print)
        "public_rank": None,
        "best_public_score": None,
        "user": {"username": "inactiveuser"},
        "submission_count": 0,
        "best_public_submitted_at": None,
    },
]

SAMPLE_SUBMISSION_BOARD_DATA = [
    {
        "id": "sub-1",
        "status": "successful",
        "created_at": "2023-01-10T10:00:00Z",
        "filename": "submission1.csv",
        "public_score": 0.92,
        "private_score": 0.91,
        "comment": "First attempt",
        "status_description": None,
    },
    {  # In processing
        "id": "sub-2",
        "status": "initial",
        "created_at": "2023-01-11T11:00:00Z",
        "filename": "submission2_long_filename_to_test_truncation.csv",
        "public_score": None,
        "private_score": None,
        "comment": None,  # No comment
        "status_description": None,
    },
    {  # Failed submission
        "id": "sub-3",
        "status": "failed",
        "created_at": "2023-01-12T12:00:00Z",
        "filename": "submission3.csv",
        "public_score": None,
        "private_score": None,
        "comment": "Failed one",
        "status_description": "Invalid file format provided by user.",
    },
]

SAMPLE_PARTICIPATIONS_RESPONSE = {
    "data": {
        "challenge-1": {"team_id": None},
        "challenge-2": {"team_id": "team-abc"},
    }
}

SAMPLE_CHALLENGE_RULES_PAGE = {
    "data": {
        "pages": [
            {"title": "Overview", "content_html": "Some content"},
            {
                "title": "Rules",
                "content_html": "Blah blah You may make a maximum of 7 submissions per day. Blah blah",
            },
        ]
    }
}

SAMPLE_CHALLENGE_NO_RULES_PAGE = {
    "data": {
        "pages": [
            {"title": "Overview", "content_html": "Some content"},
            {"title": "Data", "content_html": "Data details"},
        ]
    }
}

SAMPLE_CHALLENGE_MALFORMED_RULES = {
    "data": {
        "pages": [
            {"title": "Rules", "content_html": "Submit whenever you want."},
        ]
    }
}


# --- Test Class for File Operations (Download, Upload) ---
class TestFileOperations(unittest.TestCase):
    @patch("zindi.utils.requests.get")
    @patch("zindi.utils.open", new_callable=mock_open)
    @patch("zindi.utils.tqdm")
    def test_download_success(self, mock_tqdm, mock_open_func, mock_get):
        """Test successful file download."""
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.headers.get.return_value = "10240"  # content-length
        mock_response.iter_content.return_value = [b"chunk1", b"chunk2"]
        mock_get.return_value = mock_response

        mock_bar = MagicMock()
        mock_tqdm.return_value.__enter__.return_value = mock_bar

        mock_file_handle = mock_open_func.return_value.__enter__.return_value
        mock_file_handle.write.side_effect = [len(b"chunk1"), len(b"chunk2")]

        url = "http://example.com/file.csv"
        filename = "local_file.csv"
        headers = {"auth_token": "test_token"}

        utils.download(url=url, filename=filename, headers=headers)

        mock_get.assert_called_once_with(
            url, headers=headers, data={"auth_token": "test_token"}, stream=True
        )
        mock_response.raise_for_status.assert_called_once()
        mock_open_func.assert_called_once_with(filename, "wb")
        mock_tqdm.assert_called_once_with(
            desc=filename, total=10240, unit="o", unit_scale=True, unit_divisor=1024
        )
        self.assertEqual(mock_file_handle.write.call_count, 2)
        mock_file_handle.write.assert_has_calls([call(b"chunk1"), call(b"chunk2")])
        self.assertEqual(mock_bar.update.call_count, 2)
        mock_bar.update.assert_has_calls([call(len(b"chunk1")), call(len(b"chunk2"))])

    @patch("zindi.utils.requests.get")
    def test_download_error(self, mock_get):
        """Test download with a request error."""
        mock_response = MagicMock()
        # Use requests.exceptions.RequestException directly
        mock_response.raise_for_status.side_effect = (
            requests.exceptions.RequestException("Error")
        )
        mock_get.return_value = mock_response

        with self.assertRaises(requests.exceptions.RequestException):
            # Pass a dict to headers, even if empty, due to type hint
            utils.download(url="http://badurl.com/file", filename="bad.csv", headers={})
        mock_get.assert_called_once()
        mock_response.raise_for_status.assert_called_once()

    @patch("zindi.utils.requests.post")
    @patch("zindi.utils.open", new_callable=mock_open, read_data=b"file content")
    @patch("zindi.utils.tqdm")
    @patch("zindi.utils.MultipartEncoder")
    @patch("zindi.utils.MultipartEncoderMonitor")
    @patch("zindi.utils.os.sep", "/")  # Mock os separator for consistency
    def test_upload_success(
        self, mock_post, mock_open_func, mock_tqdm, mock_encoder, mock_monitor, mock_sep
    ):
        """Test successful file upload."""
        mock_encoder_instance = MagicMock()
        mock_encoder_instance.len = 5000
        mock_encoder.return_value = mock_encoder_instance

        mock_monitor_instance = MagicMock()
        mock_monitor_instance.content_type = "mock/content-type"
        mock_monitor.return_value = mock_monitor_instance

        mock_response = MagicMock()
        mock_post.return_value = mock_response

        mock_bar = MagicMock()
        mock_tqdm.return_value.__enter__.return_value = mock_bar

        filepath = "/path/to/submission.csv"
        comment = "My submission"
        url = "http://example.com/upload"
        headers = {"auth_token": "test_token"}

        response = utils.upload(
            filepath=filepath, comment=comment, url=url, headers=headers
        )

        mock_open_func.assert_called_once_with(filepath, "rb")
        mock_encoder.assert_called_once()
        # Check that the file tuple was passed correctly to MultipartEncoder
        args, kwargs = mock_encoder.call_args
        self.assertIn("file", kwargs)
        self.assertEqual(kwargs["file"][0], "to/submission.csv")  # Check filename part
        self.assertEqual(kwargs["file"][2], "text/plain")
        self.assertEqual(kwargs["comment"], comment)

        mock_monitor.assert_called_once_with(mock_encoder_instance, unittest.mock.ANY)
        mock_tqdm.assert_called_once_with(
            desc="Submit to/submission.csv",
            total=5000,
            ncols=100,
            unit="o",
            unit_scale=True,
            unit_divisor=1024,
        )

        expected_headers = {
            "auth_token": "test_token",
            "Content-Type": "mock/content-type",
        }
        mock_post.assert_called_once_with(
            url,
            data=mock_monitor_instance,
            params={"auth_token": "test_token"},
            headers=expected_headers,
        )
        self.assertEqual(response, mock_response)


# --- Test Class for Printing Functions ---
class TestPrinting(unittest.TestCase):
    @patch("builtins.print")
    def test_print_challenges(self, mock_print):
        """Test printing challenges table."""
        utils.print_challenges(SAMPLE_CHALLENGES_DATA)
        # Check if print was called multiple times (header, separator, rows)
        self.assertGreater(mock_print.call_count, 5)
        # Check specific row content (e.g., first challenge)
        mock_print.assert_any_call(
            "|{:^5}|{:^14.14}|{:^18.18}|{:^20.20}| {:10}".format(
                0,
                "Public Compet",
                "Classification",
                "prize",
                "challenge-1-long-id-string-that-needs-truncating..."[:10],
            )
        )
        # Check second challenge (private hackathon, no problem type)
        mock_print.assert_any_call(
            "|{:^5}|{:^14.14}|{:^18.18}|{:^20.20}| {:10}".format(
                1, "Private Hack", "", "points", "challenge-2"[:10]
            )
        )

    @patch("builtins.print")
    @patch(
        "zindi.utils.pd.to_datetime"
    )  # Mock datetime conversion for consistent output
    def test_print_lb(self, mock_to_datetime, mock_print):
        """Test printing leaderboard table."""
        # Mock datetime conversion to return predictable strings
        mock_to_datetime.return_value.strftime.side_effect = [
            "10 January 2023, 10:00",  # leader
            "09 January 2023, 15:30",  # testuser
            # None for Team Awesome
            "12 January 2023, 11:00",  # anotheruser (private)
        ]

        user_rank = 2  # Rank of 'testuser'
        utils.print_lb(SAMPLE_LEADERBOARD_DATA, user_rank)

        self.assertGreater(mock_print.call_count, 5)
        # Check header
        mock_print.assert_any_call(
            "|{:^6}|{:^20}|{:^44}|{:^12}|{:^12}".format(
                "rank", "score", "name", "counter", "last_submission"
            )
        )
        # Check user row (marked with green circle)
        mock_print.assert_any_call(
            "|{:^6}|{:^20.20}|{:^44.44}|{:^12.12}|{:^12}".format(
                "2", "0.92", "testuser 🟢", "3", "09 January 2023, 15:30"
            )
        )
        # Check team row
        mock_print.assert_any_call(
            "|{:^6}|{:^20.20}|{:^44.44}|{:^12.12}|{:^12}".format(
                "3", "0.9", "TEAM - Team Awesome", "8", ""
            )
        )
        # Check private rank row
        mock_print.assert_any_call(
            "|{:^6}|{:^20.20}|{:^44.44}|{:^12.12}|{:^12}".format(
                "4", "0.88", "anotheruser", "2", "12 January 2023, 11:00"
            )
        )
        # Ensure the row with rank None was skipped (check call count or absence of 'inactiveuser')
        print_calls = [args[0] for args, kwargs in mock_print.call_args_list]
        self.assertFalse(any("inactiveuser" in call_str for call_str in print_calls))

    @patch("builtins.print")
    @patch("zindi.utils.pd.to_datetime")
    def test_print_submission_board(self, mock_to_datetime, mock_print):
        """Test printing submission board table."""
        mock_to_datetime.return_value.strftime.side_effect = [
            "10 Jan 2023, 10:00",  # sub-1
            "11 Jan 2023, 11:00",  # sub-2
            "12 Jan 2023, 12:00",  # sub-3
        ]

        utils.print_submission_board(SAMPLE_SUBMISSION_BOARD_DATA)

        self.assertGreater(mock_print.call_count, 4)
        # Check header
        mock_print.assert_any_call(
            "|{:^6}|{:^10}|{:^18}|{:^16}|{:^30} |{:^25}".format(
                "status", "id", "date", "score", "filename", "comment"
            )
        )
        # Check successful submission row
        mock_print.assert_any_call(
            "|{:^5}|{:^10}|{:^12}| {:^14.14} |{:30.30} |{:40.40}".format(
                "🟢",
                "sub-1",
                "10 Jan 2023, 10:00",
                "0.91",
                "submission1.csv",
                "First attempt",
            )
        )
        # Check initial/processing submission row
        mock_print.assert_any_call(
            "|{:^5}|{:^10}|{:^12}| {:^14.14} |{:30.30} |{:40.40}".format(
                "🟢",
                "sub-2",
                "11 Jan 2023, 11:00",
                "In processing",
                "submission2_long_filename_to_",
                "",
            )
        )
        # Check failed submission row
        mock_print.assert_any_call(
            "|{:^5}|{:^10}|{:^12}| {:^14.14} |{:30.30} |{:40.40}".format(
                "🔴",
                "sub-3",
                "12 Jan 2023, 12:00",
                "-",
                "submission3.csv",
                "Invalid file format provided by user.",
            )
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


# --- Test Class for User Input Functions ---
class TestUserInput(unittest.TestCase):
    @patch(
        "builtins.input", side_effect=["abc", "-1", "100", "1", "q"]
    )  # Invalid, invalid, invalid, valid, quit
    @patch("builtins.print")
    def test_challenge_idx_selector(self, mock_print, mock_input):
        """Test challenge index selector with various inputs."""
        n_challenges = 3

        # Test invalid inputs then valid
        index = utils.challenge_idx_selector(n_challenges)
        self.assertEqual(mock_input.call_count, 4)  # abc, -1, 100, 1
        self.assertEqual(mock_print.call_count, 3)  # Error messages
        self.assertEqual(index, 1)

        # Reset mock and test quit
        mock_input.reset_mock()
        mock_print.reset_mock()
        mock_input.side_effect = ["q"]
        index = utils.challenge_idx_selector(n_challenges)
        self.assertEqual(mock_input.call_count, 1)
        self.assertEqual(index, -1)


# --- Test Class for Data Parsing/Retrieval Functions ---
class TestDataParsing(unittest.TestCase):
    @patch("zindi.utils.requests.get")
    def test_participations_found(self, mock_get):
        """Test participations check when user is participating."""
        mock_get.return_value.json.return_value = SAMPLE_PARTICIPATIONS_RESPONSE
        mock_get.return_value.raise_for_status.return_value = None
        headers = {"auth_token": "token"}

        team_id_none = utils.participations("challenge-1", headers)
        self.assertIsNone(team_id_none)

        team_id_exists = utils.participations("challenge-2", headers)
        self.assertEqual(team_id_exists, "team-abc")

        self.assertEqual(mock_get.call_count, 2)
        mock_get.assert_called_with(
            "https://api.zindi.africa/v1/participations", headers=headers
        )

    @patch("zindi.utils.requests.get")
    def test_participations_not_found(self, mock_get):
        """Test participations check when challenge ID is not in response."""
        mock_get.return_value.json.return_value = SAMPLE_PARTICIPATIONS_RESPONSE
        mock_get.return_value.raise_for_status.return_value = None
        headers = {"auth_token": "token"}

        with self.assertRaises(KeyError):  # Expect KeyError if challenge_id is missing
            utils.participations("challenge-missing", headers)

    @patch("zindi.utils.participations")
    def test_user_on_lb_direct_user(self, mock_participations):
        """Test finding user rank directly."""
        mock_participations.return_value = None  # User is not in a team
        headers = {"auth_token": "token"}
        rank = utils.user_on_lb(
            SAMPLE_LEADERBOARD_DATA, "challenge-id", "testuser", headers
        )
        self.assertEqual(rank, 2)  # 'testuser' is at index 1, rank 2
        mock_participations.assert_called_once_with(
            challenge_id="challenge-id", headers=headers
        )

    @patch("zindi.utils.participations")
    def test_user_on_lb_team_user(self, mock_participations):
        """Test finding user rank via team."""
        mock_participations.return_value = "team-123"  # User is in this team
        headers = {"auth_token": "token"}
        rank = utils.user_on_lb(
            SAMPLE_LEADERBOARD_DATA, "challenge-id", "anyuser_in_team", headers
        )
        self.assertEqual(rank, 3)  # 'Team Awesome' (team-123) is at index 2, rank 3
        mock_participations.assert_called_once_with(
            challenge_id="challenge-id", headers=headers
        )

    @patch("zindi.utils.participations")
    def test_user_on_lb_not_found(self, mock_participations):
        """Test when user is not found on the leaderboard."""
        mock_participations.return_value = None
        headers = {"auth_token": "token"}
        rank = utils.user_on_lb(
            SAMPLE_LEADERBOARD_DATA, "challenge-id", "nonexistentuser", headers
        )
        self.assertEqual(rank, 0)  # Should return 0 if not found
        mock_participations.assert_called_once_with(
            challenge_id="challenge-id", headers=headers
        )

    @patch("zindi.utils.requests.get")
    def test_n_submissions_per_day_found(self, mock_get):
        """Test finding the number of submissions per day."""
        mock_get.return_value.json.return_value = SAMPLE_CHALLENGE_RULES_PAGE
        headers = {"auth_token": "token"}
        url = "http://example.com/challenge"
        n_sub = utils.n_subimissions_per_day(url, headers)
        self.assertEqual(n_sub, 7)
        mock_get.assert_called_once_with(url=url, headers=headers)

    @patch("zindi.utils.requests.get")
    def test_n_submissions_per_day_not_found_in_rules(self, mock_get):
        """Test when the submission limit string is not in the rules page."""
        mock_get.return_value.json.return_value = SAMPLE_CHALLENGE_MALFORMED_RULES
        headers = {"auth_token": "token"}
        url = "http://example.com/challenge"
        n_sub = utils.n_subimissions_per_day(url, headers)
        self.assertEqual(n_sub, 0)  # Expect 0 if parsing fails
        mock_get.assert_called_once_with(url=url, headers=headers)

    @patch("zindi.utils.requests.get")
    def test_n_submissions_per_day_no_rules_page(self, mock_get):
        """Test when there is no page titled 'Rules'."""
        mock_get.return_value.json.return_value = SAMPLE_CHALLENGE_NO_RULES_PAGE
        headers = {"auth_token": "token"}
        url = "http://example.com/challenge"
        # Based on the previous test run, the current code returns 0 gracefully.
        n_sub = utils.n_subimissions_per_day(url, headers)
        self.assertEqual(
            n_sub, 0
        )  # Expect 0 if 'Rules' page or the specific text isn't found
        mock_get.assert_called_once_with(url=url, headers=headers)


if __name__ == "__main__":
    unittest.main()
