import unittest
from unittest.mock import patch

from zindi import utils


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


if __name__ == "__main__":
    unittest.main()
