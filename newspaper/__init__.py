# Copyright (c) [2023-] [Andrei Paraschiv]
#
# This file is part of [Newspaper4k].
#   https://github.com/AndyTheFactory/newspaper4k
#
# [Newspaper4k] includes code from the original project,
# [newspaper4k], which is licensed under [MIT].
#
# I would like to express gratitude to the creator of [newspaper4k],
# Lucas Ou-Yang (codelucas) for their valuable work.
# You can find the original project here: https://github.com/codelucas/newspaper


import logging
from importlib import import_module
from logging import NullHandler
from typing import TYPE_CHECKING

from .api import Configuration as Config
from .api import build, build_article, fulltext, hot, languages, popular_urls
from .article import Article
from .exceptions import ArticleBinaryDataException, ArticleException
from .languages import valid_languages
from .source import Source
from .version import __version__

# Set default logging handler to avoid "No handler found" warnings.
logging.getLogger(__name__).addHandler(NullHandler())


def __getattr__(name: str):
    """Lazily load optional async functionality."""
    _ASYNC_EXPORTS = {
        "async_article": ("async_func.api", "async_article"),
        "async_build": ("async_func.api", "async_build"),
        "AsyncArticle": ("async_func.article", "AsyncArticle"),
        "AsyncSource": ("async_func.source", "AsyncSource"),
    }
    if name not in _ASYNC_EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    module_name, attribute_name = _ASYNC_EXPORTS[name]

    module = import_module(f".{module_name}", package=__name__)
    value = getattr(module, attribute_name)

    # Cache the resolved attribute to avoid repeated imports.
    globals()[name] = value

    return value


def article(url: str, language: str | None = None, **kwargs) -> Article:
    """Shortcut function to fetch and parse a newspaper article from a URL.

    Args:
        url (str): The URL of the article to download and parse.
        language (str): The language of the article to download and parse.
        input_html (str): The HTML of the article to parse. This
            is used for pre-downloaded articles. If this is set,
            then there will be no download requests made.
        kwargs: Any other keyword arguments to pass to the Article constructor.

    Returns:
        Article: The article downloaded and parsed.

    Raises:
        ArticleException: If the article could not be downloaded or parsed.
    """
    if "input_html" in kwargs:
        input_html = kwargs["input_html"]
        del kwargs["input_html"]
    else:
        input_html = None
    a = Article(url, language=language, **kwargs)
    a.download(input_html=input_html)
    a.parse()
    return a


if TYPE_CHECKING:
    from .async_func.api import async_article, async_build
    from .async_func.article import AsyncArticle
    from .async_func.source import AsyncSource

__all__ = [
    "build",
    "build_article",
    "article",
    "async_article",
    "async_build",
    "fulltext",
    "hot",
    "languages",
    "valid_languages",
    "popular_urls",
    "Config",
    "Article",
    "AsyncArticle",
    "AsyncSource",
    "ArticleException",
    "ArticleBinaryDataException",
    "Source",
    "__version__",
]
