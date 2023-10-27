# -*- coding: utf-8 -*-

# Copyright (c) [2023] [Andrei Paraschiv]
#
# This file is part of [Newspaper4k].
#   https://github.com/AndyTheFactory/newspaper4k
#
# [Newspaper4k] includes code from the original project,
# [Newspaper3k], which is licensed under [MIT].
#
# I would like to express gratitude to the creator of [Newspaper3k],
# Lucas Ou-Yang (codelucas) for their valuable work.
# You can find the original project here: https://github.com/codelucas/newspaper


from .api import (
    build,
    build_article,
    fulltext,
    hot,
    languages,
    popular_urls,
    Configuration as Config,
)
from .article import Article, ArticleException
from .mthreading import NewsPool
from .source import Source
from .version import __version__
import logging
from logging import NullHandler

news_pool = NewsPool()


# Set default logging handler to avoid "No handler found" warnings.
logging.getLogger(__name__).addHandler(NullHandler())

__all__ = [
    "build",
    "build_article",
    "fulltext",
    "hot",
    "languages",
    "popular_urls",
    "Config",
    "Article",
    "ArticleException",
    "Source",
    "__version__",
    "news_pool",
]
