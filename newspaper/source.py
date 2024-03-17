# -*- coding: utf-8 -*-
# Much of the code here was forked from https://github.com/codelucas/newspaper
# Copyright (c) Lucas Ou-Yang (codelucas)

"""
Source objects abstract online news websites & domains. One Source object
can contain multiple Articles. If you want to pull articles from a single
url use the Article object.
Source provdides basic crawling + parsing logic for a news source homepage.
"""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
import logging
import re
from typing import List, Optional
from urllib.parse import urljoin, urlsplit, urlunsplit
import lxml

from tldextract import tldextract

import newspaper.parsers as parsers
from . import network
from . import urls
from . import utils
from .article import Article
from .configuration import Configuration
from .extractors import ContentExtractor
from .settings import NUM_THREADS_PER_SOURCE_WARN_LIMIT

log = logging.getLogger(__name__)


@dataclass
class Category:
    """A category object is a representation of a category of news
    on a news source's homepage. For example, on cnn.com, the category
    "world" would be a category object.

    Attributes:
        url(str): The url of the category's homepage. e.g. https://www.cnn.com/world
        html(str): The html of the category's homepage as downloaded by requests.
        doc(lxml.html.HtmlElement): The parsed lxml root of the category's homepage.
    """

    url: str
    html: Optional[str] = None
    doc: Optional[lxml.html.Element] = None

    def __getstate__(self):
        """Return state values to be pickled."""
        state = self.__dict__.copy()
        # Don't pickle the Lxml root

        if state.get("doc"):
            state["_doc_html"] = parsers.node_to_string(state["doc"])
            state.pop("doc", None)

        return state

    def __setstate__(self, state):
        """Restore state from the unpickled state values."""
        if state.get("_doc_html"):
            state["doc"] = parsers.fromstring(state["_doc_html"])
            state.pop("_doc_html", None)

        self.__dict__.update(state)


@dataclass
class Feed:
    """A feed object is a representation of an RSS feed on a news source's
    homepage. For example, on cnn.com, the feed
    "http://rss.cnn.com/rss/edition_world.rss" would represent a feed object.
    Attributes:
        url(str): The url of the feed's homepage. e.g. http://rss.cnn.com/rss/edition_world.rss
        rss(str): The rss of the feed's content (xml) as downloaded by requests.
    """

    url: str
    rss: Optional[str] = None
    # TODO self.dom = None, speed up Feedparser


class Source:
    """Sources are abstractions of online news websites such as huffpost or cnn.
    The object will create a list of article urls that belong to the source and
    the list of categories of news (world, politics, etc.) that the source has.
    These categories are inferred from the source's homepage structure.

    Attributes:
        url(str): The url of the source's homepage. e.g. https://www.cnn.com
        config(:any:`Configuration`): The configuration object for this source.
        domain(str): The domain of the source's homepage. e.g. cnn.com
        scheme(str): The scheme of the source's homepage. e.g. https
        categories(list): A list of :any:`Category` objects that belong to the source.
        feeds(list): A list of :any:`Feed` objects that belong to the source containing
            information about the source's RSS feeds.
        articles(list): A list of :any:`Article` objects that belong to the source.
        brand(str): The domain name root of the source. e.g. cnn
        description(str): The description of the source as found in the
            source's meta tags
        doc(lxml.html.HtmlElement): The parsed lxml root of the source's homepage.
        html(str): The html of the source's homepage as downloaded by requests.
        favicon(str): The url of the source's favicon.
        logo_url(str): The url of the source's logo.
    """

    def __init__(
        self,
        url: str,
        read_more_link: str = "",
        config: Optional[Configuration] = None,
        **kwargs,
    ):
        """The config object for this source will be passed into all of this
        source's children articles unless specified otherwise or re-set.

        Arguments:
            url(str): The url of the source's homepage. e.g. https://www.cnn.com
            read_more_link (str, optional): A xpath selector for the link to the
                full article. make sure that the selector works for all casese,
                not only for one specific article. If needed, you can use
                several xpath selectors separated by `|`. Defaults to "".
            config(:any:`Configuration`, optional): The configuration object
                for this source. Defaults to None.

        Keyword Args:
            **kwargs: Any Configuration class propriety can be overwritten
                    through init keyword  params.
                    Additionally, you can specify any of the following
                    requests parameters:
                    headers, cookies, auth, timeout, allow_redirects,
                    proxies, verify, cert

        """
        if (url is None) or ("://" not in url) or (url[:4] != "http"):
            raise ValueError("Input url is bad!")

        self.config = config or Configuration()
        self.config.update(**kwargs)

        self.extractor = ContentExtractor(self.config)

        self.url = url
        self.url = urls.prepare_url(url)

        self.domain = urls.get_domain(self.url)
        self.scheme = urls.get_scheme(self.url)

        self.categories: List[Category] = []
        self.feeds: List[Feed] = []
        self.articles: List[Article] = []

        self.html = ""
        self.doc = None

        self.logo_url = ""
        self.favicon = ""
        self.brand = tldextract.extract(self.url).domain
        self.description = ""
        self.read_more_link = read_more_link

        self.is_parsed = False
        self.is_downloaded = False

    def build(self, input_html=None, only_homepage=False, only_in_path=False):
        """Encapsulates download and basic parsing with lxml.
        Executes download, parse, gets categories and article links,
        parses rss feeds and finally creates a list of :any:`Article`
        objects. Articles are not yet downloaded.

        Args:
            input_html (str, optional): The cached html of the source to parse.
                Leave None to download the html. Defaults to None.
            only_homepage (bool, optional): If true, the source object will only
                parse the homepage of the source. Defaults to False.
            only_in_path (bool, optional): If true, the source object will only
                parse the articles that are in the same path as the source's
                homepage. You can scrape a specific category this way.
                Defaults to False.
        """
        if input_html:
            self.html = input_html
        else:
            self.download()
        self.parse()

        if only_homepage:
            # The only category we will parse is Homepage
            self.categories = [Category(url=self.url, html=self.html, doc=self.doc)]
        else:
            self.set_categories()
            self.download_categories()  # mthread
        self.parse_categories()

        if not only_homepage:
            self.set_feeds()
            self.download_feeds()  # mthread
            # self.parse_feeds()

        self.generate_articles(only_in_path=only_in_path)

    @utils.cache_disk(seconds=86400)
    def _get_category_urls(self, domain):  # pylint: disable=unused-argument
        """The domain param is **necessary**, since disk caching usese this
        parameter to save the cached categories. Even if it seems unused
        in this method, removing it would render disk_cache useless.
        By default we are caching categories for 1 day.

        You can enable/disable disk_cache in run-time by setting
            utils.cache_disk.enabled = True/False
        """
        return self.extractor.get_category_urls(self.url, self.doc)

    def set_categories(self):
        """
        Sets the categories (List of Category object) for the newspaper source.

        This method result is cached if the `disable_category_cache` is False in
        configuration.
        It retrieves the category URLs for the domain and creates a list
        of Category objects.
        """
        utils.cache_disk.enabled = not self.config.disable_category_cache
        url_list = self._get_category_urls(self.domain)
        self.categories = [Category(url=url) for url in set(url_list)]

    def set_feeds(self):
        """Don't need to cache getting feed urls, it's almost
        instant with xpath
        """
        common_feed_sufixes = ["/feed", "/feeds", "/rss"]
        common_feed_urls = [urljoin(self.url, url) for url in common_feed_sufixes]

        split = urlsplit(self.url)
        if split.netloc in ("medium.com", "www.medium.com"):
            # should handle URL to user or user's post
            if split.path.startswith("/@"):
                new_path = "/feed/" + split.path.split("/")[1]
                new_parts = split.scheme, split.netloc, new_path, "", ""
                common_feed_urls.append(urlunsplit(new_parts))

        for cat in self.categories:
            path_chunks = [x for x in cat.url.split("/") if len(x) > 0]
            if len(path_chunks) and "." in path_chunks[-1]:
                # skip urls with file extensions (.php, .html)
                continue
            for suffix in common_feed_sufixes:
                common_feed_urls.append(cat.url + suffix)

        responses = network.multithread_request(common_feed_urls, self.config)

        common_feed_urls_as_categories = []
        for response in responses:
            if not response or response.status_code > 299:
                continue
            feed = Category(url=response.url, html=response.text)
            feed.doc = parsers.fromstring(feed.html)
            if feed.doc:
                common_feed_urls_as_categories.append(feed)

        categories_and_common_feed_urls = (
            self.categories + common_feed_urls_as_categories
        )
        # Add the main webpage of the Source
        categories_and_common_feed_urls.append(
            Category(
                url=self.url,
                html=self.html,
                doc=self.doc,
            )
        )
        url_list = self.extractor.get_feed_urls(
            self.url, categories_and_common_feed_urls
        )
        self.feeds = [Feed(url=url) for url in url_list]

    def set_description(self):
        """Sets a blurb for this source, for now we just query the
        desc html attribute
        """
        metadata = self.extractor.get_metadata(self.url, self.doc)
        self.description = metadata["description"]

    def download(self):
        """Downloads html of source, i.e. the news site homppage"""
        self.html = network.get_html(self.url, self.config)

    def download_categories(self):
        """Download all category html, can use mthreading"""
        category_urls = self.category_urls()
        responses = network.multithread_request(category_urls, self.config)

        for response, category in zip(responses, self.categories):
            if response and response.status_code < 400:
                category.html = network.get_html(category.url, response=response)

        self.categories = [c for c in self.categories if c.html]

        return self.categories

    def download_feeds(self):
        """Download all feed html, can use mthreading"""
        feed_urls = self.feed_urls()
        responses = network.multithread_request(feed_urls, self.config)

        for response, feed in zip(responses, self.feeds):
            if response and response.status_code < 400:
                feed.rss = network.get_html(feed.url, response=response)
        self.feeds = [f for f in self.feeds if f.rss]
        return self.feeds

    def parse(self):
        """Sets the lxml root, also sets lxml roots of all
        children links, also sets description
        """
        self.doc = parsers.fromstring(self.html)
        if self.doc is None:
            log.warning("Source %s parse error.", self.url)
            return
        self.set_description()

    def parse_categories(self):
        """Parse out the lxml root in each category"""
        log.debug("We are extracting from %d categories", self.categories)
        for category in self.categories:
            doc = parsers.fromstring(category.html)
            category.doc = doc

        self.categories = [c for c in self.categories if c.doc is not None]

    def _map_title_to_feed(self, feed):
        doc = parsers.fromstring(feed.rss)
        if doc is None:
            # http://stackoverflow.com/a/24893800
            return None

        elements = parsers.get_tags(doc, tag="title")
        feed.title = next(
            (element.text for element in elements if element.text), self.brand
        )
        return feed

    def parse_feeds(self):
        """Add titles to feeds"""
        log.debug("We are parsing %d feeds", self.feeds)
        self.feeds = [self._map_title_to_feed(f) for f in self.feeds]

    def feeds_to_articles(self) -> List[Article]:
        """Returns a list of :any:`Article` objects based on
        articles found in the Source's RSS feeds"""
        articles = []

        def get_urls(feed):
            feed = re.sub("<[^<]+?>", " ", str(feed))
            results = re.findall(
                r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|"
                "(?:%[0-9a-fA-F][0-9a-fA-F]))+",
                feed,
            )
            results = [x.strip() for x in results]
            return results

        for feed in self.feeds:
            url_list = get_urls(feed.rss)

            cur_articles = [
                Article(
                    url=url,
                    source_url=feed.url,
                    read_more_link=self.read_more_link,
                    config=self.config,
                )
                for url in url_list
                if urls.valid_url(url)
            ]
            log.debug(
                "For Category %s got %d articles from %d candidates",
                feed.url,
                len(cur_articles),
                len(url_list),
            )

            if self.config.memorize_articles:
                log.debug("Removing already downloaded articles")
                cur_articles = utils.memorize_articles(self, cur_articles)
                log.debug("Remaining articles: %d", len(cur_articles))

            articles.extend(cur_articles)

        return articles

    def categories_to_articles(self) -> List[Article]:
        """Takes the categories, splays them into a big list of urls and churns
        the articles out of each url with the url_to_article method
        """
        articles = []

        def prepare_url(url):
            if urls.is_abs_url(url):
                return url
            else:
                return urls.urljoin_if_valid(self.url, url)

        def get_urls(doc):
            if doc is None:
                return []
            return [
                (prepare_url(a.get("href")), a.text)
                for a in parsers.get_tags(doc, tag="a")
                if a.get("href")
            ]

        for category in self.categories:
            url_title_tups = get_urls(category.doc)

            cur_articles = [
                Article(
                    url=url,
                    source_url=category.url,
                    read_more_link=self.read_more_link,
                    title=title,
                    config=self.config,
                )
                for url, title in url_title_tups
                if urls.valid_url(url)
            ]
            log.debug(
                "For Category %s got %d articles from %d candidates",
                category.url,
                len(cur_articles),
                len(url_title_tups),
            )

            if self.config.memorize_articles:
                log.debug("Removing already downloaded articles")
                cur_articles = utils.memorize_articles(self, cur_articles)
                log.debug("Remaining articles: %d", len(cur_articles))

            articles.extend(cur_articles)

        return articles

    def _generate_articles(self):
        """Returns a list of all articles, from both categories and feeds"""
        category_articles = self.categories_to_articles()
        feed_articles = self.feeds_to_articles()

        articles = feed_articles + category_articles
        uniq = {article.url: article for article in articles}
        return list(uniq.values())

    def generate_articles(self, limit=5000, only_in_path=False):
        """Creates the :any:`Source.articles` List of :any:`Article` objects.
        It gets the Urls from all detected categories and RSS feeds, checks
        them for plausibility based on their URL (using some heuristics defined
        in the ``urls.valid_url`` function). These can be further
        downloaded using :any:`Source.download_articles()`

        Args:
            limit (int, optional): The maximum number of articles to generate.
                Defaults to 5000.
            only_in_path (bool, optional): If true, the source object will only
                parse the articles that are in the same path as the source's
                homepage. You can scrape a specific category this way.
                Defaults to False.
        """
        articles = self._generate_articles()
        if only_in_path:

            def get_path(url):
                path = urls.get_path(url, allow_fragments=False)
                path_chunks = [x for x in path.split("/") if len(x) > 0]
                if path_chunks and (
                    path_chunks[-1].endswith(".html")
                    or path_chunks[-1].endswith(".php")
                ):
                    path_chunks.pop()
                return "/".join(path_chunks)

            current_domain = urls.get_domain(self.url)
            current_path = get_path(self.url) + "/"
            articles = [
                article
                for article in articles
                if current_domain == urls.get_domain(article.url)
                and get_path(article.url).startswith(current_path)
            ]
        self.articles = articles[:limit]
        log.debug("%d articles generated and cutoff at %d", len(articles), limit)

    def download_articles(self) -> List[Article]:
        """Starts the ``download()`` for all :any:`Article` objects
        in the :any:`Source.articles` property. It can run single threaded or
        multi-threaded.
        Returns:
            List[:any:`Article`]: A list of downloaded articles.
        """
        url_list = self.article_urls()
        failed_articles = []

        threads = self.config.number_threads

        if threads > NUM_THREADS_PER_SOURCE_WARN_LIMIT:
            log.warning(
                "Using %s+ threads on a single source may result in rate limiting!",
                NUM_THREADS_PER_SOURCE_WARN_LIMIT,
            )
        responses = network.multithread_request(url_list, self.config)
        # Note that the responses are returned in original order
        with ThreadPoolExecutor(max_workers=threads) as tpe:
            futures = []
            for response, article in zip(responses, self.articles):
                if response and response.status_code < 400:
                    html = network.get_html(article.url, response=response)
                else:
                    html = ""
                    failed_articles.append(article.url)

                futures.append(tpe.submit(article.download, input_html=html))

            self.articles = [future.result() for future in futures]

        self.is_downloaded = True

        if len(failed_articles) > 0:
            log.warning(
                "There were %d articles that failed to download: %s",
                len(failed_articles),
                ", ".join(failed_articles),
            )
        return self.articles

    def parse_articles(self):
        """Parse all articles, delete if too small"""
        for article in self.articles:
            article.parse()

        # Remove articles that are too small or do not have meaningful content
        self.articles = [a for a in self.articles if a.is_valid_body()]
        self.is_parsed = True

    def size(self):
        """Returns the number of articles linked to this news source"""
        if self.articles is None:
            return 0
        return len(self.articles)

    def clean_memo_cache(self):
        """Clears the memoization cache for this specific news domain"""
        utils.clear_memo_cache(self)

    def feed_urls(self):
        """Returns a list of feed urls"""
        return [feed.url for feed in self.feeds]

    def category_urls(self):
        """Returns a list of category urls"""
        return [category.url for category in self.categories]

    def article_urls(self):
        """Returns a list of article urls"""
        return [article.url for article in self.articles]

    def print_summary(self):
        """Prints out a summary of the data in our source instance"""
        print(str(self))

    def __getstate__(self):
        """Return state values to be pickled."""
        state = self.__dict__.copy()
        # Don't pickle the extractor

        if state.get("doc"):
            state["_doc_html"] = parsers.node_to_string(state["doc"])
            state.pop("doc", None)

        state.pop("extractor", None)

        return state

    def __setstate__(self, state):
        """Restore state from the unpickled state values."""
        if state.get("_doc_html"):
            state["doc"] = parsers.fromstring(state["_doc_html"])
            state.pop("_doc_html", None)

        self.__dict__.update(state)

        self.extractor = ContentExtractor(self.config)

    def __str__(self):
        res = (
            f"Source (\n\t\turl={self.url} \n"
            f"t\tbrand={self.brand} \n"
            f"t\tdomain={self.domain} \n"
            f"t\tlen(articles)={len(self.articles)} \n"
            f"t\tdescription={self.description[:50]}\n)"
        )

        res += "\n 10 sample Articles: \n"

        for a in self.articles[:10]:
            res += f"{str(a)} \n"
            res += "=" * 40 + "\n"

        res += "category_urls: \n\n" + str(self.category_urls())
        res += "\nfeed_urls:\n\n" + str(self.feed_urls())

        return res
