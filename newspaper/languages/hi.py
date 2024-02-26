import re
import string

try:
    from indicnlp.tokenize.indic_tokenize import trivial_tokenize
except ImportError as e:
    raise ImportError(
        "You must install indic-nlp-library before using the Hindi tokenizer. \n"
        "Try pip install indic-nlp-library\n"
        "or pip install newspaper3k[hi]\n"
        "or pip install newspaper3k[all]\n"
    ) from e


def tokenizer(text):
    punct = re.escape(string.punctuation)
    text = re.sub(rf"[\s\t{punct}]+", " ", text)
    return trivial_tokenize(text, "hi")
