# -*- coding: utf-8 -*-
# Much of the code here was forked from https://github.com/codelucas/newspaper
# Copyright (c) Lucas Ou-Yang (codelucas)

"""
Holds the code for cleaning out unwanted tags from the lxml
dom xpath.
"""
import re
from lxml.html import HtmlElement
import newspaper.parsers as parsers
from newspaper.configuration import Configuration


class DocumentCleaner:
    """
    A class that provides methods to clean and manipulate HTML documents.
    """

    def __init__(self, config: Configuration):
        """Set appropriate tag names and regexes of tags to remove
        from the HTML
        """
        self.config = config
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
        self.remove_nodes_related_re = (
            r"related[-\s\_]?(search|topics|media|info|tags|article|content|links)|"
            r"(search|topics|media|info|tags|article|content|links)[-\s\_]?related"
        )
        self.div_to_p_re = r"<(a|blockquote|dl|div|img|ol|p|pre|table|ul)"
        self.caption_re = "^caption$"
        self.google_re = " google "
        self.entries_re = "^[^entry-]more.*$"
        self.facebook_re = "[^-]facebook"
        self.facebook_broadcasting_re = "facebook-broadcasting"
        self.twitter_re = "[^-]twitter|twitter-tweet"
        self.contains_article = (
            './/article|.//*[@id="article"]|.//*[contains(@itemprop,"articleBody")]'
        )

    def clean(self, doc_to_clean: HtmlElement) -> HtmlElement:
        """Remove chunks of the DOM as specified"""
        doc_to_clean = self.clean_body_classes(doc_to_clean)
        doc_to_clean = self.clean_article_tags(doc_to_clean)
        doc_to_clean = self.clean_em_tags(doc_to_clean)
        doc_to_clean = self.remove_drop_caps(doc_to_clean)
        doc_to_clean = self.remove_scripts_styles(doc_to_clean)
        doc_to_clean = self.clean_bad_tags(doc_to_clean)

        # Remove image captions
        doc_to_clean = self.remove_nodes_regex(doc_to_clean, self.caption_re)
        doc_to_clean = self.clean_caption_tags(doc_to_clean)

        doc_to_clean = self.remove_nodes_regex(doc_to_clean, self.google_re)
        doc_to_clean = self.remove_nodes_regex(doc_to_clean, self.entries_re)

        # Remove social media cards
        doc_to_clean = self.remove_nodes_regex(doc_to_clean, self.facebook_re)
        doc_to_clean = self.remove_nodes_regex(doc_to_clean, self.twitter_re)
        doc_to_clean = self.remove_nodes_regex(
            doc_to_clean, self.facebook_broadcasting_re
        )
        # Remove "related" sections
        doc_to_clean = self.remove_nodes_regex(
            doc_to_clean, self.remove_nodes_related_re
        )

        # Remove spans inside of paragraphs
        doc_to_clean = self.clean_para_spans(doc_to_clean)

        doc_to_clean = self.reduce_article(doc_to_clean)

        return doc_to_clean

    def clean_whitespace(self, text: str) -> str:
        """Remove tabs, whitespace lines from text
        add double newlines to paragraphs
        """
        text = text.replace("\t", "")
        text = re.sub(r"(?<!\n)\n(?!\n)", "\n\n", text)
        text = re.sub(r"^\s+$", "", text)
        return text

    def clean_body_classes(self, doc: HtmlElement) -> HtmlElement:
        """Removes the `class` attribute from the <body> tag because
        if there is a bad match, the entire DOM will be empty!
        """
        elements = parsers.get_tags(doc, tag="body")
        if elements:
            # Remove attribute
            elements[0].attrib.pop("class", None)
        return doc

    def clean_article_tags(self, doc: HtmlElement) -> HtmlElement:
        """Removes specified attributes from <article> tags in the given document.
        Args:
            doc (ElementTree.Element): The document to clean.
        Returns:
            ElementTree.Element: The cleaned document.
        """
        articles = parsers.get_tags(doc, tag="article")

        # Remove specified attributes from every <article> tag
        for article in articles:
            for attr in ["id", "name", "class"]:
                article.attrib.pop(attr, None)
        return doc

    def clean_em_tags(self, doc: HtmlElement) -> HtmlElement:
        """Removes <em> tags from the given HTML document if they
        don't contain any <img> tags.

        Args:
            doc (HtmlElement): The HTML document to clean.

        Returns:
            HtmlElement: The cleaned HTML document.
        """
        ems = parsers.get_tags(doc, tag="em")
        for node in ems:
            images = parsers.get_tags(node, tag="img")
            if len(images) == 0:
                parsers.drop_tags(node)
        return doc

    def clean_caption_tags(self, doc: HtmlElement) -> HtmlElement:
        """Removes image caption tags from the given HTML document.

        Args:
            doc (HtmlElement): The HTML document to clean.

        Returns:
            HtmlElement: The cleaned HTML document.
        """
        captions = parsers.get_tags(doc, tag="figure")
        parsers.remove(captions, keep_tags=["img"])

        captions = parsers.get_tags(doc, tag="figcaption")
        parsers.remove(captions, keep_tags=["img"])

        captions = parsers.get_tags(doc, attribs={"itemprop": "caption"})
        parsers.remove(captions)

        captions = parsers.get_tags(doc, attribs={"class": "instagram-media"})
        parsers.remove(captions)

        captions = parsers.get_tags(doc, attribs={"class": "image-caption"})
        parsers.remove(captions)

        captions = parsers.get_tags(
            doc, attribs={"class": "caption"}, attribs_match="substring"
        )
        captions = [c for c in captions if c.tag in ["div", "span", "header"]]
        parsers.remove(captions)

        return doc

    def remove_drop_caps(self, doc: HtmlElement) -> HtmlElement:
        """Removes spans with ckass dropcap from the given HTML document.

        Args:
            doc (HtmlElement): The HTML document to remove drop caps from.

        Returns:
            HtmlElement: The modified HTML document without drop caps.
        """
        items = parsers.get_tags(
            doc, "span", {"class": "dropcap"}, attribs_match="word"
        )
        items += parsers.get_tags(
            doc, "span", {"class": "drop_cap"}, attribs_match="word"
        )

        parsers.drop_tags(items)
        return doc

    def remove_scripts_styles(self, doc: HtmlElement) -> HtmlElement:
        """Removes scripts, styles, and comments from the given HTML document.

        Args:
            doc (HtmlElement): The HTML document to remove scripts,
            styles, and comments from.

        Returns:
            HtmlElement: The modified HTML document with scripts, styles,
            and comments removed.
        """
        # remove scripts
        scripts = parsers.get_tags(doc, tag="script")
        for item in scripts:
            parsers.remove(item)
        # remove styles
        styles = parsers.get_tags(doc, tag="style")
        for item in styles:
            parsers.remove(item)
        # remove comments <--! like this one -->
        comments = doc.xpath("//comment()")

        parsers.remove(comments)

        return doc

    def clean_bad_tags(self, doc: HtmlElement) -> HtmlElement:
        """Cleans some known bad tags from the given HTML document.

        Args:
            doc (HtmlElement): The HTML document to clean.

        Returns:
            HtmlElement: The cleaned HTML document.
        """
        # bad ids
        naughty_list = parsers.get_tags_regex(doc, attribs={"id": self.remove_nodes_re})
        for node in naughty_list:
            if not node.xpath(self.contains_article):
                parsers.remove(node)
        # class
        naughty_list = parsers.get_tags_regex(
            doc, attribs={"class": self.remove_nodes_re}
        )
        for node in naughty_list:
            if not node.xpath(self.contains_article):
                parsers.remove(node)
        # name
        naughty_list = parsers.get_tags_regex(
            doc, attribs={"name": self.remove_nodes_re}
        )
        parsers.remove(naughty_list)

        # Navigation, menus, headers, footers, etc.
        bad_tags = ["aside", "nav", "noscript", "menu"]
        naughty_list = parsers.get_elements_by_tagslist(doc, bad_tags)
        parsers.remove(naughty_list)

        return doc

    def remove_nodes_regex(self, doc: HtmlElement, pattern: str) -> HtmlElement:
        """Removes HTML nodes from the given document that match the specified
        regex pattern.

        Args:
            doc (HtmlElement): The HTML document to remove nodes from.
            pattern (str): The regex pattern to match against the node attributes.

        Returns:
            HtmlElement: The modified HTML document with the matched nodes removed.
        """
        naughty_list = parsers.get_tags_regex(doc, attribs={"id": pattern})
        naughty_list += parsers.get_tags_regex(doc, attribs={"class": pattern})

        parsers.remove(naughty_list)

        return doc

    def clean_para_spans(self, doc: HtmlElement) -> HtmlElement:
        """Removes span tags within paragraph tags from the given HTML document.

        Args:
            doc (HtmlElement): The HTML document to clean.

        Returns:
            HtmlElement: The cleaned HTML document.
        """
        spans = doc.xpath(".//p/span")
        parsers.drop_tags(spans)
        return doc

    def reduce_article(self, doc: HtmlElement) -> HtmlElement:
        """Reduces the article by removing unnecessary tags from the
        given HTML document. Keeps only tags that might contain the article and
        its images.

        Args:
            doc (HtmlElement): The HTML document to be reduced.

        Returns:
            HtmlElement: The reduced HTML document.
        """
        body_tag = parsers.get_tags(doc, tag="body")
        if not body_tag:
            return doc

        for item in body_tag[0].iter():
            if item.tag not in [
                "p",
                "br",
                "img",
                "h1",
                "h2",
                "h3",
                "h4",
                "h5",
                "h6",
                "ul",
                "body",
                "article",
                "section",
            ]:
                if item.text is None and item.tail is None:
                    item.drop_tag()

        return doc
