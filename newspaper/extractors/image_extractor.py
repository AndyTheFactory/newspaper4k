import logging
import urllib.parse
from copy import copy
import re
from typing import List, Optional
import lxml
from PIL import Image, ImageFile
import requests
from newspaper import urls
from newspaper.configuration import Configuration
import newspaper.extractors.defines as defines
from newspaper.urls import urljoin_if_valid

log = logging.getLogger(__name__)


class ImageExtractor:
    """Extractor class for images in articles. Getting top image,
    image list, favicon, etc."""

    def __init__(self, config: Configuration) -> None:
        self.config = config
        self.parser = self.config.get_parser()
        self.top_image: Optional[str] = None
        self.meta_image: Optional[str] = None
        self.images: List[str] = []
        self.favicon: Optional[str] = None
        self._chunksize = 1024

    def parse(
        self, doc: lxml.html.Element, top_node: lxml.html.Element, article_url: str
    ) -> None:
        """main method to extract images from a document

        Args:
            doc (lxml.html.Element): _description_
        """
        self.favicon = self._get_favicon(doc)

        self.meta_image = self._get_meta_image(doc)
        if self.meta_image:
            self.meta_image = urljoin_if_valid(article_url, self.meta_image)
        self.images = [
            urljoin_if_valid(article_url, u)
            for u in self._get_images(doc)
            if u and u.strip()
        ]
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
                    doc,
                    attr=elem["attr"],
                    value=elem["value"],
                    use_regex=("|" in elem["value"]),
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
        def node_distance(node1, node2):
            path1 = node1.getroottree().getpath(node1).split("/")
            path2 = node2.getroottree().getpath(node2).split("/")
            for i, (step1, step2) in enumerate(zip(path1, path2)):
                if step1 != step2:
                    return len(path1[i:]) + len(path2[i:])

            return abs(len(path1) - len(path2))

        if self.meta_image:
            if not self.config.fetch_images or self._check_image_size(
                self.meta_image, article_url
            ):
                return self.meta_image

        img_cand = []
        for img in self.parser.getElementsByTag(doc, tag="img"):
            if len(top_node):
                distance = node_distance(top_node, img)
                img_cand.append((img, distance))
            else:
                if self._check_image_size(img.get("src"), article_url):
                    return img.get("src")

        img_cand.sort(key=lambda x: x[1])

        for img in img_cand:
            if self._check_image_size(img[0].get("src"), article_url):
                return img[0].get("src")

        return ""

    def _check_image_size(self, url: str, referer: Optional[str]) -> bool:
        img = self._fetch_image(
            url,
            referer,
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

    def _fetch_image(self, url: str, referer: Optional[str]) -> Optional[Image.Image]:
        def clean_url(url):
            """Url quotes unicode data out of urls"""
            if not isinstance(url, str):
                return url

            url = url.encode("utf8")
            url = "".join(
                [
                    urllib.parse.quote(c) if ord(c) >= 127 else c
                    for c in url.decode("utf-8")
                ]
            )
            return url

        requests_params = copy(self.config.requests_params)
        requests_params["headers"]["Referer"] = referer
        max_retries = self.config.top_image_settings["max_retries"]

        cur_try = 0
        url = clean_url(url)
        if not url or not url.startswith(("http://", "https://")):
            return None

        response = None
        while True:
            try:
                response = requests.get(
                    url,
                    stream=True,
                    **requests_params,
                )

                content_type = response.headers.get("Content-Type")

                if not content_type or "image" not in content_type.lower():
                    return None

                p = ImageFile.Parser()
                new_data = response.raw.read(self._chunksize)
                while not p.image and new_data:
                    try:
                        p.feed(new_data)
                    except (IOError, ValueError) as e:
                        log.warning(
                            "error %s while fetching: %s refer: %s",
                            str(e),
                            url,
                            requests_params["headers"].get("Referer"),
                        )
                        return None
                    except Exception as e:
                        # For some favicon.ico images, the image is so small
                        # that our PIL feed() method fails a length test.
                        is_favicon = urls.url_to_filetype(url) == "ico"
                        if not is_favicon:
                            raise e
                        return None
                    new_data = response.raw.read(self._chunksize)
                return p.image
            except requests.exceptions.RequestException:
                cur_try += 1
                if cur_try >= max_retries:
                    log.warning(
                        "error while fetching: %s refer: %s",
                        url,
                        requests_params["headers"].get("Referer"),
                    )
                    return None
            finally:
                if response is not None:
                    response.raw.close()
                    if response.raw._connection:
                        response.raw._connection.close()
