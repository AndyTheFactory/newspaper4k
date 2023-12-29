# -*- coding: utf-8 -*-
# Much of the code here was forked from https://github.com/codelucas/newspaper
# Copyright (c) Lucas Ou-Yang (codelucas)

"""
All code involving requests and responses over the http network
must be abstracted in this file.
"""
from concurrent.futures import ThreadPoolExecutor
import logging
from typing import Callable
import requests
from requests import RequestException
import tldextract

from .configuration import Configuration
from newspaper import parsers

log = logging.getLogger(__name__)

FAIL_ENCODING = "ISO-8859-1"


class ArticleBinaryDataException(Exception):
    pass


def do_cache(func: Callable):
    def wrapper(*args, **kwargs):
        if not hasattr(func, "cache"):
            func.cache = {}
        if kwargs.get("url"):
            url = kwargs["url"]
        else:
            url = args[0] if len(args) > 0 else None
        if url:
            tld = tldextract.extract(url).domain + "." + tldextract.extract(url).suffix
        else:
            return func(*args, **kwargs)

        if tld not in func.cache:
            func.cache[tld] = func(*args, **kwargs)
        return func.cache[tld]

    return wrapper


@do_cache
def has_get_ranges(url: str) -> bool:
    """Does this url support HTTP Range requests?"""
    try:
        resp = requests.head(url, timeout=3, allow_redirects=False)
        if resp.status_code in [301, 302, 303, 307, 308]:
            new_url = resp.headers.get("Location")
            if new_url:
                resp = requests.head(url, timeout=3, allow_redirects=True)
                url = new_url

        if "Accept-Ranges" in resp.headers:
            return True

        resp = requests.get(url, headers={"Range": "bytes=0-4"}, timeout=3)
        if resp.status_code == 206:
            return True
    except RequestException as e:
        log.debug("has_get_ranges() error. %s on URL: %s", e, url)
    return False


def is_binary_url(url: str) -> bool:
    """Does this url point to a binary file?"""
    try:
        resp = requests.head(url, timeout=3)
        if "Content-Type" in resp.headers:
            if resp.headers["Content-Type"].startswith("application"):
                if (
                    "json" not in resp.headers["Content-Type"]
                    and "xml" not in resp.headers["Content-Type"]
                ):
                    return True
            if resp.headers["Content-Type"].startswith("image"):
                return True
            if resp.headers["Content-Type"].startswith("video"):
                return True
            if resp.headers["Content-Type"].startswith("audio"):
                return True
            if resp.headers["Content-Type"].startswith("font"):
                return True

        if "Content-Disposition" in resp.headers:
            return True

        if not has_get_ranges(url):
            return False
        resp = requests.get(
            url, headers={"Range": "bytes=0-1000"}, timeout=3, allow_redirects=False
        )
        if resp.status_code in [301, 302, 303, 307, 308]:
            new_url = resp.headers.get("Location")
            if new_url:
                resp = requests.get(
                    new_url,
                    headers={"Range": "bytes=0-1000"},
                    timeout=3,
                    allow_redirects=True,
                )

        content = resp.content
        if isinstance(content, bytes):
            try:
                content = content.decode("utf-8", errors="replace")
            except UnicodeDecodeError:
                pass

        content = content[:1000]

        if len(content) == 0:
            return False

        if "<html" in content:
            return False

        chars = len(
            [
                char
                for char in content
                if 31 < ord(char) < 128 or ord(char) in [9, 10, 13]
            ]
        )
        if chars / len(content) < 0.6:  # 40% of the content is binary
            return True

        return False

    except RequestException as e:
        log.debug("is_binary_url() error. %s on URL: %s", e, url)
    return False


def do_request(url, config):
    if not config.allow_binary_content and has_get_ranges(url):
        if is_binary_url(url):
            raise ArticleBinaryDataException(f"Article is binary data: {url}")

    response = requests.get(
        url=url,
        **config.requests_params,
    )

    return response


def get_html(url, config=None, response=None):
    """HTTP response code agnostic"""
    html = ""
    try:
        html, status_code = get_html_2XX_only(url, config, response)
        if status_code >= 400:
            log.warning("get_html() bad status code %s on URL: %s", status_code, url)

    except RequestException as e:
        log.debug("get_html() error. %s on URL: %s", e, url)

    return html


def get_html_2XX_only(url, config=None, response=None):
    """Consolidated logic for http requests from newspaper. We handle error cases:
    - Attempt to find encoding of the html by using HTTP header. Fallback to
      'ISO-8859-1' if not provided.
    - Error out if a non 2XX HTTP response code is returned.
    """
    config = config or Configuration()

    if response is not None:
        return _get_html_from_response(response, config), response.status_code

    response = do_request(url, config)

    if response.status_code != 200:
        log.warning(
            "get_html_2XX_only(): bad status code %s on URL: %s, html: %s",
            response.status_code,
            url,
            response.text[:200],
        )
    html = _get_html_from_response(response, config)
    if isinstance(html, bytes):
        html = parsers.get_unicode_html(html)

    return html, response.status_code


def _get_html_from_response(response, config):
    if response.headers.get("content-type") in config.ignored_content_types_defaults:
        return config.ignored_content_types_defaults[
            response.headers.get("content-type")
        ]
    if response.encoding != FAIL_ENCODING:
        # return response as a unicode string
        html = response.text
    else:
        html = response.content
        if "charset" not in response.headers.get("content-type"):
            encodings = requests.utils.get_encodings_from_content(response.text)
            if len(encodings) > 0:
                response.encoding = encodings[0]
                html = response.text

    return html or ""


def multithread_request(urls, config=None):
    """Request multiple urls via mthreading, order of urls & requests is stable
    returns same requests but with response variables filled.
    """
    config = config or Configuration()

    timeout = config.thread_timeout_seconds
    requests_timeout = config.requests_params.get("timeout", 7)

    if timeout < requests_timeout:
        log.warning(
            "multithread_request(): Thread timeout %s < Requests timeout %s, could"
            " cause threads to be stopped before getting the chance to finish. Consider"
            " increasing the thread timeout.",
            timeout,
            requests_timeout,
        )
    results = []
    with ThreadPoolExecutor(max_workers=config.number_threads) as tpe:
        result_futures = [
            tpe.submit(do_request, url=url, config=config) for url in urls
        ]
        for idx, future in enumerate(result_futures):
            url = urls[idx]
            try:
                results.append(future.result())
            except TimeoutError:
                results.append(None)
                log.error("multithread_request(): Thread timeout for URL: %s", url)
            except RequestException as e:
                results.append(None)
                log.warning(
                    "multithread_request(): Http download error %s on URL: %s", e, url
                )

    return results
