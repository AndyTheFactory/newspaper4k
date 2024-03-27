"""This module provides a tokenizer function for Nepalese
text using the IndicNLP library.

In order to create a language specific module, the python file
must be located in the newspaper/languages directory and the name
of the file must be the ISO 639-1 code for the language.

The module should export at least one of the following methods:
- `tokenizer(text:str)->List[str]`: A method that tokenizes the given text.
    for languages that use only latin word sepparators, such as space, punctuation,
    there is no need to provide a special tokenization method. It is required
    for language that have another method of sepparating words, such as
    Chinese or Japanese.

- `find_stopwords(tokens:List[str], stopwords:List[str])->List[str]`: A method that
    finds the stopwords in the given list of tokens. In case that stopwords are not
    whole words, but suffixes, such in Korean, then this method should return a
    list of stopwords located in the tokens. If needed, here would take place a
    preprocessing step such as lemmatization or stemming before checking for stopwords.

"""

import re
import string

try:
    from indicnlp.tokenize.indic_tokenize import trivial_tokenize
except ImportError as e:
    raise ImportError(
        "You must install indic-nlp-library before using the Nepali tokenizer. \n"
        "Try pip install indic-nlp-library\n"
        "or pip install newspaper4k[np]\n"
        "or pip install newspaper4k[all]\n"
    ) from e


def tokenizer(text):
    """
    Tokenizes the given Nepali text by removing punctuation and extra spaces and
    using the `trivial_tokenize` method from the `indicnlp` library.

    Args:
        text (str): The input text to be tokenized.

    Returns:
        str: The tokenized text.

    """
    punct = re.escape(string.punctuation)
    text = re.sub(rf"[\s\t{punct}]+", " ", text)
    return trivial_tokenize(text, "ne")
