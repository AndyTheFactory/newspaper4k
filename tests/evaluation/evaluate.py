from collections import Counter
import re
import statistics
from typing import Dict, Tuple, List
from urllib.parse import urljoin
import requests
import argparse
import json
import gzip
from tqdm import tqdm
from pathlib import Path
import newspaper
from nltk.translate import bleu_score
from nltk.util import ngrams


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
        res = requests.get(url_or_path, timeout=(5, 10))
        if res.status_code == 404 and url_or_path.endswith(".gz"):
            url_or_path = url_or_path[:-3]
            res = requests.get(url_or_path, timeout=(5, 10))
        if res.status_code == 404:
            raise ValueError(f"404: {url_or_path}")
        content = res.content
    else:
        with open(url_or_path, "rb", encoding="utf-8") as f:
            content = f.read()

    if not url_or_path.lower().endswith(".gz"):
        if isinstance(content, bytes):
            content = content.decode("utf-8")
        return content

    content = gzip.decompress(content)
    return content.decode("utf-8")


def string_shingle_matching(
    true: str,
    pred: str,
    ngram_n: int = 4,
) -> Tuple[float, float, float]:
    """Compute TP/FP/FN across shingles (joined ngrams).
    Intended to be used for articleBody comparison,
    similar to the one used here (with shingles instead of tokens):
    https://moz.com/devblog/benchmarking-python-content-extraction-algorithms-dragnet-readability-goose-and-eatiht/
    """
    _TOKEN_RE = re.compile(
        r"\w+", re.UNICODE | re.MULTILINE | re.IGNORECASE | re.DOTALL
    )

    def _ngrams(text: str, n: int) -> List[Tuple[str, ...]]:
        tokens = _TOKEN_RE.findall(text or "")
        n_grams = ngrams(tokens, n)

        return n_grams

    def _all_shingles(text, ngram_n):
        return dict(Counter(_ngrams(text, ngram_n)))

    true_shingles = _all_shingles(true, ngram_n)
    pred_shingles = _all_shingles(pred, ngram_n)
    tp = fp = fn = 0.0
    for key in set(true_shingles) | set(pred_shingles):
        true_count = true_shingles.get(key, 0)
        pred_count = pred_shingles.get(key, 0)
        tp += min(true_count, pred_count)
        fp += max(0, pred_count - true_count)
        fn += max(0, true_count - pred_count)
    tp_fp_fn = [tp, fp, fn]
    s = sum(tp_fp_fn)
    # Normalize metrics so that longer texts do not have more weight.
    if s > 0:
        tp_fp_fn = [x / s for x in tp_fp_fn]
    prec = precision_score(*tp_fp_fn)
    rec = recall_score(*tp_fp_fn)
    f1 = 2 * prec * rec / (prec + rec) if prec + rec > 0 else 0.0
    _accuracy = (tp) / (tp + fp + fn) if tp + fp + fn > 0 else 0.0

    tp_fp_fn.extend([_accuracy, prec, rec, f1])

    return tuple(tp_fp_fn)  # type: ignore


def metrics_shingle(tp_fp_fns) -> Dict[str, float]:
    res = []
    for i in range(len(tp_fp_fns[0])):
        res.append(statistics.mean([x[i] for x in tp_fp_fns]))

    prec, recall = res[4:6]

    f1 = 2 * prec * recall / (prec + recall) if prec + recall > 0 else 0.0

    return {
        "accuracy": res[3],
        "precision": prec,
        "recall": recall,
        "f1": f1,
    }


def precision_score(tp: float, fp: float, fn: float) -> float:
    if fp == fn == 0:
        return 1.0
    if tp == fp == 0:
        return 0.0
    return tp / (tp + fp)


def recall_score(tp: float, fp: float, fn: float) -> float:
    if fp == fn == 0:
        return 1.0
    if tp == fn == 0:
        return 0.0
    return tp / (tp + fn)


def main(args):
    ground_truth = read_or_download_json(args.ground_truth)
    results = {}
    metrics = []
    for filename, expected_article in tqdm(ground_truth.items()):
        if not filename.endswith(".html") and not filename.endswith(".html.gz"):
            filename += ".html.gz"

        if args.html_folder.startswith("http"):
            html = get_html(urljoin(args.html_folder, filename))
        else:
            html = get_html(Path(args.html_folder) / filename)

        article = newspaper.article(
            url=expected_article["url"],
            input_html=html,
            fetch_images=False,
        )

        parsed_result = article.text
        metric = string_shingle_matching(expected_article["articleBody"], parsed_result)
        metrics.append(metric)

        results[filename] = {
            "url": expected_article["url"],
            "truth": expected_article["articleBody"],
            "parsed": parsed_result,
            "bleu_score": bleu_score.sentence_bleu(
                [expected_article["articleBody"]], parsed_result
            ),
            "precision": float(
                bleu_score.modified_precision(
                    [expected_article["articleBody"]], parsed_result, n=5
                )
            ),
            "acc": metric[3],
            "prec": metric[4],
            "recall": metric[5],
            "f1": metric[6],
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
    metric_corpora = metrics_shingle(metrics)

    print(f"Corpus BLEU score: {copora_score}")
    print(f"Corpus Accuracy score: {metric_corpora['accuracy']}")
    print(f"Corpus Precision score: {metric_corpora['precision']}")
    print(f"Corpus Recall score: {metric_corpora['recall']}")
    print(f"Corpus F1 score: {metric_corpora['f1']}")

    print("Top 10 worst results:")
    for filename, url, score in sorted_results[:10]:
        print(f"{score} {filename} {url} ")

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=4, ensure_ascii=False)


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
    parser.add_argument(
        "--output",
        type=str,
        help="Write parsing results and scores into an json file",
    )
    args = parser.parse_args()
    main(args)
