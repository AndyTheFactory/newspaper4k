import os
import pytest
import newspaper
from newspaper.configuration import Configuration


def test_hot_trending():
    hot_stuff = newspaper.hot()
    assert len(hot_stuff) > 0


def test_popular_urls():
    popular_urls = newspaper.popular_urls()
    assert len(popular_urls) > 0


def test_languages():
    newspaper.languages()


# Skip if GITHUB_ACTIONS
@pytest.mark.skipif("GITHUB_ACTIONS" in os.environ, reason="Skip if GITHUB_ACTIONS")
def test_multithread_download():
    config = Configuration()
    config.memorize_articles = False
    slate_paper = newspaper.build("http://slate.com", config=config)
    tc_paper = newspaper.build("http://techcrunch.com", config=config)
    espn_paper = newspaper.build("http://time.com", config=config)

    papers = [slate_paper, tc_paper, espn_paper]
    for paper in papers:
        paper.articles = paper.articles[:20]
    newspaper.news_pool.set(papers, threads_per_source=2)

    newspaper.news_pool.join()

    assert len(slate_paper.articles[-1].html) > 0
    assert len(espn_paper.articles[-1].html) > 0
    assert len(tc_paper.articles[-1].html) > 0
