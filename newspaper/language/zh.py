try:
    import jieba
except ImportError as e:
    raise ImportError(
        "You must install jieba before using the Chinese tokenizer. \n"
        "Try pip install jieba\n"
        "or pip install newspaper3k[zh]\n"
        "or pip install newspaper3k[all]\n"
    ) from e

tokenizer = lambda x: jieba.cut(x, cut_all=True)  # noqa: E731
