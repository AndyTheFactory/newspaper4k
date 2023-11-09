.. _quickstart:

Quickstart
==========

Eager to get started? This page gives a good introduction in how to get started
with newspaper. This assumes you already have newspaper installed. If you do not,
head over to the :ref:`Installation <install>` section.

Building a news source
----------------------

:any:`Source` objects are an abstraction of online news media
websites like CNN or ESPN.
You can initialize them in two *different* ways.

Building a :any:`Source` object for a news site  will extract its categories,
feeds, articles, brand, and description for you.

You may also provide configuration parameters
like ``language``, ``browser_user_agent``, and etc seamlessly.
Navigate to the :ref:`advanced <advanced>` section for details.

.. code-block:: python

    import newspaper
    cnn_paper = newspaper.build('http://cnn.com')

    other_paper = newspaper.build('http://www.lemonde.fr/', language='fr')

However, if needed, you can be more specific in your implementation by using
some advanced features and parameters of the  :any:`Source` object as described
in the :ref:`advanced <advanced>` section.

Extracting articles from a news source
--------------------------------------

Every news source has a set of *recent* articles, mainly present in the
homepage and category pages. The :any:`Source` object will extract references
to these articles and store them in the as a list of :any:`Article` objects in
its :any:`Source.articles` property.

The following examples assume that a news source has been
initialized and built.

.. code-block:: python

    import newspaper
    cnn_paper = newspaper.build('http://cnn.com')

    for article in cnn_paper.articles:
        print(article.url)

    # 'http://www.cnn.com/2013/11/27/justice/tucson-arizona-captive-girls/'
    # 'http://www.cnn.com/2013/12/11/us/texas-teen-dwi-wreck/index.html'
    ...

    print(cnn_paper.size()) # cnn has 3100 articles
    # 3100

Article caching
---------------

By default, newspaper caches all previously extracted articles and **will not
redownload any article which it has already extracted**.

This feature exists to prevent duplicate articles and to increase extraction speed.
For instance, if you run the build command twice on a news source, the second time
it will only download and parse only the new articles:

.. code-block:: python

    cbs_paper = newspaper.build('http://cbs.com')
    cbs_paper.size()
    # 1030

    cbs_paper = newspaper.build('http://cbs.com')
    cbs_paper.size()
    # 2

The return value of ``cbs_paper.size()`` changes from 1030 to 2 because when we first
crawled cbs we found 1030 articles. However, on our second crawl, we eliminate all
articles which have already been crawled.

This means only **2** new articles have been published since our first extraction.

You can disable this feature with setting the ``memoize_articles`` parameter to False.

This can also be achieved by setting the ``memoize_articles`` property of the
:any:`Configuration` object to False. More examples are available in
the :ref:`advanced <advanced>` section.

.. code-block:: python

    import newspaper

    cbs_paper = newspaper.build('http://cbs.com', memoize_articles=False)
    cbs_paper.size()
    # 1030

    cbs_paper = newspaper.build('http://cbs.com', memoize_articles=False)
    cbs_paper.size()
    # 1030


Extracting Source categories
----------------------------

One important feature of the :any:`Source` object is the ability to extract
the website categories from the main page of a news source. This way you can
extract articles from a specific category.

.. code-block:: python

    for category in cnn_paper.category_urls():
         print(category)

    # 'http://lifestyle.cnn.com'
    # 'http://cnn.com/world'
    # 'http://tech.cnn.com'
    ...

Extracting Source feeds
-----------------------

RSS feeds play an important role in the news ecosystem. They allow news to propagate
and be shared across the web. The :any:`Source` object will extract the RSS feeds

.. code-block:: python

    for feed_url in cnn_paper.feed_urls():
        print(feed_url)

    # 'http://rss.cnn.com/rss/cnn_crime.rss'
    # 'http://rss.cnn.com/rss/cnn_tech.rss'
    ...

Extracting Source brand & description
-------------------------------------

You can use the :any:`Source` object to extract the souce's website base
name (e.g. bbc from bbc.co.uk) and its description from known metatags

.. code-block:: python

    print(cnn_paper.brand)
    # 'cnn'

    print(cnn_paper.description)
    # 'CNN.com delivers the latest breaking news and information on the latest...'

Extracting individual News Articles
-----------------------------------

Article objects are abstractions of news articles (news stories).
For example, a news :any:`Source` is CNN (cnn.com), a news article is
a specific link containing a news story, like https://edition.cnn.com/2023/11/09/tech/...
You can use any  :any:`Article` from an existing (and initialized) news :any:`Source`
or use the :any:`Article` object by itself. Just pass in the url to the article,
and call :any:`Article.download()` and :any:`Article.parse()`.
You can also use the shortcut call from newspaper :ref:`newspaper.article()<article shortcut>`
that will create the :any:`Article` object for you, and
call :any:`Article.download()` and :any:`Article.parse()`.

Referencing an article from a :any:`Source` object:

.. code-block:: python

    first_article = cnn_paper.articles[0]

Alternatively, initializing an :any:`Article` object on its own:

.. code-block:: python

    first_article = newspaper.Article(url="http://www.lemonde.fr/...", language='fr')

All the initialization parameters that work for :any:`Source` objects also work for :any:`Article` objects.
There are some differences, however. For example, the ``title`` parameter is available only for :any:`Article` objects.

Ignorig particular content-types for :any:`Source` objects and :any:`Article` objects
-------------------------------------------------------------------------------------

Using the ``ignored_content_types_defaults`` parameter, it is possible to ignore particular content-types
for :any:`Source` objects and :any:`Article` objects. This parameter is also available as a property of the
:any:`Configuration` object.

You cam provide a dictionary of content-types and their placeholder value. Any articles
having that content-type will be ignored and the placeholder value will be used instead of the actual content.

.. code-block:: python

    import newspaper
    pdf_defaults = {"application/pdf": "%PDF-",
                      "application/x-pdf": "%PDF-",
                      "application/x-bzpdf": "%PDF-",
                      "application/x-gzpdf": "%PDF-"}
    pdf_article = newspaper.article(url='https://www.adobe.com/pdf/pdfs/ISO32000-1PublicPatentLicense.pdf',
                                            ignored_content_types_defaults=pdf_defaults)
    print(pdf_article.html)
    # %PDF-

Most important :any:`Article` methods
-------------------------------------

The stages of an :any:`Article` extraction are as follows:

Downloading an Article
^^^^^^^^^^^^^^^^^^^^^^

An :any:`Article` freshly initialized will have no html, title, text. You first
must call ``download()``. Downloading can be called also in a multi-threading
fashion. Check out the :ref:`advanced <advanced>` section for more details.

.. code-block:: python

    first_article = cnn_paper.articles[0]

    first_article.download()

    print(first_article.html)
    # '<!DOCTYPE HTML><html itemscope itemtype="http://...'

    print(cnn_paper.articles[7].html)
    # will fail, since article is not downloaded yet

Parsing an Article
^^^^^^^^^^^^^^^^^^

In order to parse the meaningful plain text from an article, extract its title,
publication date, authors, top image, etc. we must call ``parse()`` on it.
If you call ``parse()`` before a ``download()`` it will throw an ``ArticleException``.

.. code-block:: python

    first_article.parse()

    print(first_article.text)
    # 'Three sisters who were imprisoned for possibly...'

    print(first_article.top_image)
    # 'http://some.cdn.com/3424hfd4565sdfgdg436/

    print(first_article.authors)
    # ['Eliott C. McLaughlin', 'Some CoAuthor']

    print(first_article.title)
    # u'Police: 3 sisters imprisoned in Tucson home'

    print(first_article.images)
    # ['url_to_img_1', 'url_to_img_2', 'url_to_img_3', ...]

    print(first_article.movies)
    # ['url_to_youtube_link_1', ...] # youtube, vimeo, etc


Performing NLP on an Article
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Finally, you can process the text obtained above and extract some natural language features using
the ``nlp()`` method. This will populate the ``summary`` and ``keywords`` properties of the article.

**Note:** ``nlp()`` is a computationally expensive operation. It is recommended to use it only when needed
and not recommended to run on all articles in a :any:`Source` object


You **must** have called both ``download()`` and ``parse()`` on the article
before calling ``nlp()``.

**As of the current build, nlp() features only work on western languages.**

.. code-block:: python

    first_article.nlp()

    print(first_article.summary)
    # '...imprisoned for possibly a constant barrage...'

    print(first_article.keywords)
    # ['music', 'Tucson', ... ]

    print(cnn_paper.articles[100].nlp()) # fail, not been downloaded yet
    # Traceback (...
    # ArticleException: You must parse an article before you try to..


Additional methods
^^^^^^^^^^^^^^^^^^

Here are random but hopefully useful features! ``hot()`` returns a list of the top
trending terms on Google using a public api. ``popular_urls()`` returns a list
of popular news source urls.. In case you need help choosing a news source!

.. code-block:: python

    import newspaper

    newspaper.hot()
    # ['Ned Vizzini', Brian Boitano', Crossword Inventor', 'Alex & Sierra', ... ]

    newspaper.popular_urls()
    # ['http://slate.com', 'http://cnn.com', 'http://huffingtonpost.com', ... ]
