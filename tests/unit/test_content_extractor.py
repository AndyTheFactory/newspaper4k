# ruff: noqa: D100, D103

from datetime import datetime
from types import SimpleNamespace

import lxml.html

from newspaper.configuration import Configuration
from newspaper.extractors.content_extractor import ContentExtractor


def test_init_builds_all_subextractors_with_same_config(mocker):
    factories = {}
    for class_name in (
        "TitleExtractor",
        "AuthorsExtractor",
        "PubdateExtractor",
        "ArticleBodyExtractor",
        "MetadataExtractor",
        "CategoryExtractor",
        "ImageExtractor",
        "VideoExtractor",
    ):
        factories[class_name] = mocker.patch(
            f"newspaper.extractors.content_extractor.{class_name}", return_value=object()
        )
    config = Configuration()

    ContentExtractor(config)

    for factory in factories.values():
        factory.assert_called_once_with(config)


def test_simple_accessors_delegate_to_subextractors(mocker):
    extractor = ContentExtractor(Configuration())
    doc = object()
    top_node = object()
    published = datetime(2024, 2, 3)
    extractor.author_extractor.parse = mocker.Mock(return_value=["Ada"])
    extractor.pubdate_extractor.parse = mocker.Mock(return_value=published)
    extractor.title_extractor.parse = mocker.Mock(return_value="A title")
    extractor.metadata_extractor.parse = mocker.Mock(return_value={"language": "en"})
    extractor.categories_extractor.parse = mocker.Mock(return_value=["https://example.com/news"])
    extractor.video_extractor.parse = mocker.Mock(return_value=["video"])

    assert extractor.get_authors(doc) == ["Ada"]
    assert extractor.get_publishing_date("https://example.com/a", doc) == published
    assert extractor.get_title(doc) == "A title"
    assert extractor.get_metadata("https://example.com/a", doc) == {"language": "en"}
    assert extractor.get_category_urls("https://example.com", doc) == ["https://example.com/news"]
    assert extractor.get_videos(doc, top_node) == ["video"]

    extractor.author_extractor.parse.assert_called_once_with(doc)
    extractor.pubdate_extractor.parse.assert_called_once_with("https://example.com/a", doc)
    extractor.video_extractor.parse.assert_called_once_with(doc, top_node)


def test_get_feed_urls_resolves_deduplicates_and_limits_results():
    extractor = ContentExtractor(Configuration())
    doc = lxml.html.fromstring(
        '<html><link type="application/rss+xml" href="/feed.xml">'
        '<link type="application/rss+xml" href="https://feeds.example.net/all.xml"></html>'
    )
    categories = [SimpleNamespace(doc=doc), SimpleNamespace(doc=doc)]

    result = extractor.get_feed_urls("https://example.com/news/", categories)

    assert set(result) == {
        "https://example.com/feed.xml",
        "https://feeds.example.net/all.xml",
    }


def test_image_and_article_body_methods_update_and_expose_state(mocker):
    extractor = ContentExtractor(Configuration())
    doc = object()
    top_node = object()
    complemented = object()
    extractor.image_extractor.parse = mocker.Mock()
    extractor.article_body_extractor.parse = mocker.Mock()
    extractor.article_body_extractor.top_node = top_node
    extractor.article_body_extractor.top_node_complemented = complemented

    extractor.parse_images("https://example.com/a", doc, top_node)

    extractor.image_extractor.parse.assert_called_once_with(doc, top_node, "https://example.com/a")
    assert extractor.calculate_best_node(doc) is top_node
    extractor.article_body_extractor.parse.assert_called_once_with(doc)
    assert extractor.top_node is top_node
    assert extractor.top_node_complemented is complemented
