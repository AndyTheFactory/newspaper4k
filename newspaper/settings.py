# -*- coding: utf-8 -*-
# Much of the code here was forked from https://github.com/codelucas/newspaper
# Copyright (c) Lucas Ou-Yang (codelucas)

"""
Global package-wide settings and constants live here.
"""
import logging
from pathlib import Path
import tempfile

from .version import __version__

log = logging.getLogger(__name__)

NUM_THREADS_PER_SOURCE_WARN_LIMIT = 5

# Expected value for sentence length
MEAN_SENTENCE_LEN = 20.0
SUMMARIZE_KEYWORD_COUNT = 10

PARENT_DIRECTORY = Path(__file__).resolve().parent
POPULAR_URLS = PARENT_DIRECTORY / "resources/misc/popular_sources.txt"
USERAGENTS = PARENT_DIRECTORY / "resources/misc/useragents.txt"
STOPWORDS_DIR = PARENT_DIRECTORY / "resources/text"

DATA_DIRECTORY = ".newspaper_scraper"

TOP_DIRECTORY = Path(tempfile.gettempdir()).resolve() / DATA_DIRECTORY

# Fields used to construct the article json string.

article_json_fields = [
    "url",
    "read_more_link",
    "language",
    "title",
    "top_image",
    "meta_img",
    "images",
    "movies",
    "keywords",
    "meta_keywords",
    "tags",
    "authors",
    "publish_date",
    "summary",
    "meta_description",
    "meta_lang",
    "meta_favicon",
    "meta_site_name",
    "canonical_link",
    "text",
]

# Tags we allow to be left in the cleaned article body
CLEAN_ARTICLE_TAGS = [
    "a",
    "span",
    "p",
    "br",
    "strong",
    "b",
    "em",
    "i",
    "tt",
    "code",
    "pre",
    "blockquote",
    "img",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "ul",
    "ol",
    "li",
    "dl",
    "dt",
    "dd",
]
# Tags that get a newline appended to them during conversion to text
BLOCK_LEVEL_TAGS = [
    "address",
    "article",
    "aside",
    "blockquote",
    "canvas",
    "dd",
    "div",
    "dl",
    "dt",
    "fieldset",
    "figcaption",
    "figure",
    "footer",
    "form",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "header",
    "hr",
    "li",
    "main",
    "nav",
    "noscript",
    "ol",
    "p",
    "pre",
    "section",
    "table",
    "tfoot",
    "ul",
    "video",
]

# Tags that we remove from cleaned article HTML
ARTICLE_STRIP_TAGS = ["a", "b", "strong", "i", "br", "sup"]

# Known Advertisement Attributes and IDs
ADVERTISEMENT_ATTR_VALUES = r"inline-ads|promotion|sponsor|banner"

# Error log
LOGFILE = TOP_DIRECTORY / f"newspaper_errors_{__version__}.log"
MONITOR_LOGFILE = TOP_DIRECTORY / "newspaper_monitors_{__version__}.log"

# Memo directory (same for all concur crawlers)
MEMO_FILE = "memoized"
MEMO_DIR = TOP_DIRECTORY / MEMO_FILE

# category cache
CACHE_DIRECTORY = TOP_DIRECTORY / "category_cache"

TRENDING_URL = "http://www.google.com/trends/hottrends/atom/feed?pn=p1"

for path in (TOP_DIRECTORY, MEMO_DIR, CACHE_DIRECTORY):
    path.mkdir(parents=True, exist_ok=True)
