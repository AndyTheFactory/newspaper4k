import newspaper
from newspaper import nlp
from newspaper.text import StopWords


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

    def test_summarize(self, cnn_article_with_nlp):
        text = cnn_article_with_nlp.get("text_content")
        title = cnn_article_with_nlp.get("title")
        stopwords = StopWords("en")

        summary = nlp.summarize(title, text, stopwords)

        assert summary == cnn_article_with_nlp.get("summary")
