from newspaper.article import Article
from newspaper.configuration import Configuration
from newspaper.source import Source


class TestConfiguration:
    # not sure if these tests do verify anything useful
    def test_article_default_params(self):
        a = Article(url="http://www.cnn.com/2013/11/27/travel/weather-thanksgiving/index.html")
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

    def test_article_gets_own_config_copy(self):
        """Articles created from a Source config should each get their own
        config copy so that one article's language detection does not affect
        other articles (regression test for shared-config mutation bug)."""
        source_config = Configuration()
        source_config.language = "en"  # explicitly set, use_meta_language=False

        a1 = Article(url="http://example.com/article1", config=source_config)
        a2 = Article(url="http://example.com/article2", config=source_config)

        # Each article should have its own config copy, not the source config
        assert a1.config is not source_config
        assert a2.config is not source_config
        assert a1.config is not a2.config

        # All start with the same language
        assert a1.config.language == "en"
        assert a2.config.language == "en"

        # Mutating one article's config should not affect the others
        a1.config.language = "zh"

        assert a1.config.language == "zh"
        assert a2.config.language == "en"  # should be unaffected
        assert source_config.language == "en"  # source config should be unaffected

    def test_meta_language_detection_does_not_pollute_sibling_articles(self):
        """When an article auto-detects its language from meta tags
        (use_meta_language=True), the detected language should NOT be applied
        to other articles sharing the original source config."""
        source_config = Configuration()
        # default: use_meta_language=True, language='en'
        assert source_config.use_meta_language is True

        a1 = Article(url="http://example.com/zh/article1", config=source_config)
        a2 = Article(url="http://example.com/zh/article2", config=source_config)

        # Simulate a1 detecting Chinese language from meta tags.
        # Setting config.language also sets use_meta_language=False (see Configuration.language setter).
        a1.meta_lang = "zh"
        if a1.config.use_meta_language:
            a1.config.language = "zh"

        assert a1.config.language == "zh"
        assert a1.config.use_meta_language is False  # set to False by language setter

        # a2 should be unaffected: still has the default use_meta_language=True
        assert a2.config.language == "en"
        assert a2.config.use_meta_language is True

        # The original source config should also be unaffected
        assert source_config.language == "en"
        assert source_config.use_meta_language is True
