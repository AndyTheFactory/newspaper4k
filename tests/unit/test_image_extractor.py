# ruff: noqa: D100, D103

from types import SimpleNamespace

import lxml.html
import requests

from newspaper.configuration import Configuration
from newspaper.extractors.image_extractor import ImageExtractor


def make_extractor(fetch_images=True):
    config = Configuration()
    config.fetch_images = fetch_images
    return ImageExtractor(config)


def test_init_sets_defaults():
    config = Configuration()
    extractor = ImageExtractor(config)

    assert extractor.config is config
    assert extractor.top_image is None
    assert extractor.meta_image is None
    assert extractor.images == []
    assert extractor.favicon is None


def test_parse_resolves_extracted_image_urls(mocker):
    extractor = make_extractor(fetch_images=False)
    doc = lxml.html.fromstring("<html></html>")
    top_node = object()
    mocker.patch.object(extractor, "_get_favicon", return_value="/favicon.ico")
    mocker.patch.object(extractor, "_get_meta_image", return_value="/meta.jpg")
    mocker.patch.object(extractor, "_get_images", return_value=[" /skip-whitespace.jpg ", "/one.jpg", ""])
    top = mocker.patch.object(extractor, "_get_top_image", return_value="https://example.com/top.jpg")

    extractor.parse(doc, top_node, "https://example.com/news/story")

    assert extractor.favicon == "/favicon.ico"
    assert extractor.meta_image == "https://example.com/meta.jpg"
    assert extractor.images == ["https://example.com/skip-whitespace.jpg ", "https://example.com/one.jpg"]
    assert extractor.top_image == "https://example.com/top.jpg"
    top.assert_called_once_with(doc, top_node, "https://example.com/news/story")


def test_get_favicon_returns_first_matching_link_or_empty():
    extractor = make_extractor()
    doc = lxml.html.fromstring(
        '<html><link rel="shortcut icon" href="/first.ico"><link rel="icon" href="/second.ico"></html>'
    )

    assert extractor._get_favicon(doc) == "/first.ico"
    assert extractor._get_favicon(lxml.html.fromstring("<html/>")) == ""


def test_get_meta_image_uses_highest_scored_nonempty_candidate(mocker):
    extractor = make_extractor()
    doc = lxml.html.fromstring("<html></html>")
    high = lxml.html.Element("meta")
    high.set("content", "high.jpg")
    low = lxml.html.Element("meta")
    low.set("content", "low.jpg")
    mocker.patch(
        "newspaper.extractors.image_extractor.defines.META_IMAGE_TAGS",
        [
            {"tag": "meta", "attr": "property", "value": "og:image", "content": "content", "score": 20},
            {"tag": "meta", "attr": "name", "value": "twitter:image|image", "content": "content", "score": 10},
        ],
    )
    mocker.patch(
        "newspaper.extractors.image_extractor.parsers.get_tags",
        return_value=[high],
    )
    regex = mocker.patch(
        "newspaper.extractors.image_extractor.parsers.get_tags_regex",
        return_value=[low],
    )

    assert extractor._get_meta_image(doc) == "high.jpg"
    regex.assert_called_once()


def test_get_images_prefers_http_source_and_ignores_data_urls():
    extractor = make_extractor()
    doc = lxml.html.fromstring(
        '<html><img src="/fallback.jpg" data-src="https://example.com/preferred.jpg">'
        '<img src="data:image/png;base64,abc"><img data-lazy-src="/lazy.jpg"></html>'
    )

    assert extractor._get_images(doc) == ["https://example.com/preferred.jpg", "/lazy.jpg"]


def test_get_top_image_returns_meta_without_fetching():
    extractor = make_extractor(fetch_images=False)
    extractor.meta_image = "https://example.com/meta.jpg"

    result = extractor._get_top_image(lxml.html.fromstring("<html/>"), None, "https://example.com/a")

    assert result == extractor.meta_image


def test_get_top_image_validates_meta_then_nearest_dom_candidate(mocker):
    extractor = make_extractor(fetch_images=True)
    extractor.meta_image = "https://example.com/meta.jpg"
    doc = lxml.html.fromstring(
        '<html><body><img src="https://example.com/far.jpg"><article><p>text</p>'
        '<img src="https://example.com/near.jpg"><img src="data:image/png;base64,x"></article></body></html>'
    )
    top_node = doc.xpath("//article")[0]
    check = mocker.patch.object(
        extractor,
        "_check_image_size",
        side_effect=lambda url, _referer: url == "https://example.com/near.jpg",
    )

    assert extractor._get_top_image(doc, top_node, "https://example.com/a") == "https://example.com/near.jpg"
    assert check.call_args_list[0].args[0] == "https://example.com/meta.jpg"


def test_get_top_image_without_top_node_returns_first_valid_source(mocker):
    extractor = make_extractor(fetch_images=True)
    extractor.meta_image = None
    doc = lxml.html.fromstring(
        '<html><img src="data:image/png;base64,x"><img data-src="ignored.jpg">'
        '<img src="https://example.com/good.jpg"></html>'
    )
    mocker.patch.object(extractor, "_check_image_size", return_value=True)

    assert extractor._get_top_image(doc, None, "https://example.com/a") == "https://example.com/good.jpg"


def test_check_image_size_enforces_dimensions_area_and_logo_rule(mocker):
    extractor = make_extractor()
    fetch = mocker.patch.object(extractor, "_fetch_image")

    fetch.return_value = None
    assert extractor._check_image_size("https://example.com/a.jpg", None) is False
    fetch.return_value = SimpleNamespace(size=(299, 500))
    assert extractor._check_image_size("https://example.com/a.jpg", None) is False
    fetch.return_value = SimpleNamespace(size=(400, 199))
    assert extractor._check_image_size("https://example.com/a.jpg", None) is False
    fetch.return_value = SimpleNamespace(size=(300, 200))
    assert extractor._check_image_size("https://example.com/logo.jpg", None) is False
    assert extractor._check_image_size("https://example.com/photo.jpg", None) is True


def test_fetch_image_rejects_invalid_urls_without_network(mocker):
    extractor = make_extractor()
    get = mocker.patch("newspaper.extractors.image_extractor.session.get")

    assert extractor._fetch_image("/relative.jpg", None) is None
    assert extractor._fetch_image(None, None) is None
    get.assert_not_called()


def test_fetch_image_uses_mocked_response_and_closes_it(mocker):
    extractor = make_extractor()
    connection = mocker.Mock()
    raw = mocker.Mock()
    raw._connection = connection
    response = SimpleNamespace(headers={"Content-Type": "image/jpeg"}, raw=raw)
    get = mocker.patch("newspaper.extractors.image_extractor.session.get", return_value=response)
    image = SimpleNamespace(size=(640, 480))
    mocker.patch(
        "newspaper.extractors.image_extractor.ImageFile.Parser",
        return_value=SimpleNamespace(image=image),
    )

    assert extractor._fetch_image("https://example.com/café.jpg", "https://example.com/a") is image
    assert get.call_args.args[0] == "https://example.com/caf%C3%A9.jpg"  # codespell:ignore caf
    assert get.call_args.kwargs["headers"]["Referer"] == "https://example.com/a"
    raw.close.assert_called_once_with()
    connection.close.assert_called_once_with()


def test_fetch_image_retries_request_errors_without_remote_access(mocker):
    extractor = make_extractor()
    extractor.config.top_image_settings["max_retries"] = 2
    get = mocker.patch(
        "newspaper.extractors.image_extractor.session.get",
        side_effect=requests.exceptions.ConnectionError("offline"),
    )

    assert extractor._fetch_image("https://example.com/a.jpg", None) is None
    assert get.call_count == 2
