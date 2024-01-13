from copy import deepcopy
import re
import lxml
from typing import Any, List, Tuple, Union
from collections import OrderedDict
from newspaper.configuration import Configuration
import newspaper.parsers as parsers
from newspaper.extractors.defines import AUTHOR_ATTRS, AUTHOR_STOP_WORDS, AUTHOR_VALS


class AuthorsExtractor:
    def __init__(self, config: Configuration) -> None:
        self.config = config
        self.authors: List[str] = []

    def parse(self, doc: lxml.html.Element) -> List[str]:
        """Fetch the authors of the article, return as a list
        Only works for english articles
        """
        _digits = re.compile(r"\d")
        author_stopwords_patt = [re.escape(x) for x in AUTHOR_STOP_WORDS]
        author_stopwords = re.compile(
            r"\b(" + "|".join(author_stopwords_patt) + r")\b", flags=re.IGNORECASE
        )

        def contains_digits(d):
            return bool(_digits.search(d))

        def uniqify_list(lst: List[str]) -> List[str]:
            """Remove duplicates from provided list but maintain original order.
            Ignores trailing spaces and case.

            Args:
                lst (List[str]): Input list of strings, with potential duplicates

            Returns:
                List[str]: Output list of strings, with duplicates removed
            """
            seen = OrderedDict()
            for item in lst:
                seen[item.lower().strip()] = item.strip()
            return [value for item, value in seen.items() if item]

        def parse_byline(search_str):
            """
            Takes a candidate line of html or text and
            extracts out the name(s) in list form:
            >>> parse_byline('<div>By: <strong>Lucas Ou-Yang</strong>,
                    <strong>Alex Smith</strong></div>')
            ['Lucas Ou-Yang', 'Alex Smith']
            """
            # Remove HTML boilerplate
            search_str = re.sub("<[^<]+?>", "", search_str)
            search_str = re.sub("[\n\t\r\xa0]", " ", search_str)

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
            name_tokens = [s.strip() for s in name_tokens if not contains_digits(s)]
            name_tokens = [s for s in name_tokens if 5 > len(re.findall(r"\w+", s)) > 1]

            return name_tokens

        # Try 1: Search popular author tags for authors

        matches = []
        authors = []

        json_ld_scripts = parsers.get_ld_json_object(doc)

        def get_authors(vals):
            if isinstance(vals, dict):
                if isinstance(vals.get("name"), str):
                    authors.append(vals.get("name"))
                elif isinstance(vals.get("name"), list):
                    authors.extend(vals.get("name"))
            elif isinstance(vals, list):
                for val in vals:
                    if isinstance(val, dict):
                        authors.append(val.get("name"))
                    elif isinstance(val, str):
                        authors.append(val)
            elif isinstance(vals, str):
                authors.append(vals)

        for script_tag in json_ld_scripts:
            if "@graph" in script_tag:
                g = script_tag.get("@graph", [])
                for item in g:
                    if not isinstance(item, dict):
                        continue
                    if item.get("@type") == "Person":
                        authors.append(item.get("name"))
                    if "author" in item:
                        get_authors(item["author"])
            else:
                if "author" in script_tag:
                    get_authors(script_tag["author"])

        def get_text_from_element(node: lxml.html.HtmlElement) -> str:
            """Return the text from an element, including the text from its children
            Args:
                node (lxml.html.HtmlElement): Input node
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
            text = parsers.get_text(node)
            return text

        authors = [re.sub("[\n\t\r\xa0]", " ", x) for x in authors if x]
        doc_root = doc.getroottree()

        def getpath(node):
            if doc_root is not None:
                return doc_root.getpath(node)

        # TODO: be more specific, not a combination of all attributes and values
        for attr in AUTHOR_ATTRS:
            for val in AUTHOR_VALS:
                # found = doc.xpath('//*[@%s="%s"]' % (attr, val))
                found = parsers.get_elements_by_attribs(doc, attribs={attr: val})
                matches.extend([(found, getpath(found)) for found in found])

        matches.sort(
            key=lambda x: x[1], reverse=True
        )  # sort by xpath. we want the most specific match
        matches_reduced: List[Tuple[Any, str]] = []
        for m in matches:
            if len(matches_reduced) == 0:
                matches_reduced.append(m)
            elif not matches_reduced[-1][1].startswith(
                m[1]
            ):  # remove parents of previous node
                matches_reduced.append(m)
        matches_reduced.sort(
            key=lambda x: x[1]
        )  # Preserve some sort of order for the authors

        for match, _ in matches_reduced:
            content: Union[str, List] = ""
            if match.tag == "meta":
                mm = match.xpath("@content")
                if len(mm) > 0:
                    content = mm[0]
            else:
                # TODO: ignore <time> tags, or tags with "on ..."
                # TODO: remove <style> tags https://washingtonindependent.com/how-to-apply-for-reseller-permit-in-washington-state/
                content = get_text_from_element(match)
            if len(content) > 0:
                authors.extend(parse_byline(content))

        # Clean up authors of stopwords such as Reporter, Senior Reporter
        authors = [re.sub(author_stopwords, "", x).strip(" .,-/") for x in authors]
        self.authors = uniqify_list(authors)

        return self.authors
