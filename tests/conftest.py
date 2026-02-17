# Some utility functions for testing
"""Helper functions for Tests"""

import json
from pathlib import Path

import pytest

import newspaper


def get_url_filecontent(filename):
    with open(Path(__file__).parent / "data" / filename) as f:
        lines = f.readlines()
        return [tuple(line.strip().split(" ")) for line in lines if " " in line]


def get_data(filename, resource_type):
    """Mocks an HTTP request by pulling text from a pre-downloaded file"""
    assert resource_type in [
        "html",
        "txt",
        "metadata",
    ], f"Invalid resource type {resource_type}"
    file = Path(__file__).resolve().parent / "data" / resource_type / f"{filename}.{resource_type}"
    if resource_type != "metadata":
        with open(file, encoding="utf-8") as f:
            return f.read()
    else:
        with open(file.with_suffix(".json"), encoding="utf-8") as f:
            return json.load(f)


@pytest.fixture(scope="module")
def cnn_article():
    url = "http://www.cnn.com/2013/11/27/travel/weather-thanksgiving/index.html?iref=allsearch"
    html_content = get_data("cnn_article", "html")
    text_content = get_data("cnn_article", "txt")
    json_content = get_data("cnn_article", "metadata")

    return {
        "url": url,
        "html_content": html_content,
        "text_content": text_content,
        "summary": json_content["summary"],
        "keywords": json_content["keywords"],
    }


@pytest.fixture(scope="module")
def meta_refresh():
    return [
        (get_data("google_meta_refresh", "html"), "Example Domain"),
        (
            get_data("ap_meta_refresh", "html"),
            "News from The Associated Press",
        ),
    ]


@pytest.fixture(scope="module")
def read_more_fixture():
    # noqa: E501
    return [
        {
            "url": "https://finance.yahoo.com/m/fd86d317-c06d-351a-ab62-f7f2234ccc35/art-cashin%3A-once-the-10-year.html",
            "selector_button": ("//a[contains(text(), 'Continue reading') and contains(@class, 'caas-button')]"),
            "min_text_length": 1000,
        },
    ]


@pytest.fixture(scope="module")
def known_websites():
    res = []
    for file in [
        "cnn_001",
        "cnn_002",
        "time_001",
        "wired_001",
        "article_with_br",
        "article_with_divs",
        "yna_co_kr",
    ]:
        html = get_data(file, "html")
        metadata = get_data(file, "metadata")
        text = get_data(file, "txt")
        res.append(
            {
                "url": "www.test.com",
                "html": html,
                "text": text,
                "metadata": metadata,
                "file": file,
            }
        )
    return res


@pytest.fixture(scope="module")
def article_video_fixture():
    res = []

    for file in [
        "video_article_01",
        "video_article_02",
    ]:
        html = get_data(file, "html")
        metadata = get_data(file, "metadata")
        res.append({"url": "www.test.com", "html": html, "movies": metadata["movies"]})
    return res


@pytest.fixture(scope="module")
def top_image_fixture():
    res = []

    for file in [
        "cnn_001",
        "cnn_002",
    ]:
        html = get_data(file, "html")
        metadata = get_data(file, "metadata")
        res.append({"url": "www.test.com", "html": html, "top_image": metadata["top_image"]})
    return res


@pytest.fixture
def output_file(tmp_path):
    return {
        "json": tmp_path / "output_file.json",
        "csv": tmp_path / "output_file.csv",
    }


@pytest.fixture
def language_article_fixture():
    return [
        (
            "thai_article",
            "https://prachatai.com/journal/2019/01/80642",
            "th",
        ),
        (
            "arabic_article",
            "http://arabic.cnn.com/2013/middle_east/8/2/syria.clashes/index.html",
            "ar",
        ),
        (
            "spanish_article",
            (
                "http://ultimahora.es/mallorca/noticia/noticias/local/fiscal"
                "ia-anticorrupcion-estudia-recurre-imputacion-infanta.html"
            ),
            "es",
        ),
        (
            "chinese_article",
            "http://news.sohu.com/20050601/n225789219.shtml",
            "zh",
        ),
        (
            "japanese_article",
            "https://www.nikkei.com/article/DGXMZO31897660Y8A610C1000000/?n_cid=DSTPCS001",
            "ja",
        ),
        (
            "japanese_article2",
            "http://www.afpbb.com/articles/-/3178894",
            "ja",
        ),
        (
            "chinese_article_001",
            "https://china.chinadaily.com.cn/a/202311/17/WS65571297a310d5acd876f404.html",
            "zh",
        ),
        (
            "chinese_article_002",
            "http://www.news.cn/fortune/2023-11/17/c_1129981476.htm",
            "zh",
        ),
        (
            "latvian_article",
            "https://www.lsm.lv/raksts/zinas/arzemes/norvegija-pec-zemes-nogruvuma-pieci-bojagajusie.a387519/",
            "lv",
        ),
        (
            "burmese_article",
            "https://www.bbc.com/burmese/burma-45989453",
            "my",
        ),
    ]


@pytest.fixture
def valid_language_fixture():
    return newspaper.valid_languages()


@pytest.fixture
def language_text_fixture():
    return {
        "en": {
            "text": get_data("cnn_article", "txt"),
            "stopwords": 638,
        },
        "th": {
            "text": get_data("thai_article", "txt"),
            "stopwords": 98,
        },
        "ar": {
            "text": get_data("arabic_article", "txt"),
            "stopwords": 87,
        },
        "es": {
            "text": get_data("spanish_article", "txt"),
            "stopwords": 221,
        },
        "zh": {
            "text": get_data("chinese_article", "txt"),
            "stopwords": 88,
        },
        "ja": {
            "text": get_data("japanese_article", "txt"),
            "stopwords": 46,
        },
        "ko": {
            "text": get_data("korean_article", "txt"),
            "stopwords": 122,
        },
        "hi": {
            "text": get_data("hindi_article", "txt"),
            "stopwords": 220,
        },
    }


@pytest.fixture
def download_urls():
    return [
        {"url": "http://ipv4.download.thinkbroadband.com/5MB.zip", "size": 5000000},
        {"url": "https://httpbin.org/delay/5", "size": 100},
        {"url": "https://httpbin.org/image/jpeg", "size": 35000},
        {
            "url": "https://freetestdata.com/wp-content/uploads/2023/11/7.7-KB.txt",
            "size": 7700,
        },
        {
            "url": "https://freetestdata.com/wp-content/uploads/2023/11/23KB.txt",
            "size": 23000,
        },
        {
            "url": "https://freetestdata.com/wp-content/uploads/2023/11/40-KB.txt",
            "size": 40000,
        },
        {
            "url": "https://freetestdata.com/wp-content/uploads/2023/11/160-KB.txt",
            "size": 160000,
        },
    ]


@pytest.fixture
def article_urls():
    return [
        "https://edition.cnn.com/travel/air-algeria-airplane-stowaway-critical-condition/index.html",
        "https://edition.cnn.com/videos/us/2023/12/28/man-pulls-gun-on-woman-road-rage-pkg-vpx.knxv",
        "https://www.foxnews.com/us/antisemitism-exposed-hate-soars-on-campus-tennis-legend-weighs-in-on-viral-video",
        "https://www.foxnews.com/media/homeowner-new-florida-bill-close-squatting-loophole-return-some-fairness",
        "https://edition.cnn.com/2023/12/27/middleeast/dutch-diplomat-humanitarian-aid-gaza-sigrid-kaag-intl/index.html",
    ]


@pytest.fixture
def newssites():
    return [
        "http://slate.com",
        "http://techcrunch.com",
        "https://www.euronews.com/just-in",
    ]


@pytest.fixture
def cnn_source():
    DESC = (
        "CNN.com International delivers breaking news from across "
        "the globe and information on the latest top stories, "
        "business, sports and entertainment headlines. Follow the "
        "news as it happens through: special reports, videos, "
        "audio, photo galleries plus interactive maps and timelines."
    )
    CATEGORY_URLS = [
        "http://www.cnn.com",
        "http://cnn.com",
        "http://cnn.com/CNNI",
        "http://mexico.cnn.com",
        "http://cnn.com/MIDDLEEAST",
        "http://cnn.com/LATINAMERICA",
        "http://edition.cnn.com",
        "http://cnn.com/TECH",
        "http://money.cnn.com",
        "http://cnn.com/ASIA",
        "http://cnn.com/WORLD",
        "http://cnn.com/EUROPE",
        "http://ireport.cnn.com",
        "http://arabic.cnn.com",
        "http://us.cnn.com",
        "http://amanpour.blogs.cnn.com",
        "http://cnn.com/espanol",
        "http://cnn.com/HLN",
        "http://cnn.com/US",
        "http://transcripts.cnn.com",
        "http://cnn.com/TRAVEL",
        "http://cnn.com/cnni",
        "http://cnn.com/SHOWBIZ",
        "http://cnn.com/tools/index.html",
        "http://travel.cnn.com",
        "http://connecttheworld.blogs.cnn.com",
        "http://cnn.com/mostpopular",
        "http://business.blogs.cnn.com",
        "http://cnn.com/AFRICA",
        "http://www.cnn.co.jp",
        "http://cnnespanol.cnn.com",
        "http://cnn.com/video",
        "http://cnn.com/BUSINESS",
        "http://cnn.com/SPORT",
    ]

    FEEDS = [
        "http://feeds.cnn.co.jp/cnn/rss",
        "http://rss.cnn.com/rss/cnn_freevideo.rss",
        "http://rss.cnn.com/rss/cnn_latest.rss",
        "http://rss.cnn.com/rss/cnn_topstories.rss",
        "http://rss.cnn.com/rss/edition.rss",
        "http://rss.cnn.com/rss/edition_africa.rss",
        "http://rss.cnn.com/rss/edition_americas.rss",
        "http://rss.cnn.com/rss/edition_asia.rss",
        "http://rss.cnn.com/rss/edition_connecttheworld.rss",
        "http://rss.cnn.com/rss/edition_entertainment.rss",
        "http://rss.cnn.com/rss/edition_europe.rss",
        "http://rss.cnn.com/rss/edition_football.rss",
        "http://rss.cnn.com/rss/edition_meast.rss",
        "http://rss.cnn.com/rss/edition_space.rss",
        "http://rss.cnn.com/rss/edition_sport.rss",
        "http://rss.cnn.com/rss/edition_technology.rss",
        "http://rss.cnn.com/rss/edition_travel.rss",
        "http://rss.cnn.com/rss/edition_us.rss",
        "http://rss.cnn.com/rss/edition_world.rss",
        "http://rss.cnn.com/rss/edition_worldsportblog.rss",
        "http://rss.cnn.com/rss/money_news_international.rss",
        "https://arabic.cnn.com/api/v1/rss/rss.xml",
        "https://cnnespanol.cnn.com/home/feed/",
    ]

    BRAND = "cnn"
    html_content = get_data("cnn_main_site", "html")

    return {
        "url": "http://cnn.com",
        "brand": BRAND,
        "description": DESC,
        "category_urls": CATEGORY_URLS,
        "feeds": FEEDS,
        "html_content": html_content,
    }
