📰Newspaper4k: Web article scraping, analysis & processing
============================================================

.. image:: https://badge.fury.io/py/newspaper4k.svg
    :target: https://pypi.org/project/newspaper4k/
        :alt: Latest version

.. image:: https://github.com/AndyTheFactory/newspaper4k/actions/workflows/pipeline.yml/badge.svg
        :target: https://github.com/AndyTheFactory/newspaper4k/
        :alt: Build status

.. image:: https://coveralls.io/repos/github/AndyTheFactory/newspaper4k/badge.svg?branch=master
        :target: https://coveralls.io/github/AndyTheFactory/newspaper4k
        :alt: Coverage status


At the moment the Newspaper4k Project is a fork of the well known newspaper3k by
codelucas which was not updated since Sept 2020. The initial goal of this fork is to
keep the project alive and to add new features and fix bugs. The prior existing
coding API is kept as much as possible.

`View on Github here`_

Python compatibility
--------------------

- Python 3.8+ minimum


At a glance:
------------

.. code-block:: bash

    $ pip3 install newspaper4k

.. code-block:: python

    import newspaper

    article = newspaper.article('https://edition.cnn.com/2023/10/29/sport/nfl-week-8-how-to-watch-spt-intl/index.html')

    print(article.authors)
    # ['Hannah Brewitt', 'Minute Read', 'Published', 'Am Edt', 'Sun October']

    print(article.publish_date)
    # 2023-10-29 09:00:15.717000+00:00

    print(article.text)
    # New England Patriots head coach Bill Belichick, right, embraces Buffalo Bills head coach Sean McDermott ...

    print(article.top_image)
    #https://media.cnn.com/api/v1/images/stellar/prod/231015223702-06-nfl-season-gallery-1015.jpg?c=16x9&q=w_800,c_fill

    print(article.movies)
    # []

    article.nlp()
    print(article.keywords)
    # ['broncos', 'game', 'et', 'wide', 'chiefs', 'mahomes', 'patrick', 'denver', 'nfl', 'stadium', 'week', 'quarterback', 'win', 'history', 'images']

    print(article.summary)
    # Kevin Sabitus/Getty Images Denver Broncos running back Javonte Williams evades Green Bay Packers safety Darnell Savage, bottom.
    # Kathryn Riley/Getty Images Kansas City Chiefs quarterback Patrick Mahomes calls a play during the Chiefs' 19-8 Thursday Night Football win over the Denver Broncos on October 12.
    # Paul Sancya/AP New York Jets running back Breece Hall carries the ball during a game against the Denver Broncos.
    # The Broncos have not beaten the Chiefs since 2015, and have never beaten Chiefs quarterback Patrick Mahomes.
    # Australia: NFL+, ESPN, 7Plus Brazil: NFL+, ESPN Canada: NFL+, CTV, TSN, RDS Germany: NFL+, ProSieben MAXX, DAZN Mexico: NFL+, TUDN, ESPN, Fox Sports, Sky Sports UK: NFL+, Sky Sports, ITV, Channel 5 US: NFL+, CBS, NBC, FOX, ESPN, Amazon Prime

Using the builder API
---------------------

.. code-block:: python

    import newspaper

    cnn_paper = newspaper.build('http://cnn.com')
    print(cnn_paper.category_urls())
    # ['https://cnn.com', 'https://money.cnn.com', 'https://arabic.cnn.com', 'https://cnnespanol.cnn.com', 'http://edition.cnn.com', 'https://edition.cnn.com', 'https://us.cnn.com', 'https://www.cnn.com']

    article_urls = [article.url for article in cnn_paper.articles]
    print(article_urls[:3])
    # ['https://arabic.cnn.com/middle-east/article/2023/10/30/number-of-hostages-held-in-gaza-now-up-to-239-idf-spokesperson', 'https://arabic.cnn.com/middle-east/video/2023/10/30/v146619-sotu-sullivan-hostage-negotiations', 'https://arabic.cnn.com/middle-east/article/2023/10/29/norwegian-pm-israel-gaza']

    article = cnn_paper.articles[0]
    article.download()
    article.parse()

    print(article.title)
    # المتحدث باسم الجيش الإسرائيلي: عدد الرهائن المحتجزين في غزة يصل إلى


.. code-block:: python

    from newspaper import fulltext

    html = requests.get(...).text
    text = fulltext(html)


Newspaper can extract and detect languages *seamlessly*. If no language
is specified, Newspaper will attempt to auto detect a language.

.. code-block:: python

    import newspaper

    article = newspaper.article('https://www.bbc.com/zhongwen/simp/chinese-news-67084358')

    print(article.title)
    # 晶片大战：台湾厂商助攻华为突破美国封锁？


Installation
-------------

✅ ``pip3 install newspaper4k`` ✅



User Guide
----------

.. toctree::
   :maxdepth: 2

   user_guide/quickstart
   user_guide/installation
   user_guide/cli_reference
   user_guide/examples
   user_guide/advanced
   user_guide/api_reference
   user_guide/known_newssites
   user_guide/known_issues
   user_guide/languages

LICENSE
-------

Authored and maintained by [`Andrei Paraschiv`_].

Newspaper4k was originally developed by Lucas Ou-Yang (codelucas_), the original
repository can be found [here](https://github.com/codelucas/newspaper).
Newspaper4k is licensed under the MIT license.

Credits
--------

Thanks to **Lucas Ou-Yang** for creating the original Newspaper3k
project and to all contributors of the original project.


.. _`Lucas Ou-Yang`: http://codelucas.com
.. _`codelucas`: http://codelucas.com
.. _`contact me`: https://github.com/AndyTheFactory

.. _`Quickstart guide`: https://newspaper4k.readthedocs.io/en/latest/
.. _`The Documentation`: https://newspaper4k.readthedocs.io
.. _`View on Github here`: https://github.com/AndyTheFactory/newspaper4k
.. _`Andrei Paraschiv`: https://github.com/AndyTheFactory
