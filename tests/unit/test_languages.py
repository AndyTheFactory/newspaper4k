import pytest

from newspaper.article import Article
from newspaper.configuration import Configuration
from newspaper.text import StopWords
from newspaper.languages import normalize_language_code, ISO639_3_TO_1
from newspaper.extractors.metadata_extractor import MetadataExtractor
import newspaper.parsers as parsers
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

    def test_normalize_language_code(self):
        """Test that ISO 639-3 codes are normalized to ISO 639-1"""
        # Kurdish variants should map to 'ku'
        assert normalize_language_code("ckb") == "ku"
        assert normalize_language_code("kmr") == "ku"
        # Standard 2-char codes should remain unchanged
        assert normalize_language_code("ku") == "ku"
        assert normalize_language_code("en") == "en"
        assert normalize_language_code("ar") == "ar"

    def test_iso639_3_to_1_map_contains_kurdish(self):
        """Test that the mapping contains Kurdish variants"""
        assert "ckb" in ISO639_3_TO_1
        assert "kmr" in ISO639_3_TO_1
        assert ISO639_3_TO_1["ckb"] == "ku"
        assert ISO639_3_TO_1["kmr"] == "ku"

    def test_stopwords_with_kurdish_iso639_3_codes(self):
        """Test that StopWords works with ISO 639-3 Kurdish codes"""
        # All three codes should load the same stopwords
        stopwords_ku = StopWords("ku")
        stopwords_ckb = StopWords("ckb")
        stopwords_kmr = StopWords("kmr")

        assert stopwords_ku.stop_words == stopwords_ckb.stop_words
        assert stopwords_ku.stop_words == stopwords_kmr.stop_words
        assert len(stopwords_ku.stop_words) > 0

    def test_metadata_extractor_kurdish_language_detection(self):
        """Test that MetadataExtractor correctly detects Kurdish ISO 639-3 codes"""
        config = Configuration()
        extractor = MetadataExtractor(config)

        # Test ckb (Central Kurdish/Sorani)
        html_ckb = '<html lang="ckb"><head></head><body></body></html>'
        doc_ckb = parsers.fromstring(html_ckb)
        metadata_ckb = extractor.parse("http://example.com", doc_ckb)
        assert metadata_ckb["language"] == "ku"

        # Test kmr (Northern Kurdish/Kurmanji)
        html_kmr = '<html lang="kmr"><head></head><body></body></html>'
        doc_kmr = parsers.fromstring(html_kmr)
        metadata_kmr = extractor.parse("http://example.com", doc_kmr)
        assert metadata_kmr["language"] == "ku"

        # Test standard ku code still works
        html_ku = '<html lang="ku"><head></head><body></body></html>'
        doc_ku = parsers.fromstring(html_ku)
        metadata_ku = extractor.parse("http://example.com", doc_ku)
        assert metadata_ku["language"] == "ku"
