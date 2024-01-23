import re
import string

try:
    from indicnlp.tokenize.indic_tokenize import trivial_tokenize
except ImportError as e:
    raise ImportError(
        "You must install jieba before using the Chinese tokenizer. \n"
        "Try pip install jieba\n"
        "or pip install newspaper3k[zh]\n"
        "or pip install newspaper3k[all]\n"
    ) from e


def tokenizer(text):
    punct = re.escape(string.punctuation)
    text = re.sub(rf"[\s\t{punct}]+", " ", text)
    return trivial_tokenize(text, "bn")
