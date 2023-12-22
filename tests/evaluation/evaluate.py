from urllib.parse import urljoin
import requests
import argparse
import json
import gzip
from pathlib import Path
import newspaper
from nltk.translate import bleu_score

from newspaper.utils import progressbar


def read_or_download_json(url_or_path):
    """Reads a json file from a url or a local path"""
    if url_or_path.startswith("http"):
        return requests.get(url_or_path, timeout=(5, 10)).json()
    else:
        with open(url_or_path, "r", encoding="utf-8") as f:
            return json.load(f)


def get_html(url_or_path):
    """Gets the html from a url or a local path"""
    if url_or_path.startswith("http"):
        content = requests.get(url_or_path, timeout=(5, 10)).content
    else:
        with open(url_or_path, "rb", encoding="utf-8") as f:
            content = f.read()

    if not url_or_path.lower().endswith(".gz"):
        if isinstance(content, bytes):
            content = content.decode("utf-8")
        return content

    content = gzip.decompress(content)
    return content.decode("utf-8")


def main(args):
    ground_truth = read_or_download_json(args.ground_truth)
    results = {}
    for filename, expected_article in progressbar(ground_truth.items()):
        if not filename.endswith(".html") and not filename.endswith(".html.gz"):
            filename += ".html.gz"

        if args.html_folder.startswith("http"):
            html = get_html(urljoin(args.html_folder, filename))
        else:
            html = get_html(Path(args.html_folder) / filename)

        article = newspaper.article(url=expected_article["url"], input_html=html)

        parsed_result = article.text

        results[filename] = {
            "url": expected_article["url"],
            "truth": expected_article["articleBody"],
            "parsed": parsed_result,
            "bleu_score": bleu_score.sentence_bleu(
                [expected_article["articleBody"]], parsed_result
            ),
            "precision": bleu_score.modified_precision(
                [expected_article["articleBody"]], parsed_result, n=5
            ),
        }
    copora_score = bleu_score.corpus_bleu(
        [[result["truth"]] for result in results.values()],
        [result["parsed"] for result in results.values()],
    )
    sorted_results = sorted(
        [(k, result["url"], result["bleu_score"]) for k, result in results.items()],
        key=lambda x: x[2],
        reverse=False,
    )

    print(f"Corpus BLEU score: {copora_score}")

    print("Top 10 worst results:")
    for filename, url, score in sorted_results[:10]:
        print(f"{score} {filename} {url} ")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--ground-truth",
        type=str,
        default="https://raw.githubusercontent.com/scrapinghub/article-extraction-benchmark/master/ground-truth.json",
        help="URL to the groundtruth json or a local path to the json file",
    )
    parser.add_argument(
        "--html-folder",
        type=str,
        default="https://github.com/scrapinghub/article-extraction-benchmark/raw/master/html/",
        help=(
            "URL to the folder containing the html files or a local path to the folder"
        ),
    )
    args = parser.parse_args()
    main(args)
