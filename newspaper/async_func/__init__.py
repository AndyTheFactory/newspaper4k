"""Async package for newspaper4k.

This package collects all async-related modules under a single namespace.
"""

from .api import async_article, async_build
from .article import AsyncArticle
from .network import async_batch_request, async_do_request, async_get_html, async_get_html_status
from .source import AsyncSource

__all__ = [
    "async_article",
    "async_build",
    "AsyncArticle",
    "AsyncSource",
    "async_batch_request",
    "async_do_request",
    "async_get_html",
    "async_get_html_status",
]
