from newspaper.article import Article
from newspaper.source import Source


class TestConfiguration:
    # not sure if these tests do verify anything useful
    def test_article_default_params(self):
        a = Article(
            url="http://www.cnn.com/2013/11/27/travel/weather-thanksgiving/index.html"
        )
        assert "en" == a.config.language
        assert a.config.memorize_articles
        assert a.config.use_meta_language

    def test_article_custom_params(self):
        a = Article(
            url="http://www.cnn.com/2013/11/27/travel/weather-thanksgiving/index.html",
            language="zh",
            memorize_articles=False,
        )
        assert "zh" == a.config.language
        assert not a.config.memorize_articles
        assert not a.config.use_meta_language

    def test_source_default_params(self):
        s = Source(url="http://cnn.com")
        assert "en" == s.config.language
        assert 20000 == s.config.max_file_memo
        assert s.config.memorize_articles
        assert s.config.use_meta_language

    def test_source_custom_params(self):
        s = Source(
            url="http://cnn.com",
            memorize_articles=False,
            max_file_memo=10000,
            language="en",
        )
        assert not s.config.memorize_articles
        assert 10000 == s.config.max_file_memo
        assert "en" == s.config.language
        assert not s.config.use_meta_language
