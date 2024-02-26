import re
from typing import Any, Dict, Optional, Set, Union
from urllib.parse import urlparse, urlunparse

import lxml
from newspaper.configuration import Configuration
import newspaper.parsers as parsers
from newspaper.extractors.defines import (
    A_HREF_TAG_SELECTOR,
    A_REL_TAG_SELECTOR,
    META_LANGUAGE_TAGS,
    RE_LANG,
)


class MetadataExtractor:
    def __init__(self, config: Configuration) -> None:
        self.config = config
        self.meta_data: Dict[str, Any] = {
            "language": None,
            "type": None,
            "canonical_link": None,
            "site_name": None,
            "description": None,
            "keywords": None,
            "tags": None,
            "data": None,
        }

    def parse(self, article_url: str, doc: lxml.html.Element) -> Dict[str, Any]:
        """Parse the article's HTML for any known metadata attributes"""
        self.meta_data["language"] = self._get_meta_language(doc)
        self.meta_data["type"] = self._get_meta_field(doc, "og:type")
        self.meta_data["canonical_link"] = self._get_canonical_link(article_url, doc)
        self.meta_data["site_name"] = self._get_meta_field(doc, "og:site_name")
        self.meta_data["description"] = self._get_meta_field(
            doc, ["description", "og:description"]
        )
        self.meta_data["keywords"] = [
            k.strip() for k in self._get_meta_field(doc, "keywords").split(",")
        ]
        self.meta_data["data"] = self._get_metadata(doc)

        return self.meta_data

    def _get_meta_language(self, doc: lxml.html.Element) -> Optional[str]:
        """Return the language string of the article, or None if it cannot be
        determined.
        """

        def get_if_valid(s: Optional[str]) -> Optional[str]:
            if s is None or len(s) < 2:
                return None
            s = s[:2]
            if re.search(RE_LANG, s):
                return s.lower()
            return None

        attr = get_if_valid(parsers.get_attribute(doc, "lang"))
        if attr:
            return attr

        for elem in META_LANGUAGE_TAGS:
            meta_tag = parsers.get_tags(
                doc, tag=elem["tag"], attribs={elem["attr"]: elem["value"]}
            )

            if meta_tag:
                attr = get_if_valid(meta_tag[0])
                if attr:
                    return attr

        return None

    def _get_canonical_link(
        self, article_url: str, doc: lxml.html.Element
    ) -> Optional[str]:
        """Return the article's canonical URL

        Gets the first available value of:
        1. The rel=canonical tag
        2. The og:url tag
        """
        candidates = [
            node.get("href")
            for node in parsers.get_tags(doc, tag="link", attribs={"rel": "canonical"})
        ]

        candidates.append(self._get_meta_field(doc, "og:url"))
        candidates = [c.strip() for c in candidates if c and c.strip()]

        if candidates:
            meta_url = candidates[0]
            parsed_meta_url = urlparse(meta_url)
            if not parsed_meta_url.hostname:
                # MIGHT not have a hostname in meta_url
                # parsed_url.path might be 'example.com/article.html' where
                # clearly example.com is the hostname
                parsed_article_url = urlparse(article_url)
                strip_hostname_in_meta_path = re.match(
                    rf".*{parsed_article_url.hostname}(?=/)/(.*)",
                    parsed_meta_url.path,
                )
                if strip_hostname_in_meta_path:
                    true_path = strip_hostname_in_meta_path.group(1)
                else:
                    true_path = parsed_meta_url.path

                # true_path may contain querystrings and fragments
                meta_url = urlunparse(
                    (
                        parsed_article_url.scheme,
                        parsed_article_url.hostname,
                        true_path,
                        "",
                        "",
                        "",
                    )
                )
            return meta_url

        return None

    def _get_metadata(self, doc: lxml.html.Element) -> Dict[str, Any]:
        """Extracts metadata from the article's HTML"""
        data: Dict[str, Any] = {}
        properties = parsers.get_tags(doc, "meta")
        for prop in properties:
            key = prop.attrib.get("property") or prop.attrib.get("name")
            value = prop.attrib.get("content") or prop.attrib.get("value")

            if not key or not value:
                continue

            key, value = key.strip(), value.strip()
            if value.isdigit():
                value = int(value)

            if ":" not in key:
                data[key] = value
                continue

            key = key.split(":")
            key_head = key.pop(0)
            ref = data.get(key_head, {})

            if isinstance(ref, str) or isinstance(ref, int):
                data[key_head] = {key_head: ref}
                ref = data[key_head]

            for idx, part in enumerate(key):
                if idx == len(key) - 1:
                    ref[part] = value
                    break
                if not ref.get(part):
                    ref[part] = dict()
                elif isinstance(ref.get(part), (str, int)):
                    # Not clear what to do in this scenario,
                    # it's not always a URL, but an ID of some sort
                    ref[part] = {"identifier": ref[part]}
                ref = ref[part]
        return data

    def _get_tags(self, doc: lxml.html.Element) -> Set[str]:
        """Extracts tags from the article's HTML"""

        elements = doc.xpath(A_HREF_TAG_SELECTOR)
        elements += doc.xpath(A_REL_TAG_SELECTOR)

        if not elements:
            return set()

        tags = [parsers.get_text(el) for el in elements if parsers.get_text(el)]
        return set(tags)

    def _get_meta_field(self, doc: lxml.html.Element, fields: Union[str, list]) -> str:
        """Extract a given meta field from document."""
        if isinstance(fields, str):
            fields = [fields]
        for f in fields:
            meta_fields = parsers.get_metatags(doc, value=f)
            for meta_field in meta_fields:
                val = meta_field.get("content", "").strip()
                if val:
                    return val
        return ""
