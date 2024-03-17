# pytest file for testing the article class
from datetime import datetime
import io
import os
from pathlib import Path
import pickle
import pytest
from dateutil.parser import parse as date_parser
import newspaper
from newspaper import urls
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
    json_content = conftest.get_data("cnn_article", "metadata")

    return {
        "url": url,
        "html_content": html_content,
        "text_content": text_content,
        "summary": json_content["summary"],
        "keywords": json_content["keywords"],
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
    # noqa: E501
    return [
        {
            "url": "https://finance.yahoo.com/m/fd86d317-c06d-351a-ab62-f7f2234ccc35/art-cashin%3A-once-the-10-year.html",
            "selector_button": (
                "//a[contains(text(), 'Continue reading') and contains(@class,"
                " 'caas-button')]"
            ),
            "min_text_length": 1000,
        },
    ]


@pytest.fixture(scope="module")
def known_websites():
    res = []
    for file in [
        "cnn_001",
        "cnn_002",
        "time_001",
        "wired_001",
        "article_with_br",
        "article_with_divs",
        "yna_co_kr",
    ]:
        html = conftest.get_data(file, "html")
        metadata = conftest.get_data(file, "metadata")
        text = conftest.get_data(file, "txt")
        res.append(
            {
                "url": "www.test.com",
                "html": html,
                "text": text,
                "metadata": metadata,
                "file": file,
            }
        )
    return res


@pytest.fixture(scope="module")
def article_video_fixture():
    res = []

    for file in [
        "video_article_01",
        "video_article_02",
    ]:
        html = conftest.get_data(file, "html")
        metadata = conftest.get_data(file, "metadata")
        res.append({"url": "www.test.com", "html": html, "movies": metadata["movies"]})
    return res


@pytest.fixture(scope="module")
def top_image_fixture():
    res = []

    for file in [
        "cnn_001",
        "cnn_002",
    ]:
        html = conftest.get_data(file, "html")
        metadata = conftest.get_data(file, "metadata")
        res.append(
            {"url": "www.test.com", "html": html, "top_image": metadata["top_image"]}
        )
    return res


class TestArticle:
    def test_article(self, cnn_article):
        article = newspaper.Article(cnn_article["url"], fetch_images=False)
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
        article = newspaper.Article(cnn_article["url"], fetch_images=False)
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
        article = newspaper.Article(cnn_article["url"], fetch_images=False)
        article.download(input_html=cnn_article["html_content"])
        article.parse()
        article.nlp()

        assert sorted(article.keywords) == sorted(cnn_article["keywords"])
        assert article.summary.strip() == cnn_article["summary"].strip()

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
        test_file = Path(__file__).resolve().parent / "data/html/cnn_article.html"
        url = "file://" + str(test_file)
        article = Article(url=url)
        article.download()

        assert len(article.html) > 75000
        assert article.download_state == ArticleDownloadState.SUCCESS
        assert article.download_exception_msg is None

    def test_get_video_links(self, article_video_fixture):
        for test_case in article_video_fixture:
            article = Article(url=test_case["url"], fetch_images=False)
            article.download(input_html=test_case["html"])
            article.parse()

            assert sorted(article.movies) == sorted(test_case["movies"])

    def test_get_top_image(self, top_image_fixture):
        for test_case in top_image_fixture:
            article = Article(url=test_case["url"], fetch_images=False)
            article.download(input_html=test_case["html"])
            article.parse()

            assert article.top_image == test_case["top_image"]

    @pytest.mark.skipif("GITHUB_ACTIONS" in os.environ, reason="Skip on Github Actions")
    def test_follow_read_more_button(self, read_more_fixture):
        for test_case in read_more_fixture:
            article = Article(
                url=test_case["url"],
                fetch_images=False,
                read_more_link=test_case["selector_button"],
                browser_user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                    " (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                ),
                header={
                    "Referer": test_case["url"],
                    "Accept": (
                        "text/html,application/xhtml+xml,"
                        "application/xml;q=0.9,image/avif,"
                        "image/webp,image/apng,*/*;q=0.8,"
                        "application/signed-exchange;v=b3;q=0.7"
                    ),
                },
            )
            article.download()
            article.parse()

            assert (
                len(article.text) > test_case["min_text_length"]
            ), f"Button for {test_case['url']} not followed correctly"

    def test_known_websites(self, known_websites):
        errors = {}

        def add_error(file, field):
            if file not in errors:
                errors[file] = []
            errors[file].append(field)

        for test_case in known_websites:
            article = Article(
                url=test_case["url"],
                fetch_images=False,
            )
            article.download(test_case["html"])
            article.parse()
            article.nlp()
            # for now we skip it because it is not reliable
            for k in test_case["metadata"]:
                if k in ["html", "url", "language", "text_cleaned", "images"]:
                    continue
                if k in ["top_img", "meta_img"]:
                    if urls.get_path(getattr(article, k)) != urls.get_path(
                        test_case["metadata"][k]
                    ):
                        add_error(test_case["file"], k)
                    continue
                if k in ["imgs", "images", "movies"]:
                    u1 = [urls.get_path(u) for u in getattr(article, k)]
                    u2 = [urls.get_path(u) for u in test_case["metadata"][k]]
                    if sorted(u1) != sorted(u2):
                        add_error(test_case["file"], k)
                    continue

                if isinstance(getattr(article, k), list):
                    if sorted(getattr(article, k)) != sorted(test_case["metadata"][k]):
                        add_error(test_case["file"], k)
                elif isinstance(getattr(article, k), datetime):
                    if str(getattr(article, k))[:10] != test_case["metadata"][k][:10]:
                        add_error(test_case["file"], k)
                else:
                    if getattr(article, k) != test_case["metadata"][k]:
                        add_error(test_case["file"], k)

        assert len(errors) == 0, f"Test case failed on : {errors}"

    def test_redirect_url(self):
        url = "https://shotcut.in/YrVZ"
        article = Article(url=url)
        article.download()

        assert len(article.history) > 0

    def test_pickle(self, cnn_article):
        article = newspaper.article(
            cnn_article["url"],
            input_html=cnn_article["html_content"],
            fetch_images=False,
        )
        bytes_io = io.BytesIO()
        pickle.dump(article, bytes_io)

        bytes_io.seek(0)

        article_ = pickle.load(bytes_io)
        assert article == article_
