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

    mock_patch = mocker.patch("newspaper.source.Article.parse")
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

    # Capture the hook registered via add_hook
    captured = {}

    def fake_add_hook(name, func):
        captured[name] = func

    monkeypatch.setattr("newspaper.source.add_hook", fake_add_hook)

    src = Source("http://example.com")
    # Call the method under test
    src._init_robots_parser()

    # Ensure the before_request hook was registered
    assert "before_request" in captured

    # Calling the registered hook should raise RobotsException because
    # our fake Protego.can_fetch returns False
    hook = captured["before_request"]

    with pytest.raises(RobotsException):
        hook("http://example.com/blocked", src.config)
