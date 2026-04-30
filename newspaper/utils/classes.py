"""This module contains the class for Video object and CacheDiskDecorator
CacheDiskDecorator provides the caching for the source categories on disk
The object allows runtime enabling and disabling of the cache (by using
utils.cache_disk.enabled = False) or Configuration.disable_category_cache = True
"""

import hashlib
import pickle
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from newspaper.settings import CACHE_DIRECTORY


@dataclass
class Video:
    """Video object"""

    embed_type: str | None = None
    # Video provider name
    provider: str | None = None
    width: int | None = None
    height: int | None = None
    # embedding html code
    embed_code: str | None = None
    src: str | None = None


class CacheDiskDecorator:
    """Cache disk decorator for caching the results of the source
    category discovery on disk. It is a simple decorator that uses the pickle
    module to serialize the result of a function and save it to disk. It also
    deserializes the result from disk if the cache is not stale.
    It can be disabled by setting utils.cache_disk.enabled = False or by setting
    Configuration.disable_category_cache = True in the Configuration object.
    """

    def __init__(self, enabled: bool = True) -> None:
        self._enabled = enabled
        self._seconds = 86400
        self._cache_folder = CACHE_DIRECTORY

    @property
    def enabled(self) -> bool:
        """Whether disk caching is enabled."""
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        self._enabled = value

    def get_cache_file(self, domain: str) -> Path:
        """Return the path for the cache file for the given domain.

        Args:
            domain (str): The domain to get the cache file for.

        Returns:
            Path: The path to the cache file.
        """
        filename = hashlib.sha1((domain).encode("utf-8")).hexdigest()
        return Path(self._cache_folder) / filename

    def _do_cache(self, target_function: Callable) -> Callable:
        def inner_function(*args: Any, **kwargs: Any) -> Any:
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

    def __call__(self, seconds: int | None = None) -> Callable:
        """Set the cache duration and return the cache decorator.

        Args:
            seconds (int | None): Cache duration in seconds. Defaults to None (uses current value).

        Returns:
            Callable: The inner cache decorator.
        """
        self._seconds = seconds or self._seconds
        return self._do_cache
