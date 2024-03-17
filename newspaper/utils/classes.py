"""
This module contains the class for Video object and CacheDiskDecorator
CacheDiskDecorator provides the caching for the source categories on disk
The object allows runtime enabling and disabling of the cache (by using
utils.cache_disk.enabled = False) or Configuration.disable_category_cache = True
"""

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


class CacheDiskDecorator:
    """Cache disk decorator for caching the results of the source
    category discovery on disk. It is a simple decorator that uses the pickle
    module to serialize the result of a function and save it to disk. It also
    deserializes the result from disk if the cache is not stale.
    It can be disabled by setting utils.cache_disk.enabled = False or by setting
    Configuration.disable_category_cache = True in the Configuration object.
    """

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
