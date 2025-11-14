"""Test if the newspaper library is working properly."""

from newspaper import valid_languages


def test_smoke():
    """A simple smoke test to check if the newspaper library is functioning."""
    assert len(valid_languages()) > 10, "There should be more than 10 languages available"
