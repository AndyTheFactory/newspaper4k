import pytest
import os
import newspaper.network as network
from newspaper import article, ArticleException


@pytest.fixture
def binary_url():
    return [
        "https://media.cnn.com/api/v1/images/stellar/prod/230703114840-anna-cooban-byline.jpg?c=16x9&q=h_270,w_480,c_fill/c_thumb,g_face,w_100,h_100",
        "https://edition.cnn.com/media/sites/cnn/video-placeholder.svg",
        "https://assets.the-independent.com/fonts/Independent-Serif-Medium.woff2",
    ]


class TestNetwork:
    @pytest.mark.skipif("GITHUB_ACTIONS" in os.environ, reason="Skip on Github Actions")
    def test_detect_cloudflair(self):
        with pytest.raises(ArticleException) as e:
            _ = article(
                "https://www.investors.com/news/technology/biotech-stocks-the-war-in-alzheimers-treatment-is-just-beginning-why-there-is-still-hope/"
            )

        assert "PerimeterX" in str(e.value)

        with pytest.raises(ArticleException) as e:
            _ = article(
                "https://www.alarabiya.net/last-page/2023/11/19/%D8%AC%D8%AB%D8%AB-%D8%B3%D8%B1%D9%82%D8%AA-%D9%88%D8%AC%D8%B1%D9%88%D8%AD-%D8%A3%D9%83%D9%84%D9%87%D8%A7-%D8%A7%D9%84%D8%AF%D9%88%D8%AF-%D8%B7%D8%A8%D9%8A%D8%A8-%D9%85%D9%86-%D8%A7%D9%84%D8%B4%D9%81%D8%A7%D8%A1-%D9%8A%D8%B1%D9%88%D9%8A"
            )

        assert "Cloudflare" in str(e.value)

    @pytest.mark.skipif("GITHUB_ACTIONS" in os.environ, reason="Skip on Github Actions")
    def test_detect_binary(self, binary_url):
        url = "https://media.cnn.com/api/v1/loops/stellar/prod/jellyfish-loop.mp4?c=original"

        assert network.has_get_ranges(url), "detect range requests failed"

        for url in binary_url:
            with pytest.raises(network.ArticleBinaryDataException):
                network.get_html(url)

        url = "https://aol.com"  # does not have Ranges
        assert not network.has_get_ranges(url), "detect range requests failed"
