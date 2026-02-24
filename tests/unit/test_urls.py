import pytest

from newspaper.urls import (
    get_domain,
    get_path,
    get_scheme,
    is_abs_url,
    prepare_url,
    redirect_back,
    url_to_filetype,
    urljoin_if_valid,
    valid_url,
)


@pytest.mark.parametrize(
    "url, source_domain, expected",
    [
        (
            "http://www.pinterest.com/pin/2815659554469Pinterest-for-Android-Download/",
            "yahoo.com",
            "http://www.pinterest.com/pin/2815659554469Pinterest-for-Android-Download/",
        ),
        (
            "https://www.pinterest.com/pin/1316595554469-for-Android-Download/?url=https://techcrunch.com/2016/09/20/pinterest-for-android-gets-a-new-look-and-a-built-in-browser/",
            "yahoo.com",
            "https://techcrunch.com/2016/09/20/pinterest-for-android-gets-a-new-look-and-a-built-in-browser/",
        ),
        ("https://www.google.com", "google.com", "https://www.google.com"),
    ],
)
def test_redirect_back(url, source_domain, expected):
    assert redirect_back(url, source_domain) == expected


@pytest.mark.parametrize(
    "url, source_url, expected",
    [
        ("http://www.example.com/path", None, "http://www.example.com/path"),
        ("/path", "http://www.example.com", "http://www.example.com/path"),
        (
            "//www.example.com/path",
            "http://www.anotherexample.com",
            "http://www.example.com/path",
        ),
        (
            "https://www.pinterest.com/pin/1316595554469-for-Android-Download/?url=https://techcrunch.com/2016/09/20/pinterest-for-android-gets-a-new-look-and-a-built-in-browser/",
            "http://www.yahoo.com",
            "https://techcrunch.com/2016/09/20/pinterest-for-android-gets-a-new-look-and-a-built-in-browser/",
        ),
        ("http://www.example.com", "http://[...]/", ""),
    ],
)
def test_prepare_url(url, source_url, expected):
    assert prepare_url(url, source_url) == expected


@pytest.mark.parametrize(
    "url, expected",
    [
        ("http://www.example.com/2024/01/01/article.html", True),
        ("http://www.example.com/story/article-slug", True),
        ("http://www.example.com/article-slug-with-many-dashes-in-it", True),
        ("http://www.example.com/news/2024/article.html", True),
        ("http://www.example.com/article/12345", True),
        ("http://www.example.com/2024/01/article", True),
        ("http://www.example.com/about", False),
        ("http://careers.example.com/jobs", False),
        ("http://www.example.com/static/style.css", False),
        ("mailto:test@example.com", False),
        ("ftp://example.com/file.txt", False),
        ("http://example.com", False),
        ("http://example.com/a", False),
        ("http://www.example.com/2024/01/01/", True),
        ("http://www.example.com/2024/01/01", True),
        ("http://www.example.com/article/123", True),
        ("http://www.example.com/article/123/another/part", True),
        ("http://www.example.com/story/123", True),
        ("http://www.example.com/story/abc", True),
        ("http://www.example.com/2024/01/01/article_with_underscores", True),
        ("http://www.example.com/article_with_many_underscores_in_it", True),
        ("http://google.com/news/1234", False),
        ("http://facebook.com/news/1234", False),
        ("http://www.example.com/a/b/c/d/e/f/g/h/i/j/k/l/m/n/o/p/q/r/s/t/u/v/w/x/y/z/article.html", True),
        ("http://www.example.com/article.pdf", False),
        ("http://www.example.com/article.jpg", False),
        ("http://www.example.com/article.zip", False),
        ("http://www.example.com/index.html", False),
        ("http://www.example.com/index/article.html", False),
        ("http://www.example.com/index/article-best-story-ever-published-period.html", True),
        ("http://www.example.com/story/example-is-hiring-now", True),
        ("http://www.example.com/story/example-is-hiring-now-story", True),
        ("http://www.example.com/story/example-is-hiring-now-story-with-domain-example", True),
        ("http://www.example.com/story/example-is-hiring-now-story-with-domain-example-and-more", True),
        ("http://www.example.com/path/123", True),
        ("http://www.example.com/path/123/456", True),
        ("http://www.example.com/path/123/abc", True),
        ("http://www.example.com/path/abc/123", True),
        ("http://www.example.com/path/123/123", True),
        ("http://www.example.com/path/123/1234", True),
        ("http://www.example.com/path/1234/123", True),
        ("http://www.example.com/path/1234/1234", True),
    ],
)
def test_valid_url(url, expected):
    assert valid_url(url, test=True) == expected


@pytest.mark.parametrize(
    "url, expected",
    [
        ("http://www.example.com/article.html", "html"),
        ("http://www.example.com/article.PDF", "pdf"),
        ("http://www.example.com/path/", None),
        ("http://www.example.com/path/article", None),
        ("http://www.example.com/path/article.longextension", None),
        ("http://www.example.com/path/article.jpeg", "jpeg"),
    ],
)
def test_url_to_filetype(url, expected):
    assert url_to_filetype(url) == expected


@pytest.mark.parametrize(
    "url, expected",
    [
        ("http://www.example.com/path", "www.example.com"),
        ("https://example.com", "example.com"),
        (None, None),
    ],
)
def test_get_domain(url, expected):
    assert get_domain(url) == expected


@pytest.mark.parametrize(
    "url, expected",
    [
        ("http://www.example.com/path", "http"),
        ("https://example.com", "https"),
        (None, None),
    ],
)
def test_get_scheme(url, expected):
    assert get_scheme(url) == expected


@pytest.mark.parametrize(
    "url, expected",
    [
        ("http://www.example.com/path", "/path"),
        ("https://example.com", ""),
        (None, None),
    ],
)
def test_get_path(url, expected):
    assert get_path(url) == expected


@pytest.mark.parametrize(
    "url, expected",
    [
        ("http://www.example.com", True),
        ("https://www.example.com", True),
        ("ftp://example.com", True),
        ("http://localhost:8000", True),
        ("http://127.0.0.1:8000", True),
        ("/path/to/file", False),
        ("www.example.com", False),
    ],
)
def test_is_abs_url(url, expected):
    assert is_abs_url(url) == expected


@pytest.mark.parametrize(
    "base_url, url, expected",
    [
        ("http://www.example.com", "/path", "http://www.example.com/path"),
        ("http://www.example.com", "http://www.anotherexample.com", "http://www.anotherexample.com"),
        ("http://www.example.com", "not a url", "http://www.example.com/not a url"),
        ("http://[...]/", "path", ""),
    ],
)
def test_urljoin_if_valid(base_url, url, expected):
    assert urljoin_if_valid(base_url, url) == expected
