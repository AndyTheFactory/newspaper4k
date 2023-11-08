import pytest
from newspaper import Source
import tests.conftest as conftest


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


class TestSource:
    def test_empty_ulr_source(self):
        with pytest.raises(ValueError):
            Source("")
        with pytest.raises(ValueError):
            Source(url=None)

    def test_build_source(self, cnn_source):
        source = Source(cnn_source["url"], verbose=False, memoize_articles=False)
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
