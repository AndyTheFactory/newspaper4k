.. _cli:

Command Line Interface (CLI)
============================

Newspaper4k provides a command-line interface (CLI) that lets you download and
parse news articles without writing any Python code. You can process a single
URL, a list of URLs from a file, or a stream of URLs piped from another
command, and output the results as JSON, CSV, or plain text.

**Usage**::

    python -m newspaper [OPTIONS] (--url URL | --urls-from-file FILE | --urls-from-stdin)

.. argparse::
   :module: newspaper.cli
   :func: get_arparse
   :prog: python -m newspaper


Arguments Reference
-------------------

Input Source (mutually exclusive)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Exactly one of the following three arguments must be provided.

``--url URL``, ``-u URL``
    The URL of the article to download and parse.  Can be a standard
    ``http://`` / ``https://`` address or a ``file://`` path to a local HTML
    file.

    Example::

        python -m newspaper --url=https://www.bbc.com/news/world-12345

``--urls-from-file FILE``, ``-uf FILE``
    Path to a plain-text file that contains one URL per line.  Every URL in
    the file will be downloaded and parsed in order.

    Example::

        python -m newspaper --urls-from-file=url_list.txt --output-format=csv

``--urls-from-stdin``, ``-us``
    Read URLs from standard input (one per line).  This is useful for piping
    the output of another command directly into Newspaper4k.

    Example::

        grep "bbc.com" my_urls.txt | python -m newspaper --urls-from-stdin --output-format=json

HTML Content
^^^^^^^^^^^^

``--html-from-file FILE``, ``-hf FILE``
    Instead of downloading the article from the network, read the HTML from a
    local file.  The URL supplied via ``--url`` is still used as the canonical
    address of the article (for metadata and relative-URL resolution), but no
    HTTP request is made.  When processing multiple URLs
    (``--urls-from-file`` / ``--urls-from-stdin``), this file is applied only
    to the *first* URL; subsequent URLs are downloaded normally.

    Example::

        python -m newspaper \
            --url=https://www.bbc.com/news/world-12345 \
            --html-from-file=/tmp/cached_page.html \
            --output-format=json

Output
^^^^^^

``--output-format {json,csv,text}``, ``-of {json,csv,text}``
    Format used to write the parsed article data.  Default: ``json``.

    * ``json`` – a JSON array where each element is an article object
      containing all extracted fields (title, text, authors, publish date,
      keywords, summary, images, …).
    * ``csv`` – a CSV file with a header row followed by one row per article.
    * ``text`` – plain text containing the article title followed by the
      article body, suitable for quick human reading.

``--output-file FILE``, ``-o FILE``
    Write the output to *FILE* instead of printing to standard output.  If the
    file already exists it will be **overwritten**.  If omitted, results are
    printed to stdout.

    Example::

        python -m newspaper --url=https://www.bbc.com/news/world-12345 \
            --output-format=json --output-file=article.json

Network & HTTP
^^^^^^^^^^^^^^

``--browser-user-agent STRING``, ``-ua STRING``
    Override the HTTP ``User-Agent`` header sent when downloading articles.
    Some websites block requests with the default user-agent; setting a
    browser-like string can help bypass those restrictions.

    Example::

        --browser-user-agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"

``--proxy URL``
    Route all HTTP/HTTPS traffic through this proxy.  The expected format is
    ``http://<host>:<port>``, for example ``http://10.10.1.1:8080``.

``--request-timeout SECONDS``
    Maximum number of seconds to wait for an HTTP response.  Default: ``7``.
    Increase this value for slow or rate-limited websites.

``--cookies STRING``
    Cookies to include in every HTTP request, formatted as a semicolon-
    separated list of ``name=value`` pairs, e.g.
    ``session=abc123; consent=true``.

``--skip-ssl-verify``
    Disable SSL/TLS certificate verification.  Use with caution — this makes
    connections vulnerable to man-in-the-middle attacks.  Useful when
    accessing internal or self-signed HTTPS endpoints.

``--follow-meta-refresh``
    Follow ``<meta http-equiv="refresh">`` redirects when downloading an
    article.  Some pages use this tag to redirect visitors to the actual
    content page.

Content Parsing
^^^^^^^^^^^^^^^

``--language LANG``, ``-l LANG``
    Two-letter ISO 639-1 language code of the article (e.g. ``en``, ``fr``,
    ``de``).  Default: ``en``.  Providing the correct language improves text
    segmentation, stopword filtering, and NLP quality.  See
    :ref:`languages` for the full list of supported languages.

``--read-more-link XPATH``
    An XPath expression that identifies the *"read more"* or *"full article"*
    link present on summary/teaser pages.  When supplied, Newspaper4k will
    click through that link and parse the full article instead of the
    truncated preview.

    Example::

        --read-more-link="//a[@class='read-more']"

``--skip-fetch-images``
    Do not download images when selecting the article's top image.  This
    speeds up parsing because no additional HTTP requests are made, but may
    result in a less accurate top-image selection.

``--max-nr-keywords N``
    Maximum number of keywords to extract from the article during NLP
    processing.  Default: ``10``.

``--skip-nlp``
    Skip the Natural Language Processing step entirely.  When set, the
    ``keywords`` and ``summary`` fields in the output will be empty.  Use this
    flag when NLP is not needed and you want faster processing.


Examples
--------

Download a single article and save it as JSON:

.. code-block:: bash

    python -m newspaper \
        --url=https://edition.cnn.com/2023/11/16/politics/ethics-committee-releases-santos-report/index.html \
        --output-format=json \
        --output-file=cli_cnn_article.json

Process a list of URLs from a text file (one URL per line) and save all results as CSV:

.. code-block:: bash

    python -m newspaper --urls-from-file=url_list.txt --output-format=csv --output-file=articles.csv

Use pipe redirection to read URLs from stdin:

.. code-block:: bash

    grep "cnn" huge_url_list.txt | python -m newspaper --urls-from-stdin --output-format=csv --output-file=articles.csv

Parse a locally cached HTML file while preserving the original article URL:

.. code-block:: bash

    python -m newspaper \
        --url=https://edition.cnn.com/2023/11/16/politics/ethics-committee-releases-santos-report/index.html \
        --html-from-file=/home/user/myfile.html \
        --output-format=json

Read a local HTML file directly using a ``file://`` URL (the canonical article
URL will be derived from the file path):

.. code-block:: bash

    python -m newspaper --url=file:///home/user/myfile.html --output-format=json

The command above prints the JSON representation of the article parsed from
``/home/user/myfile.html``.

Download a French article and skip NLP processing:

.. code-block:: bash

    python -m newspaper \
        --url=https://www.lemonde.fr/international/article/2023/11/01/example \
        --language=fr \
        --skip-nlp \
        --output-format=text
