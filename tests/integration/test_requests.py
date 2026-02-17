import pytest
import requests

import newspaper.network as network
from newspaper import ArticleException, article


class TestNetwork:
    def test_detect_cloudflair(self, cloudflair_sites):
        network.session = requests.Session()
        for exc, url in cloudflair_sites:
            with pytest.raises(ArticleException) as e:
                _ = article(url)

            assert exc in str(e.value), f"Expected exception {exc} for url {url}, but got {str(e.value)}"

    def test_detect_binary(self, binary_url):
        url = "https://media.cnn.com/api/v1/loops/stellar/prod/jellyfish-loop.mp4?c=original"

        assert network.has_get_ranges(url), "detect range requests failed"

        for url in binary_url:
            with pytest.raises(network.ArticleBinaryDataException):
                network.get_html(url)

        url = "https://aol.com"  # does not have Ranges
        assert not network.has_get_ranges(url), "detect range requests failed"
