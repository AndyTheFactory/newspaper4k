import base64
import re
from typing import List
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


_ENCODED_URL_PREFIX = "https://news.google.com/rss/articles/"
_ENCODED_URL_PREFIX_WITH_CONSENT = (
    "https://consent.google.com/m?continue=https://news.google.com/rss/articles/"
)
_ENCODED_URL_RE = re.compile(
    rf"^{re.escape(_ENCODED_URL_PREFIX_WITH_CONSENT)}(?P<encoded_url>[^?]+)"
)
_ENCODED_URL_RE = re.compile(
    rf"^{re.escape(_ENCODED_URL_PREFIX)}(?P<encoded_url>[^?]+)"
)
_DECODED_URL_RE = re.compile(rb'^\x08\x13".+?(?P<primary_url>http[^\xd2]+)\xd2\x01')


class GoogleNewsSource(Source):
    def __init__(
        self,
        country=None,
        period=None,
        start_date=None,
        end_date=None,
        max_results=100,
        exclude_websites=None,
        **kwargs,
    ):
        super().__init__(url="https://news.google.com/", **kwargs)
        self.country = country
        self.period = period
        self.start_date = start_date
        self.end_date = end_date
        self.max_results = max_results
        self.exclude_websites = exclude_websites
        self.gnews_results = []
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

    def build(self, top_news=True, keyword=None, topic=None, location=None, site=None):
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
        raise NotImplementedError("Google News does not support purging articles")

    def set_feeds(self):
        raise NotImplementedError("Google News does not support purging articles")

    def download(
        self, top_news=True, keyword=None, topic=None, location=None, site=None
    ):
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
        raise NotImplementedError("Google News does not support purging articles")

    def download_feeds(self):
        raise NotImplementedError("Google News does not support purging articles")

    def parse(self):
        def prepare_gnews_url(url):
            # There seems to be a case when we get a URL with consent.google.com
            # see https://github.com/ranahaani/GNews/issues/62
            # Also, the URL is directly decoded, no need to go through news.google.com

            match = _ENCODED_URL_RE.match(url)
            encoded_text = match.groupdict()["encoded_url"]  # type: ignore
            encoded_text += (  # Fix incorrect padding. Ref: https://stackoverflow.com/a/49459036/
                "==="
            )
            decoded_text = base64.urlsafe_b64decode(encoded_text)

            match = _DECODED_URL_RE.match(decoded_text)

            primary_url = match.groupdict()["primary_url"]  # type: ignore
            primary_url = primary_url.decode()
            return primary_url

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
        raise NotImplementedError("Google News does not support purging articles")

    def parse_feeds(self):
        raise NotImplementedError("Google News does not support purging articles")

    def feeds_to_articles(self) -> List[Article]:
        raise NotImplementedError("Google News does not support purging articles")

    def categories_to_articles(self) -> List[Article]:
        raise NotImplementedError("Google News does not support purging articles")

    def generate_articles(self, limit=5000):
        self.articles = self.articles[:limit]

    def __str__(self):
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
