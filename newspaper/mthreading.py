"""
Helper functions for multihtreading news fetching.
"""

from concurrent.futures import ThreadPoolExecutor
from concurrent import futures
import logging
import queue
from typing import AsyncGenerator, Generator, List, Union
import newspaper
from newspaper.article import Article
from newspaper.source import Source
import asyncio


def fetch_news(
    news_list: List[Union[str, Article, Source]], threads: int = 5
) -> Generator[Article | Source, None, None]:
    """
    Fetch news from a list of sources, articles, or both. Threads will be
    allocated to download and parse the sources or articles. If urls are
    passed into the list, then a new `Article` object will be created for
    it and downloaded + parsed.
    There will be no nlp done on the articles.
    If there is a problem in detecting the language of the urls, then instantiate
    the `Article` object yourself with the language parameter and pass it in.

    Args:
        news_list(List[Union[str, Article, Source]]): List of sources,
            articles, urls or a mix of them.

        threads(int):  Number of threads to use for fetching. This affects
            how many items from the news_list are fetched at once. In order to
            control
            how many threads are used in a `Source` object, use the
            `Configuration`.`number_threads` setting. This could result in
            a high number of threads. Maximum number of threads would be
            `threads` * `Configuration`.`number_threads`.
    Returns:
        List[Union[Article, Source]]: List of articles or sources.
    """

    async def get_item(item: Union[str, Article, Source]) -> AsyncGenerator[Article, None]:
        if isinstance(item, Article):
            logging.error(item.title)
            item.download()
            item.parse()
            yield item
        elif isinstance(item, Source):
            logging.error(item.article_urls())
            #item.download_articles()
            #item.parse_articles()
            x = item.stream_articles()
            async for f in x:
                yield f
        elif isinstance(item, str):
            logging.error(str)
            yield newspaper.article(url=item)
        else:
            raise TypeError(f"Invalid type {type(item)} for item {item}")

    logging.error("Called Fetch News")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    with ThreadPoolExecutor(max_workers=threads) as tpe:
        _futures = [tpe.submit(get_item, item) for item in news_list]
        for future in futures.as_completed(_futures):
            logging.error("YIELD")
            result = future.result()
            yield result