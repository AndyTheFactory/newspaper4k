.. _cli:

Command Line Interface (CLI)
============================

.. argparse::
   :module: newspaper.cli
   :func: get_arparse
   :prog: python -m newspaper


Examples
--------

For instance, you can download an article from cnn and save it as a json file:

.. code-block:: bash

    python -m newspaper --url=https://edition.cnn.com/2023/11/16/politics/ethics-committee-releases-santos-report/index.html  --output-format=json --output-file=cli_cnn_article.json

Or use a list of urls from a text file (one url on each line), and store all results as a csv:

.. code-block:: bash

    python -m newspaper --urls-from-file=url_list.txt  --output-format=csv --output-file=articles.csv

You can also use pipe redirection to read urls from stdin:

.. code-block:: bash

    grep "cnn" huge_url_list.txt | python -m newspaper --urls-from-stdin  --output-format=csv --output-file=articles.csv


To read the content of a local html file, use the `--html-from-file` option:

.. code-block:: bash

    python -m newspaper --url=https://edition.cnn.com/2023/11/16/politics/ethics-committee-releases-santos-report/index.html --html-from-file=/home/user/myfile.html  --output-format=json


Files can be read as file:// urls. If you want to preserver the original webpage url, use
the previous example with `--html-from-file` :

.. code-block:: bash

    python -m newspaper --url=file:///home/user/myfile.html  --output-format=json

will print out the json representation of the article, for the html file stored in  `/home/user/myfile.html`.
