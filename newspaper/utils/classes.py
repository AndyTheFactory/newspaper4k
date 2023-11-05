# -*- coding: utf-8 -*-
# Much of the code here was forked from https://github.com/codelucas/newspaper
# Copyright (c) Lucas Ou-Yang (codelucas)

from dataclasses import dataclass
from typing import Optional


@dataclass
class Video:
    """Video object"""

    embed_type: Optional[str] = None
    # Video provider name
    provider: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    # embedding html code
    embed_code: Optional[str] = None
    src: Optional[str] = None
