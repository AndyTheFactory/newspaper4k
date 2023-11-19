import pytest
import newspaper
from newspaper.cleaners import DocumentCleaner
from newspaper.outputformatters import OutputFormatter
from newspaper import parsers


@pytest.fixture
def get_cleaner():
    config = newspaper.Config()

    return DocumentCleaner(config=config)


@pytest.fixture
def get_formatter():
    config = newspaper.Config()

    return OutputFormatter(config=config)


@pytest.fixture
def html_fixture():
    html = """
        <html>
        <head>
            <meta name="author" content="John Doe">
            <meta property="og:title" content="This is a test">
            <meta itemprop="datePublished" content="2023-10-30">
        </head>
        <body>
        <p><span class="dropcap">T</span>his is a test</p>
        <p><span class="blag bla dropcap">T</span>his is a test</p>
        <div class="class1"><div class="class2">
            <span class="bla blag dropcap">T</span>his is a test</div></div>
        </body>
        </html>
        """
    return html


class TestCleaners:
    def test_remove_drop_caps(self, get_cleaner, get_formatter):
        for class_name in ["dropcap", "drop_cap"]:
            html = f"""
            <html>
            <body>
            <p><span class="{class_name}">T</span>his is a test</p>
            <p><span class="bla bla {class_name}">T</span>his is a test</p>
            <p><span class="bla bla {class_name} lorem">T</span>his is a test</p>
            <p><span class="{class_name} lorem ipsum">T</span>his is a test</p>
            </body>
            </html>
            """
            doc = parsers.fromstring(html)

            doc = get_cleaner.remove_drop_caps(doc)
            get_formatter.top_node = doc

            assert (
                get_formatter.convert_to_text()
                == "This is a test This is a test This is a test This is a test"
            )

    def test_clean_para_spans(self, get_cleaner, get_formatter, html_fixture):
        doc = parsers.fromstring(html_fixture)

        doc = get_cleaner.clean_para_spans(doc)
        get_formatter.top_node = doc

        assert (
            get_formatter.convert_to_text()
            == "This is a test This is a test T his is a test"
        )


class TestParser:
    def test_get_tag(self, html_fixture):
        doc = parsers.fromstring(html_fixture)

        assert len(parsers.get_tags(doc, "p")) == 2
        assert len(parsers.get_tags(doc, "div")) == 2
        assert len(parsers.get_tags(doc, "span")) == 3
        assert len(parsers.get_tags(doc, "span", {"class": "dropcap"})) == 1
        assert len(parsers.get_tags(doc, "span", {"class": "bla"})) == 0
        assert (
            len(
                parsers.get_tags(
                    doc, "span", {"class": "bla"}, attribs_match="substring"
                )
            )
            == 2
        )
        assert (
            len(
                parsers.get_tags(
                    doc, "span", {"class": "blag bla"}, attribs_match="word"
                )
            )
            == 1
        )
        assert (
            len(
                parsers.get_tags(
                    doc, "span", {"class": "dropcap"}, attribs_match="word"
                )
            )
            == 3
        )

    def test_remove_captions(self, get_cleaner, get_formatter):
        # ruff: noqa: E501

        html = """
            <html>
            <body>
                <p><span class="caption">T</span>his is a test</p>
                <p><span itemprop="caption">T</span>his is a test</p>
                <div class="image__metadata">
                    <div itemprop="caption" class="image__caption attribution">
                        <span data-editable="metaCaption" class="inline-placeholder">A victim injured in the attack on a market in Yemen's Saada province receives medical attention at a local hospital on July 29.</span>
                    </div>
                    <figcaption class="image__credit">Naif Rahma/Reuters</figcaption>
                </div>
                </div>
                </div>
                <p><span class="instagram-media">T</span>his is a test</p>
                <p><span id="twitter-tweet">T</span>his is a test</p>
            </body>
            </html>
        """

        doc = parsers.fromstring(html)
        clean_doc = get_cleaner.clean(doc)
        get_formatter.top_node = clean_doc

        text = get_formatter.convert_to_text()
        assert (
            "A victim injured in the attack" not in text
        ), "DocCleaner failed to remove caption"
        assert "Naif Rahma/Reuters" not in text, "DocCleaner failed to remove caption"
        assert text == "his is a test his is a test his is a test his is a test"
