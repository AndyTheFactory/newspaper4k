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
        {
            "url": "http://echo.jsontest.com/key/value/one/two",
            "json": {"one": "two", "key": "value"},
        },
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
def test_multithread_sources(article_urls):
    config = Configuration()
    config.memorize_articles = False
    config.fetch_images = False
    config.disable_category_cache = True

    slate_paper = newspaper.build("http://slate.com", config=config)
    tc_paper = newspaper.build("http://techcrunch.com", config=config)
    espn_paper = newspaper.build("http://time.com", config=config)

    articles = [Article(url=u) for u in article_urls]

    urls = [
        "https://www.foxnews.com/media/homeowner-new-florida-bill-close-squatting-loophole-return-some-fairness",
        "https://edition.cnn.com/2023/12/27/middleeast/dutch-diplomat-humanitarian-aid-gaza-sigrid-kaag-intl/index.html",
    ]
    # Limit nr articles for speed sake
    slate_paper.articles = slate_paper.articles[:20]
    tc_paper.articles = tc_paper.articles[:20]
    espn_paper.articles = espn_paper.articles[:20]

    papers = [slate_paper, tc_paper, espn_paper]
    papers.extend(articles)
    papers.extend(urls)

    results = fetch_news(papers, threads=4)

    assert len(results) == len(papers)

    assert len(slate_paper.articles[-1].html) > 0
    assert len(espn_paper.articles[-1].html) > 0
    assert len(tc_paper.articles[-1].html) > 0
