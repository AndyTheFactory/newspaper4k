"""Extracts author names from article HTML using JSON-LD, meta tags, and bylines."""

import re
from copy import deepcopy
from typing import Any

from lxml.html import HtmlElement

import newspaper.parsers as parsers
from newspaper.configuration import Configuration
from newspaper.extractors.defines import AUTHOR_ATTRS, AUTHOR_STOP_WORDS, AUTHOR_VALS


class AuthorsExtractor:
    """Extracts author names from an article's HTML."""

    _DIGITS_RE = re.compile(r"\d")

    def __init__(self, config: Configuration) -> None:
        """Initialize the AuthorsExtractor.

        Args:
            config (Configuration): Configuration object controlling extraction behavior.
        """ = [re.escape(x) for x in AUTHOR_STOP_WORDS]
        self._author_stopwords_re = re.compile(
            r"\b(" + "|".join(author_stopwords_patt) + r")\b",
            flags=re.IGNORECASE,
        )

    @staticmethod
    def _uniqify_list(lst: list[str]) -> list[str]:
        """Remove duplicates from provided list but maintain original order.

        Ignores trailing spaces and case.

        Args:
            lst (list[str]): Input list of strings, with potential duplicates

        Returns:
            list[str]: Output list of strings, with duplicates removed
        """
        seen: dict[str, str] = {}
        for item in lst:
            seen[item.lower().strip()] = item.strip()
        return [value for key, value in seen.items() if key]

    def _parse_byline(self, search_str: str) -> list[str]:
        """Take a candidate line of html or text and extract the name(s) in list form.

        >>> _parse_byline('<div>By: <strong>Lucas Ou-Yang</strong>,
                <strong>Alex Smith</strong></div>')
        ['Lucas Ou-Yang', 'Alex Smith']

        Args:
            search_str (str): Input string to parse

        Returns:
            list[str]: List of author names found
        """
        # Remove HTML boilerplate
        search_str = re.sub("<[^<]+?>", "", search_str)
        search_str = re.sub(r"[\n\t\r\xa0]", " ", search_str)

        # Remove original By statement
        m = re.search(r"\b(by|from)[:\s](.*)", search_str, flags=re.IGNORECASE)
        if m:
            search_str = m.group(2)

        search_str = search_str.strip()

        # Chunk the line by non alphanumeric
        # tokens (few name exceptions)
        # >>> re.split("[^\w\'\-\.]",
        #           "Tyler G. Jones, Lucas Ou, Dean O'Brian and Ronald")
        # ['Tyler', 'G.', 'Jones', '', 'Lucas', 'Ou', '',
        #           'Dean', "O'Brian", 'and', 'Ronald']
        name_tokens = re.split(r"[·,\|]|\sand\s|\set\s|\sund\s|/", search_str)
        # some sanity checks
        name_tokens = [s.strip() for s in name_tokens if not self._DIGITS_RE.search(s)]
        name_tokens = [s for s in name_tokens if 5 > len(re.findall(r"\w+", s)) > 1]

        return name_tokens

    def _get_authors_from_ld(self, vals: Any) -> list[str]:
        """Extract author names from a JSON-LD author field value.

        Args:
            vals (Any): The value of the "author" key in a JSON-LD script tag.
                Can be a dict, list, or string.

        Returns:
            list[str]: List of author names found
        """
        result: list[str] = []
        if isinstance(vals, dict):
            name = vals.get("name")
            if isinstance(name, str):
                result.append(name)
            elif isinstance(name, list):
                result.extend(name)
        elif isinstance(vals, list):
            for val in vals:
                if isinstance(val, dict):
                    name = val.get("name")
                    if isinstance(name, str):
                        result.append(name)
                    elif isinstance(name, dict) and "name" in name:
                        result.append(name["name"])
                elif isinstance(val, str):
                    result.append(val)
        elif isinstance(vals, str):
            result.append(vals)
        return result

    @staticmethod
    def _get_text_from_element(node: HtmlElement) -> str:
        """Return the text from an element, including the text from its children.

        Args:
            node (HtmlElement): Input node

        Returns:
            str: Text from the node
        """
        if node is None:
            return ""
        if node.tag in ["script", "style", "time"]:
            return ""

        node = deepcopy(node)
        for tag in ["script", "style", "time"]:
            for el in node.xpath(f".//{tag}"):
                el.getparent().remove(el)
        return parsers.get_text(node)

    def parse(self, doc: HtmlElement) -> list[str]:
        """Fetch the authors of the article, return as a list.

        Only works for english articles
        """
        authors: list[str] = []
        matches = []

        json_ld_scripts = parsers.get_ld_json_object(doc)

        for script_tag in json_ld_scripts:
            if "@graph" in script_tag:
                for item in script_tag.get("@graph", []):
                    if not isinstance(item, dict):
                        continue
                    if item.get("@type") == "Person":
                        authors.append(item.get("name"))
                    if "author" in item:
                        authors.extend(self._get_authors_from_ld(item["author"]))
            else:
                if "author" in script_tag:
                    authors.extend(self._get_authors_from_ld(script_tag["author"]))

        authors = [re.sub(r"[\n\t\r\xa0]", " ", x) for x in authors if x]
        doc_root = doc.getroottree()

        # TODO: be more specific, not a combination of all attributes and values
        for attr in AUTHOR_ATTRS:
            for val in AUTHOR_VALS:
                found = parsers.get_elements_by_attribs(doc, attribs={attr: val})
                matches.extend((node, doc_root.getpath(node)) for node in found)

        matches.sort(key=lambda x: x[1], reverse=True)  # sort by xpath. we want the most specific match
        matches_reduced: list[tuple[Any, str]] = []
        for m in matches:
            if not matches_reduced or not matches_reduced[-1][1].startswith(m[1]):  # remove parents of previous node
                matches_reduced.append(m)
        matches_reduced.sort(key=lambda x: x[1])  # Preserve some sort of order for the authors

        for match, _ in matches_reduced:
            content: str = ""
            if match.tag == "meta":
                mm = match.xpath("@content")
                if mm:
                    content = mm[0]
            else:
                # TODO: ignore <time> tags, or tags with "on ..."
                # TODO: remove <style> tags https://washingtonindependent.com/how-to-apply-for-reseller-permit-in-washington-state/
                content = self._get_text_from_element(match)
            if content:
                authors.extend(self._parse_byline(content))

        # Clean up authors of stopwords such as Reporter, Senior Reporter
        authors = [re.sub(self._author_stopwords_re, "", x).strip(" .,-/") for x in authors]
        self.authors = self._uniqify_list(authors)

        return self.authors
