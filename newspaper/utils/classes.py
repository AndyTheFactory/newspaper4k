# -*- coding: utf-8 -*-
# Much of the code here was forked from https://github.com/codelucas/newspaper
# Copyright (c) Lucas Ou-Yang (codelucas)

from dataclasses import dataclass
from pathlib import Path
import pickle
from typing import Callable, Optional
import hashlib
import time

from newspaper.settings import CACHE_DIRECTORY


@dataclass
class Video:
    """Video object"""

    embed_type: Optional[str] = None
    # Video provider name
    provider: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    # embedding html code
    embed_code: Optional[str] = None
    src: Optional[str] = None


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


class CacheDiskDecorator:
    def __init__(self, enabled=True):
        self._enabled = enabled
        self._seconds = 86400
        self._cache_folder = CACHE_DIRECTORY

    @property
    def enabled(self):
        return self._enabled

    @enabled.setter
    def enabled(self, value):
        self._enabled = value

    def get_cache_file(self, domain):
        filename = hashlib.sha1((domain).encode("utf-8")).hexdigest()
        return Path(self._cache_folder) / filename

    def _do_cache(self, target_function) -> Callable:
        def inner_function(*args, **kwargs):
            """Calculate a cache key based on the decorated method signature
            args[1] indicates the domain of the inputs, we hash on domain!
            """
            if not self.enabled:
                return target_function(*args, **kwargs)

            filepath = self.get_cache_file(kwargs.get("domain") or args[1])

            # verify that the cached object exists and is less than
            # X seconds old
            if filepath.exists():
                modified = filepath.stat().st_mtime
                age_seconds = time.time() - modified
                if age_seconds < self._seconds:
                    with open(filepath, "rb") as f:
                        return pickle.load(f)

            # call the decorated function...
            result = target_function(*args, **kwargs)
            # ... and save the cached object for next time
            with open(filepath, "wb") as f:
                pickle.dump(result, f)

            return result

        return inner_function

    def __call__(self, seconds=None):
        self._seconds = seconds or self._seconds
        return self._do_cache
