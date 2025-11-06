import io
import pickle

import pytest

import newspaper
import tests.conftest as conftest
from newspaper import Source, utils
from newspaper.article import ArticleDownloadState
from newspaper.google_news import GoogleNewsSource
from newspaper.settings import MEMO_DIR
from newspaper.utils import domain_to_filename


class TestSource:
    def test_build_source(self, cnn_source):
        source = Source(cnn_source["url"], verbose=False, memorize_articles=False)
        source.clean_memo_cache()

        source.html = cnn_source["html_content"]
        source.parse()

        source.set_categories()
        source.download_categories()  # mthread
        source.parse_categories()

        source.set_feeds()
        source.download_feeds()  # mthread

        assert source.url == cnn_source["url"]
        assert source.brand == cnn_source["brand"]
        assert source.description == cnn_source["description"]
        # assert sorted(source.category_urls()) == sorted(cnn_source["category_urls"])
        # assert sorted(source.feed_urls()) == sorted(cnn_source["feeds"])

    def test_pickle_source(self, cnn_source):
        source = Source(cnn_source["url"], verbose=False, memorize_articles=False)
        source.clean_memo_cache()

        source.html = cnn_source["html_content"]
        source.parse()

        source.set_categories()
        source.download_categories()  # mthread
        source.parse_categories()

        source.set_feeds()
        source.download_feeds()  # mthread

        bytes_io = io.BytesIO()
        pickle.dump(source, bytes_io)

        bytes_io.seek(0)

        source_ = pickle.load(bytes_io)

        assert len(source.articles) == len(source_.articles)

    def test_memorize_articles(self, cnn_source):
        source_fixture = cnn_source
        source = Source(source_fixture["url"], verbose=False, memorize_articles=True)
        source.clean_memo_cache()

        source.html = source_fixture["html_content"]
        source.parse()
        source.set_feeds()
        source.download_feeds()

        articles = source.feeds_to_articles()

        urls_in_cache = MEMO_DIR / domain_to_filename(source.domain)

        assert urls_in_cache.exists()

        urls = urls_in_cache.read_text().split("\n")
        assert len([u for u in urls if u]) == len({a.url for a in articles})

        source = Source(source_fixture["url"], verbose=False, memorize_articles=True)
        source.html = source_fixture["html_content"]
        source.parse()
        source.set_feeds()
        source.download_feeds()

        # Now test that it cached all
        articles = source.feeds_to_articles()
        assert len(articles) == 0

    def test_cache_categories(self):
        """Builds two same source objects in a row examines speeds of both"""
        url = "http://uk.yahoo.com"
        source = Source(url)
        source.html = conftest.get_data("yahoo_main_site", "html")
        source.parse()
        source.set_categories()

        saved_urls = source.category_urls()
        source.categories = []
        source.set_categories()

        assert len(saved_urls) == len(source.category_urls())

        # Test cache enabled
        @utils.cache_disk(seconds=86400)
        def stub_func(_, domain):
            raise NotImplementedError("Should not be called")

        stub_func(None, source.domain)

        utils.cache_disk.enabled = False
        # test cache disabled
        with pytest.raises(NotImplementedError):
            stub_func(None, source.domain)

    def test_get_feeds(self, feed_sources):
        for feed_source in feed_sources:
            source = Source(
                feed_source["url"],
                disable_category_cache=True,
                memorize_articles=False,
                browser_user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                    " (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
                ),
            )
            source.build()
            # source.set_feeds()
            assert (feed_source["feeds"] - 2) <= len(source.feeds)

    def test_gnews(self, gnews_source):
        source = GoogleNewsSource(
            country="US",
            period="7d",
            max_results=10,
        )
        source.build(top_news=True)
        assert len(source.articles) == 10

        source.build(top_news=False, keyword=gnews_source["keyword"])
        assert len(source.articles) == 10

        source.build(top_news=False, topic=gnews_source["topic"])
        assert len(source.articles) == 10

        source.build(top_news=False, location=gnews_source["location"])
        assert len(source.articles) == 10

        source.build(top_news=False, site=gnews_source["site"])
        assert len(source.articles) == 10

        source.download_articles()
        assert all([a.download_state == ArticleDownloadState.SUCCESS for a in source.articles])  # noqa: C419

    def test_source_in_same_path(self):
        source = newspaper.build(
            "https://www.dailymail.co.uk/health/index.html",
            only_in_path=True,
            memorize_articles=False,
        )

        assert all([a.url.startswith("https://www.dailymail.co.uk/health/") for a in source.articles])  # noqa: C419
