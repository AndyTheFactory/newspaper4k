# Newspaper4k: Article Scraping & Curation, a continuation of the beloved newspaper3k by codelucas
[![PyPI version](https://badge.fury.io/py/newspaper4k.svg)](https://badge.fury.io/py/newspaper4k)
![Build status](https://github.com/AndyTheFactory/newspaper4k/actions/workflows/pipeline.yml/badge.svg)
[![Coverage status](https://coveralls.io/repos/github/AndyTheFactory/newspaper4k/badge.svg?branch=master)](https://coveralls.io/github/AndyTheFactory/newspaper4k)
[![Documentation Status](https://readthedocs.org/projects/newspaper4k/badge/?version=latest)](https://newspaper4k.readthedocs.io/en/latest/)

At the moment the Newspaper4k Project is a fork of the well known newspaper3k  by [codelucas](https://github.com/codelucas/newspaper) which was not updated since September 2020. The initial goal of this fork is to keep the project alive and to add new features and fix bugs.

I have duplicated all issues on the original project and will try to fix them. If you have any issues or feature requests please open an issue here.

| <!-- -->    | <!-- -->    |
|-------------|-------------|
| **Experimental ChatGPT helper bot for Newspaper4k:**         | [![ChatGPT helper](docs/user_guide/assets/chatgpt_chat200x75.png)](https://chat.openai.com/g/g-OxSqyKAhi-newspaper-4k-gpt)|



## Python compatibility
    - Python 3.8+ minimum

# Quick start

``` bash
pip install newspaper4k
```

## Using the CLI

You can start directly from the command line, using the included CLI:
``` bash
python -m newspaper --url="https://edition.cnn.com/2023/11/17/success/job-seekers-use-ai/index.html" --language=en --output-format=json --output-file=article.json

```
More information about the CLI can be found in the [CLI documentation](https://newspaper4k.readthedocs.io/en/latest/user_guide/cli_reference.html).
## Using the Python API

Alternatively, you can use Newspaper4k in Python:

### Processing one article / url at a time

``` python
import newspaper

article = newspaper.article('https://edition.cnn.com/2023/10/29/sport/nfl-week-8-how-to-watch-spt-intl/index.html')

print(article.authors)
# ['Hannah Brewitt', 'Minute Read', 'Published', 'Am Edt', 'Sun October']

print(article.publish_date)
# 2023-10-29 09:00:15.717000+00:00

print(article.text)
# New England Patriots head coach Bill Belichick, right, embraces Buffalo Bills head coach Sean McDermott ...

print(article.top_image)
# https://media.cnn.com/api/v1/images/stellar/prod/231015223702-06-nfl-season-gallery-1015.jpg?c=16x9&q=w_800,c_fill

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

```

## Parsing and scraping whole News Sources (websites) using the Source Class

This way you can build a Source object from a newspaper websites. This class will allow you to get all the articles and categories on the website. When you build the source, articles are not yet downloaded. The `build()` call will  parse front page, will detect category links (if possible), get any RSS feeds published by the news site, and will create a list of article links.
You need to call `download_articles()` to download the articles, but note that it can take a significant time.

`download_articles()` will download the articles in a multithreaded fashion using `ThreadPoolExecutor` from the `concurrent` package. The number of concurrent threads can be configured in `Configuration`.`number_threads` or passed as an argument to `build()`.


``` python
import newspaper

cnn_paper = newspaper.build('http://cnn.com', number_threads=3)
print(cnn_paper.category_urls())

# ['https://cnn.com', 'https://money.cnn.com', 'https://arabic.cnn.com',
# 'https://cnnespanol.cnn.com', 'http://edition.cnn.com',
# 'https://edition.cnn.com', 'https://us.cnn.com', 'https://www.cnn.com']

article_urls = [article.url for article in cnn_paper.articles]
print(article_urls[:3])
# ['https://arabic.cnn.com/middle-east/article/2023/10/30/number-of-hostages-held-in-gaza-now-up-to-239-idf-spokesperson',
# 'https://arabic.cnn.com/middle-east/video/2023/10/30/v146619-sotu-sullivan-hostage-negotiations',
# 'https://arabic.cnn.com/middle-east/article/2023/10/29/norwegian-pm-israel-gaza']


article = cnn_paper.articles[0]
article.download()
article.parse()

print(article.title)
# المتحدث باسم الجيش الإسرائيلي: عدد الرهائن المحتجزين في غزة يصل إلى

```
Or if you want to get bulk articles from the website (have in mind that this could take a long time and could get your IP blocked by the newssite):

``` python
import newspaper

cnn_source = newspaper.build('http://cnn.com', number_threads=3)

print(len(newspaper.article_urls))

articles = source.download_articles()

print(len(articles))

print(articles[0].title)
```

## Multilanguage features

Newspaper can extract and detect languages *seamlessly* based on the article meta tags. Additionally, you can specify the language for the website / article.  If no language is specified, Newspaper will attempt to auto detect a language from the available meta data. The fallback language is English.

Language detection is crucial for accurate article extraction. If the wrong language is detected or provided, chances are that no article text will be returned. Before parsing, check that your language is supported by our package.

``` python
from newspaper import Article

article = Article('https://www.bbc.com/zhongwen/simp/chinese-news-67084358')
article.download()
article.parse()

print(article.title)
# 晶片大战：台湾厂商助攻华为突破美国封锁？

if article.config.use_meta_language:
  # If we use the autodetected language, this config attribute will be true
  print(article.meta_lang)
else:
  print(article.config.language)

# zh
```

# Docs

Check out [The Docs](https://newspaper4k.readthedocs.io) for full and
detailed guides using newspaper.

# Features

-   Multi-threaded article download framework
-   Newspaper category detection
-   News url identification
-   Text extraction from html
-   Top image extraction from html
-   All image extraction from html
-   Keyword building from the extracted text
-   Autoatic article text summarization
-   Author extraction from text
-   Easy to use Command Line Interface (`python -m newspaper....`)
-   Output in various formats (json, csv, text)
-   Works in 10+ languages (English, Chinese, German, Arabic, \...)

# Evaluation

## Evaluation Results


Using the dataset from [ScrapingHub](https://github.com/scrapinghub/article-extraction-benchmark) I created an [evaluator script](tests/evaluation/evaluate.py) that compares the performance of newspaper against it's previous versions. This way we can see how newspaper updates improve or worsen the performance of the library.

| Version            | Corpus BLEU Score | Corpus Precision Score | Corpus Recall Score | Corpus F1 Score |
|--------------------|-------------------|------------------------|---------------------|-----------------|
| Newspaper3k 0.2.8  | 0.8660            | 0.9128                 | 0.9071              | 0.9100          |
| Newspaper4k 0.9.0  | 0.9212            | 0.8992                 | 0.9336              | 0.9161          |
| Newspaper4k 0.9.1  | 0.9224            | 0.8895                 | 0.9242              | 0.9065          |
| Newspaper4k 0.9.2  | 0.9426            | 0.9070                 | 0.9087              | 0.9078          |

Precision, Recall and F1 are computed using overlap of shingles with n-grams of size 4. The corpus BLEU score is computed using the [nltk's bleu_score](https://www.nltk.org/api/nltk.translate.bleu).

# Requirements and dependencies

Following system packages are required:

-   **Pillow**: `libjpeg-dev` `zlib1g-dev` `libpng12-dev`
-   **Lxml**: `libxml2-dev` `libxslt-dev`
-   Python Development version: `python-dev`


**If you are on Debian / Ubuntu**, install using the following:

-   Install `python3` and `python3-dev`:

        $ sudo apt-get install python3 python3-dev

-   Install `pip3` command needed to install `newspaper4k` package:

        $ sudo apt-get install python3-pip

-   lxml requirements:

        $ sudo apt-get install libxml2-dev libxslt-dev

-   For PIL to recognize .jpg images:

        $ sudo apt-get install libjpeg-dev zlib1g-dev libpng12-dev

NOTE: If you find problem installing `libpng12-dev`, try installing
`libpng-dev`.

-   Install the distribution via pip:

        $ pip3 install newspaper4k


**If you are on OSX**, install using the following, you may use both
homebrew or macports:

    $ brew install libxml2 libxslt

    $ brew install libtiff libjpeg webp little-cms2

    $ pip3 install newspaper4k


# Contributing

see [CONTRIBUTING.md](CONTRIBUTING.md)

# LICENSE

Authored and maintained by [Andrei Paraschiv](https://github.com/AndyTheFactory).

Newspaper was originally developed by Lucas Ou-Yang ([codelucas](https://codelucas.com/)), the original repository can be found [here](https://github.com/codelucas/newspaper). Newspaper is licensed under the MIT license.

# Credits
Thanks to Lucas Ou-Yang for creating the original Newspaper3k project and to all contributors of the original project.
