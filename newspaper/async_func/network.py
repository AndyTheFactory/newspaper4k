"""Async HTTP helper functions for newspaper4k.

This module mirrors the responsibilities of :mod:`newspaper.network` but uses
``httpx.AsyncClient`` for non-blocking I/O.  It is intentionally additive:
the synchronous ``network.py`` is not modified.

Requires the ``async`` optional dependency group::

    pip install newspaper4k[async]

or, individually::

    pip install httpx
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

try:
    import httpx
except ImportError as _exc:
    raise ImportError(
        "You must install httpx before using the async API.\nTry: pip install newspaper4k[async]"
    ) from _exc
from w3lib.encoding import html_to_unicode

from newspaper import parsers
from newspaper.configuration import Configuration
from newspaper.exceptions import ArticleBinaryDataException, ArticleException, RobotsException
from newspaper.network_hooks import HookableEvent, get_hooks

DEFAULT_ENCODING = "utf-8"

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Client factory
# ---------------------------------------------------------------------------


def _build_proxy_mounts(proxies: dict[str, Any] | None) -> dict[str, httpx.AsyncHTTPTransport] | None:
    """Translate a ``requests``-style proxy mapping into httpx ``mounts``.

    httpx >=0.28 (the pinned version) dropped ``AsyncClient(proxies=...)`` in
    favour of per-scheme ``mounts``.

    Args:
        proxies: Mapping of scheme (``"http"``/``"https"``) to proxy URL, or *None*.

    Returns:
        A mapping suitable for :paramref:`httpx.AsyncClient.mounts`, or *None*
        when there is nothing to mount.
    """
    if not proxies:
        return None
    mounts: dict[str, httpx.AsyncHTTPTransport] = {}
    for scheme, proxy_url in proxies.items():
        if not proxy_url:
            continue
        pattern = scheme if "://" in scheme else f"{scheme}://"
        mounts[pattern] = httpx.AsyncHTTPTransport(proxy=proxy_url)
    return mounts or None


def _build_client(config: Configuration) -> httpx.AsyncClient:
    """Build an :class:`httpx.AsyncClient` configured from a :class:`Configuration`.

    Args:
        config: newspaper configuration object.

    Returns:
        A new :class:`httpx.AsyncClient` instance.
    """
    headers: dict[str, str] = dict(config.requests_params.get("headers", {}))
    headers.setdefault("Accept-Encoding", "gzip, deflate, br")

    mounts = _build_proxy_mounts(config.requests_params.get("proxies"))

    timeout_val = config.requests_params.get("timeout", 7)
    timeout = httpx.Timeout(float(timeout_val))

    verify: bool | str = config.requests_params.get("verify", True)
    cert = config.requests_params.get("cert", None)

    return httpx.AsyncClient(
        headers=headers,
        mounts=mounts,
        timeout=timeout,
        verify=verify,
        cert=cert,
        follow_redirects=config.requests_params.get("allow_redirects", True),
        max_redirects=10,
    )


def _get_client(config: Configuration) -> httpx.AsyncClient:
    """Return a cached, reusable :class:`httpx.AsyncClient` for *config*.

    Building a fresh client per request throws away connection pooling and
    keep-alive, forcing a new TCP/TLS handshake for every single call. One
    client is instead built lazily per :class:`Configuration` instance and
    cached on it, mirroring how the sync :mod:`newspaper.network` module
    reuses a single module-level ``requests.Session``.

    Args:
        config: newspaper configuration object.

    Returns:
        A live, open :class:`httpx.AsyncClient` instance.
    """
    client = getattr(config, "_async_http_client", None)
    if client is None or client.is_closed:
        client = _build_client(config)
        config._async_http_client = client
    return client


# ---------------------------------------------------------------------------
# Hook support
# ---------------------------------------------------------------------------


async def _run_hooks_async(event: str, *args: Any, **kwargs: Any) -> bool:
    """Invoke registered hooks for *event*, supporting both sync and async callables.

    Args:
        event: The :class:`~newspaper.network_hooks.HookableEvent` name.
        *args: Positional arguments forwarded to each hook.
        **kwargs: Keyword arguments forwarded to each hook.

    Returns:
        ``True`` if the request should continue, ``False`` if any hook returned
        ``False`` (indicating the request should be aborted).
    """
    continue_request = True
    for hook in get_hooks(event):  # type: ignore[arg-type]
        if asyncio.iscoroutinefunction(hook):
            result = await hook(*args, **kwargs)
        else:
            result = hook(*args, **kwargs)
        if result is False:
            continue_request = False
    return continue_request


# ---------------------------------------------------------------------------
# Core request function
# ---------------------------------------------------------------------------


async def async_do_request(
    url: str,
    config: Configuration,
    method: str = "get",
    data: str | None = None,
) -> httpx.Response:
    """Perform an async HTTP request honouring registered network hooks.

    Args:
        url: Target URL.
        config: newspaper :class:`~newspaper.configuration.Configuration`.
        method: HTTP method (``"get"`` or ``"post"``).
        data: Optional request body for POST requests.

    Returns:
        :class:`httpx.Response` from the server.

    Raises:
        ArticleBinaryDataException: If the URL points to binary content and
            ``config.allow_binary_content`` is ``False``.
        ArticleException: If an unsupported HTTP method is requested.
        RobotsException: Re-raised from a ``before_request`` hook.
    """
    # Fire before_request hooks
    should_continue = await _run_hooks_async(HookableEvent.BEFORE_REQUEST, url, config, method, data)
    if not should_continue:
        # A hook signalled to skip the request entirely; return an empty 204
        return httpx.Response(204)

    if not config.allow_binary_content:
        if await _async_is_binary_url(url, config):
            raise ArticleBinaryDataException(f"Article is binary data: {url}")

    try:
        client = _get_client(config)
        cookies = config.requests_params.get("cookies", None)
        auth = config.requests_params.get("auth", None)

        if method == "get":
            response = await client.get(url, cookies=cookies, auth=auth)
        elif method == "post":
            response = await client.post(url, data=data, cookies=cookies, auth=auth)
        else:
            raise ArticleException(f"Unsupported HTTP method: {method}")
    except Exception:
        for hook in get_hooks(HookableEvent.ON_ERROR):  # type: ignore[arg-type]
            if asyncio.iscoroutinefunction(hook):
                await hook(url, config, method, data)
            else:
                hook(url, config, method, data)
        raise

    # Fire after_response hooks
    await _run_hooks_async(HookableEvent.AFTER_RESPONSE, url, config, method, data)

    return response


# ---------------------------------------------------------------------------
# Binary-content detection (async)
# ---------------------------------------------------------------------------


async def _async_is_binary_url(url: str, config: Configuration) -> bool:
    """Async variant of :func:`newspaper.network.is_binary_url`.

    Performs a lightweight HEAD check to decide whether *url* points to
    binary data that should be rejected.

    Args:
        url: URL to inspect.
        config: newspaper configuration.

    Returns:
        ``True`` if the URL appears to serve binary content.
    """
    try:
        client = _get_client(config)
        resp = await client.head(url)
        content_type = resp.headers.get("content-type", "")
        if content_type.startswith(("image", "video", "audio", "font")):
            return True
        if content_type.startswith("application"):
            if "json" not in content_type and "xml" not in content_type:
                return True
        if "content-disposition" in resp.headers:
            return True

        # Sample the first 1 KB to heuristically decide
        range_resp = await client.get(url, headers={"Range": "bytes=0-1000"})
        content = range_resp.content[:1000]
        if not content:
            return False
        try:
            text = content.decode("utf-8", errors="replace")
        except Exception:
            return True
        if "<html" in text:
            return False
        printable_chars = sum(1 for c in text if 31 < ord(c) < 128 or ord(c) in (9, 10, 13))
        if printable_chars / max(len(text), 1) < 0.6:
            return True
        return False
    except Exception as exc:
        log.debug("_async_is_binary_url() error: %s on URL: %s", exc, url)
    return False


# ---------------------------------------------------------------------------
# HTML extraction helpers
# ---------------------------------------------------------------------------


def _get_html_from_httpx_response(response: httpx.Response, config: Configuration) -> str:
    """Decode HTML from an :class:`httpx.Response`.

    Mirrors :func:`newspaper.network._get_html_from_response`.

    Args:
        response: The HTTP response object.
        config: newspaper configuration.

    Returns:
        Decoded HTML string.
    """
    content_type = response.headers.get("content-type", "")
    if content_type in config.ignored_content_types_defaults:
        return config.ignored_content_types_defaults[content_type]

    _, html = html_to_unicode(
        content_type_header=content_type,
        html_body_str=response.content,
        default_encoding=DEFAULT_ENCODING,
    )
    return html or ""


async def async_get_html_status(
    url: str,
    config: Configuration | None = None,
) -> tuple[str, int, list[httpx.Response]]:
    """Async counterpart of :func:`newspaper.network.get_html_status`.

    Downloads *url* and returns ``(html, status_code, redirect_history)``.

    Args:
        url: Target URL.
        config: Configuration to use. Uses defaults if *None*.

    Returns:
        A 3-tuple of ``(html_string, http_status_code, response_history)``.
    """
    config = config or Configuration()
    response = await async_do_request(url, config)

    if response.status_code != 200:
        log.warning(
            "async_get_html_status(): bad status code %s on URL: %s",
            response.status_code,
            url,
        )

    html = _get_html_from_httpx_response(response, config)
    if isinstance(html, bytes):
        html = parsers.get_unicode_html(html)

    history: list[httpx.Response] = list(response.history) if hasattr(response, "history") else []
    return html, response.status_code, history


async def async_get_html(
    url: str,
    config: Configuration | None = None,
) -> str:
    """Async counterpart of :func:`newspaper.network.get_html`.

    Downloads *url* and returns the decoded HTML string, or ``""`` on error.

    Args:
        url: Target URL.
        config: Configuration to use. Uses defaults if *None*.

    Returns:
        Decoded HTML string, or ``""`` when the request failed.

    Raises:
        ArticleException: If ``config.http_success_only`` is ``True`` and the
            server returns an HTTP error status.
    """
    config = config or Configuration()
    try:
        html, status_code, _ = await async_get_html_status(url, config)
        if status_code >= 400:
            log.warning("async_get_html() bad status code %s on URL: %s", status_code, url)
            if config.http_success_only:
                raise ArticleException(f"Http error when downloading {url}. Status code: {status_code}")
            return ""
    except httpx.RequestError as exc:
        log.debug("async_get_html() error: %s on URL: %s", exc, url)
        return ""
    return html


# ---------------------------------------------------------------------------
# Batch request helper
# ---------------------------------------------------------------------------


async def async_batch_request(
    urls: list[str],
    config: Configuration | None = None,
    semaphore: asyncio.Semaphore | None = None,
) -> list[httpx.Response | None]:
    """Download multiple URLs concurrently, preserving input order.

    This is the async equivalent of :func:`newspaper.network.multithread_request`.

    Args:
        urls: List of URLs to download.
        config: Configuration to use. Uses defaults if *None*.
        semaphore: Optional semaphore to limit concurrency. When *None* a new
            semaphore with ``config.async_concurrency`` slots is created.

    Returns:
        List of :class:`httpx.Response` objects (or *None* on error) in the
        same order as the input *urls*.
    """
    config = config or Configuration()
    concurrency = getattr(config, "async_concurrency", 10)
    sem = semaphore or asyncio.Semaphore(concurrency)

    async def _fetch_one(url: str) -> httpx.Response | None:
        async with sem:
            try:
                return await async_do_request(url, config)
            except httpx.RequestError as exc:
                log.warning("async_batch_request(): http error %s on URL: %s", exc, url)
                return None
            except ArticleBinaryDataException:
                log.warning("async_batch_request(): binary content skipped for URL: %s", url)
                return None
            except RobotsException as exc:
                log.warning("async_batch_request(): robots.txt blocked URL: %s. %s", url, exc)
                return None
            except Exception as exc:
                log.warning("async_batch_request(): unexpected error %s on URL: %s", exc, url)
                return None

    tasks = [asyncio.ensure_future(_fetch_one(u)) for u in urls]
    results = await asyncio.gather(*tasks)
    return list(results)


__all__ = [
    "async_do_request",
    "async_get_html",
    "async_get_html_status",
    "async_batch_request",
]
