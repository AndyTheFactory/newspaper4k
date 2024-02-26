# Some utility functions for testing
import json
from pathlib import Path
from .evaluation.helper import get_html, read_or_download_json


def get_data(filename, resource_type):
    """
    Mocks an HTTP request by pulling text from a pre-downloaded file
    """
    assert resource_type in [
        "html",
        "txt",
        "metadata",
    ], f"Invalid resource type {resource_type}"
    file = (
        Path(__file__).resolve().parent
        / "data"
        / resource_type
        / f"{filename}.{resource_type}"
    )
    if resource_type != "metadata":
        with open(file, "r", encoding="utf-8") as f:
            return f.read()
    else:
        with open(file.with_suffix(".json"), "r", encoding="utf-8") as f:
            return json.load(f)


def get_scrapinghub_data(filename: str):
    ground_truth_json = read_or_download_json(
        "https://raw.githubusercontent.com/scrapinghub/article-extraction-benchmark/master/ground-truth.json"
    )
    if filename not in ground_truth_json:
        raise ValueError(f"Invalid filename {filename}")

    html_content = get_html(
        f"https://github.com/scrapinghub/article-extraction-benchmark/raw/master/html/{filename}.html.gz"
    )

    return {
        "url": ground_truth_json[filename]["url"],
        "html": html_content,
        "text": ground_truth_json[filename]["articleBody"],
    }
