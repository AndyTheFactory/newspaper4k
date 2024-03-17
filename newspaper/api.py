# -*- coding: utf-8 -*-
# Much of the code here was forked from https://github.com/codelucas/newspaper
# Copyright (c) Lucas Ou-Yang (codelucas)
"""Module providing a simple API for the newspaper library, wrapping several
classes and functions into simple calls.
"""

from typing import List
import feedparser
import newspaper.parsers as parsers
from newspaper.article import Article
from newspaper.configuration import Configuration
from newspaper.settings import POPULAR_URLS, TRENDING_URL
from newspaper.source import Source
from newspaper.utils import print_available_languages


def build(
    url="",
    dry=False,
    only_homepage=False,
    only_in_path=False,
    input_html=None,
    config=None,
    **kwargs
) -> Source:
    """Returns a constructed :any:`Source` object without
    downloading or parsing the articles

    Args:
        url (str): The url of the source (news website) to build. For example,
            `https://www.cnn.com`.
        dry (bool): If true, the source object will be constructed but not
            downloaded or parsed.
        only_homepage (bool): If true, the source object will only parse
            the homepage of the source.
        only_in_path (bool): If true, the source object will only
            parse the articles that are in the same path as the source's
            homepage. You can scrape a specific category this way.
            Defaults to False.
        input_html (str): The HTML of the source to parse. Use this to pass cached
            HTML to the source object.
        config (Configuration): A configuration object to use for the source.
        kwargs: Any other keyword arguments to pass to the Source constructor.
            If you omit the config object, you can add any configuration
            options here.

    Returns:
        Source: The constructed :any:`Source` object.

    """
    config = config or Configuration()
    config.update(**kwargs)
    url = url or ""
    s = Source(url, config=config)
    if not dry:
        s.build(
            only_homepage=only_homepage,
            only_in_path=only_in_path,
            input_html=input_html,
        )
    return s


def build_article(url="", config=None, **kwargs) -> Article:
    """Returns a constructed article object without downloading
    or parsing
    .. deprecated:: 0.9.2
                use :any:`Article` or :any:`newspaper.article` instead
    """
    config = config or Configuration()
    config.update(**kwargs)
    url = url or ""
    a = Article(url, config=config)
    return a


def languages():
    """Prints a list of the supported languages"""
    print_available_languages()


def popular_urls() -> List[str]:
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


def fulltext(html: str, language: str = "en") -> str:
    """Takes article HTML string input and outputs the extracted
    article text. No Title, Author, Date parsing is done.
    No http requests are performed.
    """
    from .cleaners import DocumentCleaner
    from .configuration import Configuration
    from .extractors import ContentExtractor
    from .outputformatters import OutputFormatter

    config = Configuration()
    config.language = language
    config.fetch_images = False

    extractor = ContentExtractor(config)
    document_cleaner = DocumentCleaner(config)
    output_formatter = OutputFormatter(config)

    doc = parsers.fromstring(html)
    doc = document_cleaner.clean(doc)

    extractor.calculate_best_node(doc)
    top_node = extractor.top_node_complemented
    text, _ = output_formatter.get_formatted(top_node)
    return text
