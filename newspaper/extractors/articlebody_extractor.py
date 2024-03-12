import copy
from functools import partial
import re
from statistics import mean
from typing import Optional
import lxml
from newspaper.configuration import Configuration
import newspaper.extractors.defines as defines
import newspaper.parsers as parsers
from newspaper.text import StopWords

score_weights = {
    "bottom_negativescore_nodes": 0.25,
    "boost_score": 30,
    "parent_node": 1.0,
    "parent_parent_node": 0.4,
    "node_count_threshold": 15,
    "negative_score_threshold": 40,
    "negative_score_boost": 5.0,
    "boost_max_steps_from_node": 3,
    "boost_min_stopword_count": 5,
}

get_stop_words = partial(parsers.get_attribute, attr="stop_words", type_=int, default=0)
get_word_count = partial(parsers.get_attribute, attr="word_count", type_=int, default=0)


class ArticleBodyExtractor:
    def __init__(self, config: Configuration):
        self.config = config
        self.top_node = None
        self.top_node_complemented = None
        self.stopwords: Optional[StopWords] = None

    def parse(self, doc: lxml.html.Element):
        """_summary_

        Args:
            doc (lxml.html.Element): _description_
        """
        self.stopwords = StopWords(self.config.language)
        self.top_node = self.calculate_best_node(doc)
        self.top_node_complemented = self.complement_with_siblings(self.top_node)

    def calculate_best_node(self, doc):
        top_node = None
        self.boost_highly_likely_nodes(doc)

        parent_nodes = []
        nodes_with_text = self.compute_features(doc)

        # process the tree from bottom up. farthest nodes first
        nodes_with_text.sort(
            key=lambda node: parsers.get_attribute(
                node, "node_level", type_=int, default=0
            ),
            reverse=True,
        )

        parent_nodes = self.compute_gravity_scores(nodes_with_text)

        if parent_nodes:
            parent_nodes.sort(key=parsers.get_node_gravity_score, reverse=True)
            top_node = parent_nodes[0]

        return top_node

    def compute_gravity_scores(self, nodes_with_text):
        """Computes the gravity score for each node in the list.
        And propagate the score to its parents and grandparents.

        Args:
            nodes_with_text (list): list of candidate nodes that have meaningful text

        Returns:
            list: list of nodes with gravity score
        """
        parent_nodes = []

        boost_discount = 1

        nodes_count = len(nodes_with_text)
        negative_scoring = 0

        bottom_negativescore_nodes = (
            nodes_count * score_weights["bottom_negativescore_nodes"]
        )

        for i, node in enumerate(nodes_with_text):
            boost_score = 0
            # boost score decays with distance from the top node
            if self.is_boostable(node):
                boost_score = score_weights["boost_score"] / boost_discount
                boost_discount += 1

            # nodes_number
            if nodes_count > score_weights["node_count_threshold"]:
                # higher number of possible top nodes
                dist_from_end = float(nodes_count - i)
                if dist_from_end <= bottom_negativescore_nodes:
                    booster = bottom_negativescore_nodes - dist_from_end
                    boost_score = -(booster**2)
                    negscore = abs(boost_score) + negative_scoring
                    if negscore > score_weights["negative_score_threshold"]:
                        boost_score = score_weights["negative_score_boost"]

            stop_word_count = get_stop_words(node)

            upscore = stop_word_count + boost_score

            parent_node = node.getparent()

            self.update_score(parent_node, upscore)
            self.update_node_count(parent_node, 1)

            parent_nodes.append(parent_node)

            # Parent of parent node
            parent_parent_node = (
                parent_node.getparent() if parent_node is not None else None
            )

            self.update_node_count(parent_parent_node, 1)
            self.update_score(
                parent_parent_node, upscore * score_weights["parent_parent_node"]
            )

            parent_nodes.append(parent_parent_node)

        parent_nodes = [x for x in set(parent_nodes) if x is not None]

        return parent_nodes

    def compute_features(self, doc):
        candidates = []
        nodes_to_check = self.nodes_to_check(doc)
        nodes_to_check.sort(key=parsers.get_level, reverse=True)

        for node in nodes_to_check:
            # exclude nodes that are in this list

            text_content = parsers.get_text(node)
            if not text_content:
                continue

            word_stats = self.stopwords.get_stopword_count(text_content)
            high_link_density = parsers.is_highlink_density(node, self.config.language)

            children_word_stats = [
                (get_stop_words(child), get_word_count(child))
                for child in node.xpath(".//*[@stop_words>0]")
            ]
            children_word_stats = (
                sum([x[0] for x in children_word_stats]),
                sum([x[1] for x in children_word_stats]),
            )
            parsers.set_attribute(
                node, "stop_words", word_stats.stop_word_count - children_word_stats[0]
            )
            parsers.set_attribute(
                node, "word_count", word_stats.word_count - children_word_stats[1]
            )
            parsers.set_attribute(
                node, "is_highlink_density", 1 if high_link_density else 0
            )
            parsers.set_attribute(node, "node_level", parsers.get_level(node))

            if word_stats.stop_word_count > 2 and not high_link_density:
                candidates.append(node)

        return candidates

    def nodes_to_check(self, doc):
        """Returns a list of nodes we want to search
        on like paragraphs and tables
        """
        nodes_to_check = []
        for tag in ["p", "pre", "td", "article", "div"]:
            if tag == "div":
                items = []
                for attr in [
                    "articlebody",
                    "article",
                    "story",
                ]:
                    items += parsers.get_tags(
                        doc,
                        tag=tag,
                        attribs={"id": attr},
                        attribs_match="word",
                        ignore_dashes=True,
                    )
                    items += parsers.get_tags(
                        doc,
                        tag=tag,
                        attribs={"class": attr},
                        attribs_match="word",
                        ignore_dashes=True,
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
        max_stepsaway_from_node = score_weights["boost_max_steps_from_node"]

        nodes = self.walk_siblings(node)
        for current_node in nodes[:max_stepsaway_from_node]:
            if current_node.tag != node.tag:
                continue
            stop_word_count = parsers.get_attribute(
                current_node, "stop_words", type_=int, default=0
            )
            if stop_word_count > score_weights["boost_min_stopword_count"]:
                return True
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
        if node is None:
            return
        new_score = parsers.get_node_gravity_score(node) + add_to_score
        parsers.set_attribute(node, "gravityScore", str(new_score))

    def update_node_count(self, node, add_to_count):
        """Stores how many decent nodes are under a parent node"""
        if node is None:
            return
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

        if (
            node.tag == "p"
            and node.text
            and not parsers.is_highlink_density(node, self.config.language)
        ):
            element = copy.deepcopy(node)
            element.tail = ""
            return [element]

        paragraphs = parsers.get_tags(node, tag="p")
        result = []
        if not paragraphs:
            return result

        for paragraph in paragraphs:
            stop_word_count = parsers.get_attribute(
                paragraph, "stop_words", type_=int, default=0
            )
            if stop_word_count <= 0:
                continue
            if parsers.is_highlink_density(paragraph, self.config.language):
                continue

            if stop_word_count > baseline_score * score_weight:
                text = parsers.get_text(paragraph)
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

            if score > base_score * 0.3 and not parsers.is_highlink_density(
                n, self.config.language
            ):
                new_node.append(copy.deepcopy(n))
                continue

            # content_items = self.get_plausible_content(n, base_score)
            # new_node.extend(content_items)

        return new_node
