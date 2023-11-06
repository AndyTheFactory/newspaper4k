from datetime import datetime
import json
import re
from typing import Optional

import lxml
from newspaper import urls
from newspaper.configuration import Configuration
from dateutil.parser import parse as date_parser

from newspaper.extractors.defines import PUBLISH_DATE_TAGS


class PubdateExtractor:
    def __init__(self, config: Configuration) -> None:
        self.config = config
        self.parser = config.get_parser()
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
            date_str = date_match.group(0)
            datetime_obj = parse_date_str(date_str)
            if datetime_obj:
                date_matches.append((datetime_obj, 10))  # date and matchscore

        # yoast seo structured data
        yoast_script_tag = self.parser.getElementsByTag(
            doc, tag="script", attr="type", value="application/ld+json"
        )
        # TODO: get author names from Json-LD
        if yoast_script_tag:
            for script_tag in yoast_script_tag:
                if "yoast-schema-graph" in script_tag.attrib.get("class", ""):
                    try:
                        schema_json = json.loads(script_tag.text)
                    except Exception:
                        continue

                    g = schema_json.get("@graph", [])
                    for item in g:
                        date_str = item.get("datePublished")
                        datetime_obj = parse_date_str(date_str)
                        if datetime_obj:
                            date_matches.append((datetime_obj, 10))
                else:
                    # Some other type of Json-LD
                    m = re.search(
                        "[\"']datePublished[\"']\s?:\s?[\"']([^\"']+)[\"']",
                        script_tag.text,
                    )
                    if m:
                        date_str = m.group(1)
                        datetime_obj = parse_date_str(date_str)
                        if datetime_obj:
                            date_matches.append((datetime_obj, 9))

        for known_meta_tag in PUBLISH_DATE_TAGS:
            meta_tags = self.parser.getElementsByTag(
                doc, attr=known_meta_tag["attribute"], value=known_meta_tag["value"]
            )
            for meta_tag in meta_tags:
                date_str = self.parser.getAttribute(meta_tag, known_meta_tag["content"])
                datetime_obj = parse_date_str(date_str)
                if datetime_obj:
                    score = 6
                    if meta_tag.attrib.get("name") == known_meta_tag["value"]:
                        score += 2
                    days_diff = (datetime.now().date() - datetime_obj.date()).days
                    if days_diff < 0:  # articles from the future
                        score -= 2
                    elif days_diff > 25 * 365:  # very old articles
                        score -= 1
                    date_matches.append((datetime_obj, score))

        date_matches.sort(key=lambda x: x[1], reverse=True)
        self.pubdate = date_matches[0][0] if date_matches else None
        return self.pubdate
