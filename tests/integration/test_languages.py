import newspaper
from tests import conftest


class TestLanguages:
    def test_language_articles(self, language_article_fixture):
        errors = []
        for filename, url, language in language_article_fixture:
            html_content = conftest.get_data(filename, "html")
            text_content = conftest.get_data(filename, "txt")
            article = newspaper.Article(url, language=language, fetch_images=False)
            article.download(html_content)
            article.parse()

            if article.text.strip() != text_content.strip():
                if filename != "latvian_article":
                    # TODO: Known issue with latvian article.
                    # The first paragraph (leading text) is not being parsed.
                    errors.append(filename)

        assert len(errors) == 0, f"Test failed for {errors}"
