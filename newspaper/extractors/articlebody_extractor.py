import copy
import re
from statistics import mean
import lxml
import newspaper.extractors.defines as defines
import newspaper.parsers as parsers

score_weights = {
    "start_boosting_score": 1.0,
    "bottom_negativescore_nodes": 0.25,
    "boost_score": 50,
    "parent_node": 1.0,
    "parent_parent_node": 0.4,
    "node_count_threshold": 15,
    "negative_score_threshold": 40,
    "negative_score_boost": 5.0,
}


class ArticleBodyExtractor:
    def __init__(self, config):
        self.config = config
        self.top_node = None
        self.top_node_complemented = None
        self.stopwords_class = config.stopwords_class
        self.language = config.language

    def parse(self, doc: lxml.html.Element):
        """_summary_

        Args:
            doc (lxml.html.Element): _description_
        """
        self.top_node = self.calculate_best_node(doc)
        self.top_node_complemented = self.complement_with_siblings(self.top_node)

    def calculate_best_node(self, doc):
        top_node = None
        nodes_to_check = self.nodes_to_check(doc)
        self.boost_highly_likely_nodes(doc)
        starting_boost = score_weights["start_boosting_score"]

        parent_nodes = []
        nodes_with_text = []

        for node in nodes_to_check:
            text_node = parsers.get_text(node)
            if not text_node:
                continue
            word_stats = self.stopwords_class(
                language=self.language
            ).get_stopword_count(text_node)
            high_link_density = parsers.is_highlink_density(node)
            if word_stats.stop_word_count > 2 and not high_link_density:
                nodes_with_text.append(node)

        nodes_number = len(nodes_with_text)
        negative_scoring = 0
        bottom_negativescore_nodes = (
            float(nodes_number) * score_weights["bottom_negativescore_nodes"]
        )

        for i, node in enumerate(nodes_with_text):
            boost_score = float(0)
            # boost
            if self.is_boostable(node):
                if i >= 0:
                    boost_score = float(
                        (1.0 / starting_boost) * score_weights["boost_score"]
                    )
                    starting_boost += 1
            # nodes_number
            if nodes_number > score_weights["node_count_threshold"]:
                # higher number of possible top nodes
                if (nodes_number - i) <= bottom_negativescore_nodes:
                    booster = float(bottom_negativescore_nodes - (nodes_number - i))
                    boost_score = float(-pow(booster, float(2)))
                    negscore = abs(boost_score) + negative_scoring
                    if negscore > score_weights["negative_score_threshold"]:
                        boost_score = score_weights["negative_score_boost"]

            text_node = parsers.get_text(node)
            word_stats = self.stopwords_class(
                language=self.language
            ).get_stopword_count(text_node)
            upscore = int(word_stats.stop_word_count + boost_score)

            parent_node = node.getparent()
            self.update_score(parent_node, upscore)
            self.update_node_count(parent_node, 1)

            if parent_node not in parent_nodes:
                parent_nodes.append(parent_node)

            # Parent of parent node
            parent_parent_node = parent_node.getparent()
            if parent_parent_node is not None:
                self.update_node_count(parent_parent_node, 1)
                self.update_score(
                    parent_parent_node, upscore * score_weights["parent_parent_node"]
                )
                if parent_parent_node not in parent_nodes:
                    parent_nodes.append(parent_parent_node)

        if parent_nodes:
            parent_nodes.sort(key=parsers.get_node_gravity_score, reverse=True)
            top_node = parent_nodes[0]

        return top_node

    def nodes_to_check(self, doc):
        """Returns a list of nodes we want to search
        on like paragraphs and tables
        """
        nodes_to_check = []
        for tag in ["p", "pre", "td", "article", "div"]:
            if tag == "div":
                items = []
                for attr in [
                    "article-body",
                    "articlebody",
                    "article",
                    "story",
                    "article-content",
                ]:
                    items += parsers.get_tags(
                        doc, tag=tag, attribs={"id": attr}, attribs_match="word"
                    )
                    items += parsers.get_tags(
                        doc, tag=tag, attribs={"class": attr}, attribs_match="word"
                    )
                for class_ in ["paragraph"]:
                    items += parsers.get_tags_regex(
                        doc, tag=tag, attribs={"class": class_}
                    )
                if len(items) == 0 and len(nodes_to_check) < 5:
                    items = parsers.get_tags(doc, tag=tag)
                items = set(items)  # remove duplicates
            else:
                items = parsers.get_tags(doc, tag=tag)
            nodes_to_check += items

        # Do not miss some Article Bodies or Article Sections
        # for itemprop in ['articleBody', 'articlebody', 'articleText',
        #                       'articleSection']:
        #     items = [item  for item in parsers.get_tags(
        #         doc, attribs={"itemprop": itemprop}, attribs_match="word"
        #     ) if item not in nodes_to_check]
        #     nodes_to_check.extend(items)

        return nodes_to_check

    def is_boostable(self, node):
        """A lot of times the first paragraph might be the caption under an image
        so we'll want to make sure if we're going to boost a parent node that
        it should be connected to other paragraphs, at least for the first n
        paragraphs so we'll want to make sure that the next sibling is a
        paragraph and has at least some substantial weight to it.
        """
        para = "p"
        steps_away = 0
        minimum_stopword_count = 5
        max_stepsaway_from_node = 3

        nodes = self.walk_siblings(node)
        for current_node in nodes:
            # <p>
            current_node_tag = current_node.tag
            if current_node_tag == para:
                if steps_away >= max_stepsaway_from_node:
                    return False
                paragraph_text = parsers.get_text(current_node)
                word_stats = self.stopwords_class(
                    language=self.language
                ).get_stopword_count(paragraph_text)
                if word_stats.stop_word_count > minimum_stopword_count:
                    return True
                steps_away += 1
        return False

    def boost_highly_likely_nodes(self, doc: lxml.html.Element):
        """Set a bias score for all nodes under most likely
        article containers. This way we can find articles
        that have little text.

        Args:
            doc (lxml.html.Element): Document to be checked
        """
        candidates = []
        for tag in ["p", "pre", "td", "article", "div"]:
            candidates.extend(parsers.get_tags(doc, tag=tag))

        for e in candidates:
            boost = self.is_highly_likely(e)
            if boost > 0:
                self.update_score(e, boost * score_weights["parent_node"])
                # for child in e.iterdescendants():
                # TODO: find an optimum value
                #     self.update_score(child, boost // 10)

    def is_highly_likely(self, node: lxml.html.Element) -> int:
        """Checks if the node is a well known tag + attributes combination
        for article body containers. This way we can deliver even small
        article bodies with high link density
        see: https://finance.yahoo.com/m/
            0edc9aaa-e3ba-3178-be5a-f8c16fbffff2/warren-buffett-stocks-shaky.html

        Args:
            node (lxml.html.Element): Node to check

        Returns:
            bool: True if node could be an article body top node
        """

        def is_tag_match(node, tag_dict):
            if node.tag != tag_dict.get("tag", node.tag):
                return False
            for k, v in tag_dict.items():
                if k in ["tag", "score_boost"]:
                    continue
                if v.startswith("re:"):
                    v = v[3:]
                    if not re.search(v, node.get(k, ""), re.IGNORECASE):
                        return False
                elif node.get(k, "").lower() != v.lower():
                    return False
            return True

        scores = []
        for tag in defines.ARTICLE_BODY_TAGS:
            if is_tag_match(node, tag):
                scores.append(tag["score_boost"])
        if scores:
            return max(scores)

        return 0

    def update_score(self, node, add_to_score):
        """Adds a score to the gravityScore Attribute we put on divs
        we'll get the current score then add the score we're passing
        in to the current.
        """
        new_score = parsers.get_node_gravity_score(node) + add_to_score
        parsers.set_attribute(node, "gravityScore", str(new_score))

    def update_node_count(self, node, add_to_count):
        """Stores how many decent nodes are under a parent node"""
        new_count = float(node.get("gravityNodes", 0)) + add_to_count
        parsers.set_attribute(node, "gravityNodes", str(new_count))

    def add_siblings(self, top_node):
        res_node = copy.deepcopy(top_node)
        baseline_score = self.get_normalized_score(top_node)
        results = self.walk_siblings(top_node)
        for current_node in results:
            ps = self.get_plausible_content(current_node, baseline_score)
            for p in ps:
                res_node.insert(0, p)
        return res_node

    def get_plausible_content(self, node, baseline_score, score_weight=0.3):
        """Create list of (off-the-tree) paragraphs from a node (most likely a
        sibling of the top node) that are plausible to be part of the
        article body. We use the stop word count as a score of plausibility.
        We accept only paragraphs with a score higher than the baseline score
        weighted by the score_weight parameter.
        The baseline score is a normalized score of the top node.
        """
        if isinstance(
            node, (lxml.etree.CommentBase, lxml.etree.EntityBase, lxml.etree.PIBase)
        ):
            return []

        if node.tag == "p" and node.text and not parsers.is_highlink_density(node):
            element = copy.deepcopy(node)
            element.tail = ""
            return [element]

        paragraphs = parsers.get_tags(node, tag="p")
        result = []
        if not paragraphs:
            return result

        for paragraph in paragraphs:
            text = parsers.get_text(paragraph)
            if not text:
                continue
            if parsers.is_highlink_density(paragraph):
                continue

            word_stats = self.stopwords_class(
                language=self.language
            ).get_stopword_count(text)

            if word_stats.stop_word_count > baseline_score * score_weight:
                element = parsers.create_element(tag="p", text=text)
                result.append(element)

        return result

    def get_normalized_score(self, top_node):
        """We could have long articles that have tons of paragraphs
        so if we tried to calculate the base score against
        the total text score of those paragraphs it would be unfair.
        So we need to normalize the score based on the average scoring
        of the paragraphs within the top node.
        For example if our total score of 10 paragraphs was 1000
        but each had an average value of 100 then 100 should be our base.
        """

        nodes_to_check = parsers.get_tags(top_node, tag="p")

        scores = [parsers.get_node_gravity_score(node) for node in nodes_to_check]
        scores = [score for score in scores if score > 0]  # filter out 0 scores

        return mean(scores) if scores else float("inf")

    def walk_siblings(self, node):
        """returns preceding siblings in reverse order (nearest sibling is first)"""
        return [n for n in node.itersiblings(preceding=True)]

    def complement_with_siblings(self, node: lxml.html.Element) -> lxml.html.Element:
        """Adds surrounding relevant siblings to the top node.
        Attention, it generates off-the-tree node.

        Args:
            node (lxml.html.Element): Top node detected

        Returns:
            lxml.html.Element: off the tree node complemented with siblings
        """
        if node is None:
            return node
        # TODO: test if there is a problem with siblings AFTER the top node
        # node_complemented = self.add_siblings(node)

        node_complemented = self.add_same_level_candidates(node)

        # for e in node_complemented.getchildren():
        #     if e.tag != "p":
        #         if parsers.is_highlink_density(e):
        #             parsers.remove(e)
        return node_complemented

    def add_same_level_candidates(self, node):
        """Adds any siblings that may have a decent score to this node"""
        tree = node.getroottree()

        node_level = parsers.get_level(node)
        # base_score = self.get_normalized_score(node)
        base_score = parsers.get_node_gravity_score(node)

        candidates = parsers.get_nodes_at_level(tree.getroot(), node_level)

        assert node in candidates, "node not in candidates"

        # Create the new tree as a HTML document. Otherwise it will
        # be created as Element tree and cleaners won't work
        new_tree = parsers.fromstring("<html><body></body></html>")
        new_node = new_tree.find("body")

        for n in candidates:
            if n == node:
                new_node.append(copy.deepcopy(node))
                continue

            # avoid adding nodes that do not resemble the top node
            if n.tag != node.tag:
                continue

            score = parsers.get_node_gravity_score(n)

            if score > base_score * 0.3 and not parsers.is_highlink_density(n):
                new_node.append(copy.deepcopy(n))
                continue

            # content_items = self.get_plausible_content(n, base_score)
            # new_node.extend(content_items)

        return new_node
