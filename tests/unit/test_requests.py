"""Unit tests for the network module."""

from unittest.mock import Mock, patch

import pytest

from newspaper.configuration import Configuration
from newspaper.exceptions import ArticleException
from newspaper.network import get_html


class TestNetwork:
    """Test network module functions."""

    def test_get_html_exception_contains_status_code(self):
        """Test that ArticleException properly includes the status_code in its message.

        This test verifies the fix for the bug where the f-string had double braces
        {{status_code}} instead of single braces {status_code}, causing the status
        code to not be interpolated into the exception message.
        """
        # Create a mock response with a 400 status code
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_response.content = b"Bad Request"
        mock_response.headers = {}
        mock_response.encoding = "utf-8"
        mock_response.history = []

        # Configure to raise exception on http errors
        config = Configuration()
        config.http_success_only = True

        # Mock do_request to return our mock response
        with patch("newspaper.network.do_request", return_value=mock_response):
            with pytest.raises(ArticleException) as exc_info:
                get_html("https://example.com/test", config=config)

            # The exception message should contain the actual status code number
            exception_message = str(exc_info.value)

            # Check if the status code is actually in the message (not just the literal string)
            assert "400" in exception_message, (
                f"Expected '400' to be in exception message, but got: {exception_message}"
            )
            assert "{status_code}" not in exception_message, "Expected status_code to be interpolated, not literal"
            assert "Status code: 400" in exception_message

    def test_get_html_exception_different_status_codes(self):
        """Test that ArticleException properly includes various status codes."""
        test_cases = [400, 401, 403, 404, 500, 502, 503]

        config = Configuration()
        config.http_success_only = True

        for status_code in test_cases:
            # Create a mock response with the current status code
            mock_response = Mock()
            mock_response.status_code = status_code
            mock_response.text = f"Error {status_code}"
            mock_response.content = f"Error {status_code}".encode()
            mock_response.headers = {}
            mock_response.encoding = "utf-8"
            mock_response.history = []

            # Mock do_request to return our mock response
            with patch("newspaper.network.do_request", return_value=mock_response):
                with pytest.raises(ArticleException) as exc_info:
                    get_html("https://example.com/test", config=config)

                # The exception message should contain the actual status code number
                exception_message = str(exc_info.value)
                assert str(status_code) in exception_message, (
                    f"Expected '{status_code}' to be in exception message, but got: {exception_message}"
                )
