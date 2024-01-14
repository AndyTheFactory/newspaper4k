import pytest
import newspaper
from tests import conftest


@pytest.fixture(scope="module")
def cnn_article():
    url = (
        "https://edition.cnn.com/2016/12/18/politics/"
        "bob-gates-rex-tillerson-trump-russia/index.html"
    )
    html_content = conftest.get_data("cnn_test_nlp", "html")
    text_content = conftest.get_data("cnn_test_nlp", "txt")

    return {
        "url": url,
        "html_content": html_content,
        "text_content": text_content,
    }


class TestNLP:
    def test_keywords(self, cnn_article):
        a = newspaper.article(
            cnn_article.get("url"),
            language="en",
            input_html=cnn_article.get("html_content"),
            fetch_images=False,
        )
        a.nlp()

        assert len(a.keywords) == a.config.max_keywords
