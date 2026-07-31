from newspaper.article import Article


def test_issue_625_uses_json_ld_article_body_when_dom_text_is_missing():
    html = """
    <html>
      <head>
        <title>BBC News - Sample article</title>
        <meta property="og:title" content="Sample BBC article" />
        <script type="application/ld+json">
          {
            "@context": "https://schema.org",
            "@graph": [
              {
                "@type": "WebPage",
                "name": "Sample BBC article"
              },
              {
                "@type": "NewsArticle",
                "headline": "Sample BBC article",
                "articleBody": [
                  "First paragraph from structured data.",
                  "Second paragraph from structured data."
                ]
              }
            ]
          }
        </script>
      </head>
      <body>
        <main id="root">
          <div data-reactroot="true"></div>
        </main>
      </body>
    </html>
    """

    article = Article("https://www.bbc.com/news/business-67470876", fetch_images=False)
    article.download(input_html=html)
    article.parse()

    assert article.text == (
        "First paragraph from structured data.\n\n"
        "Second paragraph from structured data."
    )
