# Newspaper4k: Article scraping & curation, a continuation of the beloved newspaper3k by codelucas


[![image](https://badge.fury.io/py/newspaper4k.svg)](http://badge.fury.io/py/newspaper4k.svg%0A:alt:%20Latest%20version)

[![Build status](https://travis-ci.org/AndyTheFactory/newspaper4k.svg)](http://travis-ci.org/AndyTheFactory/newspaper4k/)

[![Coverage status](https://coveralls.io/repos/github/AndyTheFactory/newspaper4k/badge.svg?branch=master)](https://coveralls.io/github/AndyTheFactory/newspaper4k)

At the moment the Newspaper4k Project is a fork of the well known newspaper3k  by [codelucas](https://github.com/codelucas/newspaper) which was not updated since Sept 2020. The initial goal of this fork is to keep the project alive and to add new features and fix bugs.

I have duplicated all issues on the original project and will try to fix them. If you have any issues or feature requests please open an issue here.

## Python compatibility
    - Recommended: Python 3.8+
    - Python 3.6+ minimum
    - Fixes for Python < 3.8 are low priority and might not be merged

# Quick start
``` bash
pip install newspaper4k
```

``` python
from newspaper import Article

article = Article('https://edition.cnn.com/2023/10/29/sport/nfl-week-8-how-to-watch-spt-intl/index.html')
article.download()
article.parse()

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

```
## Using the builder API

``` python
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

``` pycon
from newspaper import fulltext

html = requests.get(...).text
text = fulltext(html)
```

Newspaper can extract and detect languages *seamlessly*. If no language
is specified, Newspaper will attempt to auto detect a language.

``` pycon
from newspaper import Article

article = Article('https://www.bbc.com/zhongwen/simp/chinese-news-67084358', language='zh')
a.download()
a.parse()

print(a.title)
# 晶片大战：台湾厂商助攻华为突破美国封锁？

```

# Docs

Check out [The Docs](https://newspaper4k.readthedocs.io) for full and
detailed guides using newspaper.

# Contributing

## Adding languages
Interested in adding a new language for us? Refer to: [Docs - Adding new
languages](https://newspaper4k.readthedocs.io/en/latest/user_guide/advanced.html#adding-new-languages)

## Submitting a PR
Interested in submitting a PR? Refer to: [Docs - Submitting a PR](https://newspaper4k.readthedocs.io/en/latest/user_guide/advanced.html#submitting-a-pr)

## Submitting an issue
Before submitting an issue, please check if it has already been reported. Additionally, please check that:
- The article website you have troubles with is not paywalled [Docs - Paywall](https://newspaper4k.readthedocs.io/en/latest/user_guide/advanced.html#paywall)
- The article website is not generating the webpage dynamically (e.g. using JavaScript) [Docs - Dynamic content](https://newspaper4k.readthedocs.io/en/latest/user_guide/advanced.html#dynamic-content)
- The article website is not using a language that is not supported by newspaper4k [Docs - Supported languages](https://newspaper4k.readthedocs.io/en/latest/user_guide/advanced.html#supported-languages)

Also, in any case, please provide the following information:
- The URL of the article you are trying to parse
- The code you are using to parse the article
- The error you are getting (if any)
- The parsing result you are getting (if any)


# Features

-   Multi-threaded article download framework
-   News url identification
-   Text extraction from html
-   Top image extraction from html
-   All image extraction from html
-   Keyword extraction from text
-   Summary extraction from text
-   Author extraction from text
-   Google trending terms extraction
-   Works in 10+ languages (English, Chinese, German, Arabic, \...)

# Requirements and dependencies

**If you are on Debian / Ubuntu**, install using the following:

-   Install `pip3` command needed to install `newspaper3k` package:

        $ sudo apt-get install python3-pip

-   Python development version, needed for Python.h:

        $ sudo apt-get install python-dev

-   lxml requirements:

        $ sudo apt-get install libxml2-dev libxslt-dev

-   For PIL to recognize .jpg images:

        $ sudo apt-get install libjpeg-dev zlib1g-dev libpng12-dev

NOTE: If you find problem installing `libpng12-dev`, try installing
`libpng-dev`.

-   Download NLP related corpora:

        $ curl https://raw.githubusercontent.com/codelucas/newspaper/master/download_corpora.py | python3

-   Install the distribution via pip:

        $ pip3 install newspaper3k

**If you are on OSX**, install using the following, you may use both
homebrew or macports:

    $ brew install libxml2 libxslt

    $ brew install libtiff libjpeg webp little-cms2

    $ pip3 install newspaper3k

    $ curl https://raw.githubusercontent.com/codelucas/newspaper/master/download_corpora.py | python3

**Otherwise**, install with the following:

NOTE: You will still most likely need to install the following libraries
via your package manager

-   PIL: `libjpeg-dev` `zlib1g-dev` `libpng12-dev`
-   lxml: `libxml2-dev` `libxslt-dev`
-   Python Development version: `python-dev`

```{=html}
<!-- -->
```
    $ pip3 install newspaper3k

    $ curl https://raw.githubusercontent.com/codelucas/newspaper/master/download_corpora.py | python3

# LICENSE

Authored and maintained by [Andrei Paraschiv](https://github.com/AndyTheFactory).

Newspaper was originally developed by Lucas Ou-Yang ([codelucas](https://codelucas.com/)), the original repository can be found [here](https://github.com/codelucas/newspaper). Newspaper is licensed under the MIT license.

# Credits
Thanks to Lucas Ou-Yang for creating the original Newspaper3k project and to all contributors of the original project.
