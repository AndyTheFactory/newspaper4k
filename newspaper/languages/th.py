try:
    import pythainlp
except ImportError as e:
    raise ImportError(
        "You must install pythainlp before using the Thai tokenizer. \n"
        "Try pip install pythainlp\n"
        "or pip install newspaper3k[th]\n"
        "or pip install newspaper3k[all]\n"
    ) from e

tokenizer = pythainlp.word_tokenize
