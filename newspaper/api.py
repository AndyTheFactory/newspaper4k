# -*- coding: utf-8 -*-
# Much of the code here was forked from https://github.com/codelucas/newspaper
# Copyright (c) Lucas Ou-Yang (codelucas)


import feedparser

from .article import Article
from .configuration import Configuration
from .settings import POPULAR_URLS, TRENDING_URL
from .source import Source
from .utils import extend_config, print_available_languages


def build(url="", dry=False, config=None, **kwargs) -> Source:
    """Returns a constructed source object without
    downloading or parsing the articles
    """
    config = config or Configuration()
    config = extend_config(config, kwargs)
    url = url or ""
    s = Source(url, config=config)
    if not dry:
        s.build()
    return s


def build_article(url="", config=None, **kwargs) -> Article:
    """Returns a constructed article object without downloading
    or parsing
    """
    config = config or Configuration()
    config = extend_config(config, kwargs)
    url = url or ""
    a = Article(url, config=config)
    return a


def languages():
    """Returns a list of the supported languages"""
    print_available_languages()


def popular_urls():
    """Returns a list of pre-extracted popular source urls"""
    with open(POPULAR_URLS, encoding="utf-8") as f:
        urls = ["http://" + u.strip() for u in f.readlines()]
        return urls


def hot():
    """Returns a list of hit terms via google trends"""
    try:
        listing = feedparser.parse(TRENDING_URL)["entries"]
        trends = [item["title"] for item in listing]
        return trends
    except Exception as e:
        print("ERR hot terms failed!", str(e))
        return None


def fulltext(html, language="en"):
    """Takes article HTML string input and outputs the fulltext
    Input string is decoded via UnicodeDammit if needed
    """
    from .cleaners import DocumentCleaner
    from .configuration import Configuration
    from .extractors import ContentExtractor
    from .outputformatters import OutputFormatter

    config = Configuration()
    config.language = language

    extractor = ContentExtractor(config)
    document_cleaner = DocumentCleaner(config)
    output_formatter = OutputFormatter(config)

    doc = config.get_parser().fromstring(html)
    doc = document_cleaner.clean(doc)

    extractor.calculate_best_node(doc)
    top_node = extractor.top_node_complemented
    text, _ = output_formatter.get_formatted(top_node)
    return text
