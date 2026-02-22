import pytest

import newspaper
from newspaper import Source
from newspaper.article import ArticleDownloadState
from newspaper.exceptions import RobotsException


class TestSource:
    def test_download_all_articles(self, cnn_source):
        source = Source(cnn_source["url"], verbose=False, memorize_articles=False)
        source.clean_memo_cache()

        source.html = cnn_source["html_content"]
        source.parse()
        source.set_feeds()
        source.download_feeds()  # mthread

        source.generate_articles(limit=30)
        articles = source.download_articles()

        assert len(articles) == 30
        assert all([a.download_state == ArticleDownloadState.SUCCESS for a in articles])  # noqa: C419

    def test_only_homepage(self, cnn_source):
        source = newspaper.build(
            cnn_source["url"],
            only_homepage=True,
            input_html=cnn_source["html_content"],
            memorize_articles=False,
        )

        assert len(source.articles) > 250

    def test_robots(self, cnn_source):
        config = newspaper.Config()
        # Everyone hates GPT
        config.browser_user_agent = (
            "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; GPTBot/1.0; +https://openai.com/gptbot)"
        )
        source = Source("https://www.cnn.com", verbose=False, memorize_articles=False, config=config)
        source.clean_memo_cache()

        with pytest.raises(RobotsException):
            source.download()
