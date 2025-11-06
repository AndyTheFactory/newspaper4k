import pytest

from newspaper import Source


def test_empty_url_source():
    with pytest.raises(ValueError):
        Source("")
    with pytest.raises(ValueError):
        Source(url=None)
