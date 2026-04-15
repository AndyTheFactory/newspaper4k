"""High-level async API for newspaper4k.

Provides convenience coroutines that mirror the synchronous
:func:`newspaper.article` and :func:`newspaper.build` functions.

Example::

    import asyncio
    from newspaper.async_func.api import (
        async_article,
        async_build,
    )


    async def main():
        # Fetch and parse a single article
        art = await async_article(
            "https://example.com/news/story"
        )
        print(
            art.title,
            art.text[
                :200
            ],
        )

        # Build a news source (homepage only, articles not yet downloaded)
        src = await async_build(
            "https://www.bbc.com"
        )
        await src.download_articles()
        for art in src.articles[
            :3
        ]:
            art.parse()
            print(
                art.title
            )


    asyncio.run(main())

Requires the ``async`` optional dependency group::

    pip install newspaper4k[async]
"""

from __future__ import annotations

from newspaper.configuration import Configuration

from .article import AsyncArticle
from .source import AsyncSource


async def async_article(
    url: str,
    language: str | None = None,
    input_html: str | None = None,
    **kwargs,
) -> AsyncArticle:
    """Async counterpart of :func:`newspaper.article`.

    Downloads and parses a single article from *url*.

    Args:
        url: The article URL.
        language: Two-letter ISO 639-1 language code. When provided it is set
            on the underlying :class:`~newspaper.configuration.Configuration`
            before downloading.
        input_html: Pre-downloaded HTML string. When provided no HTTP request
            is made for the main article page.
        **kwargs: Additional keyword arguments forwarded to
            :class:`~newspaper.async_func.article.AsyncArticle`.

    Returns:
        A fully downloaded and parsed :class:`~newspaper.async_func.article.AsyncArticle`.
    """
    if language is not None:
        kwargs["language"] = language

    article = AsyncArticle(url, **kwargs)
    await article.download(input_html=input_html)
    article.parse()
    return article


async def async_build(
    url: str = "",
    config: Configuration | None = None,
    only_homepage: bool = False,
    only_in_path: bool = False,
    input_html: str | None = None,
    **kwargs,
) -> AsyncSource:
    """Async counterpart of :func:`newspaper.build`.

    Builds a :class:`~newspaper.async_func.source.AsyncSource` by downloading and
    parsing its homepage, discovering categories and RSS feeds, then
    generating the article list.

    Articles are **not** downloaded automatically.  Call
    :meth:`~newspaper.async_func.source.AsyncSource.download_articles` on the
    returned object when you are ready.

    Args:
        url: Homepage URL of the news source.
        config: Optional :class:`~newspaper.configuration.Configuration`.
        only_homepage: When ``True``, skip category/feed discovery.
        only_in_path: When ``True``, restrict articles to those whose URL
            path is under the source URL path.
        input_html: Optional pre-downloaded homepage HTML.
        **kwargs: Additional keyword arguments forwarded to
            :class:`~newspaper.async_func.source.AsyncSource`.

    Returns:
        A built :class:`~newspaper.async_func.source.AsyncSource` with an
        :attr:`~newspaper.async_func.source.AsyncSource.articles` list ready for download.
    """
    config = config or Configuration()
    config.update(**kwargs)

    source = AsyncSource(url, config=config)
    await source.build(
        input_html=input_html,
        only_homepage=only_homepage,
        only_in_path=only_in_path,
    )
    return source


__all__ = ["async_article", "async_build"]
