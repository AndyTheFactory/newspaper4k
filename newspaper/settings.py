# -*- coding: utf-8 -*-
# Much of the code here was forked from https://github.com/codelucas/newspaper
# Copyright (c) Lucas Ou-Yang (codelucas)

"""
Unlike configuration.py, this file is meant for static, entire project
encompassing settings, like memoization and caching file directories.
"""
import logging
from pathlib import Path
import tempfile

from .version import __version__

log = logging.getLogger(__name__)

PARENT_DIRECTORY = Path(__file__).resolve().parent
POPULAR_URLS = PARENT_DIRECTORY / "resources/misc/popular_sources.txt"
USERAGENTS = PARENT_DIRECTORY / "resources/misc/useragents.txt"
STOPWORDS_DIR = PARENT_DIRECTORY / "resources/text"

DATA_DIRECTORY = ".newspaper_scraper"

TOP_DIRECTORY = Path(tempfile.gettempdir()).resolve() / DATA_DIRECTORY

# Error log
LOGFILE = TOP_DIRECTORY / f"newspaper_errors_{__version__}.log"
MONITOR_LOGFILE = TOP_DIRECTORY / "newspaper_monitors_{__version__}.log"

# Memo directory (same for all concur crawlers)
MEMO_FILE = "memoized"
MEMO_DIR = TOP_DIRECTORY / MEMO_FILE

# category and feed cache
CF_CACHE_DIRECTORY = "feed_category_cache"
ANCHOR_DIRECTORY = TOP_DIRECTORY / CF_CACHE_DIRECTORY

TRENDING_URL = "http://www.google.com/trends/hottrends/atom/feed?pn=p1"

for path in (TOP_DIRECTORY, MEMO_DIR, ANCHOR_DIRECTORY):
    path.mkdir(parents=True, exist_ok=True)
