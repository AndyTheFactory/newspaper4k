.. _install:

Installation
============

Pip
---

You can simply install ``newspaper4k`` with pip::

    pip install newspaper4k

Best practice is to use a virtual environment, such as virtualenv::

    virtualenv venv
    source venv/bin/activate
    pip install newspaper4k


Latest version from Github
--------------------------

If you want to install the latest version from Github, you can do so::

    pip install git+https://github.com/AndyTheFactory/newspaper4k.git



Requirements
------------

``newspaper4k`` requires Python 3.8 and above to run. It was not tested on
lower versions.

The newspaper4k package has the following dependencies:

* beautifulsoup4
* feedparser
* jieba3k
* lxml
* nltk
* requests
* tldextract
* Pillow
* PyYAML
* feedfinder2
* tinysegmenter
* pythainlp

Usage
-----

The fastest way to get started is to import the ``newspaper`` module and to call
the ``article`` function:

.. code-block:: python

    import newspaper
    a = newspaper.article('https://edition.cnn.com/2023/11/08/china/china-blizzard-disruption-intl-hnk/index.html')
    print(a.title)

The ``article`` function creates an ``Article`` object, downloads the article
and parses it. The ``Article`` object has several attributes, such as
``title``, ``authors``, ``text`` and ``top_image``.

The same can be achieved by using the  following code:

.. code-block:: python

    import newspaper
    a = newspaper.article('https://edition.cnn.com/2023/11/08/china/china-blizzard-disruption-intl-hnk/index.html')
    a.download()
    a.parse()
    print(a.title)
