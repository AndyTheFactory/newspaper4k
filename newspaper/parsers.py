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
from typing import List, Dict, Optional, Union
import lxml.etree
import lxml.html
import lxml.html.clean
from html import unescape

from bs4 import UnicodeDammit

from . import text as txt

log = logging.getLogger(__name__)


class Parser:
    @classmethod
    def drop_tags(
        cls, nodes: Union[lxml.html.HtmlElement, List[lxml.html.HtmlElement]]
    ):
        """Remove the tag(s), but not its children or text.
        The children and text are merged into the parent."""
        if not isinstance(nodes, list):
            nodes = [nodes]
        for node in nodes:
            node.drop_tag()

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
    def node_to_string(cls, node):
        """conerts the tree under node to a string representation
        e.g. "<html><body>hello</body></html>"
        """
        # decode is needed at the end because etree.tostring
        # returns a python bytestring
        return lxml.etree.tostring(node, method="html").decode()

    @classmethod
    def get_tags_regex(
        cls,
        node: lxml.html.Element,
        tag: Optional[str] = None,
        attribs: Optional[Dict[str, str]] = None,
    ) -> List[lxml.html.Element]:
        """Get list of elements of a certain tag with regex matching attributes

        Args:
            tag (str, optional): Tag to match. If None, it matches all
                tags. Defaults to None.
            attribs (Dict[str, str], optional): Dictionary containing
                attributes to match and the corresponding regex.
                Defaults to None. The result matches **all**
                attributes in the dictionary.

        Returns:
            List[lxml.html.Element]: Elements matching the tag and attributes
        """
        if not attribs:
            return cls.get_tags(node, tag=tag)

        namespace = {"re": "http://exslt.org/regular-expressions"}
        sel_list = []

        for k, v in attribs.items():
            selector = f"re:test(@{k}, '{v}', 'i')"
            sel_list.append(selector)

        selector = ".//%s[%s]" % (tag or "*", " and ".join(sel_list))
        elems = node.xpath(selector, namespaces=namespace)
        return elems

    @classmethod
    def get_tags(
        cls,
        node: lxml.html.Element,
        tag: Optional[Union[List[str], str]] = None,
        attribs: Optional[Dict[str, str]] = None,
        attribs_match: str = "exact",
    ):
        """Get list of elements of a certain tag with exact matching attributes

        Args:
            tag (str, optional): Tag to match. If None, it matches all
                tags. Defaults to None.
            attribs (Dict[str, str], optional): Dictionary containing
                attributes to match. Defaults to None. The result matches **all**
                attributes in the dictionary.
            attribs_match (str, optional): Match type. Can be "exact",
                "substring" or "word". Difference between "substring" and
                "word" is that "substring" matches any part of the attribute
                value while "word" matches attribs whose value is a
                whitespace-separated list of words, one of which is exactly
                our query string.
                Defaults to "exact".

        Returns:
            List[lxml.html.Element]: Elements matching the tag and attributes
            List[lxml.html.Element]: Elements matching the tag and attributes
        """
        if attribs_match not in ["exact", "substring", "word"]:
            raise ValueError(
                "attribs_match must be one of 'exact', 'substring' or 'word'"
            )
        if not attribs:
            selector = f".//{(tag or '*')}"
            elems = node.xpath(selector)
            return elems

        sel_list = []
        for k, v in attribs.items():
            trans = 'translate(@%s, "%s", "%s")' % (
                k,
                string.ascii_uppercase,
                string.ascii_lowercase,
            )
            if attribs_match == "exact":
                selector = '%s="%s"' % (trans, v.lower())
            elif attribs_match == "substring":
                selector = 'contains(%s, "%s")' % (trans, v.lower())
            elif attribs_match == "word":
                selector = 'contains(concat(" ", normalize-space(%s), " "), " %s ")' % (
                    trans,
                    v.lower(),
                )

            sel_list.append(selector)
        selector = ".//%s[%s]" % (tag or "*", " and ".join(sel_list))
        elems = node.xpath(selector)
        return elems

    @classmethod
    def get_elements_by_attribs(
        cls,
        node: lxml.html.Element,
        attribs: Dict[str, str],
        attribs_match: str = "exact",
    ) -> List[lxml.html.Element]:
        """Get list of elements with exact matching attributes

        Args:
            attribs (Dict[str,str]): dictionary containing attributes to match.
                e.g. {"class":"foo", "id":"bar"}. The result matches **all**
                attributes in the dictionary.
            attribs_match (str, optional): Match type. Can be "exact",
                "substring" or "word". Difference between "substring" and
                "word" is that "substring" matches any part of the attribute
                value while "word" matches attribs whose value is a
                whitespace-separated list of words, one of which is exactly
                our query string.
                Defaults to "exact".

        Returns:
            List[lxml.html.Element]: Elements matching the attributes
        """
        return cls.get_tags(node, attribs=attribs, attribs_match=attribs_match)

    @classmethod
    def get_metatags(
        cls, node: lxml.html.Element, value: Optional[str] = None
    ) -> List[lxml.html.Element]:
        """Get list of meta tags with name, property **or** itemprop equal to
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
        selector = "//meta[%s]" % " or ".join(sel_list)
        elems = node.xpath(selector)
        return elems

    @classmethod
    def get_elements_by_tagslist(cls, node: lxml.html.Element, tag_list: List[str]):
        """Get list of elements with tag in `tag_list`

        Args:
            node (lxml.html.Element): Element to search
            tag_list (List[str]): List of tags to match

        Returns:
            List[lxml.html.Element]: Elements matching the tags
        """
        selector = ".//%s" % " | ".join(tag_list)
        elems = node.xpath(selector)
        return elems

    @classmethod
    def create_element(cls, tag, text=None, tail=None):
        t = lxml.html.HtmlElement()
        t.tag = tag
        t.text = text
        t.tail = tail
        return t

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
    def get_text(cls, node):
        txts = list(node.itertext())
        return txt.innerTrim(" ".join(txts).strip())

    @classmethod
    def get_attribute(cls, node: lxml.html.Element, attr: str) -> Optional[str]:
        """get the unicode attribute of the node"""
        attr = node.attrib.get(attr, None)
        return unescape(attr) if attr else None

    @classmethod
    def set_attribute(cls, node, attr, value=None):
        # Check if immutable attribute
        if not isinstance(
            node, (lxml.etree.CommentBase, lxml.etree.EntityBase, lxml.etree.PIBase)
        ):
            node.set(attr, value)

    @classmethod
    def outer_html(cls, node):
        e0 = node
        if e0.tail:
            e0 = deepcopy(e0)
            e0.tail = None
        return cls.node_to_string(e0)

    @classmethod
    def get_ld_json_object(cls, node):
        """Get the JSON-LD object from the node"""
        # yoast seo structured data
        json_ld = cls.get_tags(
            node, tag="script", attribs={"type": "application/ld+json"}
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
