import unittest
from unittest.mock import MagicMock, call, mock_open, patch

import requests  # Import requests for exception testing

from zindi import utils


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
        self, mock_monitor, mock_encoder, mock_tqdm, mock_open_func, mock_post
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
        (args,), kwargs = mock_encoder.call_args
        self.assertIn("file", args)
        self.assertEqual(args["file"][0], "to/submission.csv")  # Check filename part
        self.assertEqual(args["file"][2], "text/plain")
        self.assertEqual(args["comment"], comment)

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


if __name__ == "__main__":
    unittest.main()
