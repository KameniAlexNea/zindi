import unittest
from unittest.mock import patch

import pandas as pd

from zindi import utils

# Sample data needed for printing tests
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


# --- Test Class for Printing Functions ---
class TestPrinting(unittest.TestCase):
    @patch("builtins.print")
    def _print_challenges(self, mock_print):
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
    def _print_submission_board(self, mock_to_datetime, mock_print):
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


if __name__ == "__main__":
    unittest.main()
