.. _api:

Newspaper API
=============

.. autosummary::
   :toctree: generated

Function calls
--------------

.. autofunction:: newspaper.article

.. autofunction:: newspaper.build

.. autofunction:: newspaper.mthreading.fetch_news

.. autofunction:: newspaper.hot

.. autofunction:: newspaper.languages


Configuration
-------------

.. autoclass:: newspaper.configuration.Configuration
    :members:

Article
-------

.. _article shortcut:

Article objects can also be created with the shortcut method::

    a = newspaper.article(url, language='en', ...)

which is equivalent to::

    a = newspaper.Article(url, language='en', ...)
    a.download()
    a.parse()

You can pass any of the Article constructor arguments to the shortcut method.

.. autoclass:: newspaper.Article
.. automethod:: newspaper.Article.__init__
.. automethod:: newspaper.Article.download()
.. automethod:: newspaper.Article.parse()
.. automethod:: newspaper.Article.nlp()

Source
------

.. autoclass:: newspaper.Source
.. automethod:: newspaper.Source.__init__
.. automethod:: newspaper.Source.build()
.. automethod:: newspaper.Source.feeds_to_articles()
.. automethod:: newspaper.Source.categories_to_articles()
.. automethod:: newspaper.Source.generate_articles()
.. automethod:: newspaper.Source.download_articles()
.. automethod:: newspaper.Source.download()
.. automethod:: newspaper.Source.size()

Category
--------

.. autoclass:: newspaper.source.Category

Feed
----
.. autoclass:: newspaper.source.Feed


Exceptions
----------
.. autoclass:: newspaper.ArticleException

.. autoclass:: newspaper.ArticleBinaryDataException
