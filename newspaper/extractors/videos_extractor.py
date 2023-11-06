# -*- coding: utf-8 -*-
# Much of the code here was forked from https://github.com/codelucas/newspaper
# Copyright (c) Lucas Ou-Yang (codelucas)

from typing import List
import lxml
from newspaper.configuration import Configuration
from newspaper.utils.classes import Video

VIDEOS_TAGS = ["iframe", "embed", "object", "video"]
VIDEO_PROVIDERS = ["youtube", "vimeo", "dailymotion", "kewego"]


class VideoExtractor:
    """Extracts a list of video from Article top node"""

    def __init__(self, config: Configuration):
        self.config = config
        self.parser = self.config.get_parser()
        self.movies: List[Video] = []

    def parse(self, doc: lxml.html.HtmlElement) -> List[Video]:
        """Extracts video information from the top node

        Args:
            doc (lxml.html.HtmlElement): document or top_node

        Returns:
            List[Video]: List of video objects
        """
        candidates = self.parser.getElementsByTags(doc, VIDEOS_TAGS)

        self.movies = []
        for candidate in candidates:
            parser_func = getattr(self, f"parse_{candidate.tag.lower()}")
            if parser_func:
                video = parser_func(candidate)
                if video:
                    self.movies.append(video)
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
        parent = self.parser.getParent(node)
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
        child_embed_tag = self.parser.getElementsByTag(node, "embed")
        if child_embed_tag:
            return None  # Will be parsed as embed

        # get the object source
        # if we don't have a src node don't continue
        src_node = self.parser.getElementsByTag(
            node, tag="param", attr="name", value="movie"
        )
        if not src_node:
            return None

        src = self.parser.getAttribute(src_node[0], "value")

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
        video.src = node.attrib.get("src")
        video.provider = self._get_provider(video.src)
        return video

    def _get_embed_code(self, node: lxml.html.HtmlElement):
        return "".join(
            [line.strip() for line in self.parser.nodeToString(node).splitlines()]
        )

    def _get_provider(self, src: lxml.html.HtmlElement):
        if src:
            for provider in VIDEO_PROVIDERS:
                if provider in src:
                    return provider
        return None
