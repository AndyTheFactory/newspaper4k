import re
from typing import Optional
import lxml

from newspaper.configuration import Configuration
from newspaper.languages import language_regex
import newspaper.parsers as parsers
from newspaper.extractors.defines import (
    MOTLEY_REPLACEMENT,
    TITLE_META_INFO,
    TITLE_REPLACEMENTS,
)


class TitleExtractor:
    def __init__(self, config: Configuration) -> None:
        self.config = config
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
        title_element = parsers.get_tags(doc, tag="title")
        # no title found
        if title_element is None or len(title_element) == 0:
            return self.title

        # title elem found
        title_text = parsers.get_text(title_element[0])
        used_delimeter = False

        # title from h1
        # - extract the longest text from all h1 elements
        # - too short texts (fewer than 2 words) are discarded
        # - clean double spaces
        title_text_h1 = ""
        title_element_h1_list = parsers.get_tags(doc, tag="h1") or []
        title_text_h1_list = [parsers.get_text(tag) for tag in title_element_h1_list]
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
        def get_fb_title():
            for known_meta_tag in TITLE_META_INFO:
                meta_tags = parsers.get_metatags(doc, value=known_meta_tag)
                for meta_tag in meta_tags:
                    title_text_fb = meta_tag.get("content", "").strip()
                    if title_text_fb:
                        return title_text_fb
            return ""

        title_text_fb = get_fb_title()

        # create filtered versions of title_text, title_text_h1, title_text_fb
        # for finer comparison
        regex_chars = language_regex(self.config.language)
        filter_regex = re.compile(f"[^{regex_chars}]")
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
                    title_text = self._split_title(title_text, delimiter, title_text_h1)
                    used_delimeter = True
                    break

        title = title_text.replace(*MOTLEY_REPLACEMENT)

        # in some cases the final title is quite similar to title_text_h1
        # (either it differs for case, for special chars, or it's truncated)
        # in these cases, we prefer the title_text_h1
        filter_title = filter_regex.sub("", title).lower()
        if filter_title_text_h1 == filter_title:
            title = title_text_h1

        self.title = title.strip()

        return self.title

    def _split_title(self, title: str, delimiter: str, hint: Optional[str] = None):
        """Split the title to best part possible"""
        large_text_length = 0
        large_text_index = 0
        title_pieces = title.split(delimiter)

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
        return title.replace(*TITLE_REPLACEMENTS)
