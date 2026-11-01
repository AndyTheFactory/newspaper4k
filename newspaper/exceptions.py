"""Common exceptions raised by the newspaper package"""

from requests.exceptions import RequestException


class PrivateHostError(RequestException):
    """Raised when a request targets a non-public host and
    :any:`Configuration.allow_private_hosts` is False.
    """


class ArticleBinaryDataException(Exception):
    """Exception raised for binary data in urls.
    will be raised if :any:`Configuration.allow_binary_content` is False.
    """


class ArticleException(Exception):
    """Generic Article Exception thrown by the article package."""


class RobotsException(Exception):
    """Robots.txt disallowed exception"""
