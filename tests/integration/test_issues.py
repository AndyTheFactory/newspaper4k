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


def test_issue_628_calarasipress_breaking_news_not_extracted():
    """Regression test for https://github.com/AndyTheFactory/newspaper4k/issues/628."""
    html = """
    <html>
      <body>
        <div class="breaking-news">
          <p>Breaking News: oamenii nu au stiut ce se intampla la alarma.</p>
          <p>Banda de breaking news continua cu alte stiri scurte de context.</p>
          <p>Inca un paragraf de tip breaking news care poate domina scorul.</p>
        </div>
        <div class="article-content">
          <p>Acesta este continutul complet al articolului despre alarmele din Calarasi.</p>
          <p>Autoritatile au transmis ulterior ca a fost doar un exercitiu de testare.</p>
        </div>
      </body>
    </html>
    """
    article = Article(
        url="https://calarasipress.ro/au-sunat-alarmele-la-calarasi-oamenii-nu-au-stiut-ce-se-intampla/img_3495/",
        language="ro",
        fetch_images=False,
    )
    article.download(html)
    article.parse()
    assert "continutul complet al articolului" in article.text
    assert "Breaking News" not in article.text
