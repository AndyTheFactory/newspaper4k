# ruff: noqa: D100, D103

from types import SimpleNamespace

import lxml.etree
import lxml.html
import pytest

from newspaper.configuration import Configuration
from newspaper.extractors.articlebody_extractor import ArticleBodyExtractor


def make_extractor():
    return ArticleBodyExtractor(Configuration())


def test_init_and_parse_set_article_nodes(mocker):
    config = Configuration()
    extractor = ArticleBodyExtractor(config)
    doc = object()
    top_node = object()
    complemented = object()
    stopwords = object()
    mocker.patch("newspaper.extractors.articlebody_extractor.StopWords", return_value=stopwords)
    mocker.patch.object(extractor, "calculate_best_node", return_value=top_node)
    complement = mocker.patch.object(extractor, "complement_with_siblings", return_value=complemented)

    extractor.parse(doc)

    assert extractor.config is config
    assert extractor.stopwords is stopwords
    assert extractor.top_node is top_node
    assert extractor.top_node_complemented is complemented
    complement.assert_called_once_with(top_node)


def test_calculate_best_node_boosts_sorts_and_uses_highest_score(mocker):
    extractor = make_extractor()
    doc = object()
    shallow = lxml.html.fromstring('<p node_level="1">x</p>')
    deep = lxml.html.fromstring('<p node_level="3">x</p>')
    lower = lxml.html.fromstring("<div>x</div>")
    higher = lxml.html.fromstring("<div>x</div>")
    lower.set("gravityScore", "2")
    higher.set("gravityScore", "8")
    boost = mocker.patch.object(extractor, "boost_highly_likely_nodes")
    mocker.patch.object(extractor, "compute_features", return_value=[shallow, deep])
    gravity = mocker.patch.object(extractor, "compute_gravity_scores", return_value=[lower, higher])

    assert extractor.calculate_best_node(doc) is higher
    boost.assert_called_once_with(doc)
    gravity.assert_called_once_with([deep, shallow])


def test_compute_gravity_scores_propagates_counts_and_scores(mocker):
    extractor = make_extractor()
    root = lxml.html.fromstring('<section><div><p stop_words="4"></p></div></section>')
    node = root.xpath("//p")[0]
    mocker.patch.object(extractor, "is_boostable", return_value=True)

    parents = extractor.compute_gravity_scores([node])

    parent = node.getparent()
    assert set(parents) == {parent, root}
    assert float(parent.get("gravityScore")) == 34
    assert float(root.get("gravityScore")) == pytest.approx(13.6)
    assert parent.get("gravityNodes") == "1.0"
    assert root.get("gravityNodes") == "1.0"


def test_compute_features_sets_attributes_and_filters_candidates(mocker):
    extractor = make_extractor()
    good = lxml.html.fromstring("<p>good</p>")
    linked = lxml.html.fromstring("<p>linked</p>")
    empty = lxml.html.fromstring("<p></p>")
    mocker.patch.object(extractor, "nodes_to_check", return_value=[good, linked, empty])
    extractor.stopwords = mocker.Mock()
    extractor.stopwords.get_stopword_count.side_effect = [
        SimpleNamespace(stop_word_count=5, word_count=8),
        SimpleNamespace(stop_word_count=6, word_count=9),
    ]
    mocker.patch(
        "newspaper.extractors.articlebody_extractor.parsers.is_highlink_density",
        side_effect=lambda node, _language: node is linked,
    )

    assert extractor.compute_features(lxml.html.fromstring("<html/>")) == [good]
    assert good.get("stop_words") == "5"
    assert good.get("word_count") == "8"
    assert good.get("is_highlink_density") == "0"
    assert linked.get("is_highlink_density") == "1"


def test_nodes_to_check_prefers_article_like_divs_and_falls_back():
    extractor = make_extractor()
    doc = lxml.html.fromstring(
        "<html><body><p>p</p><pre>pre</pre><td>td</td><article>article</article>"
        '<div class="story"><div class="paragraph">paragraph</div></div><div>other</div></body></html>'
    )

    nodes = extractor.nodes_to_check(doc)

    assert {node.tag for node in nodes} >= {"p", "pre", "td", "article", "div"}
    assert doc.xpath('//div[text()="other"]')[0] not in nodes


def test_is_boostable_checks_nearby_same_tag_stopwords(mocker):
    extractor = make_extractor()
    node = lxml.html.fromstring("<p></p>")
    other_tag = lxml.html.fromstring('<div stop_words="20"></div>')
    weak = lxml.html.fromstring('<p stop_words="5"></p>')
    strong = lxml.html.fromstring('<p stop_words="6"></p>')
    mocker.patch.object(extractor, "walk_siblings", return_value=[other_tag, weak, strong])

    assert extractor.is_boostable(node) is True
    mocker.patch.object(extractor, "walk_siblings", return_value=[weak])
    assert extractor.is_boostable(node) is False


def test_boost_highly_likely_nodes_updates_matching_candidates(mocker):
    extractor = make_extractor()
    doc = lxml.html.fromstring("<html><body><article><p>text</p></article></body></html>")
    score = mocker.patch.object(
        extractor,
        "is_highly_likely",
        side_effect=lambda node: 12 if node.tag == "article" else 0,
    )
    update = mocker.patch.object(extractor, "update_score")

    extractor.boost_highly_likely_nodes(doc)

    assert score.call_count >= 2
    update.assert_called_once_with(doc.xpath("//article")[0], 12.0)


def test_is_highly_likely_supports_exact_and_regex_definitions(mocker):
    extractor = make_extractor()
    mocker.patch(
        "newspaper.extractors.articlebody_extractor.defines.ARTICLE_BODY_TAGS",
        [
            {"tag": "div", "class": "article", "score_boost": 10},
            {"tag": "div", "id": "re:^story-", "score_boost": 20},
        ],
    )

    assert extractor.is_highly_likely(lxml.html.fromstring('<div class="ARTICLE"></div>')) == 10
    assert extractor.is_highly_likely(lxml.html.fromstring('<div id="story-main"></div>')) == 20
    assert extractor.is_highly_likely(lxml.html.fromstring('<section id="story-main"></section>')) == 0


def test_update_score_and_node_count_accumulate_and_ignore_none():
    extractor = make_extractor()
    node = lxml.html.fromstring("<div></div>")
    node.set("gravityScore", "2.5")
    node.set("gravityNodes", "1")

    extractor.update_score(node, 1.5)
    extractor.update_node_count(node, 2)
    extractor.update_score(None, 10)
    extractor.update_node_count(None, 10)

    assert node.get("gravityScore") == "4.0"
    assert node.get("gravityNodes") == "3.0"


def test_add_siblings_prepends_plausible_content_to_copy(mocker):
    extractor = make_extractor()
    top = lxml.html.fromstring("<div><p>top</p></div>")
    sibling = lxml.html.fromstring("<div></div>")
    added = lxml.html.fromstring("<p>added</p>")
    mocker.patch.object(extractor, "get_normalized_score", return_value=5)
    mocker.patch.object(extractor, "walk_siblings", return_value=[sibling])
    plausible = mocker.patch.object(extractor, "get_plausible_content", return_value=[added])

    result = extractor.add_siblings(top)

    assert result is not top
    assert [child.text for child in result] == ["added", "top"]
    plausible.assert_called_once_with(sibling, 5)


def test_get_plausible_content_handles_special_direct_and_nested_nodes(mocker):
    extractor = make_extractor()
    assert extractor.get_plausible_content(lxml.etree.Comment("ignored"), 10) == []

    direct = lxml.html.fromstring('<p tail="unused">direct text</p>')
    mocker.patch("newspaper.extractors.articlebody_extractor.parsers.is_highlink_density", return_value=False)
    result = extractor.get_plausible_content(direct, 100)
    assert [node.text for node in result] == ["direct text"]
    assert result[0] is not direct

    nested = lxml.html.fromstring(
        '<div><p stop_words="10">accepted text</p><p stop_words="2">too weak</p><p stop_words="0">no score</p></div>'
    )
    result = extractor.get_plausible_content(nested, 20)
    assert [node.text for node in result] == ["accepted text"]


def test_get_normalized_score_and_walk_siblings():
    extractor = make_extractor()
    parent = lxml.html.fromstring("<div><p>one</p><p>two</p><p>zero</p><section>top</section></div>")
    parent[0].set("gravityScore", "2")
    parent[1].set("gravityScore", "4")
    top = parent[-1]

    assert extractor.get_normalized_score(parent) == 3
    assert extractor.get_normalized_score(lxml.html.fromstring("<div/>")) == float("inf")
    assert extractor.walk_siblings(top) == [parent[2], parent[1], parent[0]]


def test_complement_with_siblings_handles_none_and_delegates(mocker):
    extractor = make_extractor()
    node = lxml.html.fromstring("<div></div>")
    expected = object()
    add = mocker.patch.object(extractor, "add_same_level_candidates", return_value=expected)

    assert extractor.complement_with_siblings(None) is None
    assert extractor.complement_with_siblings(node) is expected
    add.assert_called_once_with(node)


def test_add_same_level_candidates_keeps_similar_scored_low_density_nodes(mocker):
    extractor = make_extractor()
    doc = lxml.html.fromstring(
        "<html><body><div>top</div><div>include</div><div>weak</div><section>wrong tag</section></body></html>"
    )
    top = doc.xpath('//div[text()="top"]')[0]
    top.set("gravityScore", "10")
    doc.xpath('//div[text()="include"]')[0].set("gravityScore", "4")
    doc.xpath('//div[text()="weak"]')[0].set("gravityScore", "2")
    doc.xpath('//section[text()="wrong tag"]')[0].set("gravityScore", "9")
    mocker.patch("newspaper.extractors.articlebody_extractor.parsers.is_highlink_density", return_value=False)

    result = extractor.add_same_level_candidates(top)

    assert [child.text for child in result] == ["top", "include"]
    assert all(child.getparent() is result for child in result)
