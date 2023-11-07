# -*- coding: utf-8 -*-
# Much of the code here was forked from https://github.com/codelucas/newspaper
# Copyright (c) Lucas Ou-Yang (codelucas)

"""
All code involving requests and responses over the http network
must be abstracted in this file.
"""
import logging
import requests

from .configuration import Configuration
from .mthreading import ThreadPool


log = logging.getLogger(__name__)


FAIL_ENCODING = "ISO-8859-1"


def get_html(url, config=None, response=None):
    """HTTP response code agnostic"""
    try:
        html, status_code = get_html_2XX_only(url, config, response)
        if status_code >= 400:
            log.warning("get_html() bad status code %s on URL: %s", status_code, url)
            html = ""
    except requests.exceptions.RequestException as e:
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
        return _get_html_from_response(response, config)

    response = requests.get(
        url=url,
        **config.requests_params,
    )
    # TODO: log warning with response codes<>200
    if response.status_code != 200:
        log.warning(
            "get_html_2XX_only(): bad status code %s on URL: %s, html: %s",
            response.status_code,
            url,
            response.text[:200],
        )
    html = _get_html_from_response(response, config)
    if isinstance(html, bytes):
        html = config.get_parser().get_unicode_html(html)

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


class MRequest:
    """Wrapper for request object for multithreading. If the domain we are
    crawling is under heavy load, the self.resp will be left as None.
    If this is the case, we still want to report the url which has failed
    so (perhaps) we can try again later.
    """

    def __init__(self, url, config=None):
        self.url = url
        self.config = config
        self.config = config or Configuration()
        self.resp = None

    def send(self):
        try:
            self.resp = requests.get(
                self.url,
                **self.config.requests_params,
            )
            if self.config.http_success_only:
                self.resp.raise_for_status()
        except requests.exceptions.RequestException as e:
            log.critical("[REQUEST FAILED] %s", str(e))


def multithread_request(urls, config=None):
    """Request multiple urls via mthreading, order of urls & requests is stable
    returns same requests but with response variables filled.
    """
    config = config or Configuration()
    num_threads = config.number_threads
    timeout = config.thread_timeout_seconds

    pool = ThreadPool(num_threads, timeout)

    m_requests = []
    for url in urls:
        m_requests.append(MRequest(url, config))

    for req in m_requests:
        pool.add_task(req.send)

    pool.wait_completion()
    return m_requests
