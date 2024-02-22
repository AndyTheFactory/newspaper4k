from urllib.parse import urljoin
import argparse
import json
from tqdm import tqdm
from pathlib import Path
import newspaper
from nltk.translate import bleu_score

from helper import (
    read_or_download_json,
    get_html,
    string_shingle_matching,
    metrics_shingle,
)


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
