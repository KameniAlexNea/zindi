import unittest
from unittest.mock import patch

from zindi.user import Zindian

# Mock API responses
MOCK_SIGNIN_SUCCESS = {
    "data": {
        "auth_token": "mock_token",
        "user": {"username": "testuser", "id": 123},
    }
}
MOCK_SIGNIN_FAILURE = {"data": {"errors": {"message": "Wrong username or password"}}}


# --- Test Class for Authentication ---
class TestUserAuth(unittest.TestCase):
    @patch("zindi.user.requests.post")
    @patch("zindi.user.getpass")
    def test_init_signin_success(self, mock_getpass, mock_post):
        """Test successful initialization and sign-in."""
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
        """Test failed sign-in during initialization."""
        mock_getpass.return_value = "wrongpassword"
        mock_post.return_value.json.return_value = MOCK_SIGNIN_FAILURE
        with self.assertRaises(Exception) as cm:
            Zindian(username="testuser")
        self.assertIn("Wrong username or password", str(cm.exception))
        mock_getpass.assert_called_once()


if __name__ == "__main__":
    unittest.main()
