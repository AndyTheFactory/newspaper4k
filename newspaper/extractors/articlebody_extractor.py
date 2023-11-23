import copy
import lxml
import newspaper.extractors.defines as defines


class ArticleBodyExtractor:
    def __init__(self, config):
        self.config = config
        self.top_node = None
        self.top_node_complemented = None
        self.parser = self.config.get_parser()
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
        starting_boost = float(1.0)
        cnt = 0
        i = 0
        parent_nodes = []
        nodes_with_text = []

        for node in nodes_to_check:
            text_node = self.parser.getText(node)
            word_stats = self.stopwords_class(
                language=self.language
            ).get_stopword_count(text_node)
            high_link_density = self.is_highlink_density(node)
            if word_stats.stop_word_count > 2 and not high_link_density:
                nodes_with_text.append(node)

        nodes_number = len(nodes_with_text)
        negative_scoring = 0
        bottom_negativescore_nodes = float(nodes_number) * 0.25

        for node in nodes_with_text:
            boost_score = float(0)
            # boost
            if self.is_boostable(node):
                if cnt >= 0:
                    boost_score = float((1.0 / starting_boost) * 50)
                    starting_boost += 1
            # nodes_number
            if nodes_number > 15:
                if (nodes_number - i) <= bottom_negativescore_nodes:
                    booster = float(bottom_negativescore_nodes - (nodes_number - i))
                    boost_score = float(-pow(booster, float(2)))
                    negscore = abs(boost_score) + negative_scoring
                    if negscore > 40:
                        boost_score = float(5)

            text_node = self.parser.getText(node)
            word_stats = self.stopwords_class(
                language=self.language
            ).get_stopword_count(text_node)
            upscore = int(word_stats.stop_word_count + boost_score)

            parent_node = self.parser.getParent(node)
            self.update_score(parent_node, upscore)
            self.update_node_count(parent_node, 1)

            if parent_node not in parent_nodes:
                parent_nodes.append(parent_node)

            # Parent of parent node
            parent_parent_node = self.parser.getParent(parent_node)
            if parent_parent_node is not None:
                self.update_node_count(parent_parent_node, 1)
                self.update_score(parent_parent_node, upscore / 2)
                if parent_parent_node not in parent_nodes:
                    parent_nodes.append(parent_parent_node)
            cnt += 1
            i += 1

        if parent_nodes:
            parent_nodes.sort(key=self.get_score, reverse=True)
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
                for attr in ["id", "class"]:
                    for id_ in ["article-body", "article", "story", "article-content"]:
                        items += self.parser.getElementsByTag(
                            doc, tag=tag, attr=attr, value=id_
                        )
            else:
                items = self.parser.getElementsByTag(doc, tag=tag)
            nodes_to_check += items
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
            current_node_tag = self.parser.getTag(current_node)
            if current_node_tag == para:
                if steps_away >= max_stepsaway_from_node:
                    return False
                paragraph_text = self.parser.getText(current_node)
                word_stats = self.stopwords_class(
                    language=self.language
                ).get_stopword_count(paragraph_text)
                if word_stats.stop_word_count > minimum_stopword_count:
                    return True
                steps_away += 1
        return False

    def is_highlink_density(self, e):
        """Checks the density of links within a node, if there is a high
        link to text ratio, then the text is less likely to be relevant
        """
        links = self.parser.getElementsByTag(e, tag="a")
        if not links:
            return False

        text = self.parser.getText(e)
        words = [word for word in text.split() if word.isalnum()]
        if not words:
            return True
        words_number = float(len(words))
        sb = []
        for link in links:
            sb.append(self.parser.getText(link))

        link_text = "".join(sb)
        link_words = link_text.split()
        num_link_words = float(len(link_words))
        num_links = float(len(links))
        link_divisor = float(num_link_words / words_number)
        score = float(link_divisor * num_links)
        if score >= 1.0:
            return True
        return False
        # return True if score > 1.0 else False

    def boost_highly_likely_nodes(self, doc: lxml.html.Element):
        """Set a bias score for all nodes under most likely
        article containers. This way we can find articles
        that have little text.

        Args:
            doc (lxml.html.Element): Document to be checked
        """
        candidates = []
        for tag in ["p", "pre", "td", "article", "div"]:
            candidates.extend(self.parser.getElementsByTag(doc, tag=tag))

        for e in candidates:
            if self.is_highly_likly(e):
                for child in e.iterdescendants():
                    self.update_score(child, 25)  # TODO: find an optimum value

    def is_highly_likly(self, node: lxml.html.Element) -> bool:
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
                if k == "tag":
                    continue
                if node.get(k) != v:
                    return False
            return True

        for tag in defines.ARTICLE_BODY_TAGS:
            if is_tag_match(node, tag):
                return True

        return False

    def update_score(self, node, add_to_score):
        """Adds a score to the gravityScore Attribute we put on divs
        we'll get the current score then add the score we're passing
        in to the current.
        """
        current_score = 0
        score_string = self.parser.getAttribute(node, "gravityScore")
        if score_string:
            current_score = float(score_string)

        new_score = current_score + add_to_score
        self.parser.setAttribute(node, "gravityScore", str(new_score))

    def update_node_count(self, node, add_to_count):
        """Stores how many decent nodes are under a parent node"""
        current_score = 0
        count_string = self.parser.getAttribute(node, "gravityNodes")
        if count_string:
            current_score = int(count_string)

        new_score = current_score + add_to_count
        self.parser.setAttribute(node, "gravityNodes", str(new_score))

    def add_siblings(self, top_node):
        res_node = copy.deepcopy(top_node)
        baseline_score_siblings_para = self.get_siblings_score(top_node)
        results = self.walk_siblings(top_node)
        for current_node in results:
            ps = self.get_siblings_content(current_node, baseline_score_siblings_para)
            for p in ps:
                res_node.insert(0, p)
        return res_node

    def get_siblings_content(self, current_sibling, baseline_score_siblings_para):
        """Adds any siblings that may have a decent score to this node"""
        if current_sibling.tag == "p" and len(self.parser.getText(current_sibling)) > 0:
            e0 = current_sibling
            if e0.tail:
                e0 = copy.deepcopy(e0)
                e0.tail = ""
            return [e0]
        else:
            potential_paragraphs = self.parser.getElementsByTag(
                current_sibling, tag="p"
            )
            if potential_paragraphs is None:
                return None
            else:
                ps = []
                for first_paragraph in potential_paragraphs:
                    text = self.parser.getText(first_paragraph)
                    if len(text) > 0:
                        word_stats = self.stopwords_class(
                            language=self.language
                        ).get_stopword_count(text)
                        paragraph_score = word_stats.stop_word_count
                        sibling_baseline_score = float(0.30)
                        high_link_density = self.is_highlink_density(first_paragraph)
                        score = float(
                            baseline_score_siblings_para * sibling_baseline_score
                        )
                        if score < paragraph_score and not high_link_density:
                            p = self.parser.createElement(tag="p", text=text, tail=None)
                            ps.append(p)
                return ps

    def get_siblings_score(self, top_node):
        """We could have long articles that have tons of paragraphs
        so if we tried to calculate the base score against
        the total text score of those paragraphs it would be unfair.
        So we need to normalize the score based on the average scoring
        of the paragraphs within the top node.
        For example if our total score of 10 paragraphs was 1000
        but each had an average value of 100 then 100 should be our base.
        """
        base = 100000
        paragraphs_number = 0
        paragraphs_score = 0
        nodes_to_check = self.parser.getElementsByTag(top_node, tag="p")

        for node in nodes_to_check:
            text_node = self.parser.getText(node)
            word_stats = self.stopwords_class(
                language=self.language
            ).get_stopword_count(text_node)
            high_link_density = self.is_highlink_density(node)
            if word_stats.stop_word_count > 2 and not high_link_density:
                paragraphs_number += 1
                paragraphs_score += word_stats.stop_word_count

        if paragraphs_number > 0:
            base = paragraphs_score / paragraphs_number

        return base

    def walk_siblings(self, node):
        return self.parser.previousSiblings(node)

    def get_node_gravity_score(self, node):
        gravity_score = self.parser.getAttribute(node, "gravityScore")
        if not gravity_score:
            return None
        return float(gravity_score)

    def get_score(self, node):
        """Returns the gravityScore as an integer from this node"""
        return self.get_node_gravity_score(node) or 0

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
        node_complemented = self.add_siblings(
            node
        )  # TODO: test if there is a problem with siblings AFTER the top node
        for e in self.parser.getChildren(node_complemented):
            e_tag = self.parser.getTag(e)
            if e_tag != "p":
                if self.is_highlink_density(e):
                    self.parser.remove(e)
        return node_complemented
