from collections import Counter
import re
import statistics
from typing import Dict, Tuple, List
import requests
import gzip
from nltk.util import ngrams
import json


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
