"""
This module provides extractors for newspaper content.

The `ContentExtractor` class is the orchestrator for all extractor classes.
There are several classes specialized on certain parts of a news article.
"""

from newspaper.extractors.content_extractor import ContentExtractor

__all__ = ["ContentExtractor"]
