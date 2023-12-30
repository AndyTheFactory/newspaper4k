# -*- coding: utf-8 -*-
# Much of the code here was forked from https://github.com/codelucas/newspaper
# Copyright (c) Lucas Ou-Yang (codelucas)

"""
Functions needed for the NLP analysis of articles.
"""


import os
import re
import math
from pathlib import Path
from collections import Counter
from typing import List, Set

from . import settings

stopwords: Set[str] = set()


def load_stopwords(language):
    """
    Loads language-specific stopwords for keyword selection
    """
    # stopwords for nlp in English are not the regular stopwords
    # to pass the tests
    # can be changed with the tests

    stopwordsFile = Path(settings.STOPWORDS_DIR) / f"stopwords-{language}.txt"
    if not stopwordsFile.exists():
        raise ValueError(
            f"Language {language} is not supported "
            "(or make sure the stopwords file is present in "
            "{settings.STOPWORDS_DIR}), please use one of "
            "the following: {settings.languages}"
        )
    with open(stopwordsFile, "r", encoding="utf-8") as f:
        stopwords.update(set([w.strip() for w in f.readlines()]))


def keywords(text, max_keywords=None):
    """Get the top 10 keywords and their frequency scores ignores blacklisted
    words in stopwords, counts the number of occurrences of each word, and
    sorts them in reverse natural order (so descending) by number of
    occurrences.
    """
    # TODO: parametrable number of keywords
    text = split_words(text)
    if not text:
        return dict()
    # of words before removing blacklist words
    num_words = len(text)
    text = [x for x in text if x not in stopwords]
    freq = {}
    for word in text:
        if word in freq:
            freq[word] += 1
        else:
            freq[word] = 1

    keywords_ = sorted(freq.items(), key=lambda x: (x[1], x[0]), reverse=True)
    if max_keywords:
        keywords_ = keywords_[:max_keywords]
    keywords_ = dict((x, y) for x, y in keywords_)

    for k in keywords_:
        articleScore = keywords_[k] * 1.0 / max(num_words, 1)
        keywords_[k] = articleScore * 1.5 + 1
    return dict(keywords_)


def summarize(url="", title="", text="", max_sents=5):
    if not text or not title or max_sents <= 0:
        return []

    summaries = []
    sentences = split_sentences(text)
    keys = keywords(text, settings.SUMMARIZE_KEYWORD_COUNT)
    titleWords = split_words(title)

    # Score sentences, and use the top 5 or max_sents sentences
    ranks = score(sentences, titleWords, keys).most_common(max_sents)
    for rank in ranks:
        summaries.append(rank[0])
    summaries.sort(key=lambda summary: summary[0])
    return [summary[1] for summary in summaries]


def score(sentences, titleWords, keywords):
    """Score sentences based on different features"""
    senSize = len(sentences)
    ranks = Counter()
    for i, s in enumerate(sentences):
        sentence = split_words(s)
        titleFeature = title_score(titleWords, sentence)
        sentenceLength = length_score(len(sentence))
        sentencePosition = sentence_position(i + 1, senSize)
        sbsFeature = sbs(sentence, keywords)
        dbsFeature = dbs(sentence, keywords)
        frequency = (sbsFeature + dbsFeature) / 2.0 * 10.0
        # Weighted average of scores from four categories
        totalScore = (
            titleFeature * 1.5
            + frequency * 2.0
            + sentenceLength * 1.0
            + sentencePosition * 1.0
        ) / 4.0
        ranks[(i, s)] = totalScore
    return ranks


def sbs(words, keywords):
    score = 0.0
    if len(words) == 0:
        return 0
    for word in words:
        if word in keywords:
            score += keywords[word]
    return (1.0 / math.fabs(len(words)) * score) / 10.0


def dbs(words, keywords):
    if len(words) == 0:
        return 0
    summ = 0
    first = []
    second = []

    for i, word in enumerate(words):
        if word in keywords:
            score = keywords[word]
            if first == []:
                first = [i, score]
            else:
                second = first
                first = [i, score]
                dif = first[0] - second[0]
                summ += (first[1] * second[1]) / (dif**2)
    # Number of intersections
    k = len(set(keywords.keys()).intersection(set(words))) + 1
    return 1 / (k * (k + 1.0)) * summ


def split_words(text):
    """Split a string into array of words"""
    try:
        text = re.sub(r"[^\w ]", "", text)  # strip special chars
        return [x.strip(".").lower() for x in text.split()]
    except TypeError:
        return None


def split_sentences(text: str) -> List[str]:
    """Split a large string into sentences. Uses the Punkt Sentence Tokenizer
    from the nltk module to split strings into sentences.

    Args:
        text (str): input text

    Returns:
        List[str]: a list of sentences
    """
    try:
        tokenizer = split_sentences._tokenizer
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
        split_sentences._tokenizer = tokenizer

    sentences = tokenizer.tokenize(text)
    sentences = [re.sub("[\n ]+", " ", x) for x in sentences if len(x) > 10]
    return sentences


def length_score(sentence_len):
    return (
        1
        - math.fabs(settings.MEAN_SENTENCE_LEN - sentence_len)
        / settings.MEAN_SENTENCE_LEN
    )


def title_score(title, sentence):
    if title:
        title = [x for x in title if x not in stopwords]
        count = 0.0
        for word in sentence:
            if word not in stopwords and word in title:
                count += 1.0
        return count / max(len(title), 1)
    else:
        return 0


def sentence_position(i, size):
    """Different sentence positions indicate different
    probability of being an important sentence.
    """
    normalized = i * 1.0 / size
    if normalized > 1.0:
        return 0
    elif normalized > 0.9:
        return 0.15
    elif normalized > 0.8:
        return 0.04
    elif normalized > 0.7:
        return 0.04
    elif normalized > 0.6:
        return 0.06
    elif normalized > 0.5:
        return 0.04
    elif normalized > 0.4:
        return 0.05
    elif normalized > 0.3:
        return 0.08
    elif normalized > 0.2:
        return 0.14
    elif normalized > 0.1:
        return 0.23
    elif normalized > 0:
        return 0.17
    else:
        return 0
