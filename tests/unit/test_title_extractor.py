# ruff: noqa: D100, D103

import lxml.html
import pytest

from newspaper.configuration import Configuration
from newspaper.extractors.title_extractor import TitleExtractor


def make_extractor():
    return TitleExtractor(Configuration())


def test_init_and_missing_title():
    config = Configuration()
    extractor = TitleExtractor(config)

    assert extractor.config is config
    assert extractor.title == ""
    assert extractor.parse(lxml.html.fromstring("<html><h1>Ignored heading</h1></html>")) == ""


@pytest.mark.parametrize(
    ("html", "expected"),
    [
        (
            "<html><title>A complete article title</title><h1>A complete article title</h1></html>",
            "A complete article title",
        ),
        (
            "<html><title>A complete article title - Example</title><h1>A complete article title</h1>"
            '<meta property="og:title" content="A complete article title"></html>',
            "A complete article title",
        ),
        (
            "<html><title>A longer visible article title - Example</title><h1>A longer visible article title</h1>"
            '<meta property="og:title" content="A longer visible title"></html>',
            "A longer visible article title",
        ),
        (
            "<html><title>Open Graph Title - Example</title><h1>Different visible heading here</h1>"
            '<meta property="og:title" content="Open Graph Title"></html>',
            "Open Graph Title",
        ),
    ],
)
def test_parse_title_selection_rules(html, expected):
    assert make_extractor().parse(lxml.html.fromstring(html)) == expected


def test_parse_uses_longest_meaningful_h1_as_hint():
    doc = lxml.html.fromstring(
        "<html><title>Site | The useful and sufficiently long heading</title>"
        "<h1>Short</h1><h1>The useful and sufficiently long heading</h1></html>"
    )

    assert make_extractor().parse(doc) == "The useful and sufficiently long heading"


def test_split_title_prefers_hint_then_longest_piece_and_replaces_entities():
    extractor = make_extractor()

    assert extractor._split_title("Site | Chosen story | Other", "|", "Chosen story") == " Chosen story "
    assert extractor._split_title("Tiny | This is the longest title piece", "|") == " This is the longest title piece"
    assert extractor._split_title("Site &raquo; Story", "&raquo;") == " Story"
