# ruff: noqa: D100, D103

import lxml.html

from newspaper.configuration import Configuration
from newspaper.extractors.metadata_extractor import MetadataExtractor


def make_extractor():
    return MetadataExtractor(Configuration())


def test_init_creates_expected_metadata_shape():
    config = Configuration()
    extractor = MetadataExtractor(config)

    assert extractor.config is config
    assert set(extractor.meta_data) == {
        "language",
        "type",
        "canonical_link",
        "site_name",
        "description",
        "keywords",
        "tags",
        "data",
    }


def test_parse_populates_metadata(mocker):
    extractor = make_extractor()
    doc = lxml.html.fromstring("<html></html>")
    mocker.patch.object(extractor, "_get_meta_language", return_value="en")
    mocker.patch.object(extractor, "_get_canonical_link", return_value="https://example.com/canonical")
    mocker.patch.object(
        extractor,
        "_get_meta_field",
        side_effect=["article", "Example", "Description", "one, two"],
    )
    mocker.patch.object(extractor, "_get_metadata", return_value={"og": {"type": "article"}})

    result = extractor.parse("https://example.com/a", doc)

    assert result == {
        "language": "en",
        "type": "article",
        "canonical_link": "https://example.com/canonical",
        "site_name": "Example",
        "description": "Description",
        "keywords": ["one", "two"],
        "tags": None,
        "data": {"og": {"type": "article"}},
    }


def test_get_meta_language_prefers_html_and_maps_iso_639_3():
    extractor = make_extractor()

    assert extractor._get_meta_language(lxml.html.fromstring('<html lang="eng"></html>')) == "en"
    assert extractor._get_meta_language(lxml.html.fromstring('<html lang="EN-us"></html>')) == "en"
    assert extractor._get_meta_language(lxml.html.fromstring('<html lang="1"></html>')) is None


def test_get_meta_language_uses_meta_fallback(mocker):
    extractor = make_extractor()
    doc = lxml.html.fromstring("<html></html>")
    mocker.patch(
        "newspaper.extractors.metadata_extractor.parsers.get_tags",
        side_effect=[[], ["fra"]],
    )

    assert extractor._get_meta_language(doc) == "fr"


def test_get_canonical_link_prefers_link_and_resolves_relative_values():
    extractor = make_extractor()
    absolute = lxml.html.fromstring(
        '<html><link rel="canonical" href="https://canonical.example/a">'
        '<meta property="og:url" content="https://example.com/other"></html>'
    )
    relative = lxml.html.fromstring('<html><link rel="canonical" href="example.com/path?q=1#part"></html>')

    assert extractor._get_canonical_link("https://example.com/original", absolute) == "https://canonical.example/a"
    assert extractor._get_canonical_link("https://example.com/original", relative) == "https://example.com/path"
    assert extractor._get_canonical_link("https://example.com/original", lxml.html.fromstring("<html/>")) is None


def test_get_metadata_builds_nested_keys_and_converts_numbers():
    extractor = make_extractor()
    doc = lxml.html.fromstring(
        """
        <html><head>
          <meta name="author" content="Ada">
          <meta name="views" content="25">
          <meta name="og" content="root">
          <meta property="og:type" content="article">
          <meta property="og:image:width" content="640">
          <meta property="og:image:height" content="480">
          <meta name="empty" content="">
        </head></html>
        """
    )

    assert extractor._get_metadata(doc) == {
        "author": "Ada",
        "views": 25,
        "og": {
            "og": "root",
            "type": "article",
            "image": {"width": 640, "height": 480},
        },
    }


def test_get_tags_and_meta_field():
    extractor = make_extractor()
    doc = lxml.html.fromstring(
        """
        <html><head><meta property="og:description" content="  Summary  "></head>
        <body><a href="/tag/python">Python</a><a rel="tag">Testing</a></body></html>
        """
    )

    assert extractor._get_tags(doc) == {"Python", "Testing"}
    assert extractor._get_meta_field(doc, ["description", "og:description"]) == "Summary"
    assert extractor._get_meta_field(doc, "keywords") == ""
