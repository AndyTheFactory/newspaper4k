"""
Helper functions for http requests and remote data fetching.
"""

from concurrent.futures import ThreadPoolExecutor
from typing import Callable, List, Optional, Tuple, Union
import logging
import requests

from requests import RequestException
from requests import Response
import tldextract

from newspaper import parsers
from newspaper.exceptions import ArticleException, ArticleBinaryDataException
from newspaper.configuration import Configuration

log = logging.getLogger(__name__)

FAIL_ENCODING = "ISO-8859-1"


def get_session() -> requests.Session:
    """
    Get an HTTP requests session for making requests.

    This function returns an HTTP session object that can be used to make HTTP requests.
    If the `cloudscraper` library is available, it will be used to create the session.
    Otherwise, the `requests` library will be used as an alternative.

    Returns:
        requests.Session: An HTTP session object.

    """
    try:
        import cloudscraper  # noqa # pylint: disable=import-outside-toplevel

        sess = cloudscraper.create_scraper()
        log.info("Using cloudscraper for http requests")
    except ImportError:
        sess = requests.Session()
        log.info(
            "Using requests library for http requests (alternative cloudscraper"
            " library is recommended for bypassing Cloudflare protection)"
        )

    sess.headers.update(
        {
            "Accept-Encoding": "gzip, deflate",
        }
    )
    return sess


session = get_session()


def reset_session() -> requests.Session:
    """
    Resets the session variable to a new requests.Session object. Destroys any
    cookies and other session data that may have been stored in the previous
    object.

    Returns:
        requests.Session: The newly created session object.
    """
    global session  # pylint: disable=global-statement
    session = get_session()
    return session


def do_cache(func: Callable):
    """A decorator that caches the result of a function based on its arguments.
    expects url as one argument and caches the result based on the domain
    of the url.
    Args:
        func (Callable): The function to be cached.
    Returns:
        Callable: The wrapped function that caches the result.
    """

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
        resp = session.head(url, timeout=3, allow_redirects=False)
        if resp.status_code in [301, 302, 303, 307, 308]:
            new_url = resp.headers.get("Location")
            if new_url:
                resp = session.head(url, timeout=3, allow_redirects=True)
                url = new_url

        if "Accept-Ranges" in resp.headers:
            return True

        resp = session.get(
            url, headers={"Range": "bytes=0-100"}, timeout=3, stream=True
        )
        if resp.status_code == 206:
            return True

    except RequestException as e:
        log.debug("has_get_ranges() error. %s on URL: %s", e, url)
    return False


def is_binary_url(url: str) -> bool:
    """Does this url point to a binary file?"""
    try:
        resp = session.head(url, timeout=3, allow_redirects=True)
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
            resp = session.get(url, timeout=3, allow_redirects=True, stream=True)
            content: Union[str, bytes, None] = next(resp.iter_content(1000), None)
        else:
            resp = session.get(
                url, headers={"Range": "bytes=0-1000"}, timeout=3, allow_redirects=False
            )
            if resp.status_code in [301, 302, 303, 307, 308]:
                new_url = resp.headers.get("Location")
                if new_url:
                    resp = session.get(
                        new_url,
                        headers={"Range": "bytes=0-1000"},
                        timeout=3,
                        allow_redirects=True,
                    )
            content = resp.content

        if resp.status_code > 299 or content is None:
            return False  # We cannot test if we get an error

        if isinstance(content, bytes):
            content = content.decode("utf-8", errors="replace")

        content = content[:1000]

        if len(content) == 0:
            return False

        if "<html" in content:
            return False

        chars = len(
            [
                char
                for char in [ord(c) if isinstance(c, str) else c for c in content]
                if 31 < char < 128 or char in [9, 10, 13]
            ]
        )
        if chars / len(content) < 0.6:  # 40% of the content is binary
            return True

        return False

    except RequestException as e:
        log.debug("is_binary_url() error. %s on URL: %s", e, url)
    return False


def do_request(url: str, config: Configuration) -> Response:
    """Perform a HTTP GET request to the specified URL using the provided configuration.
    Args:
        url (str): The URL to send the request to.
        config (Configuration): The configuration object containing request parameters.

    Returns:
        requests.Response: The response object containing the server's response
            to the request.
    """
    session.headers.update(config.requests_params["headers"])

    if not config.allow_binary_content:
        if is_binary_url(url):
            raise ArticleBinaryDataException(f"Article is binary data: {url}")

    response = session.get(
        url=url,
        **config.requests_params,
    )

    return response


def get_html(
    url: str,
    config: Optional[Configuration] = None,
    response: Optional[Response] = None,
) -> str:
    """Returns the html content from an url.
    if response is provided, no download will occur. The html will be extracted
    from the provided response.
    It does encoding sanitization and dammit if necessary.
    In case of http error (e.g. 404, 500), it returns an empty string.
    If `config`.`http_success_only` is True, it raises an exception in
    case of a http error.
    """
    html = ""
    config = config or Configuration()
    try:
        html, status_code, _ = get_html_status(url, config, response)
        if status_code >= 400:
            log.warning("get_html() bad status code %s on URL: %s", status_code, url)
            if config.http_success_only:
                raise ArticleException(
                    f"Http error when downloading {url}. Status code: {{status_code}}"
                )
            return ""
    except RequestException as e:
        log.debug("get_html() error. %s on URL: %s", e, url)

    return html


def get_html_status(
    url: str,
    config: Optional[Configuration] = None,
    response: Optional[Response] = None,
) -> Tuple[str, int, List[Response]]:
    """Consolidated logic for http requests from newspaper. We handle error cases:
    - Attempt to find encoding of the html by using HTTP header. Fallback to
      'ISO-8859-1' if not provided.
    - Error out if a non 2XX HTTP response code is returned.
    """
    config = config or Configuration()

    if response is not None:
        return (
            _get_html_from_response(response, config),
            response.status_code,
            response.history,
        )

    response = do_request(url, config)

    if response.status_code != 200:
        log.warning(
            "get_html_status(): bad status code %s on URL: %s, html: %s",
            response.status_code,
            url,
            response.text[:200],
        )
    html = _get_html_from_response(response, config)
    if isinstance(html, bytes):
        html = parsers.get_unicode_html(html)

    return html, response.status_code, response.history


def _get_html_from_response(response: Response, config: Configuration) -> str:
    """Extracts and decodes the HTML content from a response object.
    Converts the response content to a utf string and returns it.

    Args:
        response (Response): The response object.
        config (Configuration): The configuration object.

    Returns:
        str: The HTML content extracted from the response.
    """
    if response.headers.get("content-type") in config.ignored_content_types_defaults:
        return config.ignored_content_types_defaults[
            response.headers.get("content-type")
        ]
    if response.encoding != FAIL_ENCODING:
        # return response as a unicode string
        html = response.text
    else:
        html = str(response.content, "utf-8", errors="replace")
        if "charset" not in response.headers.get("content-type", ""):
            encodings = requests.utils.get_encodings_from_content(response.text)
            if len(encodings) > 0:
                response.encoding = encodings[0]
                html = response.text

    return html or ""


def multithread_request(
    urls: List[str], config: Optional[Configuration] = None
) -> List[Optional[Response]]:
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
    results: List[Optional[Response]] = []
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
