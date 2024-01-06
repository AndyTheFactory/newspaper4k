import pytest
from newspaper import Source
from newspaper.article import ArticleDownloadState
from newspaper.settings import MEMO_DIR
from newspaper.utils import domain_to_filename
import tests.conftest as conftest
from newspaper import utils


@pytest.fixture
def cnn_source():
    DESC = (
        "CNN.com International delivers breaking news from across "
        "the globe and information on the latest top stories, "
        "business, sports and entertainment headlines. Follow the "
        "news as it happens through: special reports, videos, "
        "audio, photo galleries plus interactive maps and timelines."
    )
    CATEGORY_URLS = [
        "http://www.cnn.com",
        "http://cnn.com",
        "http://cnn.com/CNNI",
        "http://mexico.cnn.com",
        "http://cnn.com/MIDDLEEAST",
        "http://cnn.com/LATINAMERICA",
        "http://edition.cnn.com",
        "http://cnn.com/TECH",
        "http://money.cnn.com",
        "http://cnn.com/ASIA",
        "http://cnn.com/WORLD",
        "http://cnn.com/EUROPE",
        "http://ireport.cnn.com",
        "http://arabic.cnn.com",
        "http://us.cnn.com",
        "http://amanpour.blogs.cnn.com",
        "http://cnn.com/espanol",
        "http://cnn.com/HLN",
        "http://cnn.com/US",
        "http://transcripts.cnn.com",
        "http://cnn.com/TRAVEL",
        "http://cnn.com/cnni",
        "http://cnn.com/SHOWBIZ",
        "http://cnn.com/tools/index.html",
        "http://travel.cnn.com",
        "http://connecttheworld.blogs.cnn.com",
        "http://cnn.com/mostpopular",
        "http://business.blogs.cnn.com",
        "http://cnn.com/AFRICA",
        "http://www.cnn.co.jp",
        "http://cnnespanol.cnn.com",
        "http://cnn.com/video",
        "http://cnn.com/BUSINESS",
        "http://cnn.com/SPORT",
    ]

    FEEDS = [
        "http://feeds.cnn.co.jp/cnn/rss",
        "http://rss.cnn.com/rss/cnn_freevideo.rss",
        "http://rss.cnn.com/rss/cnn_latest.rss",
        "http://rss.cnn.com/rss/cnn_topstories.rss",
        "http://rss.cnn.com/rss/edition.rss",
        "http://rss.cnn.com/rss/edition_africa.rss",
        "http://rss.cnn.com/rss/edition_americas.rss",
        "http://rss.cnn.com/rss/edition_asia.rss",
        "http://rss.cnn.com/rss/edition_connecttheworld.rss",
        "http://rss.cnn.com/rss/edition_entertainment.rss",
        "http://rss.cnn.com/rss/edition_europe.rss",
        "http://rss.cnn.com/rss/edition_football.rss",
        "http://rss.cnn.com/rss/edition_meast.rss",
        "http://rss.cnn.com/rss/edition_space.rss",
        "http://rss.cnn.com/rss/edition_sport.rss",
        "http://rss.cnn.com/rss/edition_technology.rss",
        "http://rss.cnn.com/rss/edition_travel.rss",
        "http://rss.cnn.com/rss/edition_us.rss",
        "http://rss.cnn.com/rss/edition_world.rss",
        "http://rss.cnn.com/rss/edition_worldsportblog.rss",
        "http://rss.cnn.com/rss/money_news_international.rss",
        "https://arabic.cnn.com/api/v1/rss/rss.xml",
        "https://cnnespanol.cnn.com/home/feed/",
    ]

    BRAND = "cnn"
    html_content = conftest.get_data("cnn_main_site", "html")

    return {
        "url": "http://cnn.com",
        "brand": BRAND,
        "description": DESC,
        "category_urls": CATEGORY_URLS,
        "feeds": FEEDS,
        "html_content": html_content,
    }


@pytest.fixture
def feed_sources():
    return [
        {"url": "https://techcrunch.com", "feeds": 15},
        {"url": "https://www.npr.org/", "feeds": 15},
        {"url": "https://vox.com", "feeds": 14},
        {"url": "https://www.theverge.com/", "feeds": 14},
    ]


class TestSource:
    def test_empty_url_source(self):
        with pytest.raises(ValueError):
            Source("")
        with pytest.raises(ValueError):
            Source(url=None)

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

    def test_memorize_articles(self, cnn_source):
        source = Source(cnn_source["url"], verbose=False, memorize_articles=True)
        source.clean_memo_cache()

        source.html = cnn_source["html_content"]
        source.parse()
        source.set_feeds()
        source.download_feeds()

        articles = source.feeds_to_articles()

        urls_in_cache = MEMO_DIR / domain_to_filename(source.domain)

        assert urls_in_cache.exists()

        urls = urls_in_cache.read_text().split("\n")
        assert len([u for u in urls if u]) == len({a.url for a in articles})

        source = Source(cnn_source["url"], verbose=False, memorize_articles=True)
        source.html = cnn_source["html_content"]
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
            raise Exception("Should not be called")

        stub_func(None, source.domain)

        utils.cache_disk.enabled = False
        # test cache disabled
        with pytest.raises(Exception):
            stub_func(None, source.domain)

    def test_get_feeds(self, feed_sources):
        for feed_source in feed_sources:
            source = Source(feed_source["url"])
            source.build()
            # source.set_feeds()
            assert feed_source["feeds"] <= len(source.feeds)

    def test_download_all_articles(self, cnn_source):
        source = Source(cnn_source["url"], verbose=False, memorize_articles=False)
        source.clean_memo_cache()

        source.html = cnn_source["html_content"]
        source.parse()
        source.set_feeds()
        source.download_feeds()  # mthread

        source.generate_articles(limit=30)
        articles = source.download_articles()

        assert len(articles) == 30
        assert all([a.download_state == ArticleDownloadState.SUCCESS for a in articles])
