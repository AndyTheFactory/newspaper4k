import re

from newspaper import parsers
from newspaper.configuration import Configuration
from newspaper.extractors import ContentExtractor
from newspaper.urls import STRICT_DATE_REGEX, prepare_url
from tests.conftest import get_url_filecontent


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

    def test_pubdate(self):
        # not a real test... we test the regex??
        # TODO: add a real test
        for is_pubdate, url in get_url_filecontent("test_urls_pubdate.txt"):
            date_match = re.search(STRICT_DATE_REGEX, url)
            assert bool(date_match) == bool(int(is_pubdate)), f"Failed on {url}"

    def test_prepare_url(self):
        for real, url, source in get_url_filecontent("test_prepare_urls.txt"):
            assert real == prepare_url(url, source)
