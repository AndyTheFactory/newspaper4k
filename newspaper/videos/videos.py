# -*- coding: utf-8 -*-
# Much of the logging code here was forked from https://github.com/codelucas/newspaper
# Copyright (c) Lucas Ou-Yang (codelucas)


class Video(object):
    """Video object"""

    def __init__(self):
        # type of embed
        # embed, object, iframe
        self.embed_type = None
        # video provider name
        self.provider = None
        # width
        self.width = None
        # height
        self.height = None
        # embed code
        self.embed_code = None
        # src
        self.src = None
