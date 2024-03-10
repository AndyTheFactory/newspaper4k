try:
    import tinysegmenter
except ImportError as e:
    raise ImportError(
        "You must install tinysegmenter before using the Japapnezes tokenizer. \n"
        "Try pip install tinysegmenter\n"
        "or pip install newspaper4k[ja]\n"
        "or pip install newspaper4k[all]\n"
    ) from e

segmenter = tinysegmenter.TinySegmenter()
tokenizer = segmenter.tokenize
