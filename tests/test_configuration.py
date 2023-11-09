from newspaper.article import Article
from newspaper.source import Source


class TestConfiguration:
    # not sure if these tests do verify anything useful
    def test_article_default_params(self):
        a = Article(
            url="http://www.cnn.com/2013/11/27/travel/weather-thanksgiving/index.html"
        )
        assert "en" == a.config.language
        assert a.config.memoize_articles
        assert a.config.use_meta_language

    def test_article_custom_params(self):
        a = Article(
            url="http://www.cnn.com/2013/11/27/travel/weather-thanksgiving/index.html",
            language="zh",
            memoize_articles=False,
        )
        assert "zh" == a.config.language
        assert not a.config.memoize_articles
        assert not a.config.use_meta_language

    def test_source_default_params(self):
        s = Source(url="http://cnn.com")
        assert "en" == s.config.language
        assert 20000 == s.config.MAX_FILE_MEMO
        assert s.config.memoize_articles
        assert s.config.use_meta_language

    def test_source_custom_params(self):
        s = Source(
            url="http://cnn.com",
            memoize_articles=False,
            MAX_FILE_MEMO=10000,
            language="en",
        )
        assert not s.config.memoize_articles
        assert 10000 == s.config.MAX_FILE_MEMO
        assert "en" == s.config.language
        assert not s.config.use_meta_language
