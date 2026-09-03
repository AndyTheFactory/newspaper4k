"""Async Article class for newspaper4k.

:class:`AsyncArticle` subclasses :class:`~newspaper.article.Article` and
replaces only the network-bound methods (``download``) with async equivalents
while reusing the sync parsing, NLP, and extraction logic unchanged.

Requires the ``async`` optional dependency group::

    pip install newspaper4k[async]
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from newspaper.article import Article
from newspaper.utils import extract_meta_refresh

from .network import async_get_html_status

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

    async def _async_get_html_with_status(self, url: str | None = None) -> str | None:
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
                self._set_status_fail(status_code, html, url)
                html = None
        except Exception as exc:
            self._set_fail(exc)
            html = None

        if self.config.follow_meta_refresh and self._recursion_counter < 1 and (new_url := extract_meta_refresh(html)):
            self._recursion_counter += 1
            html = await self._async_get_html_with_status(new_url)
            self.url = new_url
        return html

    # ------------------------------------------------------------------
    # Public async interface
    # ------------------------------------------------------------------

    async def download(  # type: ignore[override]
        self,
        input_html: str | None = None,
        title: str | None = None,
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
            ignore_read_more: When ``True``, the ``read_more_link`` xpath is
                not followed even if set.

        Returns:
            *self* – to allow chaining.
        """
        if html := self._offline_html(self.url, input_html):
            self.html = html
            return self
        self._recursion_counter = 0
        html = await self._async_get_html_with_status()
        if title is not None:
            self.title = title

        if ignore_read_more:
            self.html = html or ""
            return self

        for new_url in self._parse_read_more(html):
            if (html_ := await self._async_get_html_with_status(new_url)) is not None:
                self.html = html_
                self.url = new_url
                log.info(
                    "Downloaded read more link: %s and updated url to %s",
                    new_url,
                    self.url,
                )
                return self

        self.html = html or ""

        return self

    async def build(self) -> AsyncArticle:  # type: ignore[override]
        """Async counterpart of :meth:`Article.build`.

        Downloads, parses, and runs NLP on this article in a single call.
        ``parse()`` and ``nlp()`` are both CPU-bound, so they run in the
        default executor to avoid blocking the event loop (and stalling any
        other articles being downloaded/built concurrently).

        Returns:
            *self* – to allow chaining.
        """
        await self.download()
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self.parse)
        await loop.run_in_executor(None, self.nlp)
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
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self.fetch_images)


__all__ = ["AsyncArticle"]
