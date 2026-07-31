import pytest

from newspaper.article import Article


def test_issue_628_calarasipress_breaking_news_not_extracted():
    """Regression test for https://github.com/AndyTheFactory/newspaper4k/issues/628.

    The extractor was selecting content from the 'breaking-news' navigation bar
    instead of the main article body.
    """
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


def test_issue_625_bbc_co_uk_text_extraction():
    """BBC.com is dynamically rendered via JavaScript and returns empty text.

    The suggested workaround is to use bbc.co.uk instead of bbc.com.
    This test verifies that bbc.co.uk articles can be parsed successfully.
    Issue: https://github.com/AndyTheFactory/newspaper4k/issues/625
    """
    urls = [
        "https://www.bbc.co.uk/news/articles/c9d00x5xgxyo",
        "https://www.bbc.co.uk/news/business-67470876",
    ]
    for url in urls:
        article = Article(url=url, fetch_images=False)
        article.download()
        article.parse()

        assert len(article.text) > 200, (
            f"BBC article text for {url} is too short: {article.text!r}"
        )
        assert article.title, f"BBC article title for {url} is empty"


def test_issue_375_medium_multiple_sections():
    """Medium.com articles were only returning the first <section> of content.

    The parser stopped at the first <section> tag and ignored subsequent ones,
    caused by how <section> elements were handled in parsers.py.
    Issue: https://github.com/AndyTheFactory/newspaper4k/issues/375
    """
    html = """
    <html>
    <body>
      <article>
        <section>
          <p>This is the first section of the Medium article with some introductory content.</p>
          <p>It contains the first few paragraphs establishing the topic.</p>
        </section>
        <hr/>
        <section>
          <p>This is the second section, which was previously being ignored by the parser.</p>
          <p>It contains important content that should be included in the article text.</p>
        </section>
        <section>
          <p>This is the third section with the concluding thoughts of the article.</p>
          <p>All three sections together form the complete article.</p>
        </section>
      </article>
    </body>
    </html>
    """
    article = Article(
        url="https://medium.com/anthropology-and-algorithms/on-reverse-engineering-d9f5bae87812",
        fetch_images=False,
    )
    article.download(html)
    article.parse()

    assert "first section" in article.text, "First section content missing"
    assert "second section" in article.text, "Second section content missing - parser stopped too early"
    assert "third section" in article.text, "Third section content missing"


def test_issue_203_medium_category_url_parsing():
    """Medium.com publication/category paths like /airbnb-engineering were treated
    as categories rather than article pages, causing them not to load correctly.

    Issue: https://github.com/AndyTheFactory/newspaper4k/issues/203
    """
    html = """
    <html>
    <body>
      <article>
        <h1>Building the Next Generation of Search at Airbnb</h1>
        <section>
          <p>At Airbnb Engineering, we are always looking for new ways to improve search.</p>
          <p>Our latest update introduces machine learning to personalize results for each user.</p>
        </section>
        <section>
          <p>The new algorithm considers factors like user preferences, location, and browsing history.</p>
          <p>Early tests show a 20% improvement in booking conversion rates.</p>
        </section>
      </article>
    </body>
    </html>
    """
    article = Article(
        url="https://medium.com/airbnb-engineering/building-next-gen-search",
        fetch_images=False,
    )
    article.download(html)
    article.parse()

    assert len(article.text) > 100
    assert "Airbnb" in article.text or "search" in article.text.lower()


def test_issue_364_russian_site_top_node_found():
    """Some websites (particularly Russian-language ones) returned empty text because
    the parser could not find a top_node, and parse() ended silently without errors.

    Issue: https://github.com/AndyTheFactory/newspaper4k/issues/364
    """
    html = """
    <html lang="ru">
    <head><meta charset="utf-8"><title>Новости Украины - bin.ua</title></head>
    <body>
      <div class="article-text">
        <p>Это первый параграф статьи о политической ситуации в регионе.</p>
        <p>Во втором параграфе описываются последние события и их последствия для страны.</p>
        <p>В третьем параграфе приводятся комментарии экспертов по данному вопросу.</p>
        <p>Четвёртый параграф содержит дополнительный анализ и выводы по ситуации.</p>
      </div>
    </body>
    </html>
    """
    article = Article(
        url="https://bin.ua/top/247438-yerzac-normandii-kak-medvedchuk-i-ermak-budut.html",
        language="ru",
        fetch_images=False,
    )
    article.download(html)
    article.parse()

    assert article.top_node is not None, "top_node should not be None for this article"
    assert len(article.text) > 50, f"Article text is too short: {article.text!r}"


def test_issue_274_chinese_news_text_extraction():
    """Chinese news articles were returning empty text or top_image.

    Issue: https://github.com/AndyTheFactory/newspaper4k/issues/274
    """
    pytest.importorskip("jieba", reason="jieba is required for Chinese language support; install with: pip install newspaper4k[zh]")
    html = """
    <html lang="zh-CN">
    <head>
        <meta charset="utf-8">
        <title>中国新闻 - 最新资讯</title>
    </head>
    <body>
      <div class="article-body">
        <p>这是一篇关于中国新闻的重要文章，包含了详细的背景信息和分析。</p>
        <p>文章的第二段描述了事件的起因和经过，以及各方的反应。</p>
        <p>第三段提供了专家的分析和对未来发展趋势的预测。</p>
        <p>最后一段总结了整个事件的意义和影响。</p>
      </div>
    </body>
    </html>
    """
    article = Article(
        url="https://www.toutiaoabc.com/index.php?app=news&act=view&nid=697665",
        language="zh",
        fetch_images=False,
    )
    article.download(html)
    article.parse()

    assert len(article.text) > 20, f"Chinese article text is too short: {article.text!r}"


def test_issue_200_chinese_encoding_not_garbled():
    """Chinese web sites were returning garbled/gibberish text instead of proper Chinese characters.

    Issue: https://github.com/AndyTheFactory/newspaper4k/issues/200
    """
    pytest.importorskip("jieba", reason="jieba is required for Chinese language support; install with: pip install newspaper4k[zh]")
    html = """
    <html>
    <head>
        <meta charset="utf-8">
        <title>楼市新闻 - 中文内容</title>
    </head>
    <body>
      <div class="article-content">
        <p>这是一篇关于中国房地产市场的重要文章。市场分析显示当前趋势向好。</p>
        <p>文章详细分析了当前市场趋势和投资机会，数据来源权威可靠。</p>
        <p>专家认为市场将在未来几个月内保持稳定，并给出了具体建议。</p>
      </div>
    </body>
    </html>
    """
    article = Article(
        url="http://news.dichan.sina.com.cn/2018/04/12/1257865.html",
        language="zh",
        fetch_images=False,
    )
    article.download(html)
    article.parse()

    assert len(article.text) > 10, f"Chinese article text is too short: {article.text!r}"
    # Should not contain mojibake (broken encoding indicators)
    assert "\ufffd" not in article.text, "Article text contains replacement characters (encoding error)"
    assert "â€" not in article.text, "Article text contains mojibake"


def test_issue_272_guru99_image_extraction():
    """Images were not being extracted from articles even when present in the HTML.

    Issue: https://github.com/AndyTheFactory/newspaper4k/issues/272
    """
    html = """
    <html>
    <body>
      <article>
        <h1>What is PHP? First PHP Program Tutorial</h1>
        <img src="https://www.guru99.com/images/php-logo.png" alt="PHP Logo" />
        <p>PHP (Hypertext Preprocessor) is a widely used open source general-purpose scripting language.</p>
        <img src="https://www.guru99.com/images/php-example.png" alt="PHP Example" />
        <p>PHP is especially suited for web development and can be embedded into HTML.</p>
        <img src="https://www.guru99.com/images/php-architecture.png" alt="PHP Architecture" />
        <p>PHP scripts are executed on the server, and the result is returned to the browser as plain HTML.</p>
      </article>
    </body>
    </html>
    """
    article = Article(
        url="https://www.guru99.com/what-is-php-first-php-program.html",
        fetch_images=True,
    )
    article.download(html)
    article.parse()

    assert len(article.images) > 0, "No images extracted from article"
    assert len(article.text) > 50


def test_issue_229_multi_article_page_correct_body():
    """On multi-article pages (e.g., LA Times), the parser was selecting the wrong
    article body — typically the second article instead of the first/main one.

    Issue: https://github.com/AndyTheFactory/newspaper4k/issues/229
    """
    html = """
    <html>
    <head><title>A Star Is Born: Maggie Gyllenhaal turns 40 - LA Times</title></head>
    <body>
      <article id="main-article">
        <h1>A Star Is Born: Maggie Gyllenhaal turns 40 today</h1>
        <p>I am not very trusting of directors. I go in with my fists up — or at least
        my cards really close to my chest, because I have been burned before.</p>
        <p>I find that directors have a hard time believing that a young actress is going
        to have an artistic opinion that is worth something.</p>
        <p>This is the main article content about Maggie Gyllenhaal's birthday milestone.</p>
      </article>
      <article id="related-article">
        <h2>Julia Louis-Dreyfus Veep Production Postponed</h2>
        <p>Production on the seventh and final season of HBO's Veep has been postponed.</p>
        <p>This is a different, unrelated article that should NOT be the extracted body.</p>
      </article>
    </body>
    </html>
    """
    article = Article(
        url="http://www.latimes.com/entertainment/la-et-entertainment-news-updates-a-star-is-born-maggie-gyllenhaal-turns-1510554633-htmlstory.html",
        fetch_images=False,
    )
    article.download(html)
    article.parse()

    assert len(article.text) > 50
    # The main article content should be present
    assert "Maggie" in article.text or "directors" in article.text, (
        "Main article content not found in extracted text"
    )


def test_issue_228_subscription_info_not_in_article():
    """Some articles were including irrelevant subscription prompts and notification
    popups in the extracted article text.

    Issue: https://github.com/AndyTheFactory/newspaper4k/issues/228
    """
    html = """
    <html>
    <body>
      <div class="subscription-popup" id="subscribe-overlay">
        Subscribe now to get full access to our content!
        Sign up for our newsletter to stay updated.
        Enable push notifications to never miss a story.
      </div>
      <article class="article-body">
        <p>Local businesses in the Rio Grande Valley are adapting to changing market conditions.</p>
        <p>The report covers the economic impact of recent policy changes on small businesses.</p>
        <p>Community leaders are calling for more investment in local infrastructure.</p>
        <p>The chamber of commerce held its annual meeting to discuss these pressing issues.</p>
      </article>
    </body>
    </html>
    """
    article = Article(
        url="https://www.themonitor.com/news/business/article_2dc1eb58-70fe-11e8-ba6b-7fdacdd2acb6.html",
        fetch_images=False,
    )
    article.download(html)
    article.parse()

    assert len(article.text) > 50
    assert "Subscribe now" not in article.text, "Subscription popup text was included in article"
    assert "Enable push notifications" not in article.text, (
        "Push notification prompt was included in article"
    )


def test_issue_210_economictimes_popup_not_scraped():
    """economictimes.indiatimes.com push notification popup was being scraped
    as the article content instead of the actual article body.

    Issue: https://github.com/AndyTheFactory/newspaper4k/issues/210
    """
    html = """
    <html>
    <body>
      <div id="gcm_webnotification" class="popup">
        Allow notifications from Economic Times?
        <button>Allow</button>
        <button>Block</button>
      </div>
      <div class="artText">
        <p>ICICI Direct has issued a 'Hold' recommendation for LIC Housing Finance
        with a target price of Rs 600.</p>
        <p>The brokerage firm believes the stock has limited upside from current levels.</p>
        <p>The company's quarterly results showed steady performance despite market challenges.</p>
        <p>Analysts cite stable fundamentals and consistent dividend payouts as key positives.</p>
      </div>
    </body>
    </html>
    """
    article = Article(
        url="http://economictimes.indiatimes.com/markets/stocks/recos/hold-lic-housing-finance-target-rs-600-icici-direct/articleshow/63967828.cms",
        fetch_images=False,
    )
    article.download(html)
    article.parse()

    assert "ICICI" in article.text or "LIC" in article.text, (
        "Article text not extracted correctly"
    )
    assert "Allow notifications" not in article.text, (
        "Notification popup text was included in article"
    )


def test_issue_187_jalopnik_notification_popup_not_scraped():
    """Articles with many ads and 'show notifications' popups were being scraped
    as article content instead of the actual article body.

    Issue: https://github.com/AndyTheFactory/newspaper4k/issues/187
    """
    html = """
    <html>
    <body>
      <div class="notification-request js_notification-request">
        <p>jalopnik.com wants to show notifications</p>
        <button class="allow-btn">Allow</button>
        <button class="block-btn">Block</button>
      </div>
      <div class="ad-unit ad-banner">Advertisement content here</div>
      <div class="js_post-content post-content">
        <p>Remote-controlled autonomous cars could be tested on California roads
        following new legislation passed by the state DMV.</p>
        <p>The California Department of Motor Vehicles has approved new rules allowing
        remote operation of driverless vehicles on public roads.</p>
        <p>Companies like Uber and Waymo are expected to benefit from the new
        autonomous vehicle testing regulations.</p>
        <p>The legislation paves the way for broader deployment of self-driving technology.</p>
      </div>
    </body>
    </html>
    """
    article = Article(
        url="https://jalopnik.com/remote-controlled-autonomous-cars-could-be-tested-on-ca-1823276752",
        fetch_images=False,
    )
    article.download(html)
    article.parse()

    assert "autonomous" in article.text.lower() or "California" in article.text, (
        "Article text not extracted correctly"
    )
    assert "wants to show notifications" not in article.text, (
        "Notification popup text was included in article"
    )


def test_issue_161_archive_org_article_parsing():
    """Any attempt to fetch articles archived on archive.org (wayback machine)
    resulted in an empty list or no content being returned.

    The test verifies that the parser can handle the wayback machine's HTML wrapper
    and extract the original article content.
    Issue: https://github.com/AndyTheFactory/newspaper4k/issues/161
    """
    # Simulate the structure of a Wayback Machine archived page
    html = """
    <html>
    <head>
      <title>BBC News - Technology</title>
    </head>
    <body>
      <!-- Wayback Machine toolbar -->
      <div id="wm-ipp-base" class="wb-toolbar">
        <p>Wayback Machine - This page was archived on 2023-11-15.</p>
        <p>Browse other saved snapshots of this page.</p>
      </div>
      <!-- Original article content -->
      <div id="content">
        <article>
          <h1>Technology article title from the archived page</h1>
          <p>This is the main content of the original article that was archived
          on the Wayback Machine for historical preservation.</p>
          <p>The article discusses recent technology developments and their impact
          on society and industry practices worldwide.</p>
          <p>Further details are provided about the specific technology trends
          and what experts predict for the future of the field.</p>
        </article>
      </div>
    </body>
    </html>
    """
    article = Article(
        url="https://web.archive.org/web/20231115000000/https://www.bbc.com/news/technology-67410220",
        fetch_images=False,
    )
    article.download(html)
    article.parse()

    assert len(article.text) > 100, (
        f"Article text from archived page is too short: {article.text!r}"
    )
    # Wayback toolbar content should not dominate the output
    assert "Wayback Machine" not in article.text or len(article.text) > 200


def test_issue_115_independent_co_uk_text_extraction():
    """Incorrect text was being extracted from The Independent (independent.co.uk) articles.

    Issue: https://github.com/AndyTheFactory/newspaper4k/issues/115
    """
    html = """
    <html>
    <body>
      <div class="article__body-content">
        <p>The UK budget deficit has narrowed thanks to higher tax receipts and lower spending,
        according to official figures released by the Office for National Statistics.</p>
        <p>The ONS said the public sector borrowed £52.3bn in the financial year to date,
        which was £9.2bn less than the same period last year.</p>
        <p>The improvement was boosted by strong income tax and corporation tax receipts,
        reflecting the resilience of the UK labour market and corporate sector.</p>
        <p>Chancellor Philip Hammond will update his fiscal forecasts in the Autumn Budget,
        where economists expect him to announce modest improvements to the public finances.</p>
      </div>
      <div class="related-articles">
        <p>Related: Other stories from The Independent</p>
        <p>More breaking news from around the UK</p>
      </div>
    </body>
    </html>
    """
    article = Article(
        url="http://www.independent.co.uk/news/business/news/uk-budget-deficit-brexit-interest-rates-economy-government-bank-england-a7852436.html",
        fetch_images=False,
    )
    article.download(html)
    article.parse()

    assert "budget deficit" in article.text or "ONS" in article.text, (
        "Main article content not found in extracted text"
    )
    assert len(article.text) > 100


def test_issue_109_cnn_full_article_no_truncation():
    """CNN articles were only returning the first few paragraphs, sometimes
    ending with 'Read More' instead of the full article content.

    Issue: https://github.com/AndyTheFactory/newspaper4k/issues/109
    """
    html = """
    <html>
    <body>
      <section id="body-text">
        <div class="zn-body__paragraph">
          President Trump's executive order barring entry by citizens from seven Muslim-majority countries
          sparked widespread protests at airports across the United States.
        </div>
        <div class="zn-body__paragraph">
          Federal judges in several states issued temporary stays against the order,
          creating legal uncertainty about its scope and enforcement.
        </div>
        <div class="zn-body__paragraph">
          The American Civil Liberties Union and other civil rights groups have filed
          lawsuits challenging the constitutionality of the travel ban.
        </div>
        <div class="zn-body__paragraph">
          Immigration lawyers worked around the clock at airports to help travelers
          who were detained or turned away under the new executive order.
        </div>
        <div class="zn-body__paragraph">
          The State Department said it had provisionally revoked visas for between
          60,000 and 100,000 people from the seven affected countries.
        </div>
      </section>
    </body>
    </html>
    """
    article = Article(
        url="http://www.cnn.com/2017/01/30/politics/trump-immigration-ban-refugees-trnd/index.html",
        fetch_images=False,
    )
    article.download(html)
    article.parse()

    assert len(article.text) > 200, (
        f"CNN article text is too short (was truncated): {article.text!r}"
    )
    assert "Read More" not in article.text, "Article ends with 'Read More' instead of full content"


def test_issue_106_buzzfeed_article_extraction():
    """BuzzFeed articles were not being extracted correctly due to the site's
    listicle/subbuzz HTML structure.

    Issue: https://github.com/AndyTheFactory/newspaper4k/issues/106
    """
    html = """
    <html>
    <body>
      <article>
        <h1>29 Absolutely Vital Pictures Of Puppies</h1>
        <div class="subbuzz__description">
          <p>These adorable dogs need your complete and undivided attention right now.</p>
        </div>
        <div class="subbuzz__description">
          <p>This golden retriever puppy is absolutely perfect in every single way.</p>
          <p>Just look at those tiny paws and that fluffy golden fur.</p>
        </div>
        <div class="subbuzz__description">
          <p>This corgi puppy has mastered the art of looking impossibly adorable.</p>
          <p>Science simply cannot explain this extraordinary level of cuteness.</p>
        </div>
        <div class="subbuzz__description">
          <p>Meanwhile, this dalmatian puppy is proving spots are always in fashion.</p>
          <p>A true fashion icon of the canine world.</p>
        </div>
      </article>
    </body>
    </html>
    """
    article = Article(
        url="https://www.buzzfeed.com/kaelintully/29-absolutely-vital-pictures-of-puppies",
        fetch_images=False,
    )
    article.download(html)
    article.parse()

    assert len(article.text) > 50, (
        f"BuzzFeed article text is too short: {article.text!r}"
    )
    assert "puppy" in article.text.lower() or "puppies" in article.text.lower()
