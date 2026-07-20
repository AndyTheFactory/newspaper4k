# ruff: noqa: D100, D103

import lxml.html

from newspaper.configuration import Configuration
from newspaper.extractors.authors_extractor import AuthorsExtractor


def make_extractor():
    return AuthorsExtractor(Configuration())


def test_init_sets_empty_authors_and_config():
    config = Configuration()
    extractor = AuthorsExtractor(config)

    assert extractor.config is config
    assert extractor.authors == []


def test_parse_byline_removes_markup_stop_tokens_and_invalid_names():
    extractor = make_extractor()

    result = extractor._parse_byline("<div>By: <strong>Lucas Ou-Yang</strong>, Alex Smith and Desk 123</div>")

    assert result == ["Lucas Ou-Yang", "Alex Smith"]


def test_get_authors_from_ld_supports_documented_shapes():
    extractor = make_extractor()

    assert extractor._get_authors_from_ld({"name": ["Ada Lovelace", "Grace Hopper"]}) == [
        "Ada Lovelace",
        "Grace Hopper",
    ]
    assert extractor._get_authors_from_ld(
        [{"name": "Katherine Johnson"}, {"name": {"name": "Dorothy Vaughan"}}, "Mary Jackson"]
    ) == ["Katherine Johnson", "Dorothy Vaughan", "Mary Jackson"]
    assert extractor._get_authors_from_ld("Annie Easley") == ["Annie Easley"]
    assert extractor._get_authors_from_ld(42) == []


def test_get_text_from_element_ignores_script_style_and_time():
    extractor = make_extractor()
    node = lxml.html.fromstring(
        "<div>By Ada Lovelace<script>ignored()</script><style>.ignored{}</style><time>today</time></div>"
    )

    assert extractor._get_text_from_element(node) == "By Ada Lovelace"
    assert extractor._get_text_from_element(lxml.html.fromstring("<script>ignored()</script>")) == ""
    assert extractor._get_text_from_element(None) == ""


def test_parse_combines_json_ld_meta_and_byline_and_deduplicates(mocker):
    extractor = make_extractor()
    doc = lxml.html.fromstring(
        """
        <html><head><meta name="author" content="By Ada Lovelace"></head>
        <body><span class="byline">By Grace Hopper, Senior Reporter Ada Lovelace</span></body></html>
        """
    )
    mocker.patch(
        "newspaper.extractors.authors_extractor.parsers.get_ld_json_object",
        return_value=[
            {"author": {"name": "ADA LOVELACE"}},
            {"@graph": [{"@type": "Person", "name": "Katherine Johnson"}]},
        ],
    )

    authors = extractor.parse(doc)

    assert authors == ["Ada Lovelace", "Katherine Johnson", "Grace Hopper"]
    assert extractor.authors == authors
