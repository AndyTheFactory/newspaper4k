"""This module contains the GoogleNewsSource class that provides an interface
compatible to the newspaper's :any:`Source` class for accessing articles
from Google News. This modules requires the gnews package to be installed.
It can be installed as as dependency of newspaper by running
`pip install newspaper4k[gnews]` or `pip install newspaper4k[all]`.
Install it using `pip install gnews` as a standalone package.
"""

import json
import logging
import re
from datetime import datetime
from typing import Any
from urllib.parse import quote

from newspaper import network
from newspaper.article import Article
from newspaper.parsers import fromstring, get_tags
from newspaper.source import Source

try:
    import gnews
except ImportError as e:
    raise ImportError(
        "You must install gnews before using the Google News API. \n"
        "Try pip install gnews\n"
        "or pip install newspaper4k[gnews]\n"
        "or pip install newspaper4k[all]\n"
    ) from e

# Some url encoding related constants
_ENCODED_URL_PREFIX = "https://news.google.com/rss/articles/"
_ENCODED_URL_PREFIX_WITH_CONSENT = "https://consent.google.com/m?continue=https://news.google.com/rss/articles/"
_ENCODED_URL_RE = re.compile(rf"^{re.escape(_ENCODED_URL_PREFIX_WITH_CONSENT)}(?P<encoded_url>[^?]+)")
_ENCODED_URL_RE = re.compile(rf"^{re.escape(_ENCODED_URL_PREFIX)}(?P<encoded_url>[^?]+)")
_DECODED_URL_RE = re.compile(rb'^\x08\x13".+?(?P<primary_url>http[^\xd2]+)\xd2\x01')

logger = logging.getLogger(__name__)


class GoogleNewsSource(Source):
    """A :any:`Source` compatible class for fetching news articles from Google News.
    You can filter the news articles by keyword, topic, country, location,
    time period, start date, end date. The returned articles will, of course,
    be from different News Sites, as featured in Google News.

    Args:
        country (str): The country for which to fetch news articles.
        period (str): The time period for which to fetch news articles.
            Eg: "7d" for 7 days. Available options are: "h", "d", "m", "y".
        start_date (str): The start date for fetching news articles.
        end_date (str): The end date for fetching news articles.
        max_results (int): The maximum number of news articles to fetch.
        exclude_websites (list): List of websites to exclude from the fetched
            news articles.
        **kwargs: All additional keyword arguments that are available for :any:`Source`.

    Attributes:
        country (str): The country for which news articles are fetched.
        period (str): The time period for which news articles are fetched.
        start_date (str): The start date for fetching news articles.
        end_date (str): The end date for fetching news articles.
        max_results (int): The maximum number of news articles to fetch.
        exclude_websites (list): List of websites to exclude from the fetched
            news articles.
        gnews_results (list): List of news articles fetched from Google News.
        gnews (gnews.GNews): Instance of the GNews class for fetching news articles.
    """

    def __init__(
        self,
        country: str | None = None,
        period: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        max_results: int = 100,
        exclude_websites: list[str] | None = None,
        **kwargs,
    ):
        super().__init__(url="https://news.google.com/", **kwargs)
        self.country = country
        self.period = period
        self.start_date = start_date
        self.end_date = end_date
        self.max_results = max_results
        self.exclude_websites = exclude_websites
        self.gnews_results: list[Any] = []
        proxy = None
        if "proxies" in self.config.requests_params:
            proxy = self.config.requests_params["proxies"].get("http") or self.config.requests_params["proxies"].get(
                "https"
            )
        self.config.requests_params["headers"]["Content-Type"] = "application/x-www-form-urlencoded;charset=UTF-8"

        self.gnews = gnews.GNews(
            language=self.config.language,
            country=self.country,
            period=self.period,
            start_date=self.start_date,
            end_date=self.end_date,
            max_results=self.max_results,
            exclude_websites=self.exclude_websites,
            proxy=proxy,
        )

    def build(
        self,
        top_news: bool = True,
        keyword: str | None = None,
        topic: str | None = None,
        location: str | None = None,
        site: str | None = None,
    ):
        """Fetches articles, and generates the list of :any:`Article` objects
        from Google News based on the provided arguments. The fetched articles
        will be stored in the :any:`articles` attribute. The Articles are not
        downloaded, for that you need to call :any:`Source.download_articles`
        method.

        Args:
            top_news (bool): Whether to fetch top news articles.
            keyword (str): The keyword to search for in news articles.
            topic (str): The topic to search for in news articles.
            location (str): The location for which to fetch news articles.
            site (str): The website from which to fetch news articles.
        """
        self.download(
            top_news=top_news,
            keyword=keyword,
            topic=topic,
            location=location,
            site=site,
        )
        self.parse()

        self.generate_articles()

    def set_categories(self):
        """Inherited Method from :any:`Source`. It has no usage in Google News.
        Raises NotImplementedError: Google News does not support category urls.
        """
        raise NotImplementedError("Google News does not support category urls")

    def set_feeds(self):
        """Inherited Method from :any:`Source`. It has no usage in Google News.
        Raises NotImplementedError: Google News does not support purging articles.
        """
        raise NotImplementedError("Google News does not support purging articles")

    def download(
        self,
        top_news: bool = True,
        keyword: str | None = None,
        topic: str | None = None,
        location: str | None = None,
        site: str | None = None,
    ):
        """Downloads Google news articles based on the specified parameters.

        Args:
            top_news (bool, optional): Whether to include top news articles.
                Defaults to True.
            keyword (str, optional): The keyword to search for in news articles.
                Defaults to None.
            topic (str, optional): The topic to filter news articles by.
                Defaults to None.
            location (str, optional): The location to filter news articles by.
                Defaults to None.
            site (str, optional): The site to filter news articles by.
                Defaults to None.
        """
        self.gnews_results = []
        if top_news:
            self.gnews_results += self.gnews.get_top_news()

        if keyword:
            self.gnews_results += self.gnews.get_news(keyword)

        if topic:
            self.gnews_results += self.gnews.get_news_by_topic(topic)

        if location:
            self.gnews_results += self.gnews.get_news_by_location(location)

        if site:
            self.gnews_results += self.gnews.get_news_by_site(site)

        self.is_downloaded = True

    def download_categories(self):
        """Inherited Method from :any:`Source`. It has no usage in Google News.
        Raises NotImplementedError: Google News does not support category urls.
        """
        raise NotImplementedError("Google News does not support category urls")

    def download_feeds(self):
        """Inherited Method from :any:`Source`. It has no usage in Google News.
        Raises NotImplementedError: Google News does not support feeds.
        """
        raise NotImplementedError("Google News does not support feeds")

    def parse(self):
        """Parses the Google News results and populates the `articles` list.

        This method prepares the Google News URL, decodes the URL, and extracts
            relevant information
        such as the article URL, title, source URL, and summary. The extracted
            information is then
        used to create Article objects, which are added to the `articles` list.

        Note: This method assumes that the `gnews_results` attribute has already
            been populated with
        the Google News results by the :any:`download` method.
        """

        def prepare_gnews_url(url):
            # Google keeps making life difficult for us. They encode the URL
            # in a weird way. We need to decode it to get the primary URL.
            # https://gist.github.com/huksley/bc3cb046157a99cd9d1517b32f91a99e

            logger.debug(f"Decoding Google News URL: {url}")
            match = _ENCODED_URL_RE.match(url)
            data_id = match.groupdict()["encoded_url"]

            google_content = network.get_html(url, self.config)

            node = fromstring(google_content)

            data_node = get_tags(node, tag="div", attribs={"data-n-a-id": data_id})
            for data in data_node:
                signature = data.get("data-n-a-sg")
                timestamp = data.get("data-n-a-ts")
                logger.debug(f"Signature: {signature}, Timestamp: {timestamp}")
                if signature and timestamp:
                    google_url = "https://news.google.com/_/DotsSplashUi/data/batchexecute"
                    payload = [
                        "Fbv4je",
                        f'["garturlreq",[["X","X",["X","X"],null,null,1,1,"US:en",null,1,null,null,null,null,null,0,1],"X","X",1,[1,1,1],1,1,null,0,0,null,0],"{data_id}",{timestamp},"{signature}"]',
                    ]
                    data = f"f.req={quote(json.dumps([[payload]]))}"

                    google_response = network.do_request(google_url, self.config, method="post", data=data)
                    logger.debug(f"Google News URL response: {google_response.status_code}")
                    if google_response.status_code < 299:
                        data = google_response.text.split("\n", 1)[-1]
                        try:
                            logger.debug(f"Google News URL response: {data}")
                            google_response = json.loads(data)
                            google_response = json.loads(google_response[0][2])
                            return google_response[1]
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to decode Google News URL: {url} Data received: {data}")
                            return None
            logger.warning(f"Failed to get signature and timestamp from Google News URL: {url}")
            return None

        self.articles = []
        logger.info(f"Got {len(self.gnews_results)} articles from Google News. Starting to decode them.")
        for res in self.gnews_results:
            decoded_url = prepare_gnews_url(res["url"])
            if not decoded_url:
                continue

            logger.info(f"Successfully decoded Google News URL: {decoded_url}")
            a = Article(
                url=decoded_url,
                title=res["title"],
                source_url=res["publisher"].get("href"),
            )
            a.summary = res["description"]
            self.articles.append(a)
        self.is_parsed = True

    def parse_articles(self):
        """Inherited Method from :any:`Source`. It has no usage in Google News.
        Raises NotImplementedError: Google News does not support parse articles.
        """
        raise NotImplementedError("Google News does not support parse articles")

    def parse_feeds(self):
        """Inherited Method from :any:`Source`. It has no usage in Google News.
        Raises NotImplementedError: Google News does not support feeds.
        """
        raise NotImplementedError("Google News does not support feeds")

    def feeds_to_articles(self) -> list[Article]:
        """Inherited Method from :any:`Source`. It has no usage in Google News.
        Raises NotImplementedError: Google News does not support feeds.
        """
        raise NotImplementedError("Google News does not support feeds")

    def categories_to_articles(self) -> list[Article]:
        """Inherited Method from :any:`Source`. It has no usage in Google News.
        Raises NotImplementedError: Google News does not support category urls.
        """
        raise NotImplementedError("Google News does not support category urls")

    def generate_articles(self, limit=5000):
        """Generates a list of articles from the Google News source.

        Args:
            limit (int, optional): The maximum number of articles to generate.
                Defaults to 5000.
        """
        self.articles = self.articles[:limit]

    def __str__(self):
        """Returns a string representation of the GoogleNews object.

        The string includes information about the Google News source, such as
            the country,
        period, start date, end date, and maximum number of results. It also
            includes a list
        of 10 sample articles.

        Returns:
            str: A string representation of the GoogleNews object.
        """
        res = (
            f"Google News Source: {self.country} \n"
            f"\tPeriod: {self.period} \n"
            f"\tStart Date: {self.start_date} \n"
            f"\tEnd Date: {self.end_date} \n"
            f"\tMax Results: {self.max_results} \n"
        )
        res += "\n 10 sample Articles: \n"

        for a in self.articles[:10]:
            res += f"{str(a)} \n"
            res += "=" * 40 + "\n"

        return res
