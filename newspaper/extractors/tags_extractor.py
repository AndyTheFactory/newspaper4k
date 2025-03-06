import lxml.html
from typing import List
from newspaper.configuration import Configuration
import newspaper.parsers as parsers

class TagsExtractor:
    """
    A custom extractor that attempts to find "tags" for the article.

    Looks for containers like:
      1) <div id="articleTag"> with links <a class="lnk"> ...,
      2) <div class="meta-tags"> with links <a rel="tag"> ...,
      3) <div class="tags-links"> (common pattern in some themes).

    Then extracts the text of each link and collects them as a list of tags.
    """

    def __init__(self, config: Configuration):
        self.config = config
        self.tags: List[str] = []

    def parse(self, doc: lxml.html.HtmlElement) -> List[str]:
        """
        Searches for tags in any container that matches:
          - <div id="articleTag">,
          - <div class="meta-tags">,
          - <div class="tags-links">.

        Inside those containers, it looks for <a> elements that have either
        class="lnk" or rel="tag". For each <a>, we strip its text
        and if non-empty, add to the result list.

        Returns:
            List[str]: A list of tag strings (words/labels).
        """
        # Combine possible container paths with an XPath "union"
        container_nodes = doc.xpath(
            '//div[@id="articleTag"]'
            ' | //div[contains(@class,"meta-tags")]'
            ' | //div[contains(@class,"tags-links")]'
        )
        if not container_nodes:
            self.tags = []
            return self.tags

        result = []
        for container in container_nodes:
            # We'll look for links that match (class="lnk") or (rel="tag") ...
            link_nodes = container.xpath('.//a[contains(@class,"lnk") or @rel="tag"]')

            # Alternatively, if you wanted *all* <a> tags in these containers:
            # link_nodes = container.xpath('.//a')

            for link_node in link_nodes:
                text = parsers.get_text(link_node).strip()
                if text:
                    result.append(text)

        self.tags = result
        return self.tags
