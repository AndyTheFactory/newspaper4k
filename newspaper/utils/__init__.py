# -*- coding: utf-8 -*-
# Much of the code here was forked from https://github.com/codelucas/newspaper
# Copyright (c) Lucas Ou-Yang (codelucas)

"""
Holds misc. utility methods which prove to be
useful throughout this library.
"""

import logging
from pathlib import Path
import random
import string
import sys
import time

from bs4 import BeautifulSoup

from newspaper.languages import get_language_from_iso639_1
from newspaper import settings
from .classes import CacheDiskDecorator, URLHelper, RawHelper

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

cache_disk = CacheDiskDecorator(enabled=True)


def domain_to_filename(domain):
    """All '/' are turned into '-', no trailing. schema's
    are gone, only the raw domain + ".txt" remains
    """
    filename = domain.replace("/", "-")
    if filename[-1] == "-":
        filename = filename[:-1]
    filename += ".txt"
    return filename


def filename_to_domain(filename):
    """[:-4] for the .txt at end"""
    return filename.replace("-", "/")[:-4]


def extract_meta_refresh(html):
    """Parses html for a tag like:
    <meta http-equiv="refresh" content="0;
            URL='http://sfbay.craigslist.org/eby/cto/5617800926.html'" />
    Example can be found at:
        https://www.google.com/url?rct=j&sa=t&url=
        http://sfbay.craigslist.org/eby/cto/5617800926.html&
        ct=ga&cd=CAAYATIaYTc4ZTgzYjAwOTAwY2M4Yjpjb206ZW46VVM&
        usg=AFQjCNF7zAl6JPuEsV4PbEzBomJTUpX4Lg
    """
    soup = BeautifulSoup(html, "html.parser")
    element = soup.find("meta", attrs={"http-equiv": "refresh"})
    if element:
        try:
            _, url_part = element["content"].split(";")
        except ValueError:
            # In case there are not enough values to unpack
            # for instance: <meta http-equiv="refresh" content="600" />
            return None
        else:
            # Get rid of any " or ' inside the element
            # for instance:
            # <meta http-equiv="refresh" content="0;
            #           URL='http://sfbay.craigslist.org/eby/cto/5617800926.html'" />
            if url_part.lower().startswith("url="):
                return url_part[4:].replace('"', "").replace("'", "")


def to_valid_filename(s):
    """Converts arbitrary string (for us domain name)
    into a valid file name for caching
    """
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    return "".join(c for c in s if c in valid_chars)


def clear_memo_cache(source):
    """Clears the memoization cache for this specific news domain"""
    cache_file = settings.MEMO_DIR / domain_to_filename(source.domain)
    if cache_file.exists():
        cache_file.unlink()
    else:
        log.info("memo file for %s has already been deleted!", source.domain)


def memorize_articles(source, articles):
    """When we parse the <a> links in an <html> page, on the 2nd run
    and later, check the <a> links of previous runs. If they match,
    it means the link must not be an article, because article urls
    change as time passes. This method also uniquifies articles.
    """
    if len(articles) == 0:
        return []

    source_domain = source.domain

    cache_file = settings.MEMO_DIR / domain_to_filename(source_domain)

    if cache_file.exists():
        with open(cache_file, "r", encoding="utf-8") as f:
            urls = f.readlines()

        valid_urls = [u.strip() for u in urls if u.strip()]

        # select not already seen urls
        cur_articles = {
            article.url: article
            for article in articles
            if article.url not in valid_urls
        }

        valid_urls.extend([url for url in cur_articles])

    else:
        cur_articles = {article.url: article for article in articles}
        valid_urls = list(cur_articles.keys())

    if len(valid_urls) > source.config.max_file_memo:
        valid_urls = valid_urls[: source.config.max_file_memo]
        log.warning("Source %s: memorization file overflow, truncating", source.domain)

    with open(cache_file, "w", encoding="utf-8") as f:
        f.writelines([x + "\n" for x in valid_urls if x])

    return list(cur_articles.values())


def get_useragent():
    """Returns a random useragent from our saved file"""
    with open(settings.USERAGENTS, "r", encoding="utf-8") as f:
        agents = f.readlines()
        selection = random.randint(0, len(agents) - 1)
        agent = agents[selection]
        return agent.strip()


def get_available_languages():
    """Returns a list of available languages and their 2 char input codes"""
    stopword_files = Path(settings.STOPWORDS_DIR).glob("stopwords-??.txt")
    for file in stopword_files:
        yield file.stem.split("-")[1]


def print_available_languages():
    """Prints available languages with their full names"""
    print("\nYour available languages are:")
    print("\ninput code\t\tfull name")

    for lang in get_available_languages():
        print("  %s\t\t\t  %s" % (lang, get_language_from_iso639_1(lang)))

    print()


def progressbar(it, prefix="", size=60, out=sys.stdout):
    """Display a simple progress bar without
    heavy dependencies like tqdm"""
    count = len(it)
    start = time.time()

    def show(j):
        x = int(size * j / count)
        remaining = ((time.time() - start) / j) * (count - j)

        mins, sec = divmod(remaining, 60)
        time_str = f"{int(mins):02}:{sec:05.2f}"

        print(
            f"{prefix}[{u'█'*x}{('.'*(size-x))}] {j}/{count} Est wait {time_str}",
            end="\r",
            file=out,
            flush=True,
        )

    for i, item in enumerate(it):
        yield item
        show(i + 1)
    print("\n", flush=True, file=out)


def print_node_tree(node, header="", last=True, with_gravity=True):
    """Prints out the html node tree for nodes with gravity scores
    debugging method
    """
    elbow = "└──"
    pipe = "│  "
    tee = "├──"
    if not with_gravity or node.get("gravityScore"):
        node_attribs = {
            k: node.attrib.get(k) for k in ["class", "id"] if node.attrib.get(k)
        }
        score = float(node.get("gravityScore", 0))
        print(
            header
            + (elbow if last else tee)
            + node.tag
            + f"({score:0.1f}) {node_attribs}"
        )
        blank = "   "
    else:
        blank = ""

    children = list(node.iterchildren())
    for i, c in enumerate(children):
        print_node_tree(
            c, header=header + (blank if last else pipe), last=i == len(children) - 1
        )


__all__ = [
    "RawHelper",
    "URLHelper",
    "domain_to_filename",
    "filename_to_domain",
    "extract_meta_refresh",
    "to_valid_filename",
    "cache_disk",
    "clear_memo_cache",
    "memorize_articles",
    "get_useragent",
    "get_available_languages",
    "print_available_languages",
    "progressbar",
    "print_node_tree",
]
