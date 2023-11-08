import re
import lxml

from newspaper.configuration import Configuration
from newspaper.extractors.defines import MOTLEY_REPLACEMENT, TITLE_REPLACEMENTS
from newspaper.utils import StringSplitter


class TitleExtractor:
    def __init__(self, config: Configuration) -> None:
        self.config = config
        self.parser = config.get_parser()
        self.title: str = ""

    def parse(self, doc: lxml.html.Element) -> str:
        """Fetch the article title and analyze it

        Assumptions:
        - title tag is the most reliable (inherited from Goose)
        - h1, if properly detected, is the best (visible to users)
        - og:title and h1 can help improve the title extraction
        - python == is too strict, often we need to compare filtered
          versions, i.e. lowercase and ignoring special chars

        Explicit rules:
        1. title == h1, no need to split
        2. h1 similar to og:title, use h1
        3. title contains h1, title contains og:title, len(h1) > len(og:title), use h1
        4. title starts with og:title, use og:title
        5. use title, after splitting
        """
        self.title = ""
        title_element = self.parser.getElementsByTag(doc, tag="title")
        # no title found
        if title_element is None or len(title_element) == 0:
            return self.title

        # title elem found
        title_text = self.parser.getText(title_element[0])
        used_delimeter = False

        # title from h1
        # - extract the longest text from all h1 elements
        # - too short texts (fewer than 2 words) are discarded
        # - clean double spaces
        title_text_h1 = ""
        title_element_h1_list = self.parser.getElementsByTag(doc, tag="h1") or []
        title_text_h1_list = [self.parser.getText(tag) for tag in title_element_h1_list]
        if title_text_h1_list:
            # sort by len and set the longest
            title_text_h1_list.sort(key=len, reverse=True)
            title_text_h1 = title_text_h1_list[0]
            # discard too short texts
            if len(title_text_h1.split(" ")) <= 2:
                title_text_h1 = ""
            # clean double spaces
            title_text_h1 = " ".join([x for x in title_text_h1.split() if x])

        # title from og:title
        title_text_fb = (
            self._get_meta_field(doc, 'meta[property="og:title"]')
            or self._get_meta_field(doc, 'meta[name="og:title"]')
            or ""
        )

        # create filtered versions of title_text, title_text_h1, title_text_fb
        # for finer comparison
        filter_regex = re.compile(r"[^\u4e00-\u9fa5a-zA-Z0-9\ ]")
        filter_title_text = filter_regex.sub("", title_text).lower()
        filter_title_text_h1 = filter_regex.sub("", title_text_h1).lower()
        filter_title_text_fb = filter_regex.sub("", title_text_fb).lower()

        # check for better alternatives for title_text and possibly skip splitting
        if title_text_h1 == title_text:
            used_delimeter = True
        elif filter_title_text_h1 and filter_title_text_h1 == filter_title_text_fb:
            title_text = title_text_h1
            used_delimeter = True
        elif (
            filter_title_text_h1
            and filter_title_text_h1 in filter_title_text
            and filter_title_text_fb
            and filter_title_text_fb in filter_title_text
            and len(title_text_h1) > len(title_text_fb)
        ):
            title_text = title_text_h1
            used_delimeter = True
        elif (
            filter_title_text_fb
            and filter_title_text_fb != filter_title_text
            and filter_title_text.startswith(filter_title_text_fb)
        ):
            title_text = title_text_fb
            used_delimeter = True

        if not used_delimeter:
            for delimiter in ["|", "-", "_", "/", " » "]:
                if delimiter in title_text:
                    title_text = self._split_title(
                        title_text, StringSplitter(delimiter), title_text_h1
                    )
                    used_delimeter = True
                    break

        title = MOTLEY_REPLACEMENT.replaceAll(title_text)

        # in some cases the final title is quite similar to title_text_h1
        # (either it differs for case, for special chars, or it's truncated)
        # in these cases, we prefer the title_text_h1
        filter_title = filter_regex.sub("", title).lower()
        if filter_title_text_h1 == filter_title:
            title = title_text_h1

        self.title = title.strip()

        return self.title

    def _get_meta_field(self, doc: lxml.html.Element, field: str) -> str:
        """Extract a given meta field from document."""
        metafield = self.parser.css_select(doc, field)
        if metafield:
            return metafield[0].get("content", "").strip()
        return ""

    def _split_title(self, title, splitter, hint=None):
        """Split the title to best part possible"""
        large_text_length = 0
        large_text_index = 0
        title_pieces = splitter.split(title)

        if hint:
            filter_regex = re.compile(r"[^a-zA-Z0-9\ ]")
            hint = filter_regex.sub("", hint).lower()

        # find the largest title piece
        for i, title_piece in enumerate(title_pieces):
            current = title_piece.strip()
            if hint and hint in filter_regex.sub("", current).lower():
                large_text_index = i
                break
            if len(current) > large_text_length:
                large_text_length = len(current)
                large_text_index = i

        # replace content
        title = title_pieces[large_text_index]
        return TITLE_REPLACEMENTS.replaceAll(title).strip()
