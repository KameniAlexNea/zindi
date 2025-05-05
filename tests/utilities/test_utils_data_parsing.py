import unittest
from unittest.mock import patch

from zindi import utils

# Sample data needed for data parsing tests
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
