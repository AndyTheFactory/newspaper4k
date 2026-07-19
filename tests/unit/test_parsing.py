import re
from unittest.mock import patch

from newspaper import parsers
from newspaper.configuration import Configuration
from newspaper.extractors import ContentExtractor
from newspaper.extractors.articlebody_extractor import ArticleBodyExtractor
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


class TestArticleBodyExtractor:
    def test_calculate_best_node_skips_empty_candidates(self):
        """Verify that calculate_best_node does not select a node with no text
        content, which would be emptied by post_cleanup."""
        config = Configuration()
        extractor = ArticleBodyExtractor(config)

        html = """
        <html><body>
        <div id="images-only">
          <img src="image1.jpg" />
          <img src="image2.jpg" />
        </div>
        <div id="article-content">
          <p>The first paragraph of the article contains important information.</p>
          <p>The second paragraph continues the discussion with more details.</p>
          <p>The third paragraph concludes the article with a summary of key points.</p>
        </div>
        </body></html>
        """

        doc = parsers.fromstring(html)

        # Give the empty node a higher gravity score than the text node,
        # simulating a case where the scoring algorithm would otherwise prefer it.
        empty_node = doc.xpath('//div[@id="images-only"]')[0]
        parsers.set_attribute(empty_node, "gravityScore", "1000")

        text_node = doc.xpath('//div[@id="article-content"]')[0]
        parsers.set_attribute(text_node, "gravityScore", "10")

        with patch.object(
            extractor, "compute_gravity_scores", return_value=[empty_node, text_node]
        ), patch.object(extractor, "compute_features", return_value=[]):
            top_node = extractor.calculate_best_node(doc)

        # The empty node must be skipped; the text-containing node must be chosen.
        assert top_node is not None
        assert top_node == text_node

    def test_calculate_best_node_returns_none_when_all_empty(self):
        """Verify that calculate_best_node returns None when all candidates
        have no text content."""
        config = Configuration()
        extractor = ArticleBodyExtractor(config)

        html = """
        <html><body>
        <div id="images-only">
          <img src="image1.jpg" />
        </div>
        </body></html>
        """

        doc = parsers.fromstring(html)

        empty_node = doc.xpath('//div[@id="images-only"]')[0]
        parsers.set_attribute(empty_node, "gravityScore", "500")

        with patch.object(
            extractor, "compute_gravity_scores", return_value=[empty_node]
        ), patch.object(extractor, "compute_features", return_value=[]):
            top_node = extractor.calculate_best_node(doc)

        assert top_node is None
