# -*- coding: utf-8 -*-
# Much of the code here was forked from https://github.com/codelucas/newspaper
# Copyright (c) Lucas Ou-Yang (codelucas)

"""
Stopword extraction and stopword classes.
"""

from dataclasses import dataclass, field
from pathlib import Path
import re
import string
from typing import Dict, List

from newspaper import settings


def innerTrim(value):
    if isinstance(value, str):
        # remove tab and white space
        value = re.sub(r"[\s\t]+", " ", value)
        value = "".join(value.splitlines())
        return value.strip()
    return ""


@dataclass
class WordStats:
    """Holds the number of stop words and total words in an article"""

    stop_word_count: int = 0
    word_count: int = 0
    stop_words: List[str] = field(default_factory=list)


class StopWords:
    TRANS_TABLE = str.maketrans("", "")
    _cached_stop_words: Dict[str, str] = {}

    def __init__(self, language="en"):
        if language not in self._cached_stop_words:
            stopwordsFile = Path(settings.STOPWORDS_DIR) / f"stopwords-{language}.txt"
            if not stopwordsFile.exists():
                raise FileNotFoundError(
                    f"Stopwords file for language {language} not found! Make sure that "
                    "the language is supported (see `newspaper.languages()`)"
                )
            with open(stopwordsFile, "r", encoding="utf-8") as f:
                self._cached_stop_words[language] = set(f.read().splitlines())

        self.STOP_WORDS = self._cached_stop_words[language]

    def remove_punctuation(self, content):
        # code taken form
        # http://stackoverflow.com/questions/265960/best-way-to-strip-punctuation-from-a-string-in-python
        content_is_unicode = isinstance(content, str)
        if content_is_unicode:
            content = content.encode("utf-8")
        trans_table = {ord(c): None for c in string.punctuation}
        stripped_input = content.decode("utf-8").translate(trans_table)

        return stripped_input

    def candidate_words(self, stripped_input):
        return stripped_input.split(" ")

    def get_stopword_count(self, content):
        if not content:
            return WordStats()
        ws = WordStats()
        stripped_input = self.remove_punctuation(content)
        candidate_words = self.candidate_words(stripped_input.lower())
        overlapping_stopwords = []
        c = 0
        for w in candidate_words:
            c += 1
            if w in self.STOP_WORDS:
                overlapping_stopwords.append(w)

        ws.word_count = c
        ws.stop_word_count = len(overlapping_stopwords)
        ws.stop_words = overlapping_stopwords
        return ws


class StopWordsChinese(StopWords):
    """Chinese segmentation"""

    def __init__(self, language="zh"):
        super(StopWordsChinese, self).__init__(language="zh")

    def candidate_words(self, stripped_input):
        # jieba builds a tree that takes a while. avoid building
        # this tree if we don't use the chinese language
        import jieba

        return jieba.cut(stripped_input, cut_all=True)


class StopWordsArabic(StopWords):
    """Arabic segmentation"""

    def __init__(self, language="ar"):
        # force ar language code
        super(StopWordsArabic, self).__init__(language="ar")

    def remove_punctuation(self, content):
        return content

    def candidate_words(self, stripped_input):
        import nltk

        s = nltk.stem.isri.ISRIStemmer()
        words = []
        for word in nltk.tokenize.wordpunct_tokenize(stripped_input):
            words.append(s.stem(word))
        return words


class StopWordsKorean(StopWords):
    """Korean segmentation"""

    def __init__(self, language="ko"):
        super(StopWordsKorean, self).__init__(language="ko")

    def get_stopword_count(self, content):
        if not content:
            return WordStats()
        ws = WordStats()
        stripped_input = self.remove_punctuation(content)
        candidate_words = self.candidate_words(stripped_input)
        overlapping_stopwords = []
        c = 0
        for w in candidate_words:
            c += 1
            for s in self.STOP_WORDS:
                if w.endswith(s):
                    overlapping_stopwords.append(w)

        ws.word_count = c
        ws.stop_word_count = len(overlapping_stopwords)
        ws.stop_words = overlapping_stopwords
        return ws


class StopWordsHindi(StopWords):
    """Hindi segmentation"""

    def __init__(self, language="hi"):
        super(StopWordsHindi, self).__init__(language="hi")

    def get_stopword_count(self, content):
        if not content:
            return WordStats()
        ws = WordStats()
        stripped_input = self.remove_punctuation(content)
        candidate_words = self.candidate_words(stripped_input)
        overlapping_stopwords = []
        c = 0
        for w in candidate_words:
            c += 1
            for stop_word in self.STOP_WORDS:
                overlapping_stopwords.append(stop_word)

        ws.word_count = c
        ws.stop_word_count = len(overlapping_stopwords)
        ws.stop_words = overlapping_stopwords
        return ws


class StopWordsJapanese(StopWords):
    """Japanese segmentation"""

    def __init__(self, language="ja"):
        super(StopWordsJapanese, self).__init__(language="ja")

    def candidate_words(self, stripped_input):
        import tinysegmenter

        segmenter = tinysegmenter.TinySegmenter()
        tokens = segmenter.tokenize(stripped_input)
        return tokens


class StopWordsThai(StopWords):
    """Thai segmentation"""

    def __init__(self, language="th"):
        super(StopWordsThai, self).__init__(language="th")

    def candidate_words(self, stripped_input):
        import pythainlp

        tokens = pythainlp.word_tokenize(stripped_input)
        return tokens
