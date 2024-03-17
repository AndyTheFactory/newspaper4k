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

from warnings import warn

from newspaper.utils import get_available_languages

from .version import __version__

log = logging.getLogger(__name__)


class Configuration:
    """Modifies Article / Source properties.

    Attributes:
        min_word_count (int): minimum number of word tokens in an article text
        min_sent_count (int): minimum number of sentences in an article text
        max_title (int): :any:`Article.title` max number of chars. ``title``
            is truncated to this length
        max_text (int): :any:`Article.text` max number of chars. ``text`` is
            truncated to this length
        max_keywords (int): maximum number of keywords inferred
            by :any:`Article.nlp()`
        max_authors (int): maximum number of authors returned
            in :any:`Article.authors`
        max_summary (int): max number of chars in :any:`Article.summary`,
            truncated to this length
        max_summary_sent (int): maximum number of sentences
            in :any:`Article.summary`
        max_file_memo (int): max number of urls we cache for each news source
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
        memorize_articles (bool): If True, it will cache and save
            articles run between runs. The articles are *NOT* cached.
            It will save the parsed article urls between different
            :any:`Source.generate_articles()` runs. default True.
        disable_category_cache (bool): If True, it will not cache
            the :any:`Source` category urls. default False.
        fetch_images (bool): If False, it will not download images
            to verify if they obide by the settings in top_image_settings.
            Default True.
        follow_meta_refresh (bool): if True, it will follow meta refresh
            redirect when downloading an article. default False.
        clean_article_html (bool): if True it will clean 'unnecessary' tags
            from the article body html.
            Affected property is :any:`Article.article_html`. Default True.
        http_success_only (bool): if True, it will raise an :any:`ArticleException`
            if the html status_code is >= 400 (e.g. 404 page).
            Default True.
        requests_params (dict): Any of the params for the
            `get call`_ from ``requests`` library
        number_threads (int): number of threads to use for multi-threaded downloads
        verbose (bool): if True, it will output debugging information
            **deprecated**: Use the standard python logging module instead
        thread_timeout_seconds (int): timeout for threads
        allow_binary_content (bool): if True, it will allow binary content
            to be downloaded and stored in :any:`Article.html`. Allowing
            this for Source building can lead to longer processing times
            and could hang the process due to huge binary files (such as movies)
            default False.
        ignored_content_types_defaults (dict): dictionary of content-types
            and a default stub content. These content type will not be downloaded.

            **Note:** If :any:`allow_binary_content` is False,
            binary content will lead to :any:`ArticleBinaryDataException` for
            :any:`Article.download()` and will be skipped in
            :any:`Source.build()`. This will override the defaults
            in :any:`ignored_content_types_defaults` if these match binary files.
        use_cached_categories (bool): if set to False, the cached categories
            will be ignored and a the :any:`Source` will recompute the category
             list every time you build it.
        MIN_WORD_COUNT (int):
            .. deprecated:: 0.9.2
                use :any:`Configuration.min_word_count` instead
        MIN_SENT_COUNT (int):
            .. deprecated:: 0.9.2
                use :any:`Configuration.min_sent_count` instead
        MAX_TITLE (int):
            .. deprecated:: 0.9.2
                use :any:`Configuration.max_title` instead
        MAX_TEXT (int):
            .. deprecated:: 0.9.2
                use :any:`Configuration.max_text` instead
        MAX_KEYWORDS (int):
            .. deprecated:: 0.9.2
                use :any:`Configuration.max_keywords` instead
        MAX_AUTHORS (int):
            .. deprecated:: 0.9.2
                use :any:`Configuration.max_authors` instead
        MAX_SUMMARY (int):
            .. deprecated:: 0.9.2
                use :any:`Configuration.max_summary` instead
        MAX_SUMMARY_SENT (int):
            .. deprecated:: 0.9.2
                use :any:`Configuration.max_summary_sent` instead
        MAX_FILE_MEMO (int):
            .. deprecated:: 0.9.2
                use :any:`Configuration.max_file_memo` instead

    .. _get call:
        https://requests.readthedocs.io/en/latest/api/#requests.get
    """

    def __init__(self):
        """
        Modify any of these Article / Source properties
        """
        self.min_word_count = 300  # num of word tokens in text
        self.min_sent_count = 7  # num of sentence tokens
        self.max_title = 200  # num of chars
        self.max_text = 100000  # num of chars
        self.max_keywords = 35  # num of strings in list
        self.max_authors = 10  # num strings in list
        self.max_summary = 5000  # num of chars
        self.max_summary_sent = 5  # num of sentences

        # max number of urls we cache for each news source
        self.max_file_memo = 20000

        self.top_image_settings = {
            "min_width": 300,
            "min_height": 200,
            "min_area": 10000,
            "max_retries": 2,
        }

        # Cache and save articles run after run
        self.memorize_articles = True

        # If true, it will not cache the `Source` category urls
        self.disable_category_cache = False

        # Set this to false if you don't care about getting images
        self.fetch_images = True

        # Follow meta refresh redirect when downloading
        self.follow_meta_refresh = False

        # Don't toggle this variable, done internally
        self._use_meta_language = True

        # You may keep the html of just the main article body
        self.clean_article_html = True

        # Fail for error responses (e.g. 404 page)
        self.http_success_only = True

        # English is the fallback
        self._language = "en"

        # Params for get call from `requests` lib
        self.requests_params = {
            "timeout": 7,
            "proxies": {},
            "headers": {
                "User-Agent": f"newspaper/{__version__}",
            },
        }

        # Number of threads to use for mthreaded downloads
        self.number_threads = 10

        # Deprecated, use standard python logging module instead (debug level)
        self.verbose = False  # for debugging

        self.thread_timeout_seconds = 10

        self.allow_binary_content = False

        self.ignored_content_types_defaults = {}

    def update(self, **kwargs):
        """Update the configuration object with the given keyword arguments.

        Arguments:
            **kwargs: The keyword arguments to update.

        """
        for key, value in kwargs.items():
            setattr(self, key, value)

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
        if value is None:
            # Default Language set to "en", but allow auto-detection
            self._use_meta_language = True
            self._language = "en"
            return

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

    @property
    def use_meta_language(self):
        """Read-only property that indicates whether the meta language
        read from the website was used or the language was explicitly set.

        Returns:
            bool: True if the meta language was used, False if the language
            was explicitly set.
        """
        return self._use_meta_language

    @property
    def MIN_WORD_COUNT(self):
        warn(
            "`MIN_WORD_COUNT` is deprecated, use `min_word_count` instead",
            DeprecationWarning,
        )
        return self.min_word_count

    @MIN_WORD_COUNT.setter
    def MIN_WORD_COUNT(self, value):
        warn(
            "`MIN_WORD_COUNT` is deprecated, use `min_word_count` instead",
            DeprecationWarning,
        )
        self.min_word_count = value

    @property
    def MIN_SENT_COUNT(self):
        warn(
            "`MIN_SENT_COUNT` is deprecated, use `min_sent_count` instead",
            DeprecationWarning,
        )
        return self.min_sent_count

    @MIN_SENT_COUNT.setter
    def MIN_SENT_COUNT(self, value):
        warn(
            "`MIN_SENT_COUNT` is deprecated, use `min_sent_count` instead",
            DeprecationWarning,
        )
        self.min_sent_count = value

    @property
    def MAX_TITLE(self):
        warn("`MAX_TITLE` is deprecated, use `max_title` instead", DeprecationWarning)
        return self.max_title

    @MAX_TITLE.setter
    def MAX_TITLE(self, value):
        warn("`MAX_TITLE` is deprecated, use `max_title` instead", DeprecationWarning)
        self.max_title = value

    @property
    def MAX_TEXT(self):
        warn("`MAX_TEXT` is deprecated, use `max_text` instead", DeprecationWarning)
        return self.max_text

    @MAX_TEXT.setter
    def MAX_TEXT(self, value):
        warn("`MAX_TEXT` is deprecated, use `max_text` instead", DeprecationWarning)
        self.max_text = value

    @property
    def MAX_KEYWORDS(self):
        warn(
            "`MAX_KEYWORDS` is deprecated, use `max_keywords` instead",
            DeprecationWarning,
        )
        return self.max_keywords

    @MAX_KEYWORDS.setter
    def MAX_KEYWORDS(self, value):
        warn(
            "`MAX_KEYWORDS` is deprecated, use `max_keywords` instead",
            DeprecationWarning,
        )
        self.max_keywords = value

    @property
    def MAX_AUTHORS(self):
        warn(
            "`MAX_AUTHORS` is deprecated, use `max_authors` instead", DeprecationWarning
        )
        return self.max_authors

    @MAX_AUTHORS.setter
    def MAX_AUTHORS(self, value):
        warn(
            "`MAX_AUTHORS` is deprecated, use `max_authors` instead", DeprecationWarning
        )
        self.max_authors = value

    @property
    def MAX_SUMMARY(self):
        warn(
            "`MAX_SUMMARY` is deprecated, use `max_summary` instead", DeprecationWarning
        )
        return self.max_summary

    @MAX_SUMMARY.setter
    def MAX_SUMMARY(self, value):
        warn(
            "`MAX_SUMMARY` is deprecated, use `max_summary` instead", DeprecationWarning
        )
        self.max_summary = value

    @property
    def MAX_SUMMARY_SENT(self):
        warn(
            "`MAX_SUMMARY_SENT` is deprecated, use `max_summary_sent` instead",
            DeprecationWarning,
        )
        return self.max_summary_sent

    @MAX_SUMMARY_SENT.setter
    def MAX_SUMMARY_SENT(self, value):
        warn(
            "`MAX_SUMMARY_SENT` is deprecated, use `max_summary_sent` instead",
            DeprecationWarning,
        )
        self.max_summary_sent = value

    @property
    def MAX_FILE_MEMO(self):
        warn(
            "`MAX_FILE_MEMO` is deprecated, use `max_file_memo` instead",
            DeprecationWarning,
        )
        return self.max_file_memo

    @MAX_FILE_MEMO.setter
    def MAX_FILE_MEMO(self, value):
        warn(
            "`MAX_FILE_MEMO` is deprecated, use `max_file_memo` instead",
            DeprecationWarning,
        )
        self.max_file_memo = value

    def __getstate__(self):
        """Return state values to be pickled."""
        state = self.__dict__.copy()
        return state

    def __setstate__(self, state):
        """Restore state from the unpickled state values."""
        self.__dict__.update(state)
