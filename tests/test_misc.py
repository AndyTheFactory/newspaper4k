import os

import pytest

import newspaper
from newspaper.article import Article
from newspaper.configuration import Configuration
from newspaper.mthreading import fetch_news
from newspaper.network import multithread_request


@pytest.fixture
def download_urls():
    return [
        {"url": "http://ipv4.download.thinkbroadband.com/5MB.zip", "size": 5000000},
        {"url": "https://httpbin.org/delay/5", "size": 100},
        {"url": "https://httpbin.org/image/jpeg", "size": 35000},
        {
            "url": "https://freetestdata.com/wp-content/uploads/2023/11/7.7-KB.txt",
            "size": 7700,
        },
        {
            "url": "https://freetestdata.com/wp-content/uploads/2023/11/23KB.txt",
            "size": 23000,
        },
        {
            "url": "https://freetestdata.com/wp-content/uploads/2023/11/40-KB.txt",
            "size": 40000,
        },
        {
            "url": "https://freetestdata.com/wp-content/uploads/2023/11/160-KB.txt",
            "size": 160000,
        },
    ]


@pytest.fixture
def article_urls():
    return [
        "https://edition.cnn.com/travel/air-algeria-airplane-stowaway-critical-condition/index.html",
        "https://edition.cnn.com/videos/us/2023/12/28/man-pulls-gun-on-woman-road-rage-pkg-vpx.knxv",
        "https://www.foxnews.com/us/antisemitism-exposed-hate-soars-on-campus-tennis-legend-weighs-in-on-viral-video",
        "https://www.foxnews.com/media/homeowner-new-florida-bill-close-squatting-loophole-return-some-fairness",
        "https://edition.cnn.com/2023/12/27/middleeast/dutch-diplomat-humanitarian-aid-gaza-sigrid-kaag-intl/index.html",
    ]


@pytest.fixture
def newssites():
    return [
        "http://slate.com",
        "http://techcrunch.com",
        "https://www.euronews.com/just-in",
    ]


def test_hot_trending():
    hot_stuff = newspaper.hot()
    assert len(hot_stuff) > 0


def test_popular_urls():
    popular_urls = newspaper.popular_urls()
    assert len(popular_urls) > 0


def test_languages():
    language_list = newspaper.valid_languages()
    assert len(language_list) > 20


# Skip if GITHUB_ACTIONS
@pytest.mark.skipif("GITHUB_ACTIONS" in os.environ, reason="Skip if GITHUB_ACTIONS")
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


# Skip if GITHUB_ACTIONS. It takes a lot of time
@pytest.mark.skipif("GITHUB_ACTIONS" in os.environ, reason="Skip if GITHUB_ACTIONS")
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
