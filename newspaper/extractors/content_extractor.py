import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import lxml
from newspaper import urls
import newspaper.parsers as parsers
from newspaper.configuration import Configuration
from newspaper.extractors.articlebody_extractor import ArticleBodyExtractor
from newspaper.extractors.authors_extractor import AuthorsExtractor
from newspaper.extractors.categories_extractor import CategoryExtractor
from newspaper.extractors.image_extractor import ImageExtractor
from newspaper.extractors.metadata_extractor import MetadataExtractor
from newspaper.extractors.pubdate_extractor import PubdateExtractor
from newspaper.extractors.title_extractor import TitleExtractor
from newspaper.extractors.videos_extractor import VideoExtractor
from newspaper.utils import Video

log = logging.getLogger(__name__)


class ContentExtractor:
    """Extracts various content from an article page.

    This class provides methods to extract different components of an article,
    such as authors, publishing date, title, feed URLs, metadata, images, category URLs,
    and videos.

    Args:
        config (Configuration): The configuration object for the content extraction.

    Attributes:
        config (Configuration): The configuration object for the content extraction.
        title_extractor (TitleExtractor): The title extractor object.
        author_extractor (AuthorsExtractor): The authors extractor object.
        pubdate_extractor (PubdateExtractor): The publishing date extractor object.
        atricle_body_extractor (ArticleBodyExtractor): The article body
            extractor object.
        metadata_extractor (MetadataExtractor): The metadata extractor object.
        categories_extractor (CategoryExtractor): The category extractor object.
        image_extractor (ImageExtractor): The image extractor object.
        video_extractor (VideoExtractor): The video extractor object.
    """

    def __init__(self, config: Configuration):
        self.config = config
        self.title_extractor = TitleExtractor(config)
        self.author_extractor = AuthorsExtractor(config)
        self.pubdate_extractor = PubdateExtractor(config)
        self.atricle_body_extractor = ArticleBodyExtractor(config)
        self.metadata_extractor = MetadataExtractor(config)
        self.categories_extractor = CategoryExtractor(config)
        self.image_extractor = ImageExtractor(config)
        self.video_extractor = VideoExtractor(config)

    def get_authors(self, doc: lxml.html.Element) -> List[str]:
        """Fetch the authors of the article, return as a list
        Only works for english articles
        """
        return self.author_extractor.parse(doc)

    def get_publishing_date(
        self, url: str, doc: lxml.html.Element
    ) -> Optional[datetime]:
        """Return the article publishing date as datetime object. If no valid
        date could be found, return None. The parser tries to determine the
        date from the following sources (in this order): article url
        (e.g /2019/12/31/article.html), yoast schema and json ld schema, meta
        data from metatags.

        Args:
            url (str): The article url we parse
            doc (lxml.html.Element): The DOM for the whole article page

        Returns:
            Optional[datetime]: a datetime object or None
        """
        return self.pubdate_extractor.parse(url, doc)

    def get_title(self, doc):
        """Fetch the article title and analyze it

        Assumptions:
        - title tag is the most reliable (inherited from Goose)
        - h1, if properly detected, is the best (visible to users)
        - og:title and h1 can help improve the title extraction
        - python == is too strict, often we need to compare filtered
          versions, i.e. lowercase and ignoring special chars

        Explicit rules:
        1. title == h1, no need to split
        2. h1 similar to og:title, use h1
        3. title contains h1, title contains og:title, len(h1) > len(og:title), use h1
        4. title starts with og:title, use og:title
        5. use title, after splitting
        """
        return self.title_extractor.parse(doc)

    def get_feed_urls(self, source_url, categories):
        """Takes a source url and a list of category objects and returns
        a list of feed urls
        """
        total_feed_urls = []
        for category in categories:
            attribs = {"type": "application/rss+xml"}
            feed_elements = parsers.get_tags(category.doc, attribs=attribs)
            feed_urls = [e.get("href") for e in feed_elements if e.get("href")]
            total_feed_urls.extend(feed_urls)

        total_feed_urls = list(set(total_feed_urls))
        total_feed_urls = total_feed_urls[:50]
        total_feed_urls = [urls.prepare_url(f, source_url) for f in total_feed_urls]
        total_feed_urls = list(set(total_feed_urls))
        return total_feed_urls

    def get_metadata(self, article_url: str, doc: lxml.html.Element) -> Dict[str, Any]:
        """Parse the article's HTML for any known metadata attributes"""
        return self.metadata_extractor.parse(article_url, doc)

    def parse_images(
        self, article_url: str, doc: lxml.html.Element, top_node: lxml.html.Element
    ):
        """Parse images in an article"""
        self.image_extractor.parse(doc, top_node, article_url)

    def get_category_urls(self, source_url, doc):
        """Inputs source lxml root and source url, extracts domain and
        finds all of the top level urls, we are assuming that these are
        the category urls.
        cnn.com --> [cnn.com/latest, world.cnn.com, cnn.com/asia]
        """
        return self.categories_extractor.parse(source_url, doc)

    @property
    def top_node(self) -> lxml.html.Element:
        """Returns the top node of the article.
        calculate_best_node() must be called first

        Returns:
            lxml.html.Element: The top node containing the article text
        """
        return self.atricle_body_extractor.top_node

    @property
    def top_node_complemented(self) -> lxml.html.Element:
        """The cleaned version of the top node, without any divs, linkstuffing, etc

        Returns:
            lxml.html.Element: deepcopy version of the top node, cleaned
        """
        return self.atricle_body_extractor.top_node_complemented

    def calculate_best_node(
        self, doc: lxml.html.Element
    ) -> Optional[lxml.html.Element]:
        """Extracts the most probable top node for the article text
        based on a variety of heuristics

        Args:
            doc (lxml.html.Element): Root node of the document.
              The search starts from here.
              usually it's the html tag of the web page

        Returns:
            lxml.html.Element: the article top element
            (most probable container of the article text), or None
        """
        self.atricle_body_extractor.parse(doc)

        return self.atricle_body_extractor.top_node

    def get_videos(
        self, doc: lxml.html.Element, top_node: lxml.html.Element
    ) -> List[Video]:
        """Gets video links from article

        Args:
            doc (lxml.html.Element): Top document node. Needed for json-ld
            top_node (lxml.html.Element): Article top node.

        Returns:
            List[str]: list of video urls
        """
        return self.video_extractor.parse(doc, top_node)
