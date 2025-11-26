.. _advanced:

Advanced
========

This section of the docs shows how to do some useful but advanced things
with newspaper.

Multi-threading article downloads
---------------------------------

**Downloading articles one at a time is slow.** But spamming a single news source
like cnn.com with tons of threads or with ASYNC-IO will cause rate limiting
and also doing that can lead to your ip to be blocked by the site.

We solve this problem by allocating 1-2 threads per news source to both greatly
speed up the download time while being respectful.

.. code-block:: python

    import newspaper
    from newspaper.mthreading import fetch_news

    slate_paper = newspaper.build('http://slate.com')
    tc_paper = newspaper.build('http://techcrunch.com')
    espn_paper = newspaper.build('http://espn.com')

    papers = [slate_paper, tc_paper, espn_paper]
    results = fetch_news(papers, threads=4)


    #At this point, you can safely assume that download() has been
    #called on every single article for all 3 sources.

    print(slate_paper.articles[10].tite)
    #'<html> ...'


In addition to :any:`Source` objects, :any:`fetch_news` also accepts :any:`Article` objects or simple urls.

.. code-block:: python

    article_urls = [f'https://abcnews.go.com/US/x/story?id={i}' for i in range(106379500, 106379520)]
    articles = [Article(url=u) for u in article_urls]

    results = fetch_news(articles, threads=4)

    urls = [
        "https://www.foxnews.com/media/homeowner-new-florida-bill-close-squatting-loophole-return-some-fairness",
        "https://edition.cnn.com/2023/12/27/middleeast/dutch-diplomat-humanitarian-aid-gaza-sigrid-kaag-intl/index.html",
    ]

    results = fetch_news(urls, threads=4)

    # or everything at once
    papers = [slate_paper, tc_paper, espn_paper]
    papers.extend(articles)
    papers.extend(urls)

    results = fetch_news(papers, threads=4)


**Note:** in previous versions of newspaper, this could be done with the ``news_pool`` call, but it was not very robust
and was replaced with a ThreadPoolExecutor implementation.

Keeping just the Html of the  main body article
------------------------------------------------

Keeping the html of just an article's body text can be
helpful when you want to retain some formatting information
from the original html. Also, if you want to embed the article
in a Website, which could help with the formatting.

For example, you could:

.. code-block:: python

    import newspaper

    # we are calling the shortcut function ``article()`` which will do the
    # downloading and parsing for us and return an ``Article`` object.

    a = article('http://www.cnn.com/2014/01/12/world/asia/north-korea-charles-smith/index.html')

    print(a.article_html)
    # '<div> \n<p><strong>(CNN)</strong> -- Charles Smith insisted Sunda...'

    # You can also access the article's top node (lxml node) directly

    print(a.top_node)
    # '<Element div at 0x7f2b8c0b6b90>'

    # Additionally we create a sepparate DOM tree with cleaned html.
    # This can be useful in some cases.

    print(a.clean_doc)
    # '<Element html at 0x7f2b8c0b6b90>'

    print(a.clean_top_node)
    # '<Element div at 0x7f2b8c0b6b90>'


Adding new languages
--------------------

At the moment we plan to change (simplify) the way we add new languages to.
If you still want to submit a new language, please follow the instructions below.

**For languages using the Latin characters**, it is pretty basic.
You need to provide a  list of
stopwords in the form of a ``stopwords-<language-code>.txt`` text file.

**For non-latin alphabet languages**, we need a specialized tokenizer, since
*splitting by whitespace simply won't work for
languages like Chinese or Arabic*. For the Chinese language we are using an
additional
open source library called *jieba* to split the text into words.
For arabic we are
using a special nltk tokenizer to do the same job.

**So, to add full text extraction to a new (non-latin) language, we need:**

1. Push up a stopwords file in the format of ``stopwords-<2-char-language-code>.txt``
in ``newspaper/resources/text/.``

2. Provide a way of splitting/tokenizing text in that foreign language into words.

**For latin languages:**

1. Push up a stopwords file in the format of ``stopwords-<2-char-language-code>.txt``
in ``newspaper/resources/text/.`` and we are done!


Explicitly building a news source
---------------------------------

Instead of using the ``newspaper.build(..)`` api, we can take one step lower
into newspaper's ``Source`` api.

.. code-block:: python

    from newspaper import Source
    cnn_paper = Source('http://cnn.com')

    print(cnn_paper.size()) # no articles, we have not built the source
    # 0

    cnn_paper.build()
    print(cnn_paper.size())
    # 3100

Note the ``build()`` method above. The code above is equivalent to the
following sequence of calls:

.. code-block:: python

    cnn_paper = Source('http://cnn.com')

    # These calls are taken care in build() :
    cnn_paper.download()
    cnn_paper.parse()
    cnn_paper.set_categories()
    cnn_paper.download_categories()
    cnn_paper.parse_categories()
    cnn_paper.set_feeds()
    cnn_paper.download_feeds()
    cnn_paper.generate_articles()

    print(cnn_paper.size())
    # 3100


Parameters and Configurations
-----------------------------

Newspaper provides two api's for users to configure their :any:`Article` and
:any:`Source` objects. One is via named parameter passing **recommended** and
the other is via :any:`Configuration` objects.
Any property of the Configuration can be passed as parameter to the ``article()``
function, ``Article``  object's constructor or ``Source`` object's constructor.

Here are some parameter passing examples:

.. code-block:: python

    import newspaper
    from newspaper import Article, Source

    cnn = newspaper.build('http://cnn.com', language='en', memorize_articles=False)

    article = Article(url='http://cnn.com/french/...', language='fr', fetch_images=False)

    cnn = Source(url='http://latino.cnn.com/...', language='es', request_timeout=10,
                                                                number_threads=20)


Here are some examples of how to use the :any:`Configuration` object.

.. code-block:: python

    import newspaper
    from newspaper impo, Article, Source

    config = Config()
    config.memorize_articles = False
    config.language = 'en'
    config.proxies = {'http': '192.168.1.100:8080',
                        'https': '192.168.1.100:8080'}

    cbs_paper = newspaper.build('http://cbs.com', config=config)

    article_1 = Article(url='http://espn/2013/09/...', config=config)

    cbs_paper = Source('http://cbs.com', config=config)

The full available options are available under the :any:`Configuration` section


Caching
-------

The Newspaper4k library provides a simple caching mechanism that can be used to avoid repeatedly downloading the same article. Additionally, when building an :any:`Source` object, the category url detection is cached for 24 hours.

Both mechanisms are enabled by default. The article caching is controlled by the ``memorize_articles`` parameter in the :any:`newspaper.build()` function or, alternatively, when creating an :any:`Source` object, the ``memorize_articles`` parameter in the constructor. Setting it to ``False`` will disable the caching mechanism.

The category detection caching is controlled by `utils.cache_disk.enabled` setting. This disables the caching decorator on the ``Source._get_category_urls(..)`` method.

For example:

.. code-block:: python

    import newspaper
    from newspaper import utils

    cbs_paper = newspaper.build('http://cbs.com')

    # Disable article caching
    utils.cache_disk.enabled = False

    cbs_paper2 = newspaper.build('http://cbs.com') # The categories will be re-detected

    # Enable article caching
    utils.cache_disk.enabled = True

    cbs_paper3 = newspaper.build('http://cbs.com') # The cached category urls will be loaded



Proxy Usage
--------------

Often times websites block repeated access from a single IP address. Or, some websites might limit access from certain geographic locations (due to legal reasons, etc.). To bypass these restrictions, you can use a proxy. Newspaper supports using a proxy by passing the ``proxies`` parameter to the :any:`Article` object's constructor or :any:`Source` object's constructor. The ``proxies`` parameter should be a dictionary, as required by the ``requests library``,  with the following format:

.. code-block:: python

    from newspaper import Article

    # Define your proxy
    proxies = {
        'http': 'http://your_http_proxy:port',
        'https': 'https://your_https_proxy:port'
    }

    # URL of the article you want to scrape
    url = 'https://abcnews.go.com/Technology/wireStory/indonesias-mount-marapi-erupts-leading-evacuations-reported-casualties-106358667'

    # Create an Article object, passing the proxies parameter
    article = Article(url, proxies=proxies)

    # Download and parse the article
    article.download()
    article.parse()

    # Access the article's text, keywords, and summary
    print("Title:", article.title)
    print("Text:", article.text)

or the shorter version:

.. code-block:: python

    from newspaper import article

    # Define your proxy
    proxies = {
        'http': 'http://your_http_proxy:port',
        'https': 'https://your_https_proxy:port'
    }

    # URL of the article you want to scrape
    url = 'https://abcnews.go.com/Technology/wireStory/indonesias-mount-marapi-erupts-leading-evacuations-reported-casualties-106358667'

    # Create an Article object,
    article = article(url, proxies=proxies)

    # Access the article's text, keywords, and summary
    print("Title:", article.title)
    print("Text:", article.text)


Google News Integration
-----------------------

Newspaper4k provides integration with Google News through the :any:`GoogleNewsSource` class.
This allows you to fetch and process news articles from Google News based on keywords,
topics, locations, or time periods.

.. warning::

    This feature depends on scraping Google News, which can be unstable.
    Google frequently changes their HTML structure and URL encoding schemes,
    which may cause this functionality to break without notice. Use this
    feature with the understanding that it may require updates to keep working.

Installation
^^^^^^^^^^^^

To use the Google News integration, you need to install the ``gnews`` package.
You can install it as an optional dependency of newspaper4k:

.. code-block:: bash

    pip install newspaper4k[gnews]

Or install all optional dependencies:

.. code-block:: bash

    pip install newspaper4k[all]

Alternatively, you can install ``gnews`` as a standalone package:

.. code-block:: bash

    pip install gnews

Basic Usage
^^^^^^^^^^^

The :any:`GoogleNewsSource` class provides an interface compatible with the
:any:`Source` class, but fetches articles from Google News instead of a specific
news website.

.. code-block:: python

    from newspaper.google_news import GoogleNewsSource

    # Create a Google News source
    google_news = GoogleNewsSource(
        country='US',           # Filter by country
        period='7d',            # Get news from the last 7 days
        max_results=10          # Limit the number of results
    )

    # Build the source with top news
    google_news.build(top_news=True)

    # Access the articles
    for article in google_news.articles:
        print(f"Title: {article.title}")
        print(f"URL: {article.url}")
        print(f"Summary: {article.summary}")
        print("-" * 40)

Searching by Keyword
^^^^^^^^^^^^^^^^^^^^

You can search for news articles by keyword:

.. code-block:: python

    from newspaper.google_news import GoogleNewsSource

    google_news = GoogleNewsSource(max_results=10)

    # Search for articles about 'artificial intelligence'
    google_news.build(top_news=False, keyword='artificial intelligence')

    for article in google_news.articles:
        print(f"Title: {article.title}")
        print(f"URL: {article.url}")

Filtering by Topic or Location
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can also filter articles by topic or location:

.. code-block:: python

    from newspaper.google_news import GoogleNewsSource

    # Get news by topic
    google_news = GoogleNewsSource(max_results=10)
    google_news.build(top_news=False, topic='TECHNOLOGY')

    # Get news by location
    google_news_local = GoogleNewsSource(max_results=10)
    google_news_local.build(top_news=False, location='New York')

Filtering by Date Range
^^^^^^^^^^^^^^^^^^^^^^^

You can specify a date range for the news articles:

.. code-block:: python

    from datetime import datetime
    from newspaper.google_news import GoogleNewsSource

    google_news = GoogleNewsSource(
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 1, 31),
        max_results=20
    )
    google_news.build(top_news=True)

Downloading and Parsing Articles
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

After building the Google News source, you can download and parse the full
article content:

.. code-block:: python

    from newspaper.google_news import GoogleNewsSource

    google_news = GoogleNewsSource(max_results=5)
    google_news.build(top_news=True)

    # Download all articles (using multithreading)
    google_news.download_articles()

    # Parse and access full content
    for article in google_news.articles:
        article.parse()
        print(f"Title: {article.title}")
        print(f"Authors: {article.authors}")
        print(f"Text: {article.text[:500]}...")
        print("=" * 40)

Available Parameters
^^^^^^^^^^^^^^^^^^^^

The :any:`GoogleNewsSource` class accepts the following parameters:

- ``country`` (str): The country for which to fetch news articles (e.g., 'US', 'GB', 'DE')
- ``period`` (str): Time period for news using Google's time format. Supported time units: ``h`` (hours), ``d`` (days), ``m`` (months), ``y`` (years). Examples: '1h' (1 hour), '1d' (1 day), '7d' (7 days), '1m' (1 month), '1y' (1 year). This parameter is ignored if ``start_date`` or ``end_date`` is provided.
- ``start_date`` (datetime): Start date for filtering articles
- ``end_date`` (datetime): End date for filtering articles
- ``max_results`` (int): Maximum number of articles to fetch (default: 100)
- ``exclude_websites`` (list): List of websites to exclude from results

The ``build()`` method accepts:

- ``top_news`` (bool): Whether to fetch top news (default: True)
- ``keyword`` (str): Search keyword
- ``topic`` (str): Topic filter. Available topics: 'WORLD', 'NATION', 'BUSINESS', 'TECHNOLOGY', 'ENTERTAINMENT', 'SPORTS', 'SCIENCE', 'HEALTH'
- ``location`` (str): Location filter
- ``site`` (str): Specific website to get news from


Cloudscraper Integration
------------------------

Many websites use Cloudflare's protection to prevent automated access. Newspaper4k
integrates with the ``cloudscraper`` library to help bypass some of these protections.

.. note::

    The cloudscraper integration is **automatic**. When the ``cloudscraper`` library
    is installed, newspaper4k will automatically use it for all HTTP requests instead
    of the standard ``requests`` library.

.. warning::

    Not all Cloudflare protections can be bypassed by cloudscraper. Some websites
    use advanced protections (such as CAPTCHAs or JavaScript challenges) that cannot
    be solved automatically. In such cases, you may need to use alternative methods
    like Playwright (see the :ref:`examples` section).

Installation
^^^^^^^^^^^^

To enable cloudscraper support, install it as an optional dependency:

.. code-block:: bash

    pip install newspaper4k[cloudflare]

Or install all optional dependencies:

.. code-block:: bash

    pip install newspaper4k[all]

You can also install cloudscraper directly:

.. code-block:: bash

    pip install cloudscraper

Usage
^^^^^

Once cloudscraper is installed, it will be used automatically. You don't need to
change any code - simply use newspaper4k as you normally would:

.. code-block:: python

    import newspaper

    # This will automatically use cloudscraper if it's installed
    article = newspaper.article('https://example.com/article')

    print(article.title)
    print(article.text)

You can verify that cloudscraper is being used by checking the logs:

.. code-block:: python

    import logging
    import newspaper

    # Enable logging to see which library is being used
    logging.basicConfig(level=logging.INFO)

    article = newspaper.article('https://example.com/article')
    # Look for: "Using cloudscraper for http requests"

Resetting the Session
^^^^^^^^^^^^^^^^^^^^^

If you need to reset the HTTP session (for example, to clear cookies), you can use
the ``reset_session()`` function:

.. code-block:: python

    from newspaper import network

    # Reset the session (will create a new cloudscraper session if available)
    network.reset_session()

Limitations
^^^^^^^^^^^

While cloudscraper can bypass many Cloudflare protections, it has limitations:

- **JavaScript challenges**: Some advanced Cloudflare challenges require a full
  browser environment and cannot be solved by cloudscraper.
- **CAPTCHAs**: If a website presents a CAPTCHA, cloudscraper cannot solve it.
- **Rate limiting**: Cloudflare may still rate-limit requests even with cloudscraper.
- **Frequent updates**: Cloudflare continuously updates its protection mechanisms,
  which may cause cloudscraper to stop working on some sites.

For websites with advanced protections, consider using Playwright or Selenium
to render the page in a real browser environment. See the :ref:`examples` section
for details on using Playwright with newspaper4k.


Cookie Usage (simulate logged in user)
--------------------------------------

TODO
