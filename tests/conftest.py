# Some utility functions for testing
import json
from pathlib import Path


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
