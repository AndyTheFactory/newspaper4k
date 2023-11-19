import os
import pytest
from newspaper import Article


@pytest.fixture
def pdf_article_fixture():
    return "https://www.adobe.com/pdf/pdfs/ISO32000-1PublicPatentLicense.pdf"


# Do not run in GitHub Actions
@pytest.mark.skipif(
    "GITHUB_ACTIONS" in os.environ, reason="Do not run in GitHub Actions"
)
def test_pdf_ignore(pdf_article_fixture):
    empty_pdf = "%PDF-"  # empty pdf file
    article = Article(
        url=pdf_article_fixture,
        ignored_content_types_defaults={
            "application/pdf": empty_pdf,
            "application/x-pdf": empty_pdf,
            "application/x-bzpdf": empty_pdf,
            "application/x-gzpdf": empty_pdf,
        },
        allow_binary_content=True,
    )
    article.download()
    assert article.html == empty_pdf


# Do not run in GitHub Actions
@pytest.mark.skipif(
    "GITHUB_ACTIONS" in os.environ, reason="Do not run in GitHub Actions"
)
def test_pdf_download(pdf_article_fixture):
    article = Article(
        url=pdf_article_fixture,
        allow_binary_content=True,
    )
    article.download()
    assert article.html.startswith("%PDF-") and article.html.strip().endswith("%%EOF")
