from datetime import datetime
import re
from typing import Optional

import lxml
from newspaper import urls
from newspaper.configuration import Configuration
import newspaper.parsers as parsers
from dateutil.parser import parse as date_parser

from newspaper.extractors.defines import PUBLISH_DATE_META_INFO, PUBLISH_DATE_TAGS


class PubdateExtractor:
    def __init__(self, config: Configuration) -> None:
        self.config = config
        self.pubdate: Optional[datetime] = None

    def parse(self, article_url: str, doc: lxml.html.Element) -> Optional[datetime]:
        """3 strategies for publishing date extraction. The strategies
        are descending in accuracy and the next strategy is only
        attempted if a preferred one fails.

        1. Pubdate from URL
        2. Pubdate from metadata
        3. Raw regex searches in the HTML + added heuristics
        """

        def parse_date_str(date_str):
            if date_str:
                try:
                    self.pubdate = date_parser(date_str)
                    return self.pubdate
                except (ValueError, OverflowError, AttributeError, TypeError):
                    # near all parse failures are due to URL dates without a day
                    # specifier, e.g. /2014/04/
                    return None

        date_matches = []
        date_match = re.search(urls.STRICT_DATE_REGEX, article_url)
        if date_match:
            date_match_str = date_match.group(0)
            datetime_obj = parse_date_str(date_match_str)
            if datetime_obj:
                date_matches.append((datetime_obj, 10))  # date and matchscore

        # yoast seo structured data or json-ld
        json_ld_scripts = parsers.get_ld_json_object(doc)

        for script_tag in json_ld_scripts:
            if "@graph" in script_tag:
                g = script_tag.get("@graph", [])
                for item in g:
                    if not isinstance(item, dict):
                        continue
                    date_str = item.get("datePublished")
                    if date_str is None:
                        continue
                    datetime_obj = parse_date_str(date_str)
                    if datetime_obj:
                        date_matches.append((datetime_obj, 10))
            else:
                for k in script_tag:
                    if k in ["datePublished", "dateCreated"]:
                        date_str = script_tag.get(k)
                        datetime_obj = parse_date_str(date_str)
                        if datetime_obj:
                            date_matches.append((datetime_obj, 9))

        # get <time> tags
        for item in parsers.get_tags(doc, tag="time"):
            if item.get("datetime"):
                date_str = item.get("datetime")
                datetime_obj = parse_date_str(date_str)
                if datetime_obj:
                    if item.text and re.search("published|\bon:", item.text, re.I):
                        date_matches.append(
                            (datetime_obj, 8)
                        )  # Boost if it has the word published or on
                    else:
                        date_matches.append((datetime_obj, 5))
        candidates = []

        for known_meta_info in PUBLISH_DATE_META_INFO:
            candidates.extend(parsers.get_metatags(doc, value=known_meta_info))
        candidates = [(x, "content") for x in candidates]  # property that contains
        # the date
        # is always 'content'
        for known_meta_tag in PUBLISH_DATE_TAGS:
            candidates.extend(
                [
                    (x, known_meta_tag["content"])
                    for x in parsers.get_elements_by_attribs(
                        doc,
                        attribs={known_meta_tag["attribute"]: known_meta_tag["value"]},
                    )
                ]
            )

        for meta_tag, content_attr in candidates:
            date_str = parsers.get_attribute(meta_tag, content_attr)
            datetime_obj = parse_date_str(date_str)
            if datetime_obj:
                score = 6
                if meta_tag.tag.lower() == "meta":
                    score += 1  # Boost meta tags
                days_diff = (datetime.now().date() - datetime_obj.date()).days
                if days_diff < 0:  # articles from the future
                    score -= 2
                elif days_diff > 25 * 365:  # very old articles
                    score -= 1
                date_matches.append((datetime_obj, score))

        date_matches.sort(key=lambda x: x[1], reverse=True)
        self.pubdate = date_matches[0][0] if date_matches else None
        return self.pubdate
