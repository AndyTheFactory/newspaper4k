import pytest

from tests import conftest

pytestmark = pytest.mark.unit


@pytest.fixture(scope="module")
def cnn_article_with_nlp():
    url = "https://edition.cnn.com/2016/12/18/politics/bob-gates-rex-tillerson-trump-russia/index.html"
    html_content = conftest.get_data("cnn_test_nlp", "html")
    text_content = conftest.get_data("cnn_test_nlp", "txt")

    return {
        "url": url,
        "html_content": html_content,
        "text_content": text_content,
        "title": ("Gates on Tillerson and Russia: 'You can be friendly without being friends'"),
        "summary": [
            (
                "Former Defense Secretary Robert Gates on Sunday defended"
                " President-elect Donald Trump\u2019s pick for secretary of state,"
                " ExxonMobil CEO Rex Tillerson, over his relationship with Russian"
                " President Vladimir Putin."
            ),
            (
                "But being friendly doesn\u2019t make you friends,\u201d Gates said in"
                " an interview on NBC\u2019s \u201cMeet the Press.\u201d Gates\u2019"
                " comments come after he and former Secretary of State Condoleezza Rice"
                " both recommended Tillerson for the job."
            ),
            (
                "Their recommendation has faced scrutiny since Gates and Rice both have"
                " business ties to ExxonMobil through their consulting firm."
            ),
            (
                "Tillerson has faced criticism over his relationship with Putin and"
                " Russia amid the intelligence community\u2019s finding that Russian"
                " hackers stole Democratic emails in a bid to influence the US"
                " election."
            ),
            (
                "But Gates said Tillerson\u2019s business relationship with Putin is"
                " being mistaken for a close personal friendship."
            ),
        ],
    }


@pytest.fixture(scope="module")
def keywords_fixture():
    return {
        "text": "The economy is going to be good. Have a good day. Day by day.",
        "keywords": ["day", "good"],
    }


@pytest.fixture
def title_fixture():
    return [
        ("<title>Test title</title>", "Test title"),
        ("<title>Test page » Test title</title>", "Test title"),
        ("<title>Test page &raquo; Test title</title>", "Test title"),
        (
            "<title>Test page and «something in quotes»</title>",
            "Test page and «something in quotes»",
        ),
    ]


@pytest.fixture
def canonical_url_fixture():
    return [
        ("", '<link rel="canonical" href="http://www.example.com/article.html">'),
        (
            "http://www.example.com/article?foo=bar",
            '<link rel="canonical" href="article.html">',
        ),
        (
            "http://www.example.com/article?foo=bar",
            '<meta property="og:url" content="article.html">',
        ),
        (
            "http://www.example.com/article?foo=bar",
            '<meta property="og:url" content="www.example.com/article.html">',
        ),
    ]


@pytest.fixture
def meta_image_fixture():
    return [
        (
            (
                '<meta property="og:image" '
                'content="https://example.com/meta_img_filename.jpg" />'
                '<meta name="og:image" '
                'content="https://example.com/meta_another_img_filename.jpg"/>'
            ),
            "https://example.com/meta_img_filename.jpg",
        ),
        (
            (
                '<meta property="og:image" content="" />'
                '<meta name="og:image" '
                'content="https://example.com/meta_another_img_filename.jpg"/>'
            ),
            "https://example.com/meta_another_img_filename.jpg",
        ),
        ('<meta property="og:image" content="" /><meta name="og:image" />', ""),
        (
            (
                '<meta property="og:image" content="" />'
                '<meta name="og:image" />'
                '<link rel="img_src" href="https://example.com/meta_link_image.jpg" />'
            ),
            "https://example.com/meta_link_image.jpg",
        ),
        (
            (
                '<meta property="og:image" content="" /><meta name="og:image" /><link'
                ' rel="image_src" href="https://example.com/meta_link_image2.jpg" />'
            ),
            "https://example.com/meta_link_image2.jpg",
        ),
        (
            (
                '<meta property="og:image" content="" />'
                '<meta name="og:image" />'
                '<link rel="icon" href="https://example.com/meta_link_rel_icon.ico" />'
            ),
            "https://example.com/meta_link_rel_icon.ico",
        ),
    ]
