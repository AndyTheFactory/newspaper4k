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


@pytest.mark.parametrize(
    ("html", "expected"),
    [
        # A hyphen with no surrounding whitespace belongs to the title, not to a
        # site-name suffix. Only the whitespace-padded " - " separates the two.
        (
            "<html><title>TransJamaican Highway Limited (TJH)- Trade Disclosure"
            " - Jamaica Stock Exchange</title></html>",
            "TransJamaican Highway Limited (TJH)- Trade Disclosure",
        ),
        # A hyphenated word, and no site name at all: nothing should be split off.
        (
            "<html><title>plus-minus announce first new album in a decade</title></html>",
            "plus-minus announce first new album in a decade",
        ),
        # Same for the other intra-word delimiters.
        (
            "<html><title>Converting km/h to m/s for beginners</title></html>",
            "Converting km/h to m/s for beginners",
        ),
        (
            "<html><title>Why snake_case still wins arguments</title></html>",
            "Why snake_case still wins arguments",
        ),
        # The site name must still be stripped when it really is delimited.
        (
            "<html><title>An ordinary article title - Example News</title></html>",
            "An ordinary article title",
        ),
        # A pipe needs no padding: it does not occur inside ordinary words.
        (
            "<html><title>Site|An article title that is clearly the longest</title></html>",
            "An article title that is clearly the longest",
        ),
    ],
)
def test_parse_only_splits_on_delimiters_that_separate_a_site_name(html, expected):
    assert make_extractor().parse(lxml.html.fromstring(html)) == expected


def test_split_title_prefers_hint_then_longest_piece_and_replaces_entities():
    extractor = make_extractor()

    assert extractor._split_title("Site | Chosen story | Other", "|", "Chosen story") == " Chosen story "
    assert extractor._split_title("Tiny | This is the longest title piece", "|") == " This is the longest title piece"
    assert extractor._split_title("Site &raquo; Story", "&raquo;") == " Story"
