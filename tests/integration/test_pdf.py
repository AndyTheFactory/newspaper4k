from newspaper import Article


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


def test_pdf_download(pdf_article_fixture):
    article = Article(
        url=pdf_article_fixture,
        allow_binary_content=True,
    )
    article.download()
    assert article.html.startswith("%PDF-") and article.html.strip().endswith("%%EOF")
