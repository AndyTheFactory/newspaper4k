"""Unit tests for GoogleNewsSource language configuration."""

from unittest.mock import MagicMock

import pytest

from newspaper.google_news import GoogleNewsSource


class FakeFeedData:
    status = 200
    entries = []


@pytest.fixture
def mock_gnews(mocker):
    """Mock the gnews module to avoid requiring it as a dependency in tests."""
    mock_gnews_module = MagicMock()
    mock_gnews_instance = MagicMock()
    mock_gnews_module.GNews.return_value = mock_gnews_instance
    mocker.patch.dict("sys.modules", {"gnews": mock_gnews_module})
    return mock_gnews_module, mock_gnews_instance


@pytest.fixture(autouse=True)
def reset_google_news_module():
    import sys

    # Reset the google_news module before and after each test to ensure a
    # clean state (no mocking leakage between tests)
    sys.modules.pop("newspaper.google_news", None)
    yield
    sys.modules.pop("newspaper.google_news", None)


def test_google_news_default_language(mock_gnews):
    """GoogleNewsSource should default to 'en' language."""
    mock_gnews_module, mock_gnews_instance = mock_gnews

    # Re-import after patching
    import importlib

    import newspaper.google_news as gn_module

    importlib.reload(gn_module)

    source = gn_module.GoogleNewsSource()
    assert source.config.language == "en"
    mock_gnews_module.GNews.assert_called_once()
    call_kwargs = mock_gnews_module.GNews.call_args.kwargs
    assert call_kwargs["language"] == "en"


def test_google_news_language_init_param(mock_gnews):
    """GoogleNewsSource should use the language parameter passed at init."""
    mock_gnews_module, mock_gnews_instance = mock_gnews

    import importlib

    import newspaper.google_news as gn_module

    importlib.reload(gn_module)

    source = gn_module.GoogleNewsSource(language="es")
    assert source.config.language == "es"
    call_kwargs = mock_gnews_module.GNews.call_args.kwargs
    assert call_kwargs["language"] == "es"


def test_google_news_config_language_respected_in_download(mock_gnews):
    """Setting config.language after init should be respected when download() is called."""
    mock_gnews_module, mock_gnews_instance = mock_gnews
    mock_gnews_instance.get_top_news.return_value = []

    import importlib

    import newspaper.google_news as gn_module

    importlib.reload(gn_module)

    source = gn_module.GoogleNewsSource()
    assert source.config.language == "en"

    # Change language after initialization
    source.config.language = "es"
    assert source.config.language == "es"

    # download() should sync gnews.language with config.language
    source.download(top_news=True)
    assert mock_gnews_instance.language == "es"


def test_google_news_proxy_format(mocker):
    """GoogleNewsSource should pass the full proxies dict to gnews.GNews, not just the address string."""
    proxy_dict = {"http": "http://proxy.example.com:8080"}

    source = GoogleNewsSource(proxies=proxy_dict)

    assert source.gnews._proxy == proxy_dict


def test_google_news_proxy_used_in_feedparser(mocker):
    """When proxies are provided, feedparser should be called with a ProxyHandler."""
    import urllib.request

    proxy_dict = {"http": "http://proxy.example.com:8080"}

    mock_feedparser = mocker.patch("gnews.gnews.feedparser.parse", return_value=FakeFeedData())

    source = GoogleNewsSource(proxies=proxy_dict)
    source.build(top_news=True)

    assert mock_feedparser.called
    call_kwargs = mock_feedparser.call_args
    handlers = call_kwargs.kwargs.get("handlers") or (call_kwargs.args[2] if len(call_kwargs.args) > 2 else None)
    assert handlers is not None
    assert any(isinstance(h, urllib.request.ProxyHandler) for h in handlers)


def test_google_news_no_proxy(mocker):
    """When no proxies are provided, gnews._proxy should be None."""
    source = GoogleNewsSource()
    assert source.gnews._proxy is None
