# -*- coding: utf-8 -*-
# Much of the code here was forked from https://github.com/codelucas/newspaper
# Copyright (c) Lucas Ou-Yang (codelucas)
"""
This module contains Stopword extraction and stopword classes.
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

punctuation_set = {
    c for i in range(sys.maxunicode + 1) if category(c := chr(i)).startswith("P")
}
punctuation_set.update(string.punctuation)
# remove characters used in contractions
contraction_separators = set("-'`ʹʻʼʽʾʿˈˊ‘’‛′‵Ꞌꞌ")
punctuation_set -= contraction_separators
punctuation: str = "".join(list(punctuation_set))
whitespace_tokenizer = WhitespaceTokenizer()


def inner_trim(value):
    """
    Replaces tabs and multiple spaces with one space. Removes newlines
    and leading/trailing spaces.

    Args:
        value (str or any): The input value to be trimmed. If the value is not
        a string, it will be converted to a string.

    Returns:
        str: The trimmed string.
    """
    if not isinstance(value, str):
        value = str(value) if value is not None else ""
    # remove tab and white space
    value = re.sub(r"[\s\t]+", " ", value)
    value = "".join(value.splitlines())
    return value.strip()


def default_tokenizer(text):
    """
    Tokenizes the given text using the default latin language tokenizer.
    Will split tokens on words and punctuation. Use this tokenizer for
    languages that are based on the latin alphabet or have clear word
    delimiters such as spaces and punctuation.

    Args:
        text (str): The text to be tokenized.

    Returns:
        list: A list of tokens.

    """
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
    """
    Language agnostic Class  for handling stop words in any language. It will
    instantieate the necessary tokenizer and stop words for the specified
    language.

    Args:
        language (str): The language code for the stop words.
            Defaults to "en" (English).

    Attributes:
        find_stopwords (Optional[Callable]): A function to find stopwords in a
            list of tokens. It is needed for languages where stopwords are not
            full words. For example, in Korean, stopwords are identified by
            tokens ending with the stopword (as if it's a suffix).
        tokenizer (Callable): A function to tokenize the content. It is initialized
            to the language specific tokenizer. If the language module does not
            have a tokenizer function, it will default to the latin language tokenizer.
        stop_words (Set[str]): A set of stop words for the specified language.
    """

    _cached_stop_words: Dict[str, str] = {}

    def __init__(self, language="en"):
        self.find_stopwords = None
        self.tokenizer = default_tokenizer

        if language not in self._cached_stop_words:
            stopwords_file = Path(settings.STOPWORDS_DIR) / f"stopwords-{language}.txt"
            if not stopwords_file.exists():
                raise FileNotFoundError(
                    f"Stopwords file for language {language} not found! Make sure that "
                    "the language is supported (see `newspaper.languages()`)"
                )
            with open(stopwords_file, "r", encoding="utf-8") as f:
                self._cached_stop_words[language] = set(f.read().splitlines())

        lang_module = Path(__file__).parent / "languages" / f"{language}.py"
        if lang_module.exists():
            import importlib  # pylint: disable=import-outside-toplevel

            module = importlib.import_module(f"newspaper.languages.{language}")
            if not hasattr(module, "tokenizer"):
                raise ValueError(
                    f"Language module {lang_module} has no tokenizer function!"
                )

            if hasattr(module, "find_stopwords"):
                self.find_stopwords = module.find_stopwords

            self.tokenizer = module.tokenizer

        self.stop_words = self._cached_stop_words[language]

    def get_stopword_count(self, content: str) -> WordStats:
        """Calculates the word count and  stop words count in the given content.

        Args:
            content (str): The content to analyze.

        Returns:
            WordStats: An object containing the stop word count, total word
            count, and the stop words found.

        """
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
