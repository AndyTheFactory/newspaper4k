# Script used to download the HTML of articles, save them into files for future tests
# in tests/data/html is the raw HTML of the articles,
# in tests/data/txt is the parsed article objects
# in tests/data/metadata are title, description, feeds, etc of the articles

from pathlib import Path
import json
import argparse
from newspaper import Article
from newspaper.settings import article_json_fields


def main(args):
    article = Article(args.url, language=args.language)
    if args.read_from_file:
        article.download(
            input_html=Path(args.read_from_file).read_text(encoding="utf-8")
        )
    else:
        article.download()
    article.parse()
    article.nlp()
    article_dict = article.to_json(as_string=False)

    # Save HTML
    if not args.read_from_file:
        html_path = Path(__file__).parent / f"data/html/{args.output_name}.html"
        html_path.parent.mkdir(parents=True, exist_ok=True)
        html_path.write_text(article.html, encoding="utf-8")
        print(f"HTML saved to {html_path}")

    # Save TXT
    txt_path = Path(__file__).parent / f"data/txt/{args.output_name}.txt"
    txt_path.parent.mkdir(parents=True, exist_ok=True)
    txt_path.write_text(article.text, encoding="utf-8")
    print(f"TXT saved to {txt_path}")

    # Save JSON
    json_path = Path(__file__).parent / f"data/metadata/{args.output_name}.json"
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(article_dict, indent=4, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    print(f"Metadata saved to {json_path}")

    print("All done!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create test data for newspaper4k")
    parser.add_argument("--url", type=str, help="URL to download", required=True)
    parser.add_argument(
        "--language",
        type=str,
        help="Language of the article",
        default="en",
        required=False,
    )
    parser.add_argument("--read-from-file", type=str, help="Read HTML from file")
    parser.add_argument(
        "-o",
        "--output-name",
        type=str,
        help=(
            "Output filename (without extension). "
            "The script will create a .html, .txt and .json file"
        ),
        required=True,
    )
    parser.add_argument(
        "-m",
        "--include-metadata",
        type=str,
        choices=article_json_fields,
        help="Include only these metadata information in the json file",
        required=False,
    )
    main(parser.parse_args())
