# -*- coding: utf-8 -*-
# Much of the code here was forked from https://github.com/codelucas/newspaper
# Copyright (c) Lucas Ou-Yang (codelucas)

"""
Source objects abstract online news source websites & domains.
www.cnn.com would be its own source.
"""

from dataclasses import dataclass
import logging
import re
from typing import Optional
from urllib.parse import urljoin, urlsplit, urlunsplit
import lxml

from tldextract import tldextract

from . import network
from . import urls
from . import utils
from .article import Article
from .configuration import Configuration
import newspaper.parsers as parsers
from .extractors import ContentExtractor
from .settings import ANCHOR_DIRECTORY, NUM_THREADS_PER_SOURCE_WARN_LIMIT

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
        read_more_link: str = None,
        config: Configuration = None,
        **kwargs
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
        self.config = utils.extend_config(self.config, kwargs)

        self.extractor = ContentExtractor(self.config)

        self.url = url
        self.url = urls.prepare_url(url)

        self.domain = urls.get_domain(self.url)
        self.scheme = urls.get_scheme(self.url)

        self.categories = []
        self.feeds = []
        self.articles = []

        self.html = ""
        self.doc = None

        self.logo_url = ""
        self.favicon = ""
        self.brand = tldextract.extract(self.url).domain
        self.description = ""
        self.read_more_link = read_more_link

        self.is_parsed = False
        self.is_downloaded = False

    def build(self):
        """Encapsulates download and basic parsing with lxml. May be a
        good idea to split this into download() and parse() methods.
        """
        self.download()
        self.parse()

        self.set_categories()
        self.download_categories()  # mthread
        self.parse_categories()

        self.set_feeds()
        self.download_feeds()  # mthread
        # self.parse_feeds()

        self.generate_articles()

    def purge_articles(self, reason, articles):
        """Delete rejected articles, if there is an articles param,
        purge from there, otherwise purge from source instance.

        Reference this StackOverflow post for some of the wonky
        syntax below:
        http://stackoverflow.com/questions/1207406/remove-items-from-a-list-while-iterating-in-python
        """
        if reason == "url":
            articles[:] = [a for a in articles if a.is_valid_url()]
        elif reason == "body":
            articles[:] = [a for a in articles if a.is_valid_body()]
        return articles

    @utils.cache_disk(seconds=(86400 * 1), cache_folder=ANCHOR_DIRECTORY)
    def _get_category_urls(self, domain):
        """The domain param is **necessary**, see .utils.cache_disk for reasons.
        the boilerplate method is so we can use this decorator right.
        We are caching categories for 1 day.
        """
        return self.extractor.get_category_urls(self.url, self.doc)

    def set_categories(self):
        urls = self._get_category_urls(self.domain)
        self.categories = [Category(url=url) for url in urls]

    def set_feeds(self):
        """Don't need to cache getting feed urls, it's almost
        instant with xpath
        """
        common_feed_urls = ["/feed", "/feeds", "/rss"]
        common_feed_urls = [urljoin(self.url, url) for url in common_feed_urls]

        split = urlsplit(self.url)
        if split.netloc in ("medium.com", "www.medium.com"):
            # should handle URL to user or user's post
            if split.path.startswith("/@"):
                new_path = "/feed/" + split.path.split("/")[1]
                new_parts = split.scheme, split.netloc, new_path, "", ""
                common_feed_urls.append(urlunsplit(new_parts))

        common_feed_urls_as_categories = [Category(url=url) for url in common_feed_urls]

        category_urls = [c.url for c in common_feed_urls_as_categories]
        requests = network.multithread_request(category_urls, self.config)

        for index, _ in enumerate(common_feed_urls_as_categories):
            response = requests[index].resp
            if response and response.ok:
                try:
                    common_feed_urls_as_categories[index].html = network.get_html(
                        response.url, response=response
                    )
                except network.ArticleBinaryDataException:
                    log.warning(
                        "Deleting feed %s from source %s due to binary data",
                        common_feed_urls_as_categories[index].url,
                        self.url,
                    )

        common_feed_urls_as_categories = [
            c for c in common_feed_urls_as_categories if c.html
        ]

        for _ in common_feed_urls_as_categories:
            doc = parsers.fromstring(_.html)
            _.doc = doc

        common_feed_urls_as_categories = [
            c for c in common_feed_urls_as_categories if c.doc is not None
        ]

        categories_and_common_feed_urls = (
            self.categories + common_feed_urls_as_categories
        )
        urls = self.extractor.get_feed_urls(self.url, categories_and_common_feed_urls)
        self.feeds = [Feed(url=url) for url in urls]

    def set_description(self):
        """Sets a blurb for this source, for now we just query the
        desc html attribute
        """
        metadata = self.extractor.get_metadata(self.url, self.doc)
        self.description = metadata["description"]

    def download(self):
        """Downloads html of source"""
        self.html = network.get_html(self.url, self.config)

    def download_categories(self):
        """Download all category html, can use mthreading"""
        category_urls = [c.url for c in self.categories]
        requests = network.multithread_request(category_urls, self.config)

        for index, _ in enumerate(self.categories):
            req = requests[index]
            if req.resp is not None:
                self.categories[index].html = network.get_html(
                    req.url, response=req.resp
                )
            else:
                log.warning(
                    "Deleting category %s from source %s due to download error",
                    self.categories[index].url,
                    self.url,
                )
        self.categories = [c for c in self.categories if c.html]

    def download_feeds(self):
        """Download all feed html, can use mthreading"""
        feed_urls = [f.url for f in self.feeds]
        requests = network.multithread_request(feed_urls, self.config)

        for index, _ in enumerate(self.feeds):
            req = requests[index]
            if req.resp is not None:
                self.feeds[index].rss = network.get_html(req.url, response=req.resp)
            else:
                log.warning(
                    "Deleting feed %s from source %s due to download error",
                    self.categories[index].url,
                    self.url,
                )
        self.feeds = [f for f in self.feeds if f.rss]

    def parse(self):
        """Sets the lxml root, also sets lxml roots of all
        children links, also sets description
        """
        # TODO: This is a terrible idea, ill try to fix it when i'm more rested
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

    def feeds_to_articles(self):
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
            urls = get_urls(feed.rss)
            cur_articles = []
            before_purge = len(urls)

            for url in urls:
                article = Article(
                    url=url,
                    source_url=feed.url,
                    read_more_link=self.read_more_link,
                    config=self.config,
                )
                cur_articles.append(article)

            cur_articles = self.purge_articles("url", cur_articles)
            after_purge = len(cur_articles)

            if self.config.memoize_articles:
                cur_articles = utils.memoize_articles(self, cur_articles)
            after_memo = len(cur_articles)

            articles.extend(cur_articles)

            log.debug(
                "%d->%d->%d for %s", before_purge, after_purge, after_memo, feed.url
            )
        return articles

    def categories_to_articles(self):
        """Takes the categories, splays them into a big list of urls and churns
        the articles out of each url with the url_to_article method
        """
        articles = []

        def get_urls(doc):
            if doc is None:
                return []
            return [
                (a.get("href"), a.text)
                for a in parsers.get_tags(doc, tag="a")
                if a.get("href")
            ]

        for category in self.categories:
            cur_articles = []
            url_title_tups = get_urls(category.doc)
            before_purge = len(url_title_tups)

            for tup in url_title_tups:
                indiv_url = tup[0]
                indiv_title = tup[1]

                _article = Article(
                    url=indiv_url,
                    source_url=category.url,
                    read_more_link=self.read_more_link,
                    title=indiv_title,
                    config=self.config,
                )
                cur_articles.append(_article)

            cur_articles = self.purge_articles("url", cur_articles)
            after_purge = len(cur_articles)

            if self.config.memoize_articles:
                cur_articles = utils.memoize_articles(self, cur_articles)
            after_memo = len(cur_articles)

            articles.extend(cur_articles)

            log.debug(
                "%d->%d->%d for %s", before_purge, after_purge, after_memo, category.url
            )
        return articles

    def _generate_articles(self):
        """Returns a list of all articles, from both categories and feeds"""
        category_articles = self.categories_to_articles()
        feed_articles = self.feeds_to_articles()

        articles = feed_articles + category_articles
        uniq = {article.url: article for article in articles}
        return list(uniq.values())

    def generate_articles(self, limit=5000):
        """Saves all current articles of news source, filter out bad urls"""
        articles = self._generate_articles()
        self.articles = articles[:limit]
        log.debug("%d articles generated and cutoff at %d", len(articles), limit)

    def download_articles(self, threads=1):
        """Starts the ``download()`` for all :any:`Article` objects
        from the ``articles`` property. It can run single threaded or
        multi-threaded.
        Arguments:
            threads(int): The number of threads to use for downloading
                articles. Default is 1.
        """
        # TODO fix how the article's is_downloaded is not set!
        urls = [a.url for a in self.articles]
        failed_articles = []

        def get_all_articles():
            for index, _ in enumerate(self.articles):
                url = urls[index]
                try:
                    html = network.get_html(url, config=self.config)
                except network.ArticleBinaryDataException:
                    log.warning(
                        "Deleting article %s from source %s due to binary data",
                        url,
                        self.url,
                    )
                    html = ""

                self.articles[index].html = html
                if not html:
                    failed_articles.append(self.articles[index])
            return [a for a in self.articles if a.html]

        def get_multithreaded_articles():
            filled_requests = network.multithread_request(urls, self.config)
            # Note that the responses are returned in original order
            for index, req in enumerate(filled_requests):
                html = network.get_html(req.url, response=req.resp)
                self.articles[index].html = html
                if not req.resp:
                    failed_articles.append(self.articles[index])
            return [a for a in self.articles if a.html]

        if threads == 1:
            self.articles = get_all_articles()
        else:
            if threads > NUM_THREADS_PER_SOURCE_WARN_LIMIT:
                log.warning(
                    "Using %s+ threads on a single source may result in rate limiting!",
                    NUM_THREADS_PER_SOURCE_WARN_LIMIT,
                )

            self.articles = get_multithreaded_articles()

        self.is_downloaded = True
        if len(failed_articles) > 0:
            log.warning(
                "The following article urls failed the download: %s",
                ", ".join([a.url for a in failed_articles]),
            )

    def parse_articles(self):
        """Parse all articles, delete if too small"""
        for article in self.articles:
            article.parse()

        self.articles = self.purge_articles("body", self.articles)
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
        print("[source url]:", self.url)
        print("[source brand]:", self.brand)
        print("[source domain]:", self.domain)
        print("[source len(articles)]:", len(self.articles))
        print("[source description[:50]]:", self.description[:50])

        print("printing out 10 sample articles...")

        for a in self.articles[:10]:
            print("\t", "[url]:", a.url)
            print("\t[title]:", a.title)
            print("\t[len of text]:", len(a.text))
            print("\t[keywords]:", a.keywords)
            print("\t[len of html]:", len(a.html))
            print("\t==============")

        print("feed_urls:", self.feed_urls())
        print("\r\n")
        print("category_urls:", self.category_urls())
