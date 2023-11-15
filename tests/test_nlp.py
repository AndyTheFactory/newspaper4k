import newspaper


class TestNLP:
    def test_keywords(self):
        a = newspaper.article(
            "https://edition.cnn.com/2016/12/18/politics/bob-gates-rex-tillerson-trump-russia/index.html"
        )
        a.nlp()

        assert len(a.keywords) == a.config.MAX_KEYWORDS
