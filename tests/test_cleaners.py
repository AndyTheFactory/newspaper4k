import pytest
import newspaper
from newspaper.cleaners import DocumentCleaner
from newspaper.outputformatters import OutputFormatter
from newspaper import parsers


@pytest.fixture
def get_cleaner() -> DocumentCleaner:
    config = newspaper.Config()

    return DocumentCleaner(config=config)


@pytest.fixture
def get_formatter() -> OutputFormatter:
    config = newspaper.Config()

    return OutputFormatter(config=config)


@pytest.fixture
def html_fixture() -> str:
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

        <p><span class="class2">Test class2</span></p>
        <p><span class="xx class2 zzz">Test space in class</span></p>
        <p><span class="xx class2-koko zzz">Test dash in class</span></p>
        <p><span class="xx class2_koko zzz">Test underscore in class</span></p>
        </body>
        </html>
        """
    return html


@pytest.fixture
def html_fixture_para() -> str:
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
    def test_remove_drop_caps(self, get_cleaner):
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
            result = parsers.get_text(doc)
            assert (
                result == "This is a test This is a test This is a test This is a test"
            )

    def test_clean_para_spans(self, get_cleaner, html_fixture_para):
        doc = parsers.fromstring(html_fixture_para)

        doc = get_cleaner.clean_para_spans(doc)
        result = parsers.get_text(doc)

        assert result == "This is a test This is a test T his is a test"

    def test_newlines(self, get_formatter):
        txt = """<div>
                    <p>line 1
                    still line 1</p>
                    <p>
                        <strong>line 2</strong><br>line 3
                    </p>
                    line 4
                </div>
                <span>
                    <blockquote>
                        line 5
                    </blockquote>
                    line 6
                    <ul>
                        <li>line 7</li>
                        <li>line 8</li>
                    </ul>
                    line 9
                </span>
                still line 9
            """
        expected = (
            "line 1 still line 1\n\nline 2\n\nline 3\n\n"
            "line 4\n\nline 5\n\nline 6\n\nline 7\n\nline 8\n\n"
            "line 9 still line 9"
        )

        doc = parsers.fromstring(txt)

        result_txt, _ = get_formatter.get_formatted(doc)

        assert expected == result_txt


class TestParser:
    def test_get_tag(self, html_fixture):
        doc = parsers.fromstring(html_fixture)

        assert len(parsers.get_tags(doc, "p")) == 6
        assert len(parsers.get_tags(doc, "div")) == 2
        assert len(parsers.get_tags(doc, "span")) == 7
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
        assert (
            len(
                parsers.get_tags(doc, "span", {"class": "class2"}, attribs_match="word")
            )
            == 2
        )
        assert (
            len(
                parsers.get_tags(
                    doc,
                    "span",
                    {"class": "class2"},
                    attribs_match="word",
                    ignore_dashes=True,
                )
            )
            == 4
        )

    def test_remove_captions(self, get_cleaner):
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
        text = parsers.get_text(clean_doc)

        assert (
            "A victim injured in the attack" not in text
        ), "DocCleaner failed to remove caption"
        assert "Naif Rahma/Reuters" not in text, "DocCleaner failed to remove caption"
        assert text == "his is a test his is a test his is a test his is a test"
