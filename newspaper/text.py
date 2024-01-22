# -*- coding: utf-8 -*-
# Much of the code here was forked from https://github.com/codelucas/newspaper
# Copyright (c) Lucas Ou-Yang (codelucas)
"""
Stopword extraction and stopword classes.
"""
import sys
from unicodedata import category
from dataclasses import dataclass, field
from pathlib import Path
import re
import string
from typing import Dict, List
from nltk.tokenize import WhitespaceTokenizer

from newspaper import settings

punctuation = {
    c for i in range(sys.maxunicode + 1) if category(c := chr(i)).startswith("P")
}
punctuation.update(string.punctuation)
# remove characters used in contractions
contraction_separators = set("-'`ʹʻʼʽʾʿˈˊ‘’‛′‵Ꞌꞌ")
punctuation -= contraction_separators
punctuation: str = "".join(list(punctuation))
whitespace_tokenizer = WhitespaceTokenizer()


def innerTrim(value):
    if isinstance(value, str):
        # remove tab and white space
        value = re.sub(r"[\s\t]+", " ", value)
        value = "".join(value.splitlines())
        return value.strip()
    return ""


def default_tokenizer(text):
    if isinstance(text, bytes):
        text = text.decode("utf-8", "replace")
    # Remove punctuation
    text = text.translate(
        str.maketrans(
            punctuation,
            " " * len(punctuation),
        )
    )
    # remove multiple contraction separators
    regex_str = re.escape("".join(contraction_separators))
    text = re.sub(
        rf"(?<=\W)[{regex_str}]|[{regex_str}](?=\W)|"
        f"^[{regex_str}]*|[{regex_str}]*$|[{regex_str}]{{2,}}",
        " ",
        text,
    )
    return whitespace_tokenizer.tokenize(text.lower())


@dataclass
class WordStats:
    """Holds the number of stop words and total words in an article"""

    stop_word_count: int = 0
    word_count: int = 0
    stop_words: List[str] = field(default_factory=list)


class StopWords:
    _cached_stop_words: Dict[str, str] = {}

    def __init__(self, language="en"):
        self.find_stopwords = None
        self.tokenizer = default_tokenizer

        if language not in self._cached_stop_words:
            stopwordsFile = Path(settings.STOPWORDS_DIR) / f"stopwords-{language}.txt"
            if not stopwordsFile.exists():
                raise FileNotFoundError(
                    f"Stopwords file for language {language} not found! Make sure that "
                    "the language is supported (see `newspaper.languages()`)"
                )
            with open(stopwordsFile, "r", encoding="utf-8") as f:
                self._cached_stop_words[language] = set(f.read().splitlines())

        lang_module = Path(__file__).parent / "language" / f"{language}.py"
        if lang_module.exists():
            import importlib

            module = importlib.import_module(f"newspaper.language.{language}")
            if not hasattr(module, "tokenizer"):
                raise ValueError(
                    f"Language module {lang_module} has no tokenizer function!"
                )

            if hasattr(module, "find_stopwords"):
                self.find_stopwords = module.find_stopwords

            self.tokenizer = module.tokenizer

        self.stop_words = self._cached_stop_words[language]

    def get_stopword_count(self, content):
        if not content:
            return WordStats()

        tokens = list(self.tokenizer(content))

        if self.find_stopwords:
            # some special way stopwords are identified.
            # Not as full string. Korean seems work based on tokens ending
            # with the stopword (as if it's a suffix) TODO: confirm this
            intersection = self.find_stopwords(tokens, self.stop_words)
        else:
            intersection = [w for w in tokens if w in self.stop_words]

        return WordStats(
            stop_word_count=len(intersection),
            word_count=len(tokens),
            stop_words=intersection,
        )
