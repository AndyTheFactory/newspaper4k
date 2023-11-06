import lxml
import tldextract
from typing import List
from newspaper import urls
from newspaper.configuration import Configuration
from newspaper.extractors.defines import url_stopwords


class CategoryExtractor:
    def __init__(self, config: Configuration) -> None:
        self.config = config
        self.parser = config.get_parser()
        self.categories: List[str] = []

    def parse(self, source_url: str, doc: lxml.html.Element) -> List[str]:
        """Inputs source lxml root and source url, extracts domain and
        finds all of the top level urls, we are assuming that these are
        the category urls.
        cnn.com --> [cnn.com/latest, world.cnn.com, cnn.com/asia]
        """
        page_urls = self._get_urls(doc)
        valid_categories = []
        for p_url in page_urls:
            scheme = urls.get_scheme(p_url, allow_fragments=False)
            domain = urls.get_domain(p_url, allow_fragments=False)
            path = urls.get_path(p_url, allow_fragments=False)

            if not domain and not path:
                if self.config.verbose:
                    print(f"elim category url{p_url} for no domain and path")
                continue
            if path and path.startswith("#"):
                if self.config.verbose:
                    print(f"elim category url {p_url} path starts with #")
                continue
            if scheme and (scheme != "http" and scheme != "https"):
                if self.config.verbose:
                    print(
                        f"elim category url {p_url} for bad scheme, not http nor https"
                    )
                continue

            if domain:
                child_tld = tldextract.extract(p_url)
                domain_tld = tldextract.extract(source_url)
                child_subdomain_parts = child_tld.subdomain.split(".")
                subdomain_contains = False
                for part in child_subdomain_parts:
                    if part == domain_tld.domain:
                        if self.config.verbose:
                            print(
                                f"subdomain contains at {str(part)} and"
                                f" {str(domain_tld.domain)}"
                            )
                        subdomain_contains = True
                        break

                # Ex. microsoft.com is definitely not related to
                # espn.com, but espn.go.com is probably related to espn.com
                if not subdomain_contains and (child_tld.domain != domain_tld.domain):
                    if self.config.verbose:
                        print(f"elim category url {p_url} for domain mismatch")
                        continue
                elif child_tld.subdomain in ["m", "i"]:
                    if self.config.verbose:
                        print(f"elim category url {p_url}s for mobile subdomain")
                    continue
                else:
                    valid_categories.append(scheme + "://" + domain)
                    # TODO account for case where category is in form
                    # http://subdomain.domain.tld/category/ <-- still legal!
            else:
                # we want a path with just one subdir
                # cnn.com/world and cnn.com/world/ are both valid_categories
                path_chunks = [x for x in path.split("/") if len(x) > 0]
                if "index.html" in path_chunks:
                    path_chunks.remove("index.html")

                if len(path_chunks) == 1 and len(path_chunks[0]) < 14:
                    valid_categories.append(domain + path)
                else:
                    if self.config.verbose:
                        print(
                            f"elim category url {p_url} for >1 path chunks "
                            "or size path chunks"
                        )

        _valid_categories = []

        # TODO Stop spamming urlparse and tldextract calls...

        for p_url in valid_categories:
            path = urls.get_path(p_url)
            subdomain = tldextract.extract(p_url).subdomain
            conjunction = path + " " + subdomain
            bad = False
            for badword in url_stopwords:
                if badword.lower() in conjunction.lower():
                    if self.config.verbose:
                        print(
                            f"elim category url {p_url} for subdomain contain stopword!"
                        )
                    bad = True
                    break
            if not bad:
                _valid_categories.append(p_url)

        _valid_categories.append("/")  # add the root

        for i, p_url in enumerate(_valid_categories):
            if p_url.startswith("://"):
                p_url = "http" + p_url
                _valid_categories[i] = p_url

            elif p_url.startswith("//"):
                p_url = "http:" + p_url
                _valid_categories[i] = p_url

            if p_url.endswith("/"):
                p_url = p_url[:-1]
                _valid_categories[i] = p_url

        _valid_categories = list(set(_valid_categories))

        category_urls = [
            urls.prepare_url(p_url, source_url) for p_url in _valid_categories
        ]
        self.categories = [c for c in category_urls if c is not None]
        return self.categories

    def _get_urls(self, doc):
        """Return a list of urls or a list of (url, title_text) tuples
        if specified.
        """
        if doc is None:
            return []

        return [
            a.get("href")
            for a in self.parser.getElementsByTag(doc, tag="a")
            if a.get("href")
        ]
