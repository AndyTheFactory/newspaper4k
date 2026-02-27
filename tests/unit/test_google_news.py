"""Unit tests for GoogleNewsSource language configuration."""

from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_gnews(mocker):
    """Mock the gnews module to avoid requiring it as a dependency in tests."""
    mock_gnews_module = MagicMock()
    mock_gnews_instance = MagicMock()
    mock_gnews_module.GNews.return_value = mock_gnews_instance
    mocker.patch.dict("sys.modules", {"gnews": mock_gnews_module})
    return mock_gnews_module, mock_gnews_instance


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
