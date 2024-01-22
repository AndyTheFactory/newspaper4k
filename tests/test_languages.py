import pytest

import newspaper
from newspaper import nlp
from newspaper.article import Article
from newspaper.text import StopWords
from tests import conftest


@pytest.fixture
def language_article_fixture():
    return [
        (
            "thai_article",
            "https://prachatai.com/journal/2019/01/80642",
            "th",
        ),
        (
            "arabic_article",
            "http://arabic.cnn.com/2013/middle_east/8/2/syria.clashes/index.html",
            "ar",
        ),
        (
            "spanish_article",
            (
                "http://ultimahora.es/mallorca/noticia/noticias/local/fiscal"
                "ia-anticorrupcion-estudia-recurre-imputacion-infanta.html"
            ),
            "es",
        ),
        (
            "chinese_article",
            "http://news.sohu.com/20050601/n225789219.shtml",
            "zh",
        ),
        (
            "japanese_article",
            "https://www.nikkei.com/article/DGXMZO31897660Y8A610C1000000/?n_cid=DSTPCS001",
            "ja",
        ),
        (
            "japanese_article2",
            "http://www.afpbb.com/articles/-/3178894",
            "ja",
        ),
        (
            "chinese_article_001",
            "https://china.chinadaily.com.cn/a/202311/17/WS65571297a310d5acd876f404.html",
            "zh",
        ),
        (
            "chinese_article_002",
            "http://www.news.cn/fortune/2023-11/17/c_1129981476.htm",
            "zh",
        ),
    ]


@pytest.fixture
def valid_language_fixture():
    return newspaper.valid_languages()


@pytest.fixture
def language_text_fixture():
    return {
        "en": {
            "text": conftest.get_data("cnn_article", "txt"),
            "stopwords": 638,
        },
        "th": {
            "text": conftest.get_data("thai_article", "txt"),
            "stopwords": 98,
        },
        "ar": {
            "text": conftest.get_data("arabic_article", "txt"),
            "stopwords": 87,
        },
        "es": {
            "text": conftest.get_data("spanish_article", "txt"),
            "stopwords": 221,
        },
        "zh": {
            "text": conftest.get_data("chinese_article", "txt"),
            "stopwords": 88,
        },
        "ja": {
            "text": conftest.get_data("japanese_article", "txt"),
            "stopwords": 46,
        },
        "ko": {
            "text": conftest.get_data("korean_article", "txt"),
            "stopwords": 122,
        },
        # "hi": {
        #     "text": conftest.get_data("hindi_article", "txt"),
        #     "stopwords": 0,
        # },
    }


class TestLanguages:
    def test_error_unknown_language(self):
        with pytest.raises(ValueError):
            _ = Article("http://www.cnn.com", language="zz")

    @pytest.mark.skip(reason="valid_languages not implemented")
    def test_stopwords_english(self, valid_language_fixture):
        for lang in valid_language_fixture:
            nlp.stopwords = set()
            nlp.load_stopwords(lang)
            assert len(nlp.stopwords) > 100

    def test_full_extract(self, language_article_fixture):
        errors = []
        for filename, url, language in language_article_fixture:
            html_content = conftest.get_data(filename, "html")
            text_content = conftest.get_data(filename, "txt")
            article = newspaper.Article(url, language=language, fetch_images=False)
            article.download(html_content)
            article.parse()

            if article.text.strip() != text_content.strip():
                errors.append(filename)

            # TODO: test text_cleaned

        assert len(errors) == 0, f"Test failed for {errors}"

    def test_stopwords(self, language_text_fixture):
        errors = []
        for lang, text in language_text_fixture.items():
            stopwords = StopWords(lang)

            stat = stopwords.get_stopword_count(text["text"])
            if stat.stop_word_count != text["stopwords"]:
                errors.append(
                    f"Stopwords count for {lang} is {stat.stop_word_count} instead of"
                    f" {text['stopwords']}"
                )

        assert len(errors) == 0, "Errors in Stopwords: \n" + "\n".join(errors)
