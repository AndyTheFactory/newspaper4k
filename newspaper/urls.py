# -*- coding: utf-8 -*-
# Much of the code here was forked from https://github.com/codelucas/newspaper
# Copyright (c) Lucas Ou-Yang (codelucas)

"""
Functions for analyzing and parsing news article URLS. This module
contains the logic for accepting or rejecting a link as a valid news
article in Source.build() method.
"""

import logging
import re

from typing import Optional
from urllib.parse import parse_qs, urljoin, urlparse

from tldextract import tldextract

log = logging.getLogger(__name__)


_STRICT_DATE_REGEX_PREFIX = r"(?<=\W)"
DATE_REGEX = (
    r"([\./\-_\s]?(19|20)\d{2})[\./\-_\s]?"
    r"(([0-3]?[0-9][\./\-_\s])|(\w{3,5}[\./\-_\s]))"
    r"([0-3]?[0-9]([\./\-\+\?]|$))"
)
STRICT_DATE_REGEX = _STRICT_DATE_REGEX_PREFIX + DATE_REGEX

ALLOWED_TYPES = [
    "html",
    "htm",
    "md",
    "rst",
    "aspx",
    "jsp",
    "rhtml",
    "cgi",
    "xhtml",
    "jhtml",
    "asp",
    "shtml",
]

GOOD_PATHS = [
    "story",
    "article",
    "feature",
    "featured",
    "slides",
    "slideshow",
    "gallery",
    "news",
    "video",
    "media",
    "v",
    "radio",
    "press",
]

BAD_CHUNKS = [
    "careers",
    "contact",
    "about",
    "faq",
    "terms",
    "privacy",
    "advert",
    "preferences",
    "feedback",
    "info",
    "browse",
    "howto",
    "account",
    "subscribe",
    "donate",
    "shop",
    "admin",
    "auth_user",
    "emploi",
    "annonces",
    "blog",
    "courrierdeslecteurs",
    "page_newsletters",
    "adserver",
    "clicannonces",
    "services",
    "contribution",
    "boutique",
    "espaceclient",
]

BAD_DOMAINS = [
    "amazon",
    "doubleclick",
    "twitter",
    "facebook",
    "google",
    "youtube",
    "instagram",
    "pinterest",
]


def redirect_back(url: str, source_domain: str) -> str:
    """
    Some sites like Pinterest have api's that cause news
    args to direct to their site with the real news url as a
    GET param. This method catches that and returns our param.
    Args:
        url (str): the url to check for a redirect
        source_domain (str): the domain of the source url
    Returns:
        str: the redirected url if it exists, otherwise the original url
    """
    parse_data = urlparse(url)
    domain = parse_data.netloc
    query = parse_data.query

    # If our url is even from a remotely similar domain or
    # sub domain, we don't need to redirect.
    if source_domain in domain or domain in source_domain:
        return url

    query_item = parse_qs(query)
    if query_item.get("url"):
        # log.debug('caught redirect %s into %s' % (url, query_item['url'][0]))
        return query_item["url"][0]

    return url


def prepare_url(url: str, source_url: Optional[str] = None) -> str:
    """
    Operations that cleans an url, removes arguments,
    redirects, and merges relative urls with absolute ones.
    Args:
        url (str): the url to prepare
        source_url (Optional[str]): the source url
    Returns:
        str: the prepared url
    """
    try:
        if source_url is not None:
            source_domain = urlparse(source_url).netloc
            proper_url = urljoin(source_url, url)
            proper_url = redirect_back(proper_url, source_domain)
        else:
            proper_url = url
    except ValueError as e:
        log.error("url %s failed on err %s", url, str(e))
        proper_url = ""

    return proper_url


def valid_url(url: str, test: bool = False) -> bool:
    r"""
    Is this URL a valid news-article url?

    Perform a regex check on an absolute url.

    First, perform a few basic checks like making sure the format of the url
    is right, (scheme, domain, tld).

    Second, make sure that the url isn't some static resource, check the
    file type.

    Then, search of a YYYY/MM/DD pattern in the url. News sites
    love to use this pattern, this is a very safe bet.

    Separators can be [\.-/_]. Years can be 2 or 4 digits, must
    have proper digits 1900-2099. Months and days can be
    ambiguous 2 digit numbers, one is even optional, some sites are
    liberal with their formatting also matches snippets of GET
    queries with keywords inside them. ex: asdf.php?topic_id=blahlbah
    We permit alphanumeric, _ and -.

    Our next check makes sure that a keyword is within one of the
    separators in a url (subdomain or early path separator).
    cnn.com/story/blah-blah-blah would pass due to "story".

    We filter out articles in this stage by aggressively checking to
    see if any resemblance of the source& domain's name or tld is
    present within the article title. If it is, that's bad. It must
    be a company link, like 'cnn is hiring new interns'.

    We also filter out articles with a subdomain or first degree path
    on a registered bad keyword.
    Args:
        url (str): the url to check
        test (bool): whether to preprocess the url
    Returns:
        bool: True if the url is a valid article link, False otherwise
    """
    # If we are testing this method in the testing suite, we actually
    # need to preprocess the url like we do in the article's constructor!
    if test:
        url = prepare_url(url)

    # 11 chars is shortest valid url length, eg: http://x.co
    if url is None or len(url) < 11:
        log.debug("url %s rejected due to short length < 11", url)
        return False

    r1 = "mailto:" in url  # TODO not sure if these rules are redundant
    r2 = ("http://" not in url) and ("https://" not in url)

    if r1 or r2:
        log.debug("url %s rejected due to mailto in link or no http(s) schema", url)
        return False

    path = urlparse(url).path

    # input url is not in valid form (scheme, netloc, tld)
    if not path.startswith("/"):
        return False

    # the '/' which may exist at the end of the url provides us no information
    if path.endswith("/"):
        path = path[:-1]

    # '/story/cnn/blahblah/index.html' --> ['story', 'cnn', 'blahblah', 'index.html']
    path_chunks = [x for x in path.split("/") if len(x) > 0]

    # siphon out the file type. eg: .html, .htm, .md
    if len(path_chunks) > 0:
        file_type = url_to_filetype(url)

        # if the file type is a media type, reject instantly
        if file_type and file_type not in ALLOWED_TYPES:
            log.debug("url %s rejected due to bad filetype (%s)", url, file_type)
            return False

        last_chunk = path_chunks[-1].split(".")
        # the file type is not of use to use anymore, remove from url
        if len(last_chunk) > 1:
            path_chunks[-1] = last_chunk[-2]

    # Index gives us no information
    if "index" in path_chunks:
        path_chunks.remove("index")

    # extract the tld (top level domain)
    tld_dat = tldextract.extract(url)
    subd = tld_dat.subdomain
    tld = tld_dat.domain.lower()

    url_slug = path_chunks[-1] if path_chunks else ""

    if tld in BAD_DOMAINS:
        log.debug("url %s rejected due to bad domain (%s)", url, tld)
        return False

    if len(path_chunks) == 0:
        dash_count, underscore_count = 0, 0
    else:
        dash_count = url_slug.count("-")
        underscore_count = url_slug.count("_")

    # If the url has a news slug title
    if url_slug and (dash_count > 4 or underscore_count > 4):
        if dash_count >= underscore_count:
            if tld not in [x.lower() for x in url_slug.split("-")]:
                log.debug("url %s accepted due to title slug (%s)", url, url_slug)
                return True

        if underscore_count > dash_count:
            if tld not in [x.lower() for x in url_slug.split("_")]:
                log.debug("url %s accepted due to title slug (%s)", url, url_slug)
                return True

    # There must be at least 2 subpaths
    if len(path_chunks) <= 1:
        log.debug(
            "url %s rejected due to less than two path_chunks (%s)", url, path_chunks
        )
        return False

    # Check for subdomain & path red flags
    # Eg: http://cnn.com/careers.html or careers.cnn.com --> BAD
    for b in BAD_CHUNKS:
        if b in path_chunks or b == subd:
            log.debug("url %s rejected due to bad chunk (%s)", url, b)
            return False

    match_date = re.search(DATE_REGEX, url)

    # if we caught the verified date above, it's an article
    if match_date is not None:
        log.debug("url %s accepted for date in path", url)
        return True

    if 2 <= len(path_chunks) <= 3 and re.search(r"\d{3,}$", path_chunks[-1]):
        log.debug(
            "url %s accepted for last path chunk being numeric (hopefully an"
            " article-id) ",
            url,
        )
        return True

    if len(path_chunks) == 3 and re.search(r"\d{3,}$", path_chunks[1]):
        log.debug(
            "url %s accepted for before-last path chunk being numeric (hopefully an"
            " article-id) ",
            url,
        )
        return True

    for good in GOOD_PATHS:
        if good.lower() in [p.lower() for p in path_chunks]:
            log.debug("url %s accepted for good path", url)
            return True
    log.debug("url %s rejected for default false", url)
    return False


def url_to_filetype(abs_url: str) -> Optional[str]:
    """
    Input a URL and output the filetype of the file
    specified by the url. Returns None for no filetype.
    'http://blahblah/images/car.jpg' -> 'jpg'
    'http://yahoo.com'               -> None
    Args:
        abs_url (str): the url to parse
    Returns:
        Optional[str]: the file type of the url

    """
    path = urlparse(abs_url).path
    # Eliminate the trailing '/', we are extracting the file
    if path.endswith("/"):
        path = path[:-1]
    path_chunks = [x for x in path.split("/") if len(x) > 0]
    last_chunk = path_chunks[-1].split(".")  # last chunk == file usually
    if len(last_chunk) < 2:
        return None
    file_type = last_chunk[-1]
    # Assume that file extension is maximum 5 characters long
    if len(file_type) <= 5 or file_type.lower() in ALLOWED_TYPES:
        return file_type.lower()
    return None


def get_domain(abs_url: str, **kwargs) -> Optional[str]:
    """returns a url's domain part

    Arguments:
        abs_url(str): the url to parse

    Returns:
        str: the domain part of the url
    """
    if abs_url is None:
        return None
    return urlparse(abs_url, **kwargs).netloc


def get_scheme(abs_url: str, **kwargs) -> Optional[str]:
    """returns the url scheme (http, https, ftp, etc)

    Arguments:
        abs_url(str): the url to parse

    Returns:
        str: the scheme part of the url
    """
    if abs_url is None:
        return None
    return urlparse(abs_url, **kwargs).scheme


def get_path(abs_url: str, **kwargs) -> Optional[str]:
    """returns the path part of a url (the part after the domain)

    Arguments:
        abs_url(str): the url to parse

    Returns:
        str: the path part of the url
    """
    if abs_url is None:
        return None
    return urlparse(abs_url, **kwargs).path


def is_abs_url(url: str) -> bool:
    """Returns True if the url is an absolute url, False otherwise

    Arguments:
        url(str): the url to check

    Returns:
        bool: True if the url is an absolute url, False otherwise
    """
    regex = re.compile(
        r"^(?:http|ftp)s?://"  # http:// or https://
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)"
        r"+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|"  # domain...
        r"localhost|"  # localhost...
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|"  # ...or ipv4
        r"\[?[A-F0-9]*:[A-F0-9:]+\]?)"  # ...or ipv6
        r"(?::\d+)?"  # optional port
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )

    c_regex = re.compile(regex)
    return c_regex.search(url) is not None


def urljoin_if_valid(base_url: str, url: str) -> str:
    """Join a base url and a possibly relative url, guard against
    invalid urls resulted from parsing.

    Args:
        base_url (str): the base url (namely the article url)
        url (str): a relative or absolute url

    Returns:
        str: joined url if valid, otherwise empty string
    """

    try:
        res = urljoin(base_url, url)
        return res
    except ValueError:
        return ""
