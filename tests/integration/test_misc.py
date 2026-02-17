import newspaper
from newspaper.article import Article
from newspaper.configuration import Configuration
from newspaper.mthreading import fetch_news
from newspaper.network import multithread_request


def test_hot_trending():
    hot_stuff = newspaper.hot()
    assert len(hot_stuff) > 0


def test_multihread_requests(download_urls):
    config = Configuration()
    config.number_threads = 3
    config.thread_timeout_seconds = 15
    config.http_success_only = True
    config.allow_binary_content = True
    results = multithread_request([x["url"] for x in download_urls], config=config)

    assert len(results) == len(download_urls)
    for result, expected in zip(results, download_urls):
        assert result is not None
        assert result.status_code == 200
        if "json" in expected:
            assert result.json() == expected["json"]
        elif "size" in expected:
            assert len(result.content) > expected["size"]


def test_multithread_sources(article_urls, newssites):
    config = Configuration()
    config.memorize_articles = False
    config.fetch_images = False
    config.disable_category_cache = True

    articles = [Article(url=u) for u in article_urls[:3]]

    urls = article_urls[3:]

    papers = [newspaper.build(site, config=config) for site in newssites]
    # Limit nr articles for speed sake
    for paper in papers:
        paper.articles = paper.articles[:20]

    papers.extend(articles)
    papers.extend(urls)

    results = fetch_news(papers, threads=4)

    assert len(results) == len(papers)
    for paper in papers:
        if isinstance(paper, newspaper.Source):
            assert len(paper.articles[-1].html) > 0
