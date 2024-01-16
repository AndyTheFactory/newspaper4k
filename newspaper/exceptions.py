"""Common exceptions raised by the newspaper package
"""


class ArticleBinaryDataException(Exception):
    """Exception raised for binary data in urls.
    will be raised if :any:`Configuration.allow_binary_content` is False.
    """


class ArticleException(Exception):
    """Generic Article Exception thrown by the article package."""
