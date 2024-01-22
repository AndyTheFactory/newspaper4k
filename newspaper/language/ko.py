from nltk import word_tokenize

tokenizer = word_tokenize


def find_stopwords(tokens, stopwords):
    res = []
    for w in tokens:
        for s in stopwords:
            if w.endswith(s):
                res.append(w)
                break

    return res
