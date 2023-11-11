# -*- coding: utf-8 -*-
# Much of the code here was forked from https://github.com/codelucas/newspaper
# Copyright (c) Lucas Ou-Yang (codelucas)

"""
This class holds configuration objects, which can be thought of
as settings.py but dynamic and changing for whatever parent object
holds them. For example, pass in a config object to an Article
object, Source object, or even network methods, and it just works.
"""
import logging
from http.cookiejar import CookieJar as cj

from newspaper.utils import get_available_languages

from .parsers import Parser
from .text import (
    StopWords,
    StopWordsArabic,
    StopWordsChinese,
    StopWordsKorean,
    StopWordsHindi,
    StopWordsJapanese,
    StopWordsThai,
)
from .version import __version__

log = logging.getLogger(__name__)


class Configuration:
    """Modifies Article / Source properties.
    Attributes:
        MIN_WORD_COUNT (int): minimum number of word tokens in an article text
        MIN_SENT_COUNT (int): minimum number of sentences in an article text
        MAX_TITLE (int): :any:`Article.title` max number of chars. ``title``
            is truncated to this length
        MAX_TEXT (int): :any:`Article.text` max number of chars. ``text`` is
            truncated to this length
        MAX_KEYWORDS (int): maximum number of keywords inferred
            by :any:`Article.nlp()`
        MAX_AUTHORS (int): maximum number of authors returned
            in :any:`Article.authors`
        MAX_SUMMARY (int): max number of chars in :any:`Article.summary`,
            truncated to this length
        MAX_SUMMARY_SENT (int): maximum number of sentences
            in :any:`Article.summary`
        MAX_FILE_MEMO (int): max number of urls we cache for each news source
        top_image_settings (dict): settings for finding top
            image. You can set the following:
                * ``min_width``: minimum width of image (default 300) in
                    order to be considered top image
                * ``min_height``: minimum height of image (default 200) in
                    order to be considered top image
                * ``min_area``: minimum area of image (default 10000) in
                    order to be considered top image
                * ``max_retries``: maximum number of retries to download
                    the image (default 2)
        memoize_articles (bool): If True, it will cache and save
            articles run between runs. default True.
        fetch_images (bool): If False, it will not download images
            to verify if they obide by the settings in top_image_settings.
            default True.
        follow_meta_refresh (bool): if True, it will follow meta refresh
            redirect when downloading an article. default False.
        keep_article_html (bool): if True it will replace the
            :any:`Article.html` property with the html of the body.
        http_success_only (bool): if True, it will raise an ``ArticleException``
             if the html status_code is >= 400 (e.g. 404 page)
        stopwords_class (obj): unique stopword classes for oriental languages,
            don't toggle
        requests_params (dict): Any of the params for the
            `get call`_ from ``requests`` library
        number_threads (int): number of threads to use for multi-threaded downloads
        verbose (bool): if True, it will output debugging information

            **deprecated**: Use the standard python logging module instead
        thread_timeout_seconds (int): timeout for threads
        ignored_content_types_defaults (dict): dictionary of content-types
            and a default stub content.
            These content type will not be downloaded.
        use_cached_categories (bool): if set to False, the cached categories
            will be ignored and a the :any:`Source` will recompute the category
             list every time you build it.

    .. _get call:
        https://requests.readthedocs.io/en/latest/api/#requests.get
    """

    def __init__(self):
        """
        Modify any of these Article / Source properties
        TODO: Have a separate ArticleConfig and SourceConfig extend this!
        """
        self.MIN_WORD_COUNT = 300  # num of word tokens in text
        self.MIN_SENT_COUNT = 7  # num of sentence tokens
        self.MAX_TITLE = 200  # num of chars
        self.MAX_TEXT = 100000  # num of chars
        self.MAX_KEYWORDS = 35  # num of strings in list
        self.MAX_AUTHORS = 10  # num strings in list
        self.MAX_SUMMARY = 5000  # num of chars
        self.MAX_SUMMARY_SENT = 5  # num of sentences

        # max number of urls we cache for each news source
        self.MAX_FILE_MEMO = 20000

        self.top_image_settings = {
            "min_width": 300,
            "min_height": 200,
            "min_area": 10000,
            "max_retries": 2,
        }

        # Cache and save articles run after run
        self.memoize_articles = True

        # Set this to false if you don't care about getting images
        self.fetch_images = True

        # Follow meta refresh redirect when downloading
        self.follow_meta_refresh = False

        # Don't toggle this variable, done internally
        self._use_meta_language = True

        # You may keep the html of just the main article body
        self.keep_article_html = False

        # Fail for error responses (e.g. 404 page)
        self.http_success_only = True

        # English is the fallback
        self._language = "en"

        # Unique stopword classes for oriental languages, don't toggle
        self.stopwords_class = StopWords

        # Params for get call from `requests` lib
        self.requests_params = {
            "timeout": 7,
            "proxies": {},
            "headers": {
                "User-Agent": f"newspaper/{__version__}",
            },
            "cookies": cj(),
        }

        self.number_threads = 10

        self.verbose = False  # for debugging

        self.thread_timeout_seconds = 1
        self.ignored_content_types_defaults = {}
        # Set this to False if you want to recompute the categories
        # *every* time you build a `Source` object
        # TODO: Actually make this work
        # self.use_cached_categories = True

    @property
    def browser_user_agent(self):
        """str: The user agent string sent to web servers when downloading
        articles. If not set, it will default to the following: newspaper/x.x.x
        i.e. newspaper/0.9.1"""
        if "headers" not in self.requests_params:
            self.requests_params["headers"] = {}
        return self.requests_params["headers"].get("User-Agent")

    @browser_user_agent.setter
    def browser_user_agent(self, value):
        if "headers" not in self.requests_params:
            self.requests_params["headers"] = {}
        self.requests_params["headers"]["User-Agent"] = value

    @property
    def headers(self):
        """str: The headers sent to web servers when downloading articles.
        It will set the headers for the `get call`_ from ``requests`` library.
        **Note**: If you set the :any:`browser_user_agent` property, it will
        override the ``User-Agent`` header."""
        return self.requests_params.get("headers")

    @headers.setter
    def headers(self, value):
        self.requests_params["headers"] = value

    @property
    def request_timeout(self):
        """Optional[int,Tuple[int,int]]: The timeout for the `get call`_
        from ``requests`` library. If not set, it will default to 7 seconds."""
        return self.requests_params.get("timeout")

    @request_timeout.setter
    def request_timeout(self, value):
        self.requests_params["timeout"] = value

    @property
    def proxies(self):
        """Optional[dict]: The proxies for the `get call`_ from ``requests``
        library. If not set, it will default to no proxies."""
        return self.requests_params.get("proxies")

    @proxies.setter
    def proxies(self, value):
        self.requests_params["proxies"] = value

    @property
    def language(self):
        """str: the iso-639-1 two letter code of the language.
        If not set, :any:`Article` will try to use the meta information of the webite
        to get the language. english is the fallback"""

        return self._language

    @language.setter
    def language(self, value: str):
        if not value or len(value) != 2:
            raise ValueError(
                "Your input language must be a 2 char language code,                "
                " for example: english-->en \n and german-->de"
            )
        if value not in list(get_available_languages()):
            raise ValueError(
                f"We do not currently support input language {value} yet"
                "supported languages are: {get_available_languages()}"
            )

        # If explicitly set language, don't use meta
        self._use_meta_language = False

        # Set oriental language stopword class
        self._language = value
        self.stopwords_class = self.get_stopwords_class(value)

    @property
    def use_meta_language(self):
        return self._use_meta_language

    @staticmethod
    def get_stopwords_class(language: str):
        """Get the stopwords class for the given language.
        Arguments:
            language (str): The language for which it will return the StopWords object.
        Returns:
            class(StopWords): The stopwords class for the given language.
        """
        if language == "ko":
            return StopWordsKorean
        elif language == "hi":
            return StopWordsHindi
        elif language == "zh":
            return StopWordsChinese
        # Persian and Arabic Share an alphabet
        # There is a persian parser https://github.com/sobhe/hazm,
        # but nltk is likely sufficient
        elif language == "ar" or language == "fa":
            return StopWordsArabic
        elif language == "ja":
            return StopWordsJapanese
        elif language == "th":
            return StopWordsThai
        return StopWords

    @staticmethod
    def get_parser():
        return Parser


class ArticleConfiguration(Configuration):
    pass


class SourceConfiguration(Configuration):
    pass
