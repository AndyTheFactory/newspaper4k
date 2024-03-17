# -*- coding: utf-8 -*-
# Much of the code here was forked from https://github.com/codelucas/newspaper
# Copyright (c) Lucas Ou-Yang (codelucas)

"""
Functions needed for the NLP analysis of articles.
"""
import os
import re
import math
from collections import Counter
from typing import List, Optional

from newspaper.text import StopWords

from . import settings


def keywords(text: str, stopwords: StopWords, max_keywords: Optional[int] = None):
    """Get the top 10 keywords and their frequency scores ignores
    words in stopword list, counts the number of occurrences of each word, and
    sorts them in descending by number of occurrences. The frequency scores
    are normlized to the range [0, 1], and then multiplied by 1.5 to boost

    Args:
        text (str): The text to analyze.
        stopwords (StopWords): A StopWords object for the language of the text.
        max_keywords (int): The maximum number of keywords returned. defaults
            to None, which returns all keywords.

    Returns:
        dict: The top 10 keywords and their frequency scores.
    """
    tokenised_text = list(stopwords.tokenizer(text))
    if not text:
        return dict()
    # of words before removing blacklist words
    num_words = len(tokenised_text) or 1
    tokenised_text = list(
        filter(lambda x: x not in stopwords.stop_words, tokenised_text)
    )

    freq = Counter(tokenised_text)

    keywords_ = freq.most_common(max_keywords)
    keywords_dict = {k: v * 1.5 / num_words + 1 for k, v in keywords_}

    return keywords_dict


def summarize(title: str, text: str, stopwords: StopWords, max_sents: int = 5):
    """Summarize an article into the most relevant sentences in the article.

    Args:
        title (str): the article title
        text (str): article contents
        stopwords (StopWords): stopwords object for the language of the text
        max_sents (int, optional):maximum number of sentences to
            return in the summary. Sentences are weighted by their relevance
            using the following criteria: sentence position, frequency of
            keywords, title words found in the sentence, and sentence length.
            Defaults to 5.

    Returns:
        _type_: _description_
    """
    if not text or not title or max_sents <= 0:
        return []

    summaries = []
    sentences = split_sentences(text)
    keys = keywords(text, stopwords, settings.SUMMARIZE_KEYWORD_COUNT)
    title_words = list(stopwords.tokenizer(title))

    # Score sentences, and use the top 5 or max_sents sentences
    ranks = scored_sentences(sentences, title_words, keys, stopwords)

    # Filter out the first max_sents relevant sentences
    summaries = ranks[:max_sents]
    summaries.sort(key=lambda x: x[0])  # Sort my sentence order in the text
    return [summary[1] for summary in summaries]


def title_score(title_tokens, sentence_tokens, stopwords):
    title_tokens = [x for x in title_tokens if x not in stopwords.stop_words]
    count = 0.0

    if not title_tokens:
        return count

    intersection = [
        word
        for word in sentence_tokens
        if word in title_tokens and word not in stopwords.stop_words
    ]
    return len(intersection) / len(title_tokens)


def scored_sentences(sentences, title_words, keywords, stopwords):
    """Score sentences based on different features"""
    sentence_count = len(sentences)
    ranks = []

    for i, s in enumerate(sentences):
        sentence = list(stopwords.tokenizer(s))
        title_features = title_score(title_words, sentence, stopwords)
        sent_len = length_score(len(sentence))
        sent_pos = sentence_position_score(i + 1, sentence_count)
        sbs_feature = sbs(sentence, keywords)
        dbs_feature = dbs(sentence, keywords)
        frequency = (sbs_feature + dbs_feature) / 2.0 * 10.0
        # Weighted average of scores from four categories
        totalScore = (
            title_features * 1.5 + frequency * 2.0 + sent_len * 1.0 + sent_pos * 1.0
        ) / 4.0
        ranks.append((i, s, totalScore))

    ranks.sort(key=lambda x: x[2], reverse=True)
    return ranks


def length_score(sentence_len):
    return (
        1
        - math.fabs(settings.MEAN_SENTENCE_LEN - sentence_len)
        / settings.MEAN_SENTENCE_LEN
    )


def sentence_position_score(i, size):
    """Different sentence positions indicate different
    probability of being an important sentence.
    """
    normalized = i * 1.0 / size

    ranges = [
        (1.0, 0),
        (0.9, 0.15),
        (0.8, 0.04),
        (0.7, 0.04),
        (0.6, 0.06),
        (0.5, 0.04),
        (0.4, 0.05),
        (0.3, 0.08),
        (0.2, 0.14),
        (0.1, 0.23),
        (0, 0.17),
    ]

    for r, value in ranges:
        if normalized > r:
            return value

    return 0


def sbs(words, keywords):
    score = 0.0
    if not words or not keywords:
        return score

    scores = [keywords.get(w, 0) for w in words]
    score = sum(scores) / len(words)
    score /= 10.0
    return score


def dbs(words, keywords):
    if not words or not keywords:
        return 0

    summ = 0
    words_in_keys = [
        (i, keywords[word], word) for i, word in enumerate(words) if word in keywords
    ]
    if not words_in_keys:
        return 0

    intersection = set()
    for first, second in zip(words_in_keys, words_in_keys[1:]):
        dif = second[0] - first[0]
        summ += (first[1] * second[1]) / (dif**2)
        intersection.add(first[2])

    intersection.add(words_in_keys[-1][2])
    # Number of intersections
    k = len(intersection) + 1
    return 1 / (k * (k + 1.0)) * summ


def split_sentences(text: str) -> List[str]:
    """Split a large string into sentences. Uses the Punkt Sentence Tokenizer
    from the nltk module to split strings into sentences.

    Args:
        text (str): input text

    Returns:
        List[str]: a list of sentences
    """
    try:
        tokenizer = split_sentences._tokenizer  # type: ignore[attr-defined]
    except AttributeError:
        import nltk

        nltk_data_path = os.environ.get("NLTK_DATA")
        if nltk_data_path:
            nltk.data.path.append(nltk_data_path)
        try:
            nltk.data.find("tokenizers/punkt")
        except LookupError:
            nltk.download("punkt")

        # TODO: load a language specific tokenizer
        tokenizer = nltk.data.load("tokenizers/punkt/english.pickle")
        split_sentences._tokenizer = tokenizer  # type: ignore[attr-defined]

    sentences = tokenizer.tokenize(text)
    sentences = [re.sub("[\n ]+", " ", x) for x in sentences if len(x) > 10]
    return sentences
