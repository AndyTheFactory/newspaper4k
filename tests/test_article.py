# pytest file for testing the article class
import os
from pathlib import Path
import pytest
from dateutil.parser import parse as date_parser
import newspaper
from newspaper.article import Article, ArticleDownloadState, ArticleException
from newspaper.configuration import Configuration
import tests.conftest as conftest


@pytest.fixture(scope="module")
def cnn_article():
    url = (
        "http://www.cnn.com/2013/11/27/travel/weather-"
        "thanksgiving/index.html?iref=allsearch"
    )
    html_content = conftest.get_data("cnn_article", "html")
    text_content = conftest.get_data("cnn_article", "txt")

    return {
        "url": url,
        "html_content": html_content,
        "text_content": text_content,
    }


@pytest.fixture(scope="module")
def meta_refresh():
    return [
        (conftest.get_data("google_meta_refresh", "html"), "Example Domain"),
        (
            conftest.get_data("ap_meta_refresh", "html"),
            "News from The Associated Press",
        ),
    ]


@pytest.fixture(scope="module")
def read_more_fixture():
    return [
        {
            "url": "https://finance.yahoo.com/m/ac9f22c5-6308-3ffa-96de-294c2817fd93/3-social-security-mistakes-to.html",
            "selector_button": (
                "//a[contains(text(), 'Continue reading') and contains(@class,"
                " 'caas-button')]"
            ),
            "min_text_length": 1000,
        },
    ]


class TestArticle:
    def test_article(self, cnn_article):
        article = newspaper.Article(cnn_article["url"])
        article.download(input_html=cnn_article["html_content"])
        article.parse()
        assert article.url == cnn_article["url"]
        assert article.download_state == ArticleDownloadState.SUCCESS
        assert article.download_exception_msg is None
        assert len(article.html) == 75404

        assert article.text.strip() == cnn_article["text_content"].strip()
        assert (
            article.title
            == "After storm, forecasters see smooth sailing for Thanksgiving"
        )
        assert article.authors == [
            "Dana A. Ford",
            "James S.A. Corey",
            "Chien-Ming Wang",
            "Tom Watkins",
        ]
        assert (
            article.publish_date - date_parser("2013-11-27T00:00:00Z", ignoretz=True)
        ).days == 0
        assert (
            article.top_image
            == "http://i2.cdn.turner.com/cnn/dam/assets/131129200805-01-weather-1128-story-top.jpg"
        )
        assert article.movies == []
        assert article.keywords == []
        assert article.meta_keywords == [
            "winter storm",
            "holiday travel",
            "Thanksgiving storm",
            "Thanksgiving winter storm",
        ]
        assert article.meta_lang == "en"
        assert (
            article.meta_description
            == "A strong storm struck much of the eastern United "
            "States on Wednesday, complicating holiday plans for many "
            "of the 43 million Americans expected to travel."
        )

    def test_call_parse_before_download(self):
        article = newspaper.Article("http://www.cnn.com")
        with pytest.raises(ArticleException):
            article.parse()

    def test_call_nlp_before_download(self):
        article = newspaper.Article("http://www.cnn.com")
        with pytest.raises(ArticleException):
            article.nlp()

    def test_call_nlp_before_parse(self, cnn_article):
        article = newspaper.Article(cnn_article["url"])
        article.download(input_html=cnn_article["html_content"])
        with pytest.raises(ArticleException):
            article.nlp()

    def test_meta_refresh(self, meta_refresh):
        config = Configuration()
        config.follow_meta_refresh = True
        article = Article("", config=config)
        for html, title in meta_refresh:
            article.download(input_html=html)
            article.parse()
            assert article.title == title

    def test_article_nlp(self, cnn_article):
        article = newspaper.Article(cnn_article["url"])
        article.download(input_html=cnn_article["html_content"])
        article.parse()
        article.nlp()

        summary = conftest.get_data("cnn_summary", "txt")
        summary = summary.strip()

        assert sorted(article.keywords) == sorted(
            [
                "balloons",
                "delays",
                "flight",
                "forecasters",
                "good",
                "sailing",
                "smooth",
                "storm",
                "thanksgiving",
                "travel",
                "weather",
                "winds",
                "york",
            ]
        )
        assert article.summary.strip() == summary

    def test_download_inexisting_file(self):
        url = "file://" + str(
            Path(__file__).resolve().parent / "data/html/does_not_exist.html"
        )
        article = Article(url=url)
        article.download()
        assert article.download_state == ArticleDownloadState.FAILED_RESPONSE
        assert article.download_exception_msg == "No such file or directory"
        assert article.html == ""

    def test_download_file_schema(self):
        url = "file://" + str(
            Path(__file__).resolve().parent / "data/html/cnn_article.html"
        )
        article = Article(url=url)
        article.download()

        assert len(article.html) == 75404
        assert article.download_state == ArticleDownloadState.SUCCESS
        assert article.download_exception_msg is None

    @pytest.mark.skipif("GIHUB_ACTIONS" in os.environ, reason="Skip on Github Actions")
    def test_follow_read_more_button(self, read_more_fixture):
        for test_case in read_more_fixture:
            article = Article(
                url=test_case["url"], read_more_link=test_case["selector_button"]
            )
            article.download()
            article.parse()

            assert (
                len(article.text) > test_case["min_text_length"]
            ), f"Button for {test_case['url']} not followed correctly"
