import pytest
import newspaper
from newspaper import nlp
from newspaper.text import StopWords
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
        "title": (
            "Gates on Tillerson and Russia: 'You can be friendly without being friends'"
        ),
        "summary": [
            (
                "Former Defense Secretary Robert Gates on Sunday defended"
                " President-elect Donald Trump\u2019s pick for secretary of state,"
                " ExxonMobil CEO Rex Tillerson, over his relationship with Russian"
                " President Vladimir Putin."
            ),
            (
                "But being friendly doesn\u2019t make you friends,\u201d Gates said in"
                " an interview on NBC\u2019s \u201cMeet the Press.\u201d Gates\u2019"
                " comments come after he and former Secretary of State Condoleezza Rice"
                " both recommended Tillerson for the job."
            ),
            (
                "Their recommendation has faced scrutiny since Gates and Rice both have"
                " business ties to ExxonMobil through their consulting firm."
            ),
            (
                "Tillerson has faced criticism over his relationship with Putin and"
                " Russia amid the intelligence community\u2019s finding that Russian"
                " hackers stole Democratic emails in a bid to influence the US"
                " election."
            ),
            (
                "But Gates said Tillerson\u2019s business relationship with Putin is"
                " being mistaken for a close personal friendship."
            ),
        ],
    }


@pytest.fixture(scope="module")
def keywords_fixture():
    return dict(
        text="The economy is going to be good. Have a good day. Day by day.",
        keywords=["day", "good"],
    )


class TestNLP:
    def test_article_nlp(self, cnn_article):
        a = newspaper.article(
            cnn_article.get("url"),
            language="en",
            input_html=cnn_article.get("html_content"),
            fetch_images=False,
        )
        a.nlp()

        assert len(a.keywords) == a.config.max_keywords

    def test_keywords(self, keywords_fixture):
        text = keywords_fixture.get("text")
        keywords = keywords_fixture.get("keywords")
        stopwords = StopWords("en")

        keywords_ = nlp.keywords(text, stopwords, 2)

        assert list(keywords_.keys()) == keywords

    def test_summarize(self, cnn_article):
        text = cnn_article.get("text_content")
        title = cnn_article.get("title")
        stopwords = StopWords("en")

        summary = nlp.summarize(title, text, stopwords)

        assert summary == cnn_article.get("summary")
