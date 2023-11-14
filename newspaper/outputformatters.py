# -*- coding: utf-8 -*-
# Much of the code here was forked from https://github.com/codelucas/newspaper
# Copyright (c) Lucas Ou-Yang (codelucas)

"""
Output formatting to text via lxml xpath nodes abstracted in this file.
"""
from html import unescape
import logging

import lxml
import newspaper.parsers as parsers
from .text import innerTrim

CLEAN_ARTICLE_TAGS = [
    "a",
    "span",
    "p",
    "br",
    "strong",
    "b",
    "em",
    "i",
    "tt",
    "code",
    "pre",
    "blockquote",
    "img",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "ul",
    "ol",
    "li",
    "dl",
    "dt",
    "dd",
]

log = logging.getLogger(__name__)


class OutputFormatter:
    def __init__(self, config):
        self.top_node = None
        self.config = config
        self.language = config.language
        self.stopwords_class = config.stopwords_class

    def update_language(self, meta_lang):
        """Required to be called before the extraction process in some
        cases because the stopwords_class has to set in case the lang
        is not latin based
        """
        if meta_lang:
            self.language = meta_lang
            self.stopwords_class = self.config.get_stopwords_class(meta_lang)

    def get_top_node(self):
        return self.top_node

    def get_formatted(self, top_node):
        """Returns the body text of an article, and also the body article
        html if specified. Returns in (text, html) form
        """
        self.top_node = top_node
        html, text = "", ""
        if self.top_node is None:
            return (text, html)

        self.remove_negativescores_nodes()

        if self.config.keep_article_html:
            html = self.convert_to_html()

        # remove a tags from article tree. Leaves the text intact
        lxml.etree.strip_tags(self.top_node, "a")

        self.add_newline_to_br()
        self.add_newline_to_li()

        # remove common tags from article tree. Leaves the text intact
        lxml.etree.strip_tags(self.top_node, "b", "strong", "i", "br", "sup")

        self.remove_empty_tags()
        self.remove_trailing_media_div()
        text = self.convert_to_text()
        # print(parsers.nodeToString(self.get_top_node()))
        return (text, html)

    def convert_to_text(self):
        txts = []
        for node in list(self.get_top_node()):
            try:
                txt = parsers.get_text(node)
            except ValueError as err:  # lxml error
                log.info("%s ignoring lxml node error: %s", __name__, err)
                txt = None

            if txt:
                txt = unescape(txt)
                txt_lis = innerTrim(txt).split(r"\n")
                txt_lis = [n.strip(" ") for n in txt_lis]
                txts.extend(txt_lis)
        return "\n\n".join(txts)

    def convert_to_html(self):
        article_cleaner = lxml.html.clean.Cleaner()
        article_cleaner.javascript = True
        article_cleaner.style = True
        article_cleaner.remove_unknown_tags = False

        article_cleaner.allow_tags = CLEAN_ARTICLE_TAGS

        cleaned_node = article_cleaner.clean_html(self.get_top_node())
        return parsers.node_to_string(cleaned_node)

    def add_newline_to_br(self):
        for e in parsers.get_tags(self.top_node, tag="br"):
            e.text = r"\n"

    def add_newline_to_li(self):
        for e in parsers.get_tags(self.top_node, tag="ul"):
            li_list = parsers.get_tags(e, tag="li")
            for li in li_list[:-1]:
                li.text = parsers.get_text(li) + r"\n"
                for c in li.getchildren():
                    parsers.remove(c)

    def remove_negativescores_nodes(self):
        """If there are elements inside our top node that have a
        negative gravity score, let's give em the boot.
        """
        if not self.top_node:
            return
        gravity_items = self.top_node.xpath(".//*[@gravityScore]")
        for item in gravity_items:
            score = parsers.get_attribute(item, "gravityScore")
            score = float(score) if score else 0
            if score < 1:
                item.getparent().remove(item)

    def remove_empty_tags(self):
        """It's common in top_node to exit tags that are filled with data
        within properties but not within the tags themselves, delete them
        """
        all_nodes = parsers.get_tags(self.get_top_node())
        all_nodes.reverse()
        for el in all_nodes:
            tag = el.tag
            text = parsers.get_text(el)
            if (
                (tag != "br" or text != "\\r")
                and not text
                and len(parsers.get_tags(el, tag="object")) == 0
                and len(parsers.get_tags(el, tag="embed")) == 0
            ):
                parsers.remove(el)

    def remove_trailing_media_div(self):
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

        top_level_nodes = self.get_top_node().getchildren()
        if len(top_level_nodes) < 3:
            return

        last_node = top_level_nodes[-1]

        last_node_class = parsers.get_attribute(last_node, "class")
        if last_node_class in NON_MEDIA_CLASSES:
            return

        if get_depth(last_node) >= 2:
            parsers.remove(last_node)
