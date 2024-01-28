# -*- coding: utf-8 -*-
# Much of the code here was forked from https://github.com/codelucas/newspaper
# Copyright (c) Lucas Ou-Yang (codelucas)

from typing import List
import lxml
from newspaper.configuration import Configuration
import newspaper.parsers as parsers
from newspaper.utils import Video

VIDEOS_TAGS = ["iframe", "embed", "object", "video"]
VIDEO_PROVIDERS = ["youtube", "youtu.be", "vimeo", "dailymotion", "kewego", "twitch"]


class VideoExtractor:
    """Extracts a list of video from Article top node"""

    def __init__(self, config: Configuration):
        self.config = config
        self.movies: List[Video] = []

    def parse(self, doc: lxml.html.Element, top_node: lxml.html.Element) -> List[Video]:
        """Extracts video information from the top node

        Args:
            doc (lxml.html.Element): document root
            top_node (lxml.html.Element): Top article node

        Returns:
            List[Video]: List of video objects
        """
        self.movies = []

        if top_node is not None:
            candidates = parsers.get_elements_by_tagslist(top_node, VIDEOS_TAGS)

            for candidate in candidates:
                parser_func = getattr(self, f"parse_{candidate.tag.lower()}")
                if parser_func:
                    video = parser_func(candidate)
                    if video:
                        self.movies.append(video)
        if doc is not None:
            json_ld_scripts = parsers.get_ld_json_object(doc)

            for script_tag in json_ld_scripts:
                if "@graph" in script_tag:
                    script_tag_ = script_tag.get("@graph", [])
                elif isinstance(script_tag, list):
                    script_tag_ = script_tag
                else:
                    script_tag_ = [script_tag]
                for item in script_tag_:
                    if not isinstance(item, dict):
                        continue
                    if item.get("@type") == "VideoObject":
                        m = Video()
                        m.src = item.get("contentUrl")
                        m.embed_code = item.get("embedUrl")
                        m.provider = self._get_provider(m.src)

                        self.movies.append(m)

        return self.movies

    def parse_iframe(self, node: lxml.html.HtmlElement):
        """Parse function for the iframe tag

        Args:
            node (lxml.html.HtmlElement): Input node

        Returns:
            _type_: Video object or None
        """
        return self.parse_video(node)

    def parse_embed(self, node: lxml.html.HtmlElement):
        """Parse function for the embed tag

        Args:
            node (lxml.html.HtmlElement): Input node

        Returns:
            _type_: Video object or None
        """
        parent = node.getparent()
        if parent is not None:
            if parent.tag.lower() == "object":
                return self.parse_object(node)
        return self.parse_video(node)

    def parse_object(self, node: lxml.html.HtmlElement):
        """Parse function for the object tag

        Args:
            node (lxml.html.HtmlElement): Input node

        Returns:
            _type_: Video object or None
        """
        # test if object tag has en embed child
        # in this case we want to remove the embed from
        # the candidate list to avoid parsing it twice
        child_embed_tag = parsers.get_tags(node, "embed")
        if child_embed_tag:
            return None  # Will be parsed as embed

        # get the object source
        # if we don't have a src node don't continue
        src_node = parsers.get_tags(node, tag="param", attribs={"name": "movie"})

        if not src_node:
            return None

        src = parsers.get_attribute(src_node[0], "value", default="")

        # check provider
        provider = self._get_provider(src)
        if not provider:
            return None

        video = self.parse_video(node)
        video.provider = provider
        video.src = src
        return video

    def parse_video(self, node: lxml.html.HtmlElement) -> Video:
        """Parse function for the video tag

        Args:
            node (lxml.html.HtmlElement): Input node

        Returns:
            Video: Video object or None
        """
        video = Video()
        video.embed_code = self._get_embed_code(node)
        video.embed_type = node.tag.lower()
        try:
            video.width = int(node.attrib["width"])
        except (KeyError, ValueError):
            video.width = None
        try:
            video.height = int(node.attrib["height"])
        except (KeyError, ValueError):
            video.height = None
        if node.attrib.get("data-litespeed-src"):
            video.src = node.attrib.get("data-litespeed-src")
        else:
            video.src = node.attrib.get("src")
        video.provider = self._get_provider(video.src)
        return video

    def _get_embed_code(self, node: lxml.html.HtmlElement):
        return "".join(
            [line.strip() for line in parsers.node_to_string(node).splitlines()]
        )

    def _get_provider(self, src: lxml.html.HtmlElement):
        if src:
            for provider in VIDEO_PROVIDERS:
                if provider in src:
                    return provider
        return None
