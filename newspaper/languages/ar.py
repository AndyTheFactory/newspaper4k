def tokenizer(text):
    import nltk

    s = nltk.stem.isri.ISRIStemmer()
    words = nltk.tokenize.wordpunct_tokenize(text)
    words = [s.stem(word) for word in words]
    return words
