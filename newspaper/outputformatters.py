# -*- coding: utf-8 -*-
# Much of the code here was forked from https://github.com/codelucas/newspaper
# Copyright (c) Lucas Ou-Yang (codelucas)

"""
Output formatting to text via lxml xpath nodes abstracted in this file.
"""
from copy import deepcopy
import logging
import re
from typing import Tuple

import lxml
from newspaper import parsers
from newspaper.configuration import Configuration
from newspaper import settings

log = logging.getLogger(__name__)


class OutputFormatter:
    """Class that converts the article top node into text, cleaning up
    debris tags, replacing <br> with newlines, etc.

    if `config.clean_article_html` is True, then the article's html is
    cleaned as well. Only `settings.CLEAN_ARTICLE_TAGS` are allowed to
    remain in the html.
    """

    def __init__(self, config=None):
        self.config = config or Configuration()

    def get_formatted(self, top_node: lxml.html.HtmlElement) -> Tuple[str, str]:
        """Returns the body text of an article, and also the cleaned html body
        article of the article.
        Arguments:
            top_node {lxml.html.HtmlElement} -- The top node element of the article
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

        self._remove_empty_tags(node_cleaned)
        # Not sure what it really does
        # self._remove_trailing_media_div(node_cleaned)

        if self.config.clean_article_html:
            html = self._create_clean_html(node_cleaned)

        text = self._convert_to_text(node_cleaned)

        return (text, html)

    def _convert_to_text(self, top_node: lxml.html.HtmlElement):
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

        txts = [re.sub(r"[\s\t]+", " ", value) for value in cleaned_node.itertext()]
        txts = [x.strip(" \t") for x in txts if x.strip(" \t\n\r")]

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

    def _add_newline_to_li(self, top_node: lxml.html.HtmlElement):
        for e in parsers.get_tags(top_node, tag="ul"):
            li_list = parsers.get_tags(e, tag="li")
            for li in li_list[:-1]:
                li.text = parsers.get_text(li) + r"\n"
                for c in li.getchildren():
                    parsers.remove(c)

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

            txt = el.text_content()
            txt = re.sub(r"[\s\t]+", "", txt)

            if not txt:
                parsers.remove(el)

    def _remove_trailing_media_div(self, top_node: lxml.html.HtmlElement):
        """Punish the *last top level* node in the top_node if it's
        DOM depth is too deep. Many media non-content links are
        eliminated: "related", "loading gallery", etc. It skips removal if
        last top level node's class is one of NON_MEDIA_CLASSES.
        """

        NON_MEDIA_CLASSES = ("zn-body__read-all",)

        def get_depth(node, depth=1):
            """Computes depth of an lxml element via BFS, this would be
            in parser if it were used anywhere else besides this method
            """
            children = node.getchildren()
            if not children:
                return depth
            max_depth = 0
            for c in children:
                e_depth = get_depth(c, depth + 1)
                if e_depth > max_depth:
                    max_depth = e_depth
            return max_depth

        top_level_nodes = top_node.getchildren()
        if len(top_level_nodes) < 3:
            return

        last_node = top_level_nodes[-1]

        last_node_class = parsers.get_attribute(last_node, "class")
        if last_node_class in NON_MEDIA_CLASSES:
            return

        if get_depth(last_node) >= 2:
            parsers.remove(last_node)
