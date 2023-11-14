# -*- coding: utf-8 -*-
# Much of the code here was forked from https://github.com/codelucas/newspaper
# Copyright (c) Lucas Ou-Yang (codelucas)

"""
Holds the code for cleaning out unwanted tags from the lxml
dom xpath.
"""
import copy

import lxml
from .utils import ReplaceSequence


class DocumentCleaner:
    def __init__(self, config):
        """Set appropriate tag names and regexes of tags to remove
        from the HTML
        """
        self.config = config
        self.parser = self.config.get_parser()
        self.remove_nodes_re = (
            "^side$|combx|retweet|mediaarticlerelated|menucontainer|"
            "navbar|storytopbar-bucket|utility-bar|inline-share-tools"
            "|comment|PopularQuestions|contact|foot|footer|Footer|footnote"
            "|cnn_strycaptiontxt|cnn_html_slideshow|cnn_strylftcntnt"
            "|links|meta$|shoutbox|sponsor"
            "|tags|socialnetworking|socialNetworking|cnnStryHghLght"
            "|cnn_stryspcvbx|^inset$|pagetools|post-attributes"
            "|welcome_form|contentTools2|the_answers"
            "|communitypromo|runaroundLeft|subscribe|vcard|articleheadings"
            "|date|^print$|popup|author-dropdown|tools|socialtools|byline"
            "|konafilter|KonaFilter|breadcrumbs|^fn$|wp-caption-text"
            "|legende|ajoutVideo|timestamp|js_replies"
        )

        self.div_to_p_re = r"<(a|blockquote|dl|div|img|ol|p|pre|table|ul)"
        self.caption_re = "^caption$"
        self.google_re = " google "
        self.entries_re = "^[^entry-]more.*$"
        self.facebook_re = "[^-]facebook"
        self.facebook_broadcasting_re = "facebook-broadcasting"
        self.twitter_re = "[^-]twitter"
        self.tablines_replacements = (
            ReplaceSequence().create("\n", "\n\n").append("\t").append("^\\s+$")
        )
        self.contains_article = (
            './/article|.//*[@id="article"]|.//*[contains(@itemprop,"articleBody")]'
        )

    def clean(self, doc_to_clean):
        """Remove chunks of the DOM as specified"""
        doc_to_clean = self.clean_body_classes(doc_to_clean)
        doc_to_clean = self.clean_article_tags(doc_to_clean)
        doc_to_clean = self.clean_em_tags(doc_to_clean)
        doc_to_clean = self.remove_drop_caps(doc_to_clean)
        doc_to_clean = self.remove_scripts_styles(doc_to_clean)
        doc_to_clean = self.clean_bad_tags(doc_to_clean)
        doc_to_clean = self.remove_nodes_regex(doc_to_clean, self.caption_re)
        doc_to_clean = self.remove_nodes_regex(doc_to_clean, self.google_re)
        doc_to_clean = self.remove_nodes_regex(doc_to_clean, self.entries_re)
        doc_to_clean = self.remove_nodes_regex(doc_to_clean, self.facebook_re)
        doc_to_clean = self.remove_nodes_regex(
            doc_to_clean, self.facebook_broadcasting_re
        )
        doc_to_clean = self.remove_nodes_regex(doc_to_clean, self.twitter_re)
        doc_to_clean = self.clean_para_spans(doc_to_clean)
        doc_to_clean = self.div_to_para(doc_to_clean, "div")
        doc_to_clean = self.div_to_para(doc_to_clean, "span")
        doc_to_clean = self.div_to_para(doc_to_clean, "section")
        return doc_to_clean

    def clean_body_classes(self, doc):
        """Removes the `class` attribute from the <body> tag because
        if there is a bad match, the entire DOM will be empty!
        """
        elements = self.parser.get_tags(doc, tag="body")
        if elements:
            # Remove attribute
            elements[0].attrib.pop("class", None)
        return doc

    def clean_article_tags(self, doc):
        articles = self.parser.get_tags(doc, tag="article")

        # Remove this attribute from every <article> tag
        for article in articles:
            for attr in ["id", "name", "class"]:
                article.attrib.pop(attr, None)
        return doc

    def clean_em_tags(self, doc):
        ems = self.parser.get_tags(doc, tag="em")
        for node in ems:
            images = self.parser.get_tags(node, tag="img")
            if len(images) == 0:
                self.parser.drop_tags(node)
        return doc

    def remove_drop_caps(self, doc):
        items = self.parser.get_tags(
            doc, "span", {"class": "dropcap"}, attribs_match="word"
        )
        items += self.parser.get_tags(
            doc, "span", {"class": "drop_cap"}, attribs_match="word"
        )

        self.parser.drop_tags(items)
        return doc

    def remove_scripts_styles(self, doc):
        # remove scripts
        scripts = self.parser.get_tags(doc, tag="script")
        for item in scripts:
            self.parser.remove(item)
        # remove styles
        styles = self.parser.get_tags(doc, tag="style")
        for item in styles:
            self.parser.remove(item)
        # remove comments <--! like this one -->
        comments = doc.xpath("//comment()")
        for item in comments:
            self.parser.remove(item)

        return doc

    def clean_bad_tags(self, doc):
        # bad ids
        naughty_list = self.parser.get_tags_regex(
            doc, attribs={"id": self.remove_nodes_re}
        )
        for node in naughty_list:
            if not node.xpath(self.contains_article):
                self.parser.remove(node)
        # class
        naughty_list = self.parser.get_tags_regex(
            doc, attribs={"class": self.remove_nodes_re}
        )
        for node in naughty_list:
            if not node.xpath(self.contains_article):
                self.parser.remove(node)
        # name
        naughty_list = self.parser.get_tags_regex(
            doc, attribs={"name": self.remove_nodes_re}
        )
        for node in naughty_list:
            if not node.xpath(self.contains_article):
                self.parser.remove(node)
        return doc

    def remove_nodes_regex(self, doc, pattern):
        naughty_list = self.parser.get_tags_regex(doc, attribs={"id": pattern})
        naughty_list += self.parser.get_tags_regex(doc, attribs={"class": pattern})
        for node in naughty_list:
            self.parser.remove(node)
        return doc

    def clean_para_spans(self, doc):
        spans = doc.xpath(".//p/span")
        self.parser.drop_tags(spans)
        return doc

    def replace_walk_left_right(self, kid, kid_text, replacement_text, nodes_to_remove):
        kid_text_node = kid
        replace_text = self.tablines_replacements.replaceAll(kid_text)
        if len(replace_text) > 1:
            prev_node = kid_text_node.getprevious()
            while (
                prev_node is not None
                and prev_node.tag == "a"
                and self.parser.get_attribute(prev_node, "grv-usedalready") != "yes"
            ):
                outer = " " + self.parser.outer_html(prev_node) + " "
                replacement_text.append(outer)
                nodes_to_remove.append(prev_node)
                self.parser.set_attribute(
                    prev_node, attr="grv-usedalready", value="yes"
                )
                prev_node = prev_node.getprevious()

            replacement_text.append(replace_text)
            next_node = kid_text_node.getnext()
            while (
                next_node is not None
                and next_node.tag == "a"
                and self.parser.get_attribute(next_node, "grv-usedalready") != "yes"
            ):
                outer = " " + self.parser.outer_html(next_node) + " "
                replacement_text.append(outer)
                nodes_to_remove.append(next_node)
                self.parser.set_attribute(
                    next_node, attr="grv-usedalready", value="yes"
                )
                next_node = next_node.getnext()

    def get_replacement_nodes(self, doc, div):
        replacement_text = []
        nodes_to_return = []
        nodes_to_remove = []

        def get_child_nodes_with_text(node):
            root = node
            # create the first text node
            # if we have some text in the node
            if root.text:
                t = lxml.html.HtmlElement()
                t.text = root.text
                t.tag = "text"
                root.text = None
                root.insert(0, t)
            # loop children
            for idx, n in enumerate(list(root)):
                # don't process texts nodes
                if n.tag == "text":
                    continue
                # create a text node for tail
                if n.tail:
                    t = self.parser.create_element(tag="text", text=n.tail)
                    root.insert(idx + 1, t)
            return list(root)

        kids = get_child_nodes_with_text(div)
        for kid in kids:
            # The node is a <p> and already has some replacement text
            if kid.tag == "p" and len(replacement_text) > 0:
                new_node = self.parser.fromstring("".join(replacement_text))
                nodes_to_return.append(new_node)
                replacement_text = []
                nodes_to_return.append(kid)
            # The node is a text node
            elif kid.tag == "text":
                kid_text = self.parser.get_text(kid)
                self.replace_walk_left_right(
                    kid, kid_text, replacement_text, nodes_to_remove
                )
            else:
                nodes_to_return.append(kid)

        # flush out anything still remaining
        if len(replacement_text) > 0:
            new_node = self.parser.fromstring("".join(replacement_text))
            nodes_to_return.append(new_node)
            replacement_text = []

        for n in nodes_to_remove:
            self.parser.remove(n)

        return nodes_to_return

    def div_to_para(self, doc, dom_type):
        bad_divs = 0
        else_divs = 0
        divs = self.parser.get_tags(doc, tag=dom_type)
        tags = ["a", "blockquote", "dl", "div", "img", "ol", "p", "pre", "table", "ul"]
        for div in divs:
            items = self.parser.get_elements_by_tagslist(div, tags)
            if div is not None and len(items) == 0:
                div.tag = "p"
                bad_divs += 1
            elif div is not None:
                replace_nodes = self.get_replacement_nodes(doc, div)
                replace_nodes = [n for n in replace_nodes if n is not None]
                attrib = copy.deepcopy(div.attrib)
                div.clear()
                for i, node in enumerate(replace_nodes):
                    div.insert(i, node)
                for name, value in attrib.items():
                    div.set(name, value)
                else_divs += 1
        return doc
