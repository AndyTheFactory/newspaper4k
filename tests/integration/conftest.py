import os

import pytest

pytestmark = pytest.mark.integration


def pytest_runtest_setup(item):
    """Skip integration/e2e tests automatically in CI."""
    if "GITHUB_ACTIONS" in os.environ:
        pytest.skip("Skipping integration tests in GitHub Actions")


@pytest.fixture
def pdf_article_fixture():
    return "https://www.adobe.com/pdf/pdfs/ISO32000-1PublicPatentLicense.pdf"


@pytest.fixture
def binary_url():
    return [
        "https://media.cnn.com/api/v1/images/stellar/prod/230703114840-anna-cooban-byline.jpg?c=16x9&q=h_270,w_480,c_fill/c_thumb,g_face,w_100,h_100",
        "https://edition.cnn.com/media/sites/cnn/video-placeholder.svg",
        "https://assets.the-independent.com/fonts/Independent-Serif-Medium.woff2",
    ]


@pytest.fixture
def cloudflair_sites():
    return [
        (
            "PerimeterX",
            "https://www.investors.com/news/technology/biotech-stocks-the-war-in-alzheimers-treatment-is-just-beginning-why-there-is-still-hope/",
        ),
        (
            "Cloudflare",
            "https://www.alarabiya.net/last-page/2023/11/19/%D8%AC%D8%AB%D8%AB-%D8%B3%D8%B1%D9%82%D8%AA-%D9%88%D8%AC%D8%B1%D9%88%D8%AD-%D8%A3%D9%83%D9%84%D9%87%D8%A7-%D8%A7%D9%84%D8%AF%D9%88%D8%AF-%D8%B7%D8%A8%D9%8A%D8%A8-%D9%85%D9%86-%D8%A7%D9%84%D8%B4%D9%81%D8%A7%D8%A1-%D9%8A%D8%B1%D9%88%D9%8A",
        ),
    ]


@pytest.fixture
def feed_sources():
    return [
        {"url": "https://www.thesun.co.uk/", "feeds": 20},
        {"url": "https://www.aljazeera.com/", "feeds": 1},
        {"url": "https://www.theverge.com/", "feeds": 1},
        {"url": "https://techcrunch.com", "feeds": 12},
    ]


@pytest.fixture
def gnews_source():
    return {
        "keyword": "covid",
        "topic": "BUSINESS",
        "location": "London",
        "site": "bbc.com",
    }
