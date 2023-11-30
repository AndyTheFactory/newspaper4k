# -*- coding: utf-8 -*-
# Much of the code here was forked from https://github.com/codelucas/newspaper
# Copyright (c) Lucas Ou-Yang (codelucas)

"""
Holds misc. utility methods which prove to be
useful throughout this library.
"""

import codecs
import hashlib
import logging
import os
from pathlib import Path
import pickle
import random
import re
import string
import sys
import threading
import time

from hashlib import sha1

from bs4 import BeautifulSoup

from newspaper.languages import get_language_from_iso639_1

from newspaper import settings

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


class FileHelper:
    @staticmethod
    def loadResourceFile(filename):
        if not os.path.isabs(filename):
            dirpath = os.path.abspath(os.path.dirname(__file__))
            path = os.path.join(dirpath, "resources", filename)
        else:
            path = filename
        try:
            f = codecs.open(path, "r", "utf-8")
            content = f.read()
            f.close()
            return content
        except IOError as e:
            raise IOError("Couldn't open file %s" % path) from e


class ParsingCandidate:
    def __init__(self, url, link_hash):
        self.url = url
        self.link_hash = link_hash


class RawHelper:
    @staticmethod
    def get_parsing_candidate(url, raw_html):
        if isinstance(raw_html, str):
            raw_html = raw_html.encode("utf-8", "replace")
        link_hash = "%s.%s" % (hashlib.md5(raw_html).hexdigest(), time.time())
        return ParsingCandidate(url, link_hash)


class URLHelper:
    @staticmethod
    def get_parsing_candidate(url_to_crawl):
        # Replace shebang in urls
        final_url = (
            url_to_crawl.replace("#!", "?_escaped_fragment_=")
            if "#!" in url_to_crawl
            else url_to_crawl
        )
        link_hash = "%s.%s" % (hashlib.md5(final_url).hexdigest(), time.time())
        return ParsingCandidate(final_url, link_hash)


class StringSplitter:
    def __init__(self, pattern):
        self.pattern = re.compile(re.escape(pattern))

    def split(self, string):
        if not string:
            return []
        return self.pattern.split(string)


class StringReplacement:
    def __init__(self, pattern, replaceWith):
        self.pattern = pattern
        self.replaceWith = replaceWith

    def replaceAll(self, string):
        if not string:
            return ""
        return string.replace(self.pattern, self.replaceWith)


class ReplaceSequence:
    def __init__(self):
        self.replacements = []

    def create(self, firstPattern, replaceWith=None):
        result = StringReplacement(firstPattern, replaceWith or "")
        self.replacements.append(result)
        return self

    def append(self, pattern, replaceWith=None):
        return self.create(pattern, replaceWith)

    def replaceAll(self, string):
        if not string:
            return ""

        mutatedString = string
        for rp in self.replacements:
            mutatedString = rp.replaceAll(mutatedString)
        return mutatedString


def timelimit(timeout):
    """Borrowed from web.py, rip Aaron Swartz"""

    def _1(function):
        def _2(*args, **kw):
            class Dispatch(threading.Thread):
                def __init__(self):
                    threading.Thread.__init__(self)
                    self.result = None
                    self.error = None

                    self.daemon = True
                    self.start()

                def run(self):
                    try:
                        self.result = function(*args, **kw)
                    except Exception:
                        self.error = sys.exc_info()

            c = Dispatch()
            c.join(timeout)
            if c.is_alive():
                raise TimeoutError()
            if c.error:
                raise c.error[0](c.error[1])
            return c.result

        return _2

    return _1


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


def is_ascii(word):
    """True if a word is only ascii chars"""

    def onlyascii(char):
        if ord(char) > 127:
            return ""
        else:
            return char

    for c in word:
        if not onlyascii(c):
            return False
    return True


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


def cache_disk(seconds=(86400 * 5), cache_folder="/tmp"):
    """Caching extracting category locations & rss feeds for 5 days"""

    # TODO: add option to disable cache module wide
    def do_cache(function):
        def inner_function(*args, **kwargs):
            """Calculate a cache key based on the decorated method signature
            args[1] indicates the domain of the inputs, we hash on domain!
            """
            key = sha1((str(args[1]) + str(kwargs)).encode("utf-8")).hexdigest()
            filepath = Path(cache_folder) / key

            # verify that the cached object exists and is less than
            # X seconds old
            if filepath.exists():
                modified = filepath.stat().st_mtime
                age_seconds = time.time() - modified
                if age_seconds < seconds:
                    with open(filepath, "rb") as f:
                        return pickle.load(f)

            # call the decorated function...
            result = function(*args, **kwargs)
            # ... and save the cached object for next time
            with open(filepath, "wb") as f:
                pickle.dump(result, f)

            return result

        return inner_function

    return do_cache


def print_duration(method):
    """Prints out the runtime duration of a method in seconds"""

    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()
        print("%r %2.2f sec" % (method.__name__, te - ts))
        return result

    return timed


def chunks(lst, n):
    """Yield n successive chunks from lst"""
    newn = int(len(lst) / n)
    for i in range(0, n - 1):
        yield lst[i * newn : i * newn + newn]
    yield lst[n * newn - newn :]


def purge(fn, pattern):
    """Delete files in a dir matching pattern"""
    for p in Path(fn).glob("*"):
        if re.search(pattern, str(p.name)):
            p.unlink()


def clear_memo_cache(source):
    """Clears the memoization cache for this specific news domain"""
    d_pth = settings.MEMO_DIR / domain_to_filename(source.domain)
    if d_pth.exists():
        d_pth.unlink()
    else:
        print("memo file for", source.domain, "has already been deleted!")


def memoize_articles(source, articles):
    """When we parse the <a> links in an <html> page, on the 2nd run
    and later, check the <a> links of previous runs. If they match,
    it means the link must not be an article, because article urls
    change as time passes. This method also uniquifies articles.
    """
    source_domain = source.domain
    config = source.config

    if len(articles) == 0:
        return []

    memo = {}
    cur_articles = {article.url: article for article in articles}
    d_pth = settings.MEMO_DIR / domain_to_filename(source_domain)

    if d_pth.exists():
        f = codecs.open(d_pth, "r", "utf8")
        urls = f.readlines()
        f.close()
        urls = [u.strip() for u in urls]

        memo = {url: True for url in urls}
        # prev_length = len(memo)
        for url, article in list(cur_articles.items()):
            if memo.get(url):
                del cur_articles[url]

        valid_urls = list(memo.keys()) + list(cur_articles.keys())

        memo_text = "\r\n".join([href.strip() for href in (valid_urls)])
    # Our first run with memoization, save every url as valid
    else:
        memo_text = "\r\n".join([href.strip() for href in list(cur_articles.keys())])

    # new_length = len(cur_articles)
    if len(memo) > config.MAX_FILE_MEMO:
        # We still keep current batch of articles though!
        log.critical("memo overflow, dumping")
        memo_text = ""

    # TODO if source: source.write_upload_times(prev_length, new_length)
    ff = codecs.open(d_pth, "w", "utf-8")
    ff.write(memo_text)
    ff.close()
    return list(cur_articles.values())


def get_useragent():
    """Uses generator to return next useragent in saved file"""
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


def extend_config(config, config_items):
    """
    We are handling config value setting like this for a cleaner api.
    Users just need to pass in a named param to this source and we can
    dynamically generate a config object for it.
    """
    for key, val in list(config_items.items()):
        if hasattr(config, key):
            setattr(config, key, val)

    return config


__all__ = [
    "FileHelper",
    "ParsingCandidate",
    "RawHelper",
    "URLHelper",
    "StringSplitter",
    "StringReplacement",
    "ReplaceSequence",
    "timelimit",
    "domain_to_filename",
    "filename_to_domain",
    "is_ascii",
    "extract_meta_refresh",
    "to_valid_filename",
    "cache_disk",
    "print_duration",
    "chunks",
    "purge",
    "clear_memo_cache",
    "memoize_articles",
    "get_useragent",
    "get_available_languages",
    "print_available_languages",
    "extend_config",
]
