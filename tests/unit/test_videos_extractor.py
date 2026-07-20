# ruff: noqa: D100, D103

import lxml.html

from newspaper.configuration import Configuration
from newspaper.extractors.videos_extractor import VideoExtractor


def make_extractor():
    return VideoExtractor(Configuration())


def test_init_sets_empty_movies_and_config():
    config = Configuration()
    extractor = VideoExtractor(config)

    assert extractor.config is config
    assert extractor.movies == []


def test_parse_extracts_dom_and_json_ld_videos(mocker):
    extractor = make_extractor()
    doc = lxml.html.fromstring(
        '<html><body><article><iframe src="https://youtube.com/embed/1"></iframe></article></body></html>'
    )
    top_node = doc.xpath("//article")[0]
    mocker.patch(
        "newspaper.extractors.videos_extractor.parsers.get_ld_json_object",
        return_value=[
            {"@type": "VideoObject", "contentUrl": "https://vimeo.com/2", "embedUrl": "<iframe>two</iframe>"},
            {"@graph": ["ignored", {"@type": "Article"}]},
        ],
    )

    movies = extractor.parse(doc, top_node)

    assert [movie.provider for movie in movies] == ["youtube", "vimeo"]
    assert movies[1].embed_code == "<iframe>two</iframe>"


def test_iframe_delegates_to_parse_video(mocker):
    extractor = make_extractor()
    node = lxml.html.fromstring('<iframe src="https://youtube.com/1"></iframe>')
    expected = object()
    parse_video = mocker.patch.object(extractor, "parse_video", return_value=expected)

    assert extractor.parse_iframe(node) is expected
    parse_video.assert_called_once_with(node)


def test_embed_inside_object_delegates_to_object(mocker):
    extractor = make_extractor()
    parent = lxml.html.fromstring('<object><embed src="https://youtube.com/1"></object>')
    node = parent[0]
    expected = object()
    parse_object = mocker.patch.object(extractor, "parse_object", return_value=expected)

    assert extractor.parse_embed(node) is expected
    parse_object.assert_called_once_with(node)


def test_embed_without_object_parent_delegates_to_video(mocker):
    extractor = make_extractor()
    parent = lxml.html.fromstring('<div><embed src="https://youtube.com/1"></div>')
    node = parent[0]
    expected = object()
    parse_video = mocker.patch.object(extractor, "parse_video", return_value=expected)

    assert extractor.parse_embed(node) is expected
    parse_video.assert_called_once_with(node)


def test_parse_object_handles_embed_missing_source_and_supported_provider():
    extractor = make_extractor()

    assert extractor.parse_object(lxml.html.fromstring('<object><embed src="x"></object>')) is None
    assert extractor.parse_object(lxml.html.fromstring("<object></object>")) is None
    unsupported = lxml.html.fromstring('<object><param name="movie" value="https://other.test/1"></object>')
    assert extractor.parse_object(unsupported) is None

    video = extractor.parse_object(
        lxml.html.fromstring('<object width="640"><param name="movie" value="https://youtube.com/v/1"></object>')
    )
    assert video.provider == "youtube"
    assert video.src == "https://youtube.com/v/1"


def test_parse_video_reads_dimensions_lazy_source_and_embed_code():
    extractor = make_extractor()
    node = lxml.html.fromstring(
        '<video width="640" height="bad" src="fallback.mp4" data-litespeed-src="https://vimeo.com/1"></video>'
    )

    video = extractor.parse_video(node)

    assert video.embed_type == "video"
    assert video.width == 640
    assert video.height is None
    assert video.src == "https://vimeo.com/1"
    assert video.provider == "vimeo"
    assert video.embed_code == extractor._get_embed_code(node)


def test_get_provider_returns_first_known_provider():
    extractor = make_extractor()

    assert extractor._get_provider("https://youtu.be/abc") == "youtu.be"
    assert extractor._get_provider("https://example.com/video") is None
    assert extractor._get_provider(None) is None
