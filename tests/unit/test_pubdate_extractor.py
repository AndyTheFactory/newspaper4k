# ruff: noqa: D100, D103

from datetime import datetime

import lxml.html

from newspaper.configuration import Configuration
from newspaper.extractors.pubdate_extractor import PubdateExtractor


def make_extractor():
    return PubdateExtractor(Configuration())


def test_init_and_parse_date_str():
    config = Configuration()
    extractor = PubdateExtractor(config)

    assert extractor.config is config
    assert extractor.pubdate is None
    assert extractor._parse_date_str("2024-02-03T04:05:06Z") == datetime.fromisoformat("2024-02-03T04:05:06+00:00")
    assert extractor._parse_date_str(None) is None
    assert extractor._parse_date_str("not-a-date") is None


def test_parse_prefers_url_date_over_lower_scored_sources():
    extractor = make_extractor()
    doc = lxml.html.fromstring(
        """
        <html><head><meta property="article:published_time" content="2020-01-02"></head>
        <body><time datetime="2021-03-04">Published on</time></body></html>
        """
    )

    assert extractor.parse("https://example.com/2024/05/06/story", doc) == datetime(2024, 5, 6)


def test_parse_reads_graph_and_top_level_json_ld(mocker):
    extractor = make_extractor()
    doc = lxml.html.fromstring("<html></html>")
    mocker.patch(
        "newspaper.extractors.pubdate_extractor.parsers.get_ld_json_object",
        return_value=[
            {"dateCreated": "2022-01-01", "datePublished": "2023-02-03"},
            {"@graph": ["ignored", {"datePublished": "2024-04-05"}]},
        ],
    )

    assert extractor.parse("https://example.com/story", doc) == datetime(2024, 4, 5)


def test_parse_returns_none_without_candidates(mocker):
    extractor = make_extractor()
    doc = lxml.html.fromstring("<html></html>")
    mocker.patch("newspaper.extractors.pubdate_extractor.parsers.get_ld_json_object", return_value=[])

    assert extractor.parse("https://example.com/story", doc) is None
