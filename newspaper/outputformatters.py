# -*- coding: utf-8 -*-
# Much of the code here was forked from https://github.com/codelucas/newspaper
# Copyright (c) Lucas Ou-Yang (codelucas)

"""
Module provinding the OutputFormatter class, which converts the article top node
to plain text, removing most boilerplate and other unwanted elements.
"""
from copy import deepcopy
import logging
import re
from statistics import mean, stdev
from typing import Any, Dict, Optional, Tuple

import lxml
from newspaper import parsers
from newspaper.configuration import Configuration
from newspaper import settings

log = logging.getLogger(__name__)

WHITESPACE_CHARS = "\n\r\t " + "\u00a0" + "\ufeff"
MAX_PARAGRAPH_BEFORE_TITLE = 200


class OutputFormatter:
    """Class that converts the article top node into text, cleaning up
    debris tags, replacing <br> with newlines, etc.

    if `config.clean_article_html` is True, then the article's html is
    cleaned as well. Only `settings.CLEAN_ARTICLE_TAGS` are allowed to
    remain in the html.
    """

    def __init__(self, config=None):
        self.config = config or Configuration()

    def get_formatted(
        self, top_node: lxml.html.HtmlElement, article_title: Optional[str] = None
    ) -> Tuple[str, str]:
        """Returns the body text of an article, and also the cleaned html body
        article of the article.
        Arguments:
            top_node {lxml.html.HtmlElement} -- The top node element of the article
            article_title {str} -- The title of the article, if available, to
                be removed from the text (and max 1 paragraph before it)
        Returns:
            Tuple[str, str] -- The body text of the article, and the cleaned
            html body of the article
        """
        html, text = "", ""
        if top_node is None:
            return (text, html)

        node_cleaned = deepcopy(top_node)

        self._remove_negativescores_nodes(node_cleaned)

        if not self.config.clean_article_html:
            # We deliver the HTML untouched (only the negative nodes are removed)
            html = parsers.node_to_string(node_cleaned)

        self._remove_advertisement_nodes(node_cleaned)

        self._remove_unlikely_nodes(node_cleaned)

        self._remove_empty_tags(node_cleaned)

        # removes some same level tags that might
        # contain non-content like menus, gallery,  etc.
        # this can misfire on some sites
        self._remove_trailing_media_div(node_cleaned)

        if self.config.clean_article_html:
            html = self._create_clean_html(node_cleaned)

        text = self._convert_to_text(node_cleaned, article_title)

        return (text, html)

    def _convert_to_text(
        self, top_node: lxml.html.HtmlElement, article_title: Optional[str] = None
    ) -> str:
        article_cleaner = lxml.html.clean.Cleaner()
        article_cleaner.javascript = True
        article_cleaner.style = True
        article_cleaner.remove_unknown_tags = False
        article_cleaner.meta = True
        article_cleaner.embedded = True
        article_cleaner.frames = True
        article_cleaner.allow_tags = settings.BLOCK_LEVEL_TAGS + ["br"]

        cleaned_node = article_cleaner.clean_html(top_node)
        # TODO: do not remove newlines in <pre> tags

        txts = [
            re.sub(r"[\s\t\xa0\uFEFF]+", " ", value, flags=re.UNICODE)
            for value in cleaned_node.itertext()
        ]
        txts = [x.strip(" \t") for x in txts if x.strip(WHITESPACE_CHARS)]
        if article_title and len(txts) > 1:
            # Remove the title and the first paragraph before it
            # (if it's not too long)
            def normalize_string(s: str) -> str:
                # remove punctuation, double spaces and lowers the case
                s = re.sub(r"[^\w\s]", "", s)
                s = re.sub(r"\s+", " ", s)
                s = s.lower()
                return s

            if normalize_string(txts[0]) == normalize_string(article_title):
                txts = txts[1:]
            elif len(txts[0]) < MAX_PARAGRAPH_BEFORE_TITLE and normalize_string(
                txts[1]
            ) == normalize_string(article_title):
                txts = txts[2:]

        return "\n\n".join(txts)

    def _create_clean_html(self, top_node: lxml.html.HtmlElement):
        article_cleaner = lxml.html.clean.Cleaner()
        article_cleaner.javascript = True
        article_cleaner.style = True
        article_cleaner.remove_unknown_tags = False
        article_cleaner.meta = True
        article_cleaner.embedded = True

        article_cleaner.allow_tags = settings.CLEAN_ARTICLE_TAGS

        cleaned_node = article_cleaner.clean_html(top_node)
        return parsers.node_to_string(cleaned_node)

    def _add_newline_to_br(self, top_node: lxml.html.HtmlElement):
        """Replace all br tags in 'element' with a newline character"""
        br_tags = top_node.xpath(".//br")
        for br in br_tags:
            br.tail = "\n" + br.tail if br.tail else "\n"

    def _remove_negativescores_nodes(self, top_node: lxml.html.HtmlElement):
        """If there are elements inside our top node that have a
        negative gravity score, let's give em the boot.
        """
        gravity_items = top_node.xpath(".//*[@gravityScore]")
        for item in gravity_items:
            score = item.attrib.get("gravityScore", "0")
            score = float(score)
            if score < 1:
                item.getparent().remove(item)

    def _remove_empty_tags(self, top_node: lxml.html.HtmlElement):
        """It's common in top_node to have tags that are filled with data
        in their properties but do not have any displayable text.
        """
        all_nodes = parsers.get_tags(top_node)
        all_nodes.reverse()
        for el in all_nodes:
            tag = el.tag
            if tag == "br":
                continue
            if len(parsers.get_elements_by_tagslist(el, ["object", "embed"])) > 0:
                continue

            txt = parsers.get_text(el)
            txt = re.sub(r"[\s\t]+", "", txt)

            if not txt:
                parsers.remove(el)

    def _get_top_level_nodes(self, top_node: lxml.html.HtmlElement):
        """Returns a list of nodes that are of the top level"""
        top_level_nodes = top_node.getchildren()
        if top_node.tag == "body" and len(top_level_nodes) == 1:
            top_level_nodes = top_level_nodes[0].getchildren()

        return top_level_nodes

    def _remove_trailing_media_div(self, top_node: lxml.html.HtmlElement):
        """Punish the *last top level* node in the top_node if it's
        DOM depth is too deep or has a a lot of links. Many media non-content
        links are eliminated: "related", "loading gallery", etc. It skips
        removal if last top level node's class is one of NON_MEDIA_CLASSES.
        """

        NON_MEDIA_CLASSES = ("zn-body__read-all",)

        top_level_nodes = self._get_top_level_nodes(top_node)

        if len(top_level_nodes) < 3:
            return

        last_node = top_level_nodes[-1]

        last_node_class = parsers.get_attribute(last_node, "class")
        if last_node_class in NON_MEDIA_CLASSES:
            return
        if last_node.tag != "p" and len(parsers.get_tags(last_node, "p")) > 0:
            if parsers.get_node_gravity_score(last_node) > 15:
                return

        if parsers.get_node_depth(last_node) >= 2:
            parsers.remove(last_node)
        elif parsers.is_highlink_density(last_node, self.config.language):
            parsers.remove(last_node)

    def _top_nodes_stats(self, top_node: lxml.html.HtmlElement):
        """Returns a list of top nodes and stats about them"""
        top_nodes = self._get_top_level_nodes(top_node)
        node_stats: Dict[str, Dict[str, Any]] = {}
        for el in top_nodes:
            node_stats[el.tag] = node_stats.setdefault(
                el.tag, {"count": 0, "gravity": [], "depth": []}
            )
            node_stats[el.tag]["count"] += 1
            node_stats[el.tag]["gravity"].append(parsers.get_node_gravity_score(el))
            node_stats[el.tag]["depth"].append(parsers.get_node_depth(el))

        node_stats = {
            k: {
                "count": v["count"],
                "gravity_mean": mean(v["gravity"]),
                "gravity_std": stdev(v["gravity"]) if len(v["gravity"]) > 1 else 0,
                "depth": mean(v["depth"]),
                "depth_std": stdev(v["depth"]) if len(v["depth"]) > 1 else 0,
            }
            for k, v in node_stats.items()
        }

        return node_stats

    def _remove_unlikely_nodes(self, top_node: lxml.html.HtmlElement):
        """Remove unlikely top level nodes from the top node
        based on statistical analysis based on depth and gravity score
        """
        stats = self._top_nodes_stats(top_node)
        top_nodes = self._get_top_level_nodes(top_node)

        # has p and divs. Analyse if divs are not boilerplate or ads
        if "p" in stats and "div" in stats:
            for node in top_nodes:
                if node.tag != "div":
                    continue
                gravity = parsers.get_node_gravity_score(node)
                depth = parsers.get_node_depth(node)

                if (
                    depth > round(stats["div"]["depth"] + stats["div"]["depth_std"])
                    or depth > round(stats["p"]["depth"] + stats["p"]["depth_std"])
                    or gravity
                    < stats["p"]["gravity_mean"] - 2 * stats["p"]["gravity_std"]
                    or gravity
                    < stats["div"]["gravity_mean"] - 2 * stats["div"]["gravity_std"]
                ):
                    parsers.remove(node)

    def _remove_advertisement_nodes(self, top_node: lxml.html.HtmlElement):
        """Remove nodes that may contain advertisement content."""

        divs = top_node.xpath(".//div")
        stats = self._top_nodes_stats(top_node)

        for el in divs:
            # Does it contain p tags?
            if len(parsers.get_tags(el, "p")):
                if parsers.is_highlink_density(el, self.config.language):
                    gravity = parsers.get_node_gravity_score(el)
                    if len(stats):
                        limit = max(
                            [
                                stats[x]["gravity_mean"] - 2 * stats[x]["gravity_std"]
                                for x in stats
                            ]
                        )
                    else:
                        limit = 15  # no gravity scores, then remove all

                    if gravity < limit:
                        parsers.remove(el)

                continue

            if parsers.is_highlink_density(el, self.config.language):
                parsers.remove(el)
                continue
            attrs = el.get("class", "") + " " + el.get("id", "")
            if re.search(settings.ADVERTISEMENT_ATTR_VALUES, attrs, re.IGNORECASE):
                parsers.remove(el)
                continue
