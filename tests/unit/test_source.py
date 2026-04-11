import sys
from types import ModuleType

import pytest

from newspaper import Article, Source
from newspaper.source import Category, Feed, RobotsException


def test_empty_url_source():
    with pytest.raises(ValueError):
        Source("")
    with pytest.raises(ValueError):
        Source(url=None)


def test_source_build_offline(mocker):
    # Mock all methods that would make network calls
    mocker.patch("newspaper.source.Source.download")
    mocker.patch("newspaper.source.Source.parse")
    mocker.patch("newspaper.source.Source.set_categories")
    mocker.patch("newspaper.source.Source.download_categories")
    mocker.patch("newspaper.source.Source.parse_categories")
    mocker.patch("newspaper.source.Source.set_feeds")
    mocker.patch("newspaper.source.Source.download_feeds")
    mocker.patch("newspaper.source.Source.generate_articles")

    # Create a Source object
    source = Source("http://example.com")

    # Call the build method
    source.build()

    # Assert that the mocked methods were called
    source.download.assert_called_once()
    source.parse.assert_called_once()
    source.set_categories.assert_called_once()
    source.download_categories.assert_called_once()
    source.parse_categories.assert_called_once()
    source.set_feeds.assert_called_once()
    source.download_feeds.assert_called_once()
    source.generate_articles.assert_called_once()


def test_source_set_categories(mocker):
    source = Source("http://example.com")
    mocker.patch(
        "newspaper.source.Source._get_category_urls",
        return_value=["http://example.com/category1", "http://example.com/category2"],
    )
    source.set_categories()
    assert len(source.categories) == 2
    assert source.categories[0].url in ["http://example.com/category1", "http://example.com/category2"]
    assert isinstance(source.categories[0], Category)


def test_source_set_feeds(mock_request, rss_content):
    source = Source("http://example.com")

    mock_request("http://example.com/feed", "", 200)

    source.html = (
        "<html><body><span>"
        "<a href='http://example.com/feed.xml' type='application/rss+xml'>Feed 1</a>span></body><html>"
    )
    source.parse()
    source.set_feeds()

    assert len(source.feeds) == 1
    assert source.feeds[0].url == "http://example.com/feed.xml"
    assert isinstance(source.feeds[0], Feed)


def test_source_generate_articles(mocker, mock_request):
    source = Source("http://example.com", memorize_articles=False)

    mocker.patch(
        "newspaper.source.Source._get_category_urls",
        return_value=["http://example.com/category1", "http://example.com/category2"],
    )

    mocker.patch("newspaper.urls.valid_url", return_value=True)

    mock_request(
        "http://example.com/feed",
        "<html><body><span>"
        "<a href='http://example.com/article1'>Article 1</a>"
        "</span><span><a href='http://example.com/article2'>Article 2</a></span>body><html>",
        200,
    )

    source.html = (
        "<html><body><span>"
        "<a href='http://example.com/feed.xml' type='application/rss+xml'>Feed 1</a>span></body><html>"
    )

    source.parse()
    source.set_categories()
    source.download_categories()
    source.parse_categories()

    source.generate_articles()
    assert len(source.articles) == 2
    assert source.articles[0].url == "http://example.com/article1"


def test_source_download_articles(mocker, mock_request):
    source = Source("http://example.com")
    test_content = "<html><body><span>xxx</span>body><html>"
    mock_r = mock_request(
        "http://example.com/",
        test_content,
        200,
    )

    source.articles = [
        Article(url="http://example.com/article1"),
        Article(url="http://example.com/article2"),
    ]

    source.download_articles()
    assert len(source.articles) == 2
    assert source.articles[0].html == test_content
    assert source.articles[1].html == test_content
    assert mock_r.call_count == 2


def test_source_parse_articles(mocker):
    source = Source("http://example.com")
    article1 = Article(url="http://example.com/article1")
    article2 = Article(url="http://example.com/article2")
    source.articles = [article1, article2]

    def fake_parse(self):
        # Give each article unique content so fingerprints differ
        self.title = self.url
        self.text = f"Body text for {self.url}"

    mock_patch = mocker.patch("newspaper.source.Article.parse", autospec=True, side_effect=fake_parse)
    mocker.patch("newspaper.source.Article.is_valid_body", return_value=True)

    source.parse_articles()

    assert len(source.articles) == 2
    assert source.articles[0].url == "http://example.com/article1"
    assert mock_patch.call_count == 2


def test_source_helper_methods():
    source = Source("http://example.com")
    source.articles = [
        Article(url="http://example.com/article1"),
        Article(url="http://example.com/article2"),
    ]
    source.categories = [
        Category(url="http://example.com/category1"),
        Category(url="http://example.com/category2"),
    ]
    source.feeds = [
        Feed(url="http://example.com/feed1"),
        Feed(url="http://example.com/feed2"),
    ]

    assert source.size() == 2
    assert source.article_urls() == [
        "http://example.com/article1",
        "http://example.com/article2",
    ]
    assert source.category_urls() == [
        "http://example.com/category1",
        "http://example.com/category2",
    ]
    assert source.feed_urls() == ["http://example.com/feed1", "http://example.com/feed2"]


def test_robotstxt(monkeypatch):
    # Fake response for robots.txt
    class Resp:
        text = "User-agent: *\nDisallow: /"
        status_code = 200
        url = "http://example.com/robots.txt"

        def raise_for_status(self):
            return None

    # Ensure network.do_request returns our fake response
    monkeypatch.setattr("newspaper.source.network.do_request", lambda url, config: Resp())

    # Create a fake protego module with Protego.parse returning an object
    # whose can_fetch() returns False (meaning disallowed)
    fake_protego = ModuleType("protego")

    class FakeProtego:
        @staticmethod
        def parse(text):
            class P:
                def can_fetch(self, url, ua):
                    return False

            return P()

    fake_protego.Protego = FakeProtego
    monkeypatch.setitem(sys.modules, "protego", fake_protego)
    monkeypatch.setattr("importlib.util.find_spec", lambda name, *_: fake_protego if name == "protego" else None)

    # Capture the hook registered via add_hook
    captured = {}

    def fake_add_hook(name, func):
        captured[name] = func

    monkeypatch.setattr("newspaper.source.add_hook", fake_add_hook)

    src = Source("http://example.com", honor_robots_txt=True)
    # Call the method under test
    src._init_robots_parser()

    # Ensure the before_request hook was registered
    assert "before_request" in captured

    # Calling the registered hook should raise RobotsException because
    # our fake Protego.can_fetch returns False
    hook = captured["before_request"]

    with pytest.raises(RobotsException):
        hook("http://example.com/blocked", src.config)


# ---------------------------------------------------------------------------
# Tests for URL-normalization deduplication in _generate_articles()
# ---------------------------------------------------------------------------


def test_normalize_url_for_dedup():
    """_normalize_url_for_dedup strips scheme and www. prefix."""
    # http vs https with www
    assert Source._normalize_url_for_dedup("https://www.example.com/path") == Source._normalize_url_for_dedup(
        "http://example.com/path"
    )
    # Trailing slash is stripped – both sides should normalize to the same key
    assert Source._normalize_url_for_dedup("http://example.com/path/") == Source._normalize_url_for_dedup(
        "https://example.com/path"
    )
    # www prefix with trailing slash
    assert Source._normalize_url_for_dedup("http://www.example.com/path/") == Source._normalize_url_for_dedup(
        "https://example.com/path"
    )
    # Different paths should still differ
    assert Source._normalize_url_for_dedup("https://example.com/a") != Source._normalize_url_for_dedup(
        "https://example.com/b"
    )


def test_generate_articles_deduplicates_www_vs_no_www(mocker, mock_request):
    """Articles whose URLs differ only by www. prefix should be deduplicated."""
    source = Source("http://example.com", memorize_articles=False)

    mocker.patch(
        "newspaper.source.Source._get_category_urls",
        return_value=["http://example.com/category1"],
    )
    mocker.patch("newspaper.urls.valid_url", return_value=True)

    # Category page contains both the www and the non-www URL for the same article
    mock_request(
        "http://example.com/category1",
        "<html><body>"
        "<a href='http://www.example.com/article1'>Article 1 www</a>"
        "<a href='http://example.com/article1'>Article 1 no-www</a>"
        "</body></html>",
        200,
    )

    source.parse()
    source.set_categories()
    source.download_categories()
    source.parse_categories()
    source.generate_articles()

    urls = [a.url for a in source.articles]
    # Only one of the two should survive
    assert len(source.articles) == 1, f"Expected 1 unique article, got {len(source.articles)}: {urls}"


def test_generate_articles_deduplicates_http_vs_https(mocker, mock_request):
    """Articles whose URLs differ only by scheme (http vs https) should be deduplicated."""
    source = Source("http://example.com", memorize_articles=False)

    mocker.patch(
        "newspaper.source.Source._get_category_urls",
        return_value=["http://example.com/category1"],
    )
    mocker.patch("newspaper.urls.valid_url", return_value=True)

    mock_request(
        "http://example.com/category1",
        "<html><body>"
        "<a href='http://example.com/article1'>Article 1 http</a>"
        "<a href='https://example.com/article1'>Article 1 https</a>"
        "</body></html>",
        200,
    )

    source.parse()
    source.set_categories()
    source.download_categories()
    source.parse_categories()
    source.generate_articles()

    assert len(source.articles) == 1


# ---------------------------------------------------------------------------
# Tests for content-fingerprint deduplication in parse_articles()
# ---------------------------------------------------------------------------


def test_get_article_fingerprint():
    """_get_article_fingerprint returns identical hashes for identical content."""
    a1 = Article(url="http://example.com/a1")
    a1.title = "Same Title"
    a1.text = "Same body text"

    a2 = Article(url="http://example.com/a2")
    a2.title = "Same Title"
    a2.text = "Same body text"

    a3 = Article(url="http://example.com/a3")
    a3.title = "Different Title"
    a3.text = "Different body text"

    assert Source._get_article_fingerprint(a1) == Source._get_article_fingerprint(a2)
    assert Source._get_article_fingerprint(a1) != Source._get_article_fingerprint(a3)


def test_get_article_fingerprint_normalizes_whitespace_and_case():
    """Tabs, non-breaking spaces, multiple spaces, punctuation and case differences
    should not affect the fingerprint."""
    a_base = Article(url="http://example.com/a1")
    a_base.title = "hello world"
    a_base.text = "some body text"

    a_tabs = Article(url="http://example.com/a2")
    a_tabs.title = "hello\tworld"  # tab instead of space
    a_tabs.text = "some\tbody\ttext"

    a_nbsp = Article(url="http://example.com/a3")
    a_nbsp.title = "hello\xa0world"  # non-breaking space
    a_nbsp.text = "some\xa0body\xa0text"

    a_multi = Article(url="http://example.com/a4")
    a_multi.title = "hello  world"  # multiple spaces
    a_multi.text = "some  body  text"

    a_upper = Article(url="http://example.com/a5")
    a_upper.title = "Hello World"  # mixed case
    a_upper.text = "Some Body Text"

    a_punct = Article(url="http://example.com/a6")
    a_punct.title = "hello, world!"  # punctuation
    a_punct.text = "some body text."

    fp_base = Source._get_article_fingerprint(a_base)
    assert Source._get_article_fingerprint(a_tabs) == fp_base
    assert Source._get_article_fingerprint(a_nbsp) == fp_base
    assert Source._get_article_fingerprint(a_multi) == fp_base
    assert Source._get_article_fingerprint(a_upper) == fp_base
    assert Source._get_article_fingerprint(a_punct) == fp_base


def test_parse_articles_deduplicates_by_content(mocker):
    """parse_articles() should remove articles with identical title+text fingerprints."""
    source = Source("http://example.com")

    article1 = Article(url="http://www.example.com/article1")
    article2 = Article(url="http://example.com/article1")  # same content, different URL

    source.articles = [article1, article2]

    def fake_parse(self):
        self.title = "Shared Title"
        self.text = "Shared body text that is long enough to be valid."

    mocker.patch("newspaper.source.Article.parse", autospec=True, side_effect=fake_parse)
    mocker.patch("newspaper.source.Article.is_valid_body", return_value=True)

    source.parse_articles()

    assert len(source.articles) == 1
    assert source.articles[0].url == article1.url  # first occurrence is kept
