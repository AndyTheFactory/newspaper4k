"""This module contains the GoogleNewsSource class that provides an interface
compatible to the newspaper's :any:`Source` class for accessing articles
from Google News. This modules requires the gnews package to be installed.
It can be installed as as dependency of newspaper by running
`pip install newspaper4k[gnews]` or `pip install newspaper4k[all]`.
Install it using `pip install gnews` as a standalone package.
"""

from datetime import datetime
from typing import Any, List, Optional
from newspaper.article import Article
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
try:
    from googlenewsdecoder import new_decoderv1
except ImportError as e:
    raise ImportError(
        "You must install googlenewsdecoder for fetching the actual url \n"
        "Try pip install googlenewsdecoder\n"
        "or pip install googlenewsdecoder\n"
    ) from e

class GoogleNewsSource(Source):
    """
    A :any:`Source` compatible class for fetching news articles from Google News.
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
        country: Optional[str] = None,
        period: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        max_results: int = 100,
        exclude_websites: Optional[List[str]] = None,
        **kwargs,
    ):
        super().__init__(url="https://news.google.com/", **kwargs)
        self.country = country
        self.period = period
        self.start_date = start_date
        self.end_date = end_date
        self.max_results = max_results
        self.exclude_websites = exclude_websites
        self.gnews_results: List[Any] = []
        proxy = None
        if "proxies" in self.config.requests_params:
            proxy = self.config.requests_params["proxies"].get(
                "http"
            ) or self.config.requests_params["proxies"].get("https")

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
        keyword: Optional[str] = None,
        topic: Optional[str] = None,
        location: Optional[str] = None,
        site: Optional[str] = None,
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
        """
        Inherited Method from :any:`Source`. It has no usage in Google News.
        Raises NotImplementedError: Google News does not support category urls.
        """
        raise NotImplementedError("Google News does not support category urls")

    def set_feeds(self):
        """
        Inherited Method from :any:`Source`. It has no usage in Google News.
        Raises NotImplementedError: Google News does not support purging articles.
        """
        raise NotImplementedError("Google News does not support purging articles")

    def download(
        self,
        top_news: bool = True,
        keyword: Optional[str] = None,
        topic: Optional[str] = None,
        location: Optional[str] = None,
        site: Optional[str] = None,
    ):
        """
        Downloads Google news articles based on the specified parameters.

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
        """
        Inherited Method from :any:`Source`. It has no usage in Google News.
        Raises NotImplementedError: Google News does not support category urls.
        """
        raise NotImplementedError("Google News does not support category urls")

    def download_feeds(self):
        """
        Inherited Method from :any:`Source`. It has no usage in Google News.
        Raises NotImplementedError: Google News does not support feeds.
        """
        raise NotImplementedError("Google News does not support feeds")

    def parse(self):
        """
        Parses the Google News results and populates the `articles` list.

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
            decoded_url = new_decoderv1(url, interval=5)
            if not decoded_url.get("status"):
                raise ValueError("Failed to decode the URL")
            return decoded_url.get("url")

        self.articles = []
        for res in self.gnews_results:
            a = Article(
                url=prepare_gnews_url(res["url"]),
                title=res["title"],
                source_url=res["publisher"].get("href"),
            )
            a.summary = res["description"]
            self.articles.append(a)
        self.is_parsed = True

    def parse_articles(self):
        """
        Inherited Method from :any:`Source`. It has no usage in Google News.
        Raises NotImplementedError: Google News does not support parse articles.
        """
        raise NotImplementedError("Google News does not support parse articles")

    def parse_feeds(self):
        """
        Inherited Method from :any:`Source`. It has no usage in Google News.
        Raises NotImplementedError: Google News does not support feeds.
        """
        raise NotImplementedError("Google News does not support feeds")

    def feeds_to_articles(self) -> List[Article]:
        """
        Inherited Method from :any:`Source`. It has no usage in Google News.
        Raises NotImplementedError: Google News does not support feeds.
        """
        raise NotImplementedError("Google News does not support feeds")

    def categories_to_articles(self) -> List[Article]:
        """
        Inherited Method from :any:`Source`. It has no usage in Google News.
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
        """
        Returns a string representation of the GoogleNews object.

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
