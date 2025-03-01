"""Test if the newspaper library is working properly."""

from newspaper import valid_languages

assert len(valid_languages()) > 10, "There should be more than 10 languages available"
