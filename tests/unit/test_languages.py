import pytest

from newspaper.article import Article
from newspaper.text import StopWords
from tests import conftest


class TestLanguages:
    def test_error_unknown_language(self):
        with pytest.raises(ValueError):
            _ = Article("http://www.cnn.com", language="zz")

    def test_stopwords_languages(self, valid_language_fixture):
        for lang, language_name in valid_language_fixture:
            stopwords = StopWords(lang)
            if lang in [
                "af",
                "et",
                "ha",
                "hy",
                "mn",
                "nl",
                "rn",
                "so",
                "st",
                "te",
                "yo",
                "zu",
            ]:
                # Exceptions
                assert len(stopwords.stop_words) > 25, f"Language {language_name} / {lang} has too few stopwords"
            else:
                assert len(stopwords.stop_words) > 60, f"Language {language_name} / {lang} has too few stopwords"

    def test_stopwords(self, language_text_fixture):
        errors = []
        for lang, text in language_text_fixture.items():
            stopwords = StopWords(lang)

            stat = stopwords.get_stopword_count(text["text"])
            if stat.stop_word_count != text["stopwords"]:
                errors.append(f"Stopwords count for {lang} is {stat.stop_word_count} instead of {text['stopwords']}")

        assert len(errors) == 0, "Errors in Stopwords: \n" + "\n".join(errors)

    def test_bengali(self):
        text = conftest.get_data("bengali_article", "txt")
        stopwords = StopWords("bn")
        stat = stopwords.get_stopword_count(text)

        assert stat.stop_word_count == 22, "Stopwords count for bn is not correct"

    def test_nepali(self):
        text = conftest.get_data("nepali_article", "txt")
        stopwords = StopWords("ne")
        stat = stopwords.get_stopword_count(text)

        assert stat.stop_word_count == 33, "Stopwords count for np is not correct"
