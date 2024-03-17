"""Command line interface for the newspaper package."""

import argparse
import csv
import io
import logging
from pathlib import Path
import sys
from typing import Any, Dict, Optional, List
import newspaper
from newspaper import settings

logger = logging.getLogger(__name__)


def get_arparse() -> argparse.ArgumentParser:
    """Get the ArgumentParser object for parsing command line arguments.

    Returns:
        argparse.ArgumentParser: The ArgumentParser object.
    """
    parser = argparse.ArgumentParser(description="Download and parse news articles.")
    url_group = parser.add_mutually_exclusive_group(required=True)

    url_group.add_argument(
        "--url", "-u", type=str, help="The URL of the article to download and parse."
    )
    url_group.add_argument(
        "--urls-from-file",
        "-uf",
        type=str,
        help="The file containing the URLs of the articles to download and parse.",
    )
    url_group.add_argument(
        "--urls-from-stdin", "-us", action="store_true", help="Read URLs from stdin."
    )
    parser.add_argument(
        "--html-from-file",
        "-hf",
        type=str,
        help=(
            "The HTML file to parse. This will not download the article, it will parse"
            " the HTML file directly."
        ),
    )
    parser.add_argument(
        "--language",
        "-l",
        type=str,
        default="en",
        help="The language of the article to download and parse.",
    )
    parser.add_argument(
        "--output-format",
        "-of",
        choices=["csv", "json", "text"],
        default="json",
        help="The output format of the parsed article.",
    )
    parser.add_argument(
        "--output-file", "-o", type=str, help="The file to write the parsed article to."
    )
    parser.add_argument(
        "--read-more-link",
        type=str,
        help=(
            "A xpath selector for the link to the full article for the case where the"
            ' article is only a summary, and you need to press "read-more" to read the'
            " full text."
        ),
    )
    parser.add_argument(
        "--skip-fetch-images",
        action="store_true",
        help=(
            "Whether to skip fetching images when identifying the top image. This"
            " option speeds up parsing, but can lead to erroneous top image"
            " identification."
        ),
    )
    parser.add_argument(
        "--follow-meta-refresh",
        action="store_true",
        help="Whether to follow meta refresh links when downloading the article.",
    )
    parser.add_argument(
        "--browser-user-agent",
        "-ua",
        type=str,
        help="The user agent string to use when downloading the article.",
    )
    parser.add_argument(
        "--proxy",
        type=str,
        help=(
            "The proxy to use when downloading the article. The format is:"
            " http://<proxy_host>:<proxy_port> e.g.: http://10.10.1.1:8080"
        ),
    )
    parser.add_argument(
        "--request-timeout",
        type=int,
        default=7,
        help="The timeout to use when downloading the article.",
    )
    parser.add_argument(
        "--cookies",
        type=str,
        help=(
            "The cookies to use when downloading the article. The format is:"
            " cookie1=value1; cookie2=value2; ..."
        ),
    )
    parser.add_argument(
        "--skip-ssl-verify",
        action="store_true",
        help="Whether to skip the certificate verification for the article URL ",
    )
    parser.add_argument(
        "--max-nr-keywords",
        type=int,
        default=10,
        help="The maximum number of keywords to extract from the article.",
    )
    parser.add_argument(
        "--skip-nlp", action="store_true", help="Whether to skip the NLP step."
    )

    return parser


def get_kwargs(args: argparse.Namespace) -> dict:
    """Constructs and returns a dictionary of keyword arguments for newspaper's
    :any:`Article` based on the provided command-line arguments.

    Args:
        args (argparse.Namespace): The command-line arguments parsed by argparse.

    Returns:
        dict: A dictionary of keyword arguments.

    """

    res: Dict[str, Any] = {}
    if args.html_from_file:
        if Path(args.html_from_file).exists():
            res["input_html"] = Path(args.html_from_file).read_text(encoding="utf-8")
        else:
            logger.error("The file %s does not exist.", args.html_from_file)
            raise FileNotFoundError(f"The file {args.html_from_file} does not exist.")

    if args.language:
        res["language"] = args.language
    if args.read_more_link:
        res["read_more_link"] = args.read_more_link
    if args.skip_fetch_images:
        res["fetch_images"] = False
    if args.follow_meta_refresh:
        res["follow_meta_refresh"] = True
    if args.browser_user_agent:
        res["browser_user_agent"] = args.browser_user_agent
    if args.proxy:
        res["request_kwargs"] = {"proxies": {"http": args.proxy, "https": args.proxy}}
    if args.request_timeout:
        res["request_timeout"] = args.request_timeout
    if args.skip_ssl_verify:
        res["verify"] = False
    if args.cookies:
        cookie_dict = {}
        for cookie in args.cookies.split(";"):
            key, value = cookie.split("=")
            cookie_dict[key.strip()] = value.strip()
        res["cookies"] = cookie_dict

    if args.max_nr_keywords:
        res["max_keywords"] = args.max_nr_keywords

    return res


def run(args: argparse.Namespace):
    """Run the newspaper CLI command.
    Args:
        args (argparse.Namespace): The command line arguments.
    """

    if args.html_from_file and (args.urls_from_file or args.urls_from_stdin):
        logger.warning(
            "You specified --html-from-file, but also --urls-from-file or"
            " --urls-from-stdin. The --html-from-file option will be used just for the"
            " first URL."
        )

    if args.urls_from_file:
        with open(args.urls_from_file, "r", encoding="utf-8") as f:
            urls = f.readlines()
    elif args.urls_from_stdin:
        urls = sys.stdin.readlines()
    else:
        urls = [args.url]

    kwargs = get_kwargs(args)

    # Create empty output file. Any existing data will be overwritten.
    if args.output_file:
        logger.info("Writing output to file: %s", args.output_file)
        with open(args.output_file, "w", encoding="utf-8") as f:
            _ = f.write("[") if args.output_format == "json" else f.write("")
    elif args.output_format == "json":
        print("[", end="")

    # write one article record (we can have multiple urls)
    def write_output(txt: str):
        if args.output_file:
            with open(args.output_file, "a", encoding="utf-8") as f:
                f.write(txt)
        else:
            print(txt)

    # Create the csv header
    def csv_header() -> str:
        with io.StringIO() as f:
            writer = csv.DictWriter(f, fieldnames=settings.article_json_fields)
            writer.writeheader()
            return f.getvalue()

    # create a csv line as string
    def csv_string(article_dict: dict) -> str:
        with io.StringIO() as f:
            writer = csv.DictWriter(f, fieldnames=settings.article_json_fields)
            writer.writerow(article_dict)
            return f.getvalue()

    for idx, url in enumerate(urls):
        logger.info("Parsing article %d of %d: %s", idx + 1, len(urls), url)
        article = newspaper.article(url=url, **kwargs)

        if not args.skip_nlp:
            article.nlp()
        else:
            logger.info("Skipping NLP step.")

        if "input_html" in kwargs:
            #  we use the html_from_file option just for the first URL
            del kwargs["input_html"]

        output = article.to_json(as_string=args.output_format == "json")
        if args.output_format == "json":
            if idx < len(urls) - 1:
                output += ","
            write_output(output)
        elif args.output_format == "csv":
            if idx == 0:
                write_output(csv_header())
            write_output(csv_string(output))
        elif args.output_format == "text":
            write_output(f"{article.title}\n\n")
            write_output(article.text)
        else:
            raise ValueError(f"Unknown output format: {args.output_format}")

        if args.output_file and args.output_format == "json":
            with open(args.output_file, "a", encoding="utf-8") as f:
                f.write("]")
        elif args.output_format == "json":
            print("]")


def main(argv: Optional[List] = None):
    """Run the newspaper CLI command."""
    parser = get_arparse()

    args = parser.parse_args(argv)

    try:
        run(args)
    except KeyboardInterrupt:
        sys.exit("\nERROR: Interrupted by user, exiting...\n")


__all__ = ["main"]
