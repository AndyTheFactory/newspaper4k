.. _install:

Installation
============

Pip
---

You can simply install ``newspaper4k`` with pip::

.. code-block:: bash

    pip install newspaper4k


Best practice is to use a virtual environment, such as virtualenv::

.. code-block:: bash

    virtualenv venv
    source venv/bin/activate
    pip install newspaper4k


Latest version from Github
--------------------------

If you want to install the latest version from Github, you can do so::

.. code-block:: bash

    pip install git+https://github.com/AndyTheFactory/newspaper4k.git



Requirements
------------

``newspaper4k`` requires Python 3.8 and above to run. It was not tested on
lower versions.

The newspaper4k package has the following dependencies:

* beautifulsoup4
* Pillow
* PyYAML
* lxml[html_clean]
* Pillow
* PyYAML
* lxml[html_clean]
* nltk
* requests
* feedparser
* feedparser
* tldextract
* python-dateutil
* typing-extensions
* brotli

Additionally, for extended language support, you may need to install the following:

- Chinese: jieba
- Thai: pythainlp
- Japanese: tinysegmenter
- Bengali, Hindi, Nepali, Tamil: indic-nlp-library

Other optional dependencies include:
- Cloudflare-protected sites: cloudscraper
- Google News API: gnews

To install with specific optional dependencies, you can use extras in pip.
For example, to install with Chinese and Thai support:

.. code-block:: bash

    pip install newspaper4k[zh,th]

To install cloudscraper for Cloudflare support:

.. code-block:: bash

    pip install newspaper4k[cloudflare]

To install all optional dependencies:

.. code-block:: bash

    pip install newspaper4k[all]

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
