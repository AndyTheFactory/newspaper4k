from copy import copy
import re
from typing import List, Optional
import lxml
from newspaper.configuration import Configuration
import newspaper.extractors.defines as defines
from newspaper.images import fetch_image
from newspaper.urls import urljoin_if_valid


class ImageExtractor(object):
    def __init__(self, config: Configuration) -> None:
        self.config = config
        self.parser = self.config.get_parser()
        self.top_image: Optional[str] = None
        self.meta_image: Optional[str] = None
        self.images: List[str] = []
        self.favicon: Optional[str] = None

    def parse(
        self, doc: lxml.html.Element, top_node: lxml.html.Element, article_url: str
    ) -> None:
        """_summary_

        Args:
            doc (lxml.html.Element): _description_
        """
        self.favicon = self._get_favicon(doc)

        self.meta_image = self._get_meta_image(doc)
        self.meta_image = urljoin_if_valid(article_url, self.meta_image)
        self.images = [urljoin_if_valid(article_url, u) for u in self._get_images(doc)]
        self.top_image = self._get_top_image(doc, top_node, article_url)

    def _get_favicon(self, doc: lxml.html.Element) -> str:
        """Extract the favicon from a website http://en.wikipedia.org/wiki/Favicon
        <link rel="shortcut icon" type="image/png" href="favicon.png" />
        <link rel="icon" type="image/png" href="favicon.png" />
        """
        kwargs = {"tag": "link", "attr": "rel", "value": "icon"}
        meta = self.parser.getElementsByTag(doc, **kwargs)
        if meta:
            favicon = self.parser.getAttribute(meta[0], "href")
            return favicon
        return ""

    def _get_meta_field(self, doc: lxml.html.Element, field: str) -> str:
        """Extract a given meta field from document."""
        metafield = self.parser.css_select(doc, field)
        if metafield:
            return metafield[0].get("content", "").strip()
        return ""

    def _get_meta_image(self, doc: lxml.html.Element) -> str:
        candidates = []
        for elem in defines.META_IMAGE_TAGS:
            if elem["tag"] == "meta":
                candidates.append(
                    (self._get_meta_field(doc, elem["field"]), elem["score"])
                )
            else:
                img = self.parser.getElementsByTag(
                    doc, attr=elem["attr"], value=elem["value"]
                )
                if img:
                    candidates.append((img[0].get("href"), elem["score"]))
        candidates = [c for c in candidates if c[0]]

        candidates.sort(key=lambda x: x[1], reverse=True)

        return candidates[0][0] if candidates else ""

    def _get_images(self, doc: lxml.html.Element) -> List[str]:
        images = [
            x.get("src")
            for x in self.parser.getElementsByTag(doc, tag="img")
            if x.get("src")
        ]

        return images

    def _get_top_image(
        self, doc: lxml.html.Element, top_node: lxml.html.Element, article_url: str
    ) -> str:
        if self.meta_image:
            if not self.config.fetch_images or self._check_image_size(
                self.meta_image, article_url
            ):
                return self.meta_image

        img_cand = []
        for img in self.parser.getElementsByTag(doc, tag="img"):
            if top_node:
                path = top_node.getpath(img)
                img_cand.append((img, path.count("/")))
            else:
                if self._check_image_size(img.get("src"), article_url):
                    return img.get("src")

        img_cand.sort(key=lambda x: x[1])

        for img in img_cand:
            if self._check_image_size(img[0].get("src"), article_url):
                return img[0].get("src")

        return ""

    def _check_image_size(self, url: str, referer: Optional[str]) -> bool:
        requests_params = copy(self.config.requests_params)
        requests_params["headers"]["Referer"] = referer
        img = fetch_image(
            url,
            requests_param=requests_params,
            max_retries=self.config.top_image_settings["max_retries"],
        )
        if not img:
            return False

        width, height = img.size

        if self.config.top_image_settings["min_width"] > width:
            return False
        if self.config.top_image_settings["min_height"] > height:
            return False
        if self.config.top_image_settings["min_area"] > width * height:
            return False

        if (
            re.search(r"(logo|sprite)", url, re.IGNORECASE)
            and self.config.top_image_settings["min_area"] > width * height / 10
        ):
            return False

        return True
