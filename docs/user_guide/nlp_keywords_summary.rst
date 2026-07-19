.. _nlp_keywords_summary:

Text Analysis: Keywords and Summary
=====================================

Newspaper4k provides built-in natural language processing (NLP) capabilities to
automatically extract keywords and generate extractive summaries from article text.
These features are available through the :any:`Article.nlp` method.

Requirements
------------

The NLP features depend on the `nltk <https://www.nltk.org/>`_ library, which is
included in the optional ``nlp`` extra:

.. code-block:: bash

    pip install "newspaper4k[nlp]"

Usage
-----

After downloading and parsing an article, call :any:`Article.nlp` to populate
the ``keywords``, ``keyword_scores``, and ``summary`` attributes:

.. code-block:: python

    import newspaper

    article = newspaper.article("https://edition.cnn.com/...")

    article.nlp()

    print(article.keywords)
    # ['broncos', 'mahomes', 'chiefs', 'patrick', 'denver', 'nfl', ...]

    print(article.keyword_scores)
    # {'broncos': 1.042, 'mahomes': 1.038, 'chiefs': 1.034, ...}

    print(article.summary)
    # Kevin Sabitus/Getty Images Denver Broncos running back Javonte Williams ...
    # Kathryn Riley/Getty Images Kansas City Chiefs quarterback Patrick Mahomes ...

The three attributes set by :any:`Article.nlp` are:

* ``article.keywords`` – list of keywords sorted by relevance score (descending).
* ``article.keyword_scores`` – dict mapping each keyword to its numeric score.
* ``article.summary`` – multi-sentence summary where sentences are separated by
  newline characters (``\n``).

.. note::
    :any:`Article.nlp` must be called **after** :any:`Article.parse` (or after
    using the :any:`newspaper.article` shortcut, which calls both automatically).

Keyword Extraction
------------------

Keywords are extracted from the article body text using a frequency-based
approach. The process is:

1. **Tokenisation** – the article text is split into individual word tokens using
   a language-aware tokeniser (see :doc:`languages`). Punctuation is stripped and
   tokens are lower-cased.
2. **Stop-word removal** – common words that carry little meaning (e.g. *the*,
   *and*, *is*) are removed using a language-specific stop-word list bundled with
   newspaper4k.
3. **Frequency counting** – the remaining tokens are counted with
   :class:`collections.Counter`.
4. **Score calculation** – each keyword receives a score that combines its raw
   frequency with the total number of words in the article:

   .. math::

       \text{score}(w) = \frac{\text{count}(w) \times 1.5}{N} + 1

   where :math:`N` is the total number of tokens *before* stop-word removal.
   The additive ``+1`` ensures that all retained words have a score above 1,
   while the :math:`\times 1.5` multiplier boosts words that appear more
   frequently relative to the article length.

5. **Ranking** – keywords are sorted in descending order by score, and the top
   ``max_keywords`` are kept (default: ``35``).

Additionally, the title of the article is processed in the same way, and the
title keywords are merged with the body keywords (averaging their scores when a
word appears in both).

Summarisation
-------------

The summary is an *extractive* summary: rather than generating new text,
newspaper4k selects the most relevant existing sentences from the article body.

**Step 1 – Sentence splitting**

The article text is split into individual sentences using the
`NLTK Punkt <https://www.nltk.org/api/nltk.tokenize.PunktSentenceTokenizer.html>`_
sentence tokeniser. Sentences shorter than 10 characters are discarded.

**Step 2 – Keyword extraction**

The top ``SUMMARIZE_KEYWORD_COUNT`` keywords (default: ``10``) are extracted from
the article text using the keyword algorithm described above.

**Step 3 – Sentence scoring**

Each sentence is assigned a total score based on four weighted features:

.. list-table::
   :header-rows: 1
   :widths: 25 15 60

   * - Feature
     - Weight
     - Description
   * - Title similarity
     - 1.5
     - Fraction of non-stop title words that also appear in the sentence.
   * - Keyword frequency
     - 2.0
     - Average of the *Simple Bigram Score* (SBS) and the
       *Density-Based Score* (DBS) – see below.
   * - Sentence length
     - 1.0
     - Score peaks when sentence length is close to the expected mean of
       ``MEAN_SENTENCE_LEN`` (default: ``20`` words) and decreases
       proportionally as the length deviates from that mean.
   * - Sentence position
     - 1.0
     - Heuristic score based on where the sentence appears in the article.
       Sentences near the beginning and very end of the article receive
       slightly higher scores.

The combined score is computed as a weighted sum of the four features, divided by
the number of features (4):

.. math::

    \text{total} = \frac{1.5 \cdot s_\text{title} + 2.0 \cdot s_\text{freq} + 1.0 \cdot s_\text{len} + 1.0 \cdot s_\text{pos}}{4}

**Simple Bigram Score (SBS)**

The SBS measures the average keyword weight across all tokens in a sentence:

.. math::

    \text{SBS}(S) = \frac{1}{10} \cdot \frac{\sum_{w \in S} \text{score}(w)}{|S|}

where :math:`\text{score}(w)` is the keyword score of token :math:`w` (zero for
words that are not keywords) and :math:`|S|` is the number of tokens in the sentence.

**Density-Based Score (DBS)**

The DBS rewards sentences where keywords appear *close together*. For each
consecutive pair of keyword occurrences :math:`(k_i, k_j)` in the sentence, the
contribution is proportional to the product of their keyword scores and inversely
proportional to the square of their distance (in words):

.. math::

    \text{DBS}(S) = \frac{1}{K(K+1)} \sum_{\text{consecutive pairs } (k_i, k_j)} \frac{\text{score}(k_i) \cdot \text{score}(k_j)}{d^2_{ij}}

where :math:`K` is the number of *distinct* keywords found in the sentence and
:math:`d_{ij}` is the number of tokens between occurrences :math:`k_i` and
:math:`k_j`.

**Step 4 – Selection and ordering**

The highest-scoring sentences (up to ``max_summary_sent``, default: ``5``) are
selected and then re-ordered by their original position in the article to produce
a coherent, readable summary.

Configuration
-------------

The NLP behaviour can be customised through :any:`newspaper.configuration.Configuration`:

.. code-block:: python

    import newspaper
    from newspaper import Config

    config = Config()
    config.max_keywords = 20       # maximum keywords returned (default: 35)
    config.max_summary_sent = 3    # number of sentences in the summary (default: 5)
    config.max_summary = 1000      # maximum characters in the summary (default: 5000)

    article = newspaper.article("https://...", config=config)
    article.nlp()

    print(article.keywords)   # at most 20 keywords
    print(article.summary)    # at most 3 sentences, truncated to 1000 chars

The constants used by the scoring functions can be inspected in
``newspaper/settings.py``:

* ``MEAN_SENTENCE_LEN`` (default ``20.0``) – target sentence length used by the
  length-scoring function.
* ``SUMMARIZE_KEYWORD_COUNT`` (default ``10``) – number of keywords extracted for
  use in sentence scoring.

Language Support
----------------

Both keyword extraction and summarisation are language-aware. Newspaper4k ships
with stop-word lists for many languages and uses language-specific tokenisers
where simple whitespace splitting is insufficient (e.g. for Chinese or Arabic).

The language is determined automatically or can be set explicitly via
``config.language``:

.. code-block:: python

    import newspaper

    article = newspaper.article("https://...", language="de")
    article.nlp()

    print(article.keywords)   # German keywords
    print(article.summary)    # German extractive summary

See :doc:`languages` for the full list of supported languages and instructions on
adding new ones.
