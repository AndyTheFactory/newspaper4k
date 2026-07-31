from newspaper.article import Article


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
