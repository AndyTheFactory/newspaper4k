.. _examples:

Examples and Tutorials
======================


1. Building and Crawling a News Sources using a Multithreaded approach
----------------------------------------------------------------------
Building and crawling news websites can require the handling of multiple sources simultaneously and processing a large volume of articles. You can significantly improve the performance of this process by using multiple threads when crawling. Even if Python is not truly multithreaded (due to the GIL), i/o requests can be handled in parallel.


.. code-block:: python


    from newspaper import Source
    from newspaper.mthreading import fetch_news
    import threading

    class NewsCrawler:

        def __init__(self, source_urls, config=None):
            self.sources = [Source(url, config=config) for url in source_urls]
            self.articles = []

        def build_sources(self):
            # Multithreaded source building
            threads = [threading.Thread(target=source.build) for source in self.sources]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()

        def crawl_articles(self):
            # Multithreaded article downloading
            self.articles = fetch_news(self.sources, threads=4)

        def extract_information(self):
            # Extract information from each article
            for source in self.sources:
                print(f"Source {source.url}")
                for article in source.articles[:10]:
                    article.parse()
                    print(f"Title: {article.title}")
                    print(f"Authors: {article.authors}")
                    print(f"Text: {article.text[:150]}...")  # Printing first 150 characters of text
                    print("-------------------------------")

    if __name__ == "__main__":
        source_urls = ['https://slate.com', 'https://time.com']  # Add your news source URLs here
        crawler = NewsCrawler(source_urls)
        crawler.build_sources()
        crawler.crawl_articles()
        crawler.extract_information()


2. Getting Articles with Scrapy
--------------------------------

Install Necessary Packages
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    pip install scrapy
    pip install newspaper4k

Create the scrapy project:

.. code-block:: bash

    scrapy startproject news_scraper

This command creates a new folder news_scraper with the necessary Scrapy files.


Code the Scrapy Spider
^^^^^^^^^^^^^^^^^^^^^^
Navigate to the news_scraper/spiders folder and create a new spider. For example, news_spider.py:

    .. code-block:: python

        import scrapy
        import newspaper

        class NewsSpider(scrapy.Spider):
            name = 'news'
            start_urls = ['https://abcnews.go.com/elections']  # Replace with your target URLs

            def parse(self, response):
                # Extract URLs from the response and yield Scrapy Requests
                for href in response.css('a::attr(href)'):
                    yield response.follow(href, self.parse_article)

            def parse_article(self, response):
                # Use Newspaper4k to parse the article
                article = newspaper.article(response.url, language='en', input_html=response.text)
                article.parse()
                article.nlp()

                # Extracted information
                yield {
                    'url': response.url,
                    'title': article.title,
                    'authors': article.authors,
                    'text': article.text,
                    'publish_date': article.publish_date,
                    'keywords': article.keywords,
                    'summary': article.summary,
                }


Run the Spider
^^^^^^^^^^^^^^

.. code-block:: bash

    scrapy crawl news -o output.json


3. Using Playwright to Scrape Websites built with Javascript
-------------------------------------------------------------

Install Necessary Packages
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    pip install newspaper4k
    pip install playwright
    playwright install

Scrape with Playwright
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    from playwright.sync_api import sync_playwright
    import newspaper
    import time

    def scrape_with_playwright(url):
        # Using Playwright to render JavaScript
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(url)
            time.sleep(1) # Allow the javascript to render
            content = page.content()
            browser.close()

        # Using Newspaper4k to parse the page content
        article = newspaper.article(url, input_html=content, language='en')

        return article

    # Example URL
    url = 'https://ec.europa.eu/commission/presscorner/detail/en/ac_24_84'  # Replace with the URL of your choice

    # Scrape and process the article
    article = scrape_with_playwright(url)
    article.nlp()

    print(f"Title: {article.title}")
    print(f"Authors: {article.authors}")
    print(f"Publication Date: {article.publish_date}")
    print(f"Summary: {article.summary}")
    print(f"Keywords: {article.keywords}")


4. Using Playwright to Scrape Websites that require login
----------------------------------------------------------


.. code-block:: python

    from playwright.sync_api import sync_playwright
    import newspaper

    def login_and_fetch_article(url, login_url, username, password):
        # Using Playwright to handle login and fetch article
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)  # Set headless=False to watch the browser actions
            page = browser.new_page()

            # Automating login
            page.goto(login_url)
            page.fill('input[name="log"]', username)  # Adjust the selector as per the site's HTML
            page.fill('input[name="pwd"]', password)  # Adjust the selector as per the site's HTML
            page.click('input[type="submit"][value="Login"]')  # Adjust the selector as per the site's HTML

            # Wait for navigation after login
            page.wait_for_url('/')
            # Navigating to the article
            page.goto(url)
            content = page.content()
            browser.close()

        # Using Newspaper4k to parse the page content
        article = newspaper.article(url, input_html=content, language='en')

        return article

    # Example URLs and credentials
    login_url = 'https://www.undercurrentnews.com/login/'  # Replace with the actual login URL
    article_url = 'https://www.undercurrentnews.com/2024/01/08/editors-choice-farmed-shrimp-output-to-drop-in-2024-fallout-from-us-expanded-russia-ban/'  # Replace with the URL of the article you want to scrape
    username = 'tester_news'  # Replace with your username
    password = 'test'  # Replace with your password

    # Fetch and process the article
    article = login_and_fetch_article(article_url, login_url, username, password)
    article.nlp()
    print(f"Title: {article.title}")
    print(f"Authors: {article.authors}")
    print(f"Publication Date: {article.publish_date}")
    print(f"Summary: {article.summary}")
    print(f"Keywords: {article.keywords}")


5. Setting a Custom User-Agent and Using fake-useragent
-------------------------------------------------------

Some news websites block requests that use the default user-agent string. You can set a
custom user-agent via the ``browser_user_agent`` parameter to make your requests look like
a regular browser visit.

Simple Custom User-Agent
^^^^^^^^^^^^^^^^^^^^^^^^

Pass ``browser_user_agent`` directly to :any:`newspaper.article`, :any:`Article`, or
:any:`newspaper.build`:

.. code-block:: python

    import newspaper
    from newspaper import Article, Source

    user_agent = (
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/50.0.2661.102 Safari/537.36'
    )

    # Using the shortcut function
    article = newspaper.article(
        'https://www.example.com/some-article',
        browser_user_agent=user_agent,
    )
    print(article.title)

    # Using the Article class directly
    article = Article(
        'https://www.example.com/some-article',
        browser_user_agent=user_agent,
    )
    article.download()
    article.parse()

    # Using newspaper.build for a whole news source
    source = newspaper.build('https://www.example.com', browser_user_agent=user_agent)


Rotating User-Agents with ``fake-useragent``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When scraping many articles or sources, rotating the user-agent string on every
request helps avoid rate-limiting and IP blocks. The `fake-useragent
<https://github.com/fake-useragent/fake-useragent>`_ library provides a simple
way to generate realistic, random user-agent strings.

Install the necessary packages:

.. code-block:: bash

    pip install newspaper4k fake-useragent

The example below creates a helper that picks a fresh random user-agent for each
article download:

.. code-block:: python

    import newspaper
    from newspaper import Article
    from fake_useragent import UserAgent

    ua = UserAgent()

    def download_article(url: str) -> Article:
        """Download and parse a single article with a random user-agent."""
        article = Article(url, browser_user_agent=ua.random)
        article.download()
        article.parse()
        return article

    urls = [
        'https://www.bbc.com/news/world-us-canada-68084247',
        'https://edition.cnn.com/2024/01/15/politics/biden-iowa/index.html',
        'https://www.reuters.com/world/us/',
    ]

    for url in urls:
        art = download_article(url)
        print(f"Title: {art.title}")
        print(f"Authors: {art.authors}")
        print(f"Agent: {art.config.browser_user_agent}")
        print("-" * 60)

You can also rotate the user-agent when building a :any:`Source` or when using
:any:`newspaper.mthreading.fetch_news`:

.. code-block:: python

    import newspaper
    from newspaper import Source
    from newspaper.mthreading import fetch_news
    from fake_useragent import UserAgent

    ua = UserAgent()

    # Give each source its own random user-agent
    source_urls = ['https://slate.com', 'https://time.com', 'https://www.reuters.com']
    sources = [
        Source(url, browser_user_agent=ua.random) for url in source_urls
    ]

    for source in sources:
        source.build()

    # Download all articles across all sources using multiple threads
    fetch_news(sources, threads=4)

    for source in sources:
        for article in source.articles[:3]:
            article.parse()
            print(f"[{source.url}] {article.title}")
