"""This module provides a tokenizer function for Arabic
text using the ISRIStemmer from the nltk library.

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


def tokenizer(text):
    """
    Tokenizes the given text using the ISRIStemmer from the nltk library.

    Args:
        text (str): The text to be tokenized.

    Returns:
        list: A list of stemmed words.

    """
    import nltk

    s = nltk.stem.isri.ISRIStemmer()
    words = nltk.tokenize.wordpunct_tokenize(text)
    words = [s.stem(word) for word in words]
    return words
