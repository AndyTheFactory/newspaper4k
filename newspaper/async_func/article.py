"""Async Article class for newspaper4k.

:class:`AsyncArticle` subclasses :class:`~newspaper.article.Article` and
replaces only the network-bound methods (``download``) with async equivalents
while reusing the sync parsing, NLP, and extraction logic unchanged.

Requires the ``async`` optional dependency group::

    pip install newspaper4k[async]
"""

from __future__ import annotations

import logging
from typing import Any
from urllib.parse import urlparse

from newspaper.article import Article, ArticleDownloadState
from newspaper.utils import extract_meta_refresh

from .. import parsers, urls
from .network import async_get_html, async_get_html_status

log = logging.getLogger(__name__)


class AsyncArticle(Article):
    """An :class:`~newspaper.article.Article` subclass with an async download layer.

    All parsing and NLP logic is inherited from :class:`Article` and remains
    synchronous.  Only ``download`` (and by extension ``build``) are
    async methods.

    Usage::

        import asyncio
        from newspaper.async_func.article import (
            AsyncArticle,
        )


        async def main():
            article = AsyncArticle(
                "https://example.com/news/story"
            )
            await article.download()
            article.parse()
            article.nlp()
            print(
                article.title
            )


        asyncio.run(main())

    Args:
        url (str): The article URL.
        *args: Passed through to :class:`Article`.
        **kwargs: Passed through to :class:`Article`.
    """

    def __init__(self, url: str, *args: Any, **kwargs: Any) -> None:
        super().__init__(url, *args, **kwargs)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _async_parse_scheme_http(self, url: str | None = None) -> str | None:
        """Async counterpart of :meth:`Article._parse_scheme_http`.

        Args:
            url: URL to fetch.  Falls back to ``self.url``.

        Returns:
            HTML string, or *None* on error (sets download state accordingly).
        """
        try:
            html, status_code, history = await async_get_html_status(url or self.url, self.config)
            self.history = [str(r.url) for r in history]
            if status_code >= 400:
                self.download_state = ArticleDownloadState.FAILED_RESPONSE
                protection = self._detect_protection(html)
                if protection:
                    self.download_exception_msg = f"Website protected with {protection}, url: {url or self.url}"
                else:
                    self.download_exception_msg = f"Status code {status_code} for url {url or self.url}"
                return None
        except Exception as exc:
            self.download_state = ArticleDownloadState.FAILED_RESPONSE
            self.download_exception_msg = str(exc)
            return None

        return html

    # ------------------------------------------------------------------
    # Public async interface
    # ------------------------------------------------------------------

    async def download(  # type: ignore[override]
        self,
        input_html: str | None = None,
        title: str | None = None,
        recursion_counter: int = 0,
        ignore_read_more: bool = False,
    ) -> AsyncArticle:
        """Async version of :meth:`Article.download`.

        Downloads the article HTML from :attr:`url` using
        :mod:`newspaper.async_func.network`.  All other semantics (meta-refresh
        following, read-more link resolution) mirror the sync implementation.

        Args:
            input_html: Pre-downloaded HTML string. When provided no network
                request is made (unless a read-more link is found).
            title: Force this title instead of parsing it from HTML.
            recursion_counter: Internal counter used to prevent infinite
                meta-refresh loops.
            ignore_read_more: When ``True``, the ``read_more_link`` xpath is
                not followed even if set.

        Returns:
            *self* – to allow chaining.
        """
        if input_html is None:
            parsed_url = urlparse(self.url)
            if parsed_url.scheme == "file":
                html = self._parse_scheme_file(parsed_url.path)
            else:
                html = await self._async_parse_scheme_http()
            if html is None:
                log.debug(
                    "Async download failed on URL %s because of %s",
                    self.url,
                    self.download_exception_msg,
                )
                return self
        else:
            html = input_html

        if self.config.follow_meta_refresh:
            meta_refresh_url = extract_meta_refresh(html)
            if meta_refresh_url and recursion_counter < 1:
                refreshed_html = await async_get_html(meta_refresh_url, self.config)
                return await self.download(
                    input_html=refreshed_html,
                    recursion_counter=recursion_counter + 1,
                )

        if not ignore_read_more and self.read_more_link:
            doc = parsers.fromstring(html)
            for read_more_node in doc.xpath(self.read_more_link):
                if read_more_node.get("href"):
                    new_url = read_more_node.get("href")
                    log.info(
                        "After downloading %s, found read more link: %s",
                        self.url,
                        new_url,
                    )
                    new_url = urls.prepare_url(new_url, self.url)
                    html_ = await self._async_parse_scheme_http(new_url)
                    if html_ is not None:
                        html = html_
                        self.url = new_url
                        log.info(
                            "Downloaded read more link: %s and updated url to %s",
                            new_url,
                            self.url,
                        )
                    else:
                        log.info(
                            "Failed to download read more link: %s, leaving original content in place",
                            new_url,
                        )
                    break

        self.html = html
        if title is not None:
            self.title = title

        return self

    async def build(self) -> AsyncArticle:  # type: ignore[override]
        """Async counterpart of :meth:`Article.build`.

        Downloads, parses, and runs NLP on this article in a single call.

        Returns:
            *self* – to allow chaining.
        """
        await self.download()
        self.parse()
        self.nlp()
        return self

    async def fetch_images_async(self) -> None:
        """Async-compatible image fetching.

        The underlying image validation in
        :class:`~newspaper.extractors.image_extractor.ImageExtractor`
        uses the synchronous ``requests`` session.  This method delegates to
        the synchronous :meth:`Article.fetch_images` to preserve that
        behaviour while keeping the async API consistent.

        If you need fully non-blocking image fetching in the future, override
        this method.
        """
        # Run synchronous image fetch in the default executor to avoid
        # blocking the event loop.
        import asyncio

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.fetch_images)


__all__ = ["AsyncArticle"]
