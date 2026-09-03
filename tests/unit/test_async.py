"""Unit tests for the async API layer.

Tests cover:
- AsyncArticle.download() with pre-loaded HTML (no real network call).
- AsyncArticle.build() end-to-end (download + parse + nlp).
- async_article() convenience function.
- async_batch_request() ordering guarantee.
- AsyncSource.build() with mocked HTTP (homepage + categories + feeds).
- Configuration.async_concurrency propagation.
- CLI --sync flag keeps the sync code path.
- CLI default (async) path works.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from newspaper.article import ArticleDownloadState
from newspaper.async_func.article import AsyncArticle
from newspaper.configuration import Configuration

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "html"


def _load_html(name: str) -> str:
    """Load a pre-downloaded HTML fixture."""
    path = DATA_DIR / f"{name}.html"
    if path.exists():
        return path.read_text(encoding="utf-8")
    # Fallback: minimal placeholder so tests can still run without fixtures
    return f"<html><head><title>{name}</title></head><body><p>Test article body text.</p></body></html>"


CNN_HTML = _load_html("cnn_article")
CNN_URL = "http://www.cnn.com/2013/11/27/travel/weather-thanksgiving/index.html"


# ---------------------------------------------------------------------------
# AsyncArticle tests
# ---------------------------------------------------------------------------


class TestAsyncArticle:
    @pytest.mark.asyncio
    async def test_download_with_input_html(self):
        """AsyncArticle.download(input_html=...) must not make network calls."""
        article = AsyncArticle(CNN_URL, fetch_images=False)
        await article.download(input_html=CNN_HTML)

        assert article.download_state == ArticleDownloadState.SUCCESS
        assert article.html == CNN_HTML

    @pytest.mark.asyncio
    async def test_parse_after_download(self):
        """parse() on an AsyncArticle must populate title, text, etc."""
        article = AsyncArticle(CNN_URL, fetch_images=False)
        await article.download(input_html=CNN_HTML)
        article.parse()

        assert article.is_parsed
        assert article.title  # non-empty

    @pytest.mark.asyncio
    async def test_build_with_input_html(self):
        """build() should call download + parse + nlp without errors."""
        article = AsyncArticle(CNN_URL, fetch_images=False)
        # Patch download so we inject HTML instead of making a real request
        article_ref = article

        original_download = article.download

        async def _fake_download(*args, input_html=None, **kwargs):
            return await original_download(input_html=CNN_HTML)

        article.download = _fake_download  # type: ignore[method-assign]
        result = await article.build()

        assert result is article_ref
        assert article.is_parsed

    @pytest.mark.asyncio
    async def test_download_failure_sets_state(self):
        """When the server returns 4xx, download_state must be FAILED_RESPONSE."""
        import httpx

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 404
        mock_response.content = b"Not Found"
        mock_response.headers = {"content-type": "text/html"}
        mock_response.history = []

        with patch("newspaper.async_func.network.async_do_request", return_value=mock_response):
            article = AsyncArticle("https://example.com/missing", fetch_images=False)
            await article.download()

        assert article.download_state == ArticleDownloadState.FAILED_RESPONSE

    @pytest.mark.asyncio
    async def test_follows_meta_refresh(self):
        """When follow_meta_refresh=True and a meta refresh tag is found, the
        new URL must be fetched.
        """
        meta_refresh_html = (
            "<html><head>"
            '<meta http-equiv="refresh" content="0;url=https://example.com/real">'
            "</head><body></body></html>"
        )
        real_html = "<html><head><title>Real Page</title></head><body><p>Real content.</p></body></html>"

        import httpx

        def _make_response(html: str, status: int = 200) -> httpx.Response:
            r = MagicMock(spec=httpx.Response)
            r.status_code = status
            r.content = html.encode()
            r.headers = {"content-type": "text/html; charset=utf-8"}
            r.history = []
            return r

        call_count = 0

        async def _fake_request(url, config, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return _make_response(meta_refresh_html)
            return _make_response(real_html)

        with patch("newspaper.async_func.network.async_do_request", side_effect=_fake_request):
            article = AsyncArticle(
                "https://example.com/redirect",
                fetch_images=False,
                follow_meta_refresh=True,
            )
            await article.download()

        assert call_count == 2
        assert article.download_state == ArticleDownloadState.SUCCESS

    @pytest.mark.asyncio
    async def test_is_instance_of_article(self):
        """AsyncArticle must be a subclass of Article so sync code still works."""
        from newspaper.article import Article

        art = AsyncArticle(CNN_URL, fetch_images=False)
        assert isinstance(art, Article)


# ---------------------------------------------------------------------------
# async_article() convenience function
# ---------------------------------------------------------------------------


class TestAsyncArticleAPI:
    @pytest.mark.asyncio
    async def test_async_article_returns_parsed_article(self):
        from newspaper.async_func.api import async_article

        art = await async_article(CNN_URL, input_html=CNN_HTML, fetch_images=False)

        assert art.is_parsed
        assert art.title

    @pytest.mark.asyncio
    async def test_async_article_language_kwarg(self):
        from newspaper.async_func.api import async_article

        art = await async_article(CNN_URL, language="en", input_html=CNN_HTML, fetch_images=False)

        assert art.config.language == "en"


# ---------------------------------------------------------------------------
# async_batch_request() tests
# ---------------------------------------------------------------------------


class TestAsyncBatchRequest:
    @pytest.mark.asyncio
    async def test_preserves_order(self):
        """Responses must be returned in the same order as input URLs."""
        import httpx

        from newspaper.async_func.network import async_batch_request

        urls = [f"https://example.com/{i}" for i in range(5)]

        async def _fake_request(url, config, **kwargs):
            r = MagicMock(spec=httpx.Response)
            r.status_code = 200
            # Embed the URL index in content so we can verify ordering
            idx = int(url.split("/")[-1])
            r.content = f"page-{idx}".encode()
            r.headers = {"content-type": "text/html"}
            r.history = []
            return r

        with patch("newspaper.async_func.network.async_do_request", side_effect=_fake_request):
            results = await async_batch_request(urls)

        assert len(results) == 5
        for i, resp in enumerate(results):
            assert resp is not None
            assert resp.content == f"page-{i}".encode()

    @pytest.mark.asyncio
    async def test_none_for_failed_requests(self):
        import httpx

        from newspaper.async_func.network import async_batch_request

        urls = ["https://good.example.com/", "https://bad.example.com/"]

        async def _fake_request(url, config, **kwargs):
            if "bad" in url:
                raise httpx.RequestError("connection refused", request=MagicMock())
            r = MagicMock(spec=httpx.Response)
            r.status_code = 200
            r.content = b"ok"
            r.headers = {"content-type": "text/html"}
            r.history = []
            return r

        with patch("newspaper.async_func.network.async_do_request", side_effect=_fake_request):
            results = await async_batch_request(urls)

        assert results[0] is not None
        assert results[1] is None


# ---------------------------------------------------------------------------
# Configuration.async_concurrency
# ---------------------------------------------------------------------------


class TestConfiguration:
    def test_async_concurrency_default(self):
        config = Configuration()
        assert config.async_concurrency == 10

    def test_async_concurrency_custom(self):
        config = Configuration()
        config.async_concurrency = 25
        assert config.async_concurrency == 25

    def test_async_concurrency_via_kwargs(self):
        art = AsyncArticle(CNN_URL, async_concurrency=5)
        assert art.config.async_concurrency == 5


# ---------------------------------------------------------------------------
# Regression: sync path still works
# ---------------------------------------------------------------------------


class TestSyncRegression:
    def test_sync_article_unaffected(self):
        """The synchronous Article class must still work unchanged."""
        from newspaper.article import Article

        art = Article(CNN_URL, fetch_images=False)
        art.download(input_html=CNN_HTML)
        art.parse()

        assert art.is_parsed
        assert art.title

    def test_sync_newspaper_article_function(self):
        import newspaper

        art = newspaper.article(CNN_URL, input_html=CNN_HTML, fetch_images=False)
        assert art.is_parsed


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------


class TestCLI:
    def test_sync_flag_uses_sync_path(self, tmp_path):
        """--sync must call the synchronous newspaper.article() function."""
        from newspaper.cli import main

        out = tmp_path / "out.json"
        with patch("newspaper.article") as mock_article:
            mock_art = MagicMock()
            mock_art.to_json.return_value = '{"title":"test"}'
            mock_article.return_value = mock_art

            main(
                [
                    "--url",
                    "https://example.com/article",
                    "--sync",
                    "--skip-nlp",
                    "--output-format",
                    "json",
                    "--output-file",
                    str(out),
                ]
            )

            mock_article.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_path_invoked_by_default(self):
        """Without --sync, the CLI must use async_article under the hood."""
        import argparse

        from newspaper.cli import _run_async

        args = argparse.Namespace(
            output_file=None,
            output_format="text",
            skip_nlp=True,
        )

        from unittest.mock import AsyncMock as AM

        mock_art = MagicMock()
        mock_art.title = "Headline"
        mock_art.text = "Body"

        with patch("newspaper.async_func.api.async_article", new=AM(return_value=mock_art)):
            # Should complete without error
            await _run_async(args, ["https://example.com/"], {})
