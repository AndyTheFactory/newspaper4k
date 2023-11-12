# -*- coding: utf-8 -*-
# Much of the code here was forked from https://github.com/codelucas/newspaper
# Copyright (c) Lucas Ou-Yang (codelucas)

"""
Newspaper uses a lot of python-goose's parsing code. View theirlicense:
https://github.com/codelucas/newspaper/blob/master/GOOSE-LICENSE.txt

Parser objects will only contain operations that manipulate
or query an lxml or soup dom object generated from an article's html.
"""
import json
import re
import logging
import string
from copy import deepcopy
from typing import List, Dict, Optional
import lxml.etree
import lxml.html
import lxml.html.clean
from html import unescape

from bs4 import UnicodeDammit

from . import text

log = logging.getLogger(__name__)


class Parser:
    @classmethod
    def xpath_re(cls, node, expression):
        regexp_namespace = "http://exslt.org/regular-expressions"
        items = node.xpath(expression, namespaces={"re": regexp_namespace})
        return items

    @classmethod
    def drop_tag(cls, nodes):
        if isinstance(nodes, list):
            for node in nodes:
                node.drop_tag()
        else:
            nodes.drop_tag()

    @classmethod
    def css_select(cls, node, selector):
        return node.cssselect(selector)

    @classmethod
    def get_unicode_html(cls, html):
        if isinstance(html, str):
            return html
        if not html:
            return html
        converted = UnicodeDammit(html, is_html=True)
        if not converted.unicode_markup:
            raise ValueError(
                "Failed to detect encoding of article HTML, tried: %s"
                % ", ".join(converted.tried_encodings)
            )
        html = converted.unicode_markup
        return html

    @classmethod
    def fromstring(cls, html):
        html = cls.get_unicode_html(html)
        # Enclosed in a `try` to prevent bringing the entire library
        # down due to one article (out of potentially many in a `Source`)
        try:
            # lxml does not play well with <? ?> encoding tags
            if html.startswith("<?"):
                html = re.sub(r"^\<\?.*?\?\>", "", html, flags=re.DOTALL)
            cls.doc = lxml.html.fromstring(html)
            return cls.doc
        except Exception:
            log.warning("fromstring() returned an invalid string: %s...", html[:20])
            return

    @classmethod
    def clean_article_html(cls, node):
        article_cleaner = lxml.html.clean.Cleaner()
        article_cleaner.javascript = True
        article_cleaner.style = True
        article_cleaner.allow_tags = [
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
        article_cleaner.remove_unknown_tags = False
        return article_cleaner.clean_html(node)

    @classmethod
    def nodeToString(cls, node):
        """`decode` is needed at the end because `etree.tostring`
        returns a python bytestring
        """
        return lxml.etree.tostring(node, method="html").decode()

    @classmethod
    def replaceTag(cls, node, tag):
        node.tag = tag

    @classmethod
    def stripTags(cls, node, *tags):
        lxml.etree.strip_tags(node, *tags)

    @classmethod
    def getElementById(cls, node, idd):
        selector = '//*[@id="%s"]' % idd
        elems = node.xpath(selector)
        if elems:
            return elems[0]
        return None

    @classmethod
    def getElementsByTag(
        cls, node, tag=None, attr=None, value=None, children=False, use_regex=False
    ) -> list:
        NS = None
        # selector = tag or '*'
        selector = "descendant-or-self::%s" % (tag or "*")
        if attr and value:
            if use_regex:
                NS = {"re": "http://exslt.org/regular-expressions"}
                selector = '%s[re:test(@%s, "%s", "i")]' % (selector, attr, value)
            else:
                trans = 'translate(@%s, "%s", "%s")' % (
                    attr,
                    string.ascii_uppercase,
                    string.ascii_lowercase,
                )
                selector = '%s[contains(%s, "%s")]' % (selector, trans, value.lower())
        elems = node.xpath(selector, namespaces=NS)
        # remove the root node
        # if we have a selection tag
        if node in elems and (tag or children):
            elems.remove(node)
        return elems

    @classmethod
    def get_tags(
        cls,
        node: lxml.html.Element,
        tag: Optional[str] = None,
        attribs: Optional[Dict[str, str]] = None,
    ):
        """Get list of elements of a certain tag with matching attributes

        Args:
            tag (Optional[str], optional): Tag to match. If None, it matches all
                tags. Defaults to None.
            attribs (Optional[Dict[str, str]], optional): Dictionary containing
                attributes to match. Defaults to None.

        Returns:
            List[lxml.html.Element]: Elements matching the tag and attributes
        """
        if not attribs:
            selector = "descendant-or-self::%s" % (tag or "*")
            elems = node.xpath(selector)
            return elems

        sel_list = []
        for k, v in attribs.items():
            trans = 'translate(@%s, "%s", "%s")' % (
                k,
                string.ascii_uppercase,
                string.ascii_lowercase,
            )
            selector = '%s="%s"' % (trans, v.lower())
            sel_list.append(selector)
        selector = "descendant-or-self::%s[%s]" % (tag or "*", " and ".join(sel_list))
        elems = node.xpath(selector)
        return elems

    @classmethod
    def get_elements_by_attribs(
        cls, node: lxml.html.Element, attribs: Dict[str, str]
    ) -> List[lxml.html.Element]:
        """Get list of elements with matching attributes

        Args:
            attribs (Dict[str,str]): dictionary containing attributes to match.
                e.g. {"class":"foo", "id":"bar"}

        Returns:
            List[lxml.html.Element]: Elements matching the attributes
        """
        return cls.get_tags(node, attribs=attribs)

    @classmethod
    def get_metatags(
        cls, node: lxml.html.Element, value: Optional[str] = None
    ) -> List[lxml.html.Element]:
        """Get list of meta tags with name, property or itemprop equal to
          `value`. If `value` is None, it returns all meta tags

        Args:
            node (lxml.html.Element): Element to search
            value (Optional[str], optional): Value to match. Defaults to None.

        Returns:
            List[lxml.html.Element]: Elements matching the value
        """
        if value is None:
            return cls.get_tags(node, tag="meta")

        sel_list = [f"@name='{value}'", f"@property='{value}'", f"@itemprop='{value}'"]
        selector = "descendant-or-self::meta[%s]" % " or ".join(sel_list)
        elems = node.xpath(selector)
        return elems

    @classmethod
    def appendChild(cls, node, child):
        node.append(child)

    @classmethod
    def childNodes(cls, node):
        return list(node)

    @classmethod
    def childNodesWithText(cls, node):
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
        for c, n in enumerate(list(root)):
            idx = root.index(n)
            # don't process texts nodes
            if n.tag == "text":
                continue
            # create a text node for tail
            if n.tail:
                t = cls.createElement(tag="text", text=n.tail, tail=None)
                root.insert(idx + 1, t)
        return list(root)

    @classmethod
    def textToPara(cls, text):
        return cls.fromstring(text)

    @classmethod
    def getChildren(cls, node):
        return node.getchildren()

    @classmethod
    def getElementsByTags(cls, node, tags):
        selector = "descendant::*[%s]" % (" or ".join("self::%s" % tag for tag in tags))
        elems = node.xpath(selector)
        return elems

    @classmethod
    def createElement(cls, tag="p", text=None, tail=None):
        t = lxml.html.HtmlElement()
        t.tag = tag
        t.text = text
        t.tail = tail
        return t

    @classmethod
    def getComments(cls, node):
        return node.xpath("//comment()")

    @classmethod
    def getParent(cls, node):
        return node.getparent()

    @classmethod
    def remove(cls, node):
        parent = node.getparent()
        if parent is not None:
            if node.tail:
                prev = node.getprevious()
                if prev is None:
                    if not parent.text:
                        parent.text = ""
                    parent.text += " " + node.tail
                else:
                    if not prev.tail:
                        prev.tail = ""
                    prev.tail += " " + node.tail
            node.clear()
            parent.remove(node)

    @classmethod
    def getTag(cls, node):
        return node.tag

    @classmethod
    def getText(cls, node):
        txts = [i for i in node.itertext()]
        return text.innerTrim(" ".join(txts).strip())

    @classmethod
    def previousSiblings(cls, node):
        """
        returns preceding siblings in reverse order (nearest sibling is first)
        """
        return [n for n in node.itersiblings(preceding=True)]

    @classmethod
    def previousSibling(cls, node):
        return node.getprevious()

    @classmethod
    def nextSibling(cls, node):
        return node.getnext()

    @classmethod
    def isTextNode(cls, node):
        return True if node.tag == "text" else False

    @classmethod
    def getAttribute(cls, node, attr=None):
        if attr:
            attr = node.attrib.get(attr, None)
        if attr:
            attr = unescape(attr)
        return attr

    @classmethod
    def delAttribute(cls, node, attr=None):
        if attr:
            _attr = node.attrib.get(attr, None)
            if _attr:
                del node.attrib[attr]

    @classmethod
    def setAttribute(cls, node, attr=None, value=None):
        if attr and value:
            # Check if immutable attribute
            if isinstance(
                node, (lxml.etree.CommentBase, lxml.etree.EntityBase, lxml.etree.PIBase)
            ):
                return
            node.set(attr, value)

    @classmethod
    def outerHtml(cls, node):
        e0 = node
        if e0.tail:
            e0 = deepcopy(e0)
            e0.tail = None
        return cls.nodeToString(e0)

    @classmethod
    def get_ld_json_object(cls, node):
        """Get the JSON-LD object from the node"""
        # yoast seo structured data
        json_ld = cls.getElementsByTag(
            node, tag="script", attr="type", value="application/ld+json"
        )
        res = []
        if json_ld:
            for script_tag in json_ld:
                try:
                    schema_json = json.loads(script_tag.text)
                except Exception:
                    continue
                if isinstance(schema_json, list):
                    res.extend(schema_json)
                else:
                    res.append(schema_json)

        return res
