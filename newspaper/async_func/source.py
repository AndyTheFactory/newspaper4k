"""Async Source class for newspaper4k.

:class:`AsyncSource` mirrors :class:`~newspaper.source.Source` but
performs all network I/O concurrently using :mod:`newspaper.async_func.network`
and :class:`~newspaper.async_func.article.AsyncArticle`.

Requires the ``async`` optional dependency group::

    pip install newspaper4k[async]
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any
from urllib.parse import urlunsplit

from newspaper.exceptions import RobotsException
from newspaper.settings import NUM_THREADS_PER_SOURCE_WARN_LIMIT
from newspaper.source import Category, Feed, Source

from .article import AsyncArticle
from .network import _get_html_from_httpx_response, async_batch_request, async_do_request, async_get_html

log = logging.getLogger(__name__)


class AsyncSource(Source):
    """An async-capable subclass of :class:`~newspaper.source.Source`.

    All parsing logic is inherited and runs synchronously. Every
    network-bound phase (homepage download, category/feed download, article
    download) is replaced with an async implementation that uses
    :classes:`httpx.AsyncClient` via :mod:`newspaper.async_func.network`.

    Usage::

        import asyncio
        from newspaper.async_func.source import (
            AsyncSource,
        )


        async def main():
            src = AsyncSource(
                "https://www.bbc.com"
            )
            await (
                src.build()
            )
            for article in src.articles[
                :5
            ]:
                print(
                    article.title
                )


        asyncio.run(main())

    Args:
        url (str): Homepage URL of the news source.
        read_more_link (str): Optional xpath selector for "read more" links.
        config (Configuration | None): Configuration object.
        **kwargs: Additional :class:`~newspaper.configuration.Configuration`
            attributes.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the source, forwarding to :class:`Source` and adding an async robots-init lock."""
        super().__init__(*args, **kwargs)
        # Source.__init__ sets self._robots_init_lock to a threading.Lock,
        # which does not support `async with`. AsyncSource needs its own
        # asyncio.Lock for the same purpose (serializing concurrent robots.txt
        # initialization on this instance).
        self._async_robots_init_lock = asyncio.Lock()

    # ------------------------------------------------------------------
    # Internal robot-init helper (async)
    # ------------------------------------------------------------------

    async def _async_init_robots_parser(self) -> None:
        """Async version of :meth:`Source._init_robots_parser`.

        Fetches and parses ``robots.txt`` using the async HTTP client,
        then registers a ``before_request`` hook that enforces the rules
        (via the shared :meth:`Source._register_robots_hook`).
        """
        if not self.config.honor_robots_txt:
            self._robots = None
            self._robots_init_done = True
            return

        robot_url = urlunsplit([self.scheme, self.domain, "robots.txt", "", ""])
        try:
            response = await async_do_request(robot_url, self.config)
            if response.status_code >= 400:
                raise ValueError(f"HTTP {response.status_code} fetching robots.txt")
        except Exception as exc:
            log.warning("Failed to fetch robots.txt from %s: %s", robot_url, exc)
            self._robots = None
            self._robots_init_done = True
            return

        self._register_robots_hook(response.text)
        self._robots_init_done = True

    def __getstate__(self):
        """Return state values to be pickled, excluding the unpicklable asyncio lock."""
        state = super().__getstate__()
        state.pop("_async_robots_init_lock", None)
        return state

    def __setstate__(self, state):
        """Restore state from the unpickled state values and rebuild the asyncio lock."""
        super().__setstate__(state)
        self._async_robots_init_lock = asyncio.Lock()

    # ------------------------------------------------------------------
    # Network-bound methods (async replacements)
    # ------------------------------------------------------------------

    async def download(self, input_html: str | None = None) -> None:  # type: ignore[override]
        """Async download of the source homepage.

        Args:
            input_html: Optional pre-downloaded HTML. When provided no HTTP
                request is made.
        """
        if input_html:
            self.html = input_html
        else:
            self.html = await async_get_html(self.url, self.config)
        self.is_downloaded = True

    async def download_categories(self) -> list[Category]:  # type: ignore[override]
        """Async download of all category pages.

        Returns:
            Filtered list of :class:`~newspaper.source.Category` objects that
            were downloaded successfully.
        """
        category_urls_list = self.category_urls()
        responses = await async_batch_request(category_urls_list, self.config)

        for response, category in zip(responses, self.categories, strict=False):
            if response and response.status_code < 400:
                try:
                    category.html = _get_html_from_httpx_response(response, self.config)
                except RobotsException as exc:
                    log.warning(
                        "download_categories(): Robots.txt blocked URL: %s. %s",
                        category.url,
                        exc,
                    )
                    category.html = None

        self.categories = [c for c in self.categories if c.html]
        return self.categories

    async def download_feeds(self) -> list[Feed]:  # type: ignore[override]
        """Async download of all RSS feed URLs.

        Returns:
            Filtered list of :class:`~newspaper.source.Feed` objects that
            were downloaded successfully.
        """
        feed_urls_list = self.feed_urls()
        responses = await async_batch_request(feed_urls_list, self.config)

        for response, feed in zip(responses, self.feeds, strict=False):
            if response and response.status_code < 400:
                try:
                    feed.rss = _get_html_from_httpx_response(response, self.config)
                except RobotsException as exc:
                    log.warning(
                        "download_feeds(): Robots.txt blocked URL: %s. %s",
                        feed.url,
                        exc,
                    )
                    feed.rss = None

        self.feeds = [f for f in self.feeds if f.rss]
        return self.feeds

    async def download_articles(self) -> list[AsyncArticle]:  # type: ignore[override]
        """Async concurrent download of all articles.

        Replaces the threaded implementation in :meth:`Source.download_articles`
        with fully async I/O bounded by ``config.async_concurrency``.

        Returns:
            List of :class:`~newspaper.async_funcarticle.AsyncArticle` objects that
            were downloaded (successfully or not).
        """
        if self.config.number_threads > NUM_THREADS_PER_SOURCE_WARN_LIMIT:
            log.warning(
                "Using %s+ threads on a single source may result in rate limiting!",
                NUM_THREADS_PER_SOURCE_WARN_LIMIT,
            )

        concurrency = getattr(self.config, "async_concurrency", 10)
        semaphore = asyncio.Semaphore(concurrency)

        async def _download_one(article: AsyncArticle) -> AsyncArticle:
            async with semaphore:
                await article.download()
            return article

        # Convert existing Article objects to AsyncArticle
        async_articles: list[AsyncArticle] = []
        for art in self.articles:
            if isinstance(art, AsyncArticle):
                async_articles.append(art)
            else:
                new_art = AsyncArticle(
                    url=art.url,
                    title=art._title,
                    source_url=art.source_url,
                    read_more_link=art.read_more_link,
                    config=self.config,
                )
                async_articles.append(new_art)

        tasks = [asyncio.ensure_future(_download_one(a)) for a in async_articles]
        self.articles = list(await asyncio.gather(*tasks))
        self.is_downloaded = True
        return self.articles  # type: ignore[return-value]

    # ------------------------------------------------------------------
    # Top-level build (async)
    # ------------------------------------------------------------------

    async def build(  # type: ignore[override]
        self,
        input_html: str | None = None,
        only_homepage: bool = False,
        only_in_path: bool = False,
    ) -> None:
        """Async version of :meth:`Source.build`.

        Downloads and parses the source homepage, discovers category and feed
        URLs, downloads them concurrently, and finally generates the article
        list.  Articles are **not** downloaded here; call
        :meth:`download_articles` afterwards.

        Args:
            input_html: Optional pre-downloaded homepage HTML.
            only_homepage: When ``True``, skip category and feed discovery.
            only_in_path: When ``True``, restrict articles to those whose URL
                path starts with the source URL path.
        """
        async with self._async_robots_init_lock:
            await self._async_init_robots_parser()

        await self.download(input_html=input_html)
        self.parse()

        if only_homepage:
            self.categories = [Category(url=self.url, html=self.html, doc=self.doc)]
        else:
            self.set_categories()
            await self.download_categories()
        self.parse_categories()

        if not only_homepage:
            self.set_feeds()
            await self.download_feeds()

        self.generate_articles(only_in_path=only_in_path)


__all__ = ["AsyncSource"]
