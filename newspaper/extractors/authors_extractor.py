import re
import lxml
from typing import List, Union
from collections import OrderedDict
from newspaper.configuration import Configuration

from newspaper.extractors.defines import AUTHOR_ATTRS, AUTHOR_STOP_WORDS, AUTHOR_VALS


class AuthorsExtractor:
    def __init__(self, config: Configuration) -> None:
        self.config = config
        self.parser = config.get_parser()
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
            return [seen[item] for item in seen.keys() if item]

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
            search_str = re.sub(r"[bB][yY][\:\s]|[fF]rom[\:\s]", "", search_str)

            search_str = search_str.strip()

            # Chunk the line by non alphanumeric
            # tokens (few name exceptions)
            # >>> re.split("[^\w\'\-\.]",
            #           "Tyler G. Jones, Lucas Ou, Dean O'Brian and Ronald")
            # ['Tyler', 'G.', 'Jones', '', 'Lucas', 'Ou', '',
            #           'Dean', "O'Brian", 'and', 'Ronald']
            name_tokens = re.split(r"[^\w'\-\.]", search_str)
            name_tokens = [s.strip() for s in name_tokens]

            _authors = []
            # List of first, last name tokens
            curname = []
            delimiters = ["and", ",", ""]

            for token in name_tokens:
                if token in delimiters:
                    if len(curname) > 0:
                        _authors.append(" ".join(curname))
                        curname = []

                elif not contains_digits(token):
                    curname.append(token)

            # One last check at end
            valid_name = len(curname) >= 2
            if valid_name:
                _authors.append(" ".join(curname))

            return _authors

        # Try 1: Search popular author tags for authors

        matches = []
        authors = []

        json_ld_scripts = self.parser.get_ld_json_object(doc)

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
        authors = [x for x in authors if x]
        doc_root = doc.getroottree()

        def getpath(node):
            if doc_root is not None:
                return doc_root.getpath(node)

        # TODO: be more specific, not a combination of all attributes and values
        for attr in AUTHOR_ATTRS:
            for val in AUTHOR_VALS:
                # found = doc.xpath('//*[@%s="%s"]' % (attr, val))
                found = self.parser.get_element_by_attribs(doc, attribs={attr: val})
                matches.extend([(found, getpath(found)) for found in found])

        matches.sort(
            key=lambda x: x[1], reverse=True
        )  # sort by xpath. we want the most specific match
        matches_reduced = []
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
                content = list(match.itertext())
                content = " ".join(content)
            if len(content) > 0:
                authors.extend(parse_byline(content))

        # Clean up authors of stopwords such as Reporter, Senior Reporter
        authors = [re.sub(author_stopwords, "", x) for x in authors]
        self.authors = uniqify_list(authors)

        return self.authors
