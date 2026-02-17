import re
from collections.abc import Iterator
from typing import Any

import lxml
import tldextract

import newspaper.parsers as parsers
from newspaper import urls
from newspaper.configuration import Configuration
from newspaper.extractors.defines import category_url_prefixes, url_stopwords


class CategoryExtractor:
    def __init__(self, config: Configuration) -> None:
        self.config = config
        self.categories: list[str] = []

    def parse(self, source_url: str, doc: lxml.html.Element) -> list[str]:
        """Inputs source lxml root and source url, extracts domain and
        finds all of the top level urls, we are assuming that these are
        the category urls.
        cnn.com --> [cnn.com/latest, world.cnn.com, cnn.com/asia]
        """
        domain_tld = tldextract.extract(source_url)

        links_in_doc = {a.get("href") for a in parsers.get_tags(doc, tag="a")}

        category_candidates: list[Any] = []

        for p_url in links_in_doc:
            ok, parsed_url = self.is_valid_link(p_url, domain_tld.domain, source_url)
            if ok:
                if not parsed_url["domain"]:
                    parsed_url["domain"] = urls.get_domain(source_url, allow_fragments=False)
                    parsed_url["scheme"] = urls.get_scheme(source_url, allow_fragments=False)
                    parsed_url["tld"] = domain_tld

                category_candidates.append(parsed_url)

        _valid_categories = []

        stop_words = set(url_stopwords)
        for p_url in category_candidates:
            path = p_url["path"].lower().split("/")
            subdomain = p_url["tld"].subdomain.lower().split(".")

            conjunction = set(path + subdomain)
            if len(conjunction.intersection(stop_words)) == 0:
                p_url["scheme"] = p_url["scheme"] if p_url["scheme"] else "http"
                if p_url["path"].endswith("/"):
                    p_url["path"] = p_url["path"][:-1]
                _valid_categories.append(p_url["scheme"] + "://" + p_url["domain"] + p_url["path"])

        if len(_valid_categories) == 0:
            other_links_in_doc = set(self._get_other_links(doc, source_domain=domain_tld.domain))
            for p_url in other_links_in_doc:
                ok, parsed_url = self.is_valid_link(p_url, domain_tld.domain, source_url)
                if ok:
                    path = parsed_url["path"].lower().split("/")
                    subdomain = parsed_url["tld"].subdomain.lower().split(".")
                    conjunction = set(path + subdomain)

                    if len(conjunction.intersection(stop_words)) == 0:
                        _valid_categories.append(
                            parsed_url["scheme"] + "://" + parsed_url["domain"] + parsed_url["path"]
                        )

        _valid_categories.append("/")  # add the root

        _valid_categories = list(set(_valid_categories))

        category_urls = [urls.prepare_url(p_url, source_url) for p_url in _valid_categories if p_url is not None]

        self.categories = sorted(category_urls)
        return self.categories

    def _get_other_links(self, doc: lxml.html.Element, source_domain: str | None = None) -> Iterator[str]:
        """Return all links that are not as <a> tags. These can be
        links in javascript tags, json objects, etc.
        """
        html = parsers.node_to_string(doc)
        candidates = re.findall(r'"(https?:\\?/\\?/[^"]*)"', html)

        candidates = [c.replace(r"\/", "/") for c in candidates]
        candidates = [c.replace(r"/\\", "/") for c in candidates]

        def _filter(candidate):
            if source_domain is not None:
                candidate_tld = tldextract.extract(candidate)
                if candidate_tld.domain != source_domain:
                    return False
            if re.search(r"\.(css|js|json|xml|rss|jpg|jpeg|png|)$", candidate, re.I):
                return False

            path = urls.get_path(candidate, allow_fragments=False)
            path_chunks = [x for x in path.split("/") if len(x) > 0]
            if "index.html" in path_chunks:
                path_chunks.remove("index.html")

            if len(path_chunks) > 2 or len(path_chunks) == 0:
                return False

            return True

        return filter(_filter, candidates)

    def is_valid_link(self, url: str, source_domain: str, source_url: str) -> tuple[bool, dict[str, Any]]:
        """Is the url a possible category?
        Args
            url - the url to check
            source_domain - the source url's domain for www.espn.com this would be espn
        """
        parsed_url: dict[str, Any] = {
            "scheme": urls.get_scheme(url, allow_fragments=False),
            "domain": urls.get_domain(url, allow_fragments=False),
            "path": urls.get_path(url, allow_fragments=False),
            "tld": None,
        }

        # In the case where we can't parse a scheme or domain, we must be doing a
        # relative link relative to the source url
        if source_url and (not parsed_url["scheme"] and not parsed_url["domain"]):
            parsed_url["scheme"] = urls.get_scheme(source_url)
            parsed_url["domain"] = urls.get_domain(source_url)
            url = urls.urljoin(source_url, parsed_url["path"])

        # No domain or path
        if not parsed_url["domain"] or not parsed_url["path"]:
            return False, parsed_url
        # remove any url that starts with #
        if parsed_url["path"] and parsed_url["path"].startswith("#"):
            return False, parsed_url
        # remove urls that are not http or https (ex. mailto:)
        if parsed_url["scheme"] and (parsed_url["scheme"] != "http" and parsed_url["scheme"] != "https"):
            return False, parsed_url

        path_chunks = [x for x in parsed_url["path"].split("/") if len(x) > 0]
        if "index.html" in path_chunks:
            path_chunks.remove("index.html")

        if parsed_url["domain"]:
            child_tld = tldextract.extract(url)
            parsed_url["tld"] = child_tld
            child_subdomain_parts = child_tld.subdomain.split(".")

            # Ex. microsoft.com is definitely not related to
            # espn.com, but espn.go.com is probably related to espn.com
            if child_tld.domain != source_domain and source_domain not in child_subdomain_parts:
                return False, parsed_url

            if child_tld.subdomain in ["m", "i"]:
                return False, parsed_url

            subd = "" if child_tld.subdomain == "www" else child_tld.subdomain

            if len(subd) > 0 and len(path_chunks) == 0:
                return True, parsed_url  # Allow http://category.domain.tld/

        # we want a path with just one subdir
        # cnn.com/world and cnn.com/world/ are both valid_categories
        # cnn.com/world/europe is not a valid_category
        # europe.cnn.com/economy is a valid_category
        if len(path_chunks) > 2 or len(path_chunks) == 0:
            return False, parsed_url

        if [x for x in path_chunks if x.startswith("_") or x.startswith("#")]:  # Ex. cnn.com/_static/
            return False, parsed_url

        if len(path_chunks) == 2 and path_chunks[0] in category_url_prefixes:
            return True, parsed_url

        return len(path_chunks) == 1 and 1 < len(path_chunks[0]) < 20, parsed_url
