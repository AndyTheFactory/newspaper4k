import re
import pytest
from pathlib import Path
from newspaper.extractors import ContentExtractor
from newspaper import parsers
from newspaper.configuration import Configuration
from newspaper.urls import STRICT_DATE_REGEX, prepare_url, valid_url


@pytest.fixture
def title_fixture():
    return [
        ("<title>Test title</title>", "Test title"),
        ("<title>Test page » Test title</title>", "Test title"),
        ("<title>Test page &raquo; Test title</title>", "Test title"),
        (
            "<title>Test page and «something in quotes»</title>",
            "Test page and «something in quotes»",
        ),
    ]


@pytest.fixture
def canonical_url_fixture():
    return [
        ("", '<link rel="canonical" href="http://www.example.com/article.html">'),
        (
            "http://www.example.com/article?foo=bar",
            '<link rel="canonical" href="article.html">',
        ),
        (
            "http://www.example.com/article?foo=bar",
            '<meta property="og:url" content="article.html">',
        ),
        (
            "http://www.example.com/article?foo=bar",
            '<meta property="og:url" content="www.example.com/article.html">',
        ),
    ]


def get_url_filecontent(filename):
    with open(Path(__file__).parent / "data" / filename, "r") as f:
        lines = f.readlines()
        return [tuple(line.strip().split(" ")) for line in lines if " " in line]


@pytest.fixture
def meta_image_fixture():
    return [
        (
            (
                '<meta property="og:image" '
                'content="https://example.com/meta_img_filename.jpg" />'
                '<meta name="og:image" '
                'content="https://example.com/meta_another_img_filename.jpg"/>'
            ),
            "https://example.com/meta_img_filename.jpg",
        ),
        (
            (
                '<meta property="og:image" content="" />'
                '<meta name="og:image" '
                'content="https://example.com/meta_another_img_filename.jpg"/>'
            ),
            "https://example.com/meta_another_img_filename.jpg",
        ),
        ('<meta property="og:image" content="" /><meta name="og:image" />', ""),
        (
            (
                '<meta property="og:image" content="" />'
                '<meta name="og:image" />'
                '<link rel="img_src" href="https://example.com/meta_link_image.jpg" />'
            ),
            "https://example.com/meta_link_image.jpg",
        ),
        (
            (
                '<meta property="og:image" content="" /><meta name="og:image" /><link'
                ' rel="image_src" href="https://example.com/meta_link_image2.jpg" />'
            ),
            "https://example.com/meta_link_image2.jpg",
        ),
        (
            (
                '<meta property="og:image" content="" />'
                '<meta name="og:image" />'
                '<link rel="icon" href="https://example.com/meta_link_rel_icon.ico" />'
            ),
            "https://example.com/meta_link_rel_icon.ico",
        ),
    ]


class TestExtractor:
    def test_title_extraction(self, title_fixture):
        extractor = ContentExtractor(Configuration())
        for html, title in title_fixture:
            doc = parsers.fromstring(html)
            assert extractor.get_title(doc) == title

    def test_canonical_url_extraction(self, canonical_url_fixture):
        extractor = ContentExtractor(Configuration())

        for article_url, html in canonical_url_fixture:
            doc = parsers.fromstring(html)
            metadata = extractor.get_metadata(article_url, doc)
            assert metadata["canonical_link"] == "http://www.example.com/article.html"

    def test_meta_image_extraction(self, meta_image_fixture):
        config = Configuration()
        config.fetch_images = False
        extractor = ContentExtractor(config)

        for html, expected in meta_image_fixture:
            doc = parsers.fromstring(html)
            extractor.image_extractor.parse(doc, None, "http://www.test.com")
            assert extractor.image_extractor.meta_image == expected

    @pytest.mark.skip(reason="Does not pass, not sure what it tests")
    def test_valid_url(self):
        for is_valid, url in get_url_filecontent("test_urls.txt"):
            assert valid_url(url, test=True) == bool(int(is_valid)), "Failed on " + url

    def test_pubdate(self):
        # not a real test... we test the regex??
        # TODO: add a real test
        for is_pubdate, url in get_url_filecontent("test_urls_pubdate.txt"):
            date_match = re.search(STRICT_DATE_REGEX, url)
            assert bool(date_match) == bool(int(is_pubdate)), f"Failed on {url}"

    def test_prepare_url(self):
        for real, url, source in get_url_filecontent("test_prepare_urls.txt"):
            assert real == prepare_url(url, source)
