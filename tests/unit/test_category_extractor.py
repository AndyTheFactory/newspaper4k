import lxml.html
import pytest

from newspaper.configuration import Configuration
from newspaper.extractors.categories_extractor import CategoryExtractor


@pytest.fixture
def category_extractor():
    return CategoryExtractor(Configuration())


def test_is_valid_link(category_extractor):
    # Test with a valid link
    url = "http://www.example.com/social/page.html"
    source_domain = "example"
    source_url = "http://www.example.com"
    is_valid, parsed_url = category_extractor.is_valid_link(url, source_domain, source_url)
    assert is_valid is False

    # Test with an invalid link (different domain)
    url = "http://www.another-domain.com/category/index.html"
    is_valid, _ = category_extractor.is_valid_link(url, source_domain, source_url)
    assert is_valid is False

    # Test with a valid link (subdomain)
    url = "http://www.example.com/social/index.html"
    is_valid, _ = category_extractor.is_valid_link(url, source_domain, source_url)
    assert is_valid is True

    # Test with an invalid link (no domain)
    url = "/category/page.html"
    is_valid, _ = category_extractor.is_valid_link(url, source_domain, source_url)
    assert is_valid is True

    # Test with an invalid link (mailto)
    url = "mailto:test@example.com"
    is_valid, _ = category_extractor.is_valid_link(url, source_domain, source_url)
    assert is_valid is False


def test_parse(mocker, category_extractor):
    # Sample HTML for testing
    html = """
    <html>
        <body>
            <a href="http://www.example.com/category1">Category 1</a>
            <a href="http://www.example.com/category2/">Category 2</a>
            <a href="http://www.example.com/category3/page.html">Category 3</a>
            <a href="http://www.another-domain.com/category4">Category 4</a>
            <a href="/category5">Category 5</a>
        </body>
    </html>
    """
    doc = lxml.html.fromstring(html)
    source_url = "http://www.example.com"

    categories = category_extractor.parse(source_url, doc)

    expected_categories = [
        "http://www.example.com/",
        "http://www.example.com/category1",
        "http://www.example.com/category2",
        "http://www.example.com/category5",
    ]
    assert sorted(categories) == sorted(expected_categories)


def test_get_other_links(category_extractor):
    html = """
    <html>
        <body>
            <script>
                var url1 = "https://www.example.com/news/article1";
                var url2 = "https://www.example.com/news/article2.html";
            </script>
            <a href="http://www.example.com/category1">Category 1</a>
        </body>
    </html>
    """
    doc = lxml.html.fromstring(html)
    links = list(category_extractor._get_other_links(doc, source_domain="example"))

    expected_links = [
        "https://www.example.com/news/article1",
        "https://www.example.com/news/article2.html",
        "http://www.example.com/category1",
    ]
    assert sorted(links) == sorted(expected_links)
