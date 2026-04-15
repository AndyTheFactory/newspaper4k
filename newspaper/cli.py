"""Command line interface for the newspaper package."""

import argparse
import asyncio
import csv
import io
import logging
import sys
from pathlib import Path
from typing import Any

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

    url_group.add_argument("--url", "-u", type=str, help="The URL of the article to download and parse.")
    url_group.add_argument(
        "--urls-from-file",
        "-uf",
        type=str,
        help="The file containing the URLs of the articles to download and parse.",
    )
    url_group.add_argument("--urls-from-stdin", "-us", action="store_true", help="Read URLs from stdin.")
    parser.add_argument(
        "--html-from-file",
        "-hf",
        type=str,
        help=("The HTML file to parse. This will not download the article, it will parse the HTML file directly."),
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
    parser.add_argument("--output-file", "-o", type=str, help="The file to write the parsed article to.")
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
        help=("The cookies to use when downloading the article. The format is: cookie1=value1; cookie2=value2; ..."),
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
    parser.add_argument("--skip-nlp", action="store_true", help="Whether to skip the NLP step.")
    parser.add_argument(
        "--sync",
        action="store_true",
        help=(
            "Use the synchronous (requests-based) download path instead of the default"
            " async (httpx-based) path. Useful for environments where asyncio is not"
            " available or for backward-compatibility testing."
        ),
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
    res: dict[str, Any] = {}
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


def _collect_urls(args: argparse.Namespace) -> list[str]:
    """Return the list of target URLs from CLI arguments."""
    if args.urls_from_file:
        with open(args.urls_from_file, encoding="utf-8") as f:
            return f.readlines()
    if args.urls_from_stdin:
        return sys.stdin.readlines()
    return [args.url]


def _open_output(args: argparse.Namespace) -> None:
    """Create/truncate the output file and write the JSON opening bracket."""
    if args.output_file:
        logger.info("Writing output to file: %s", args.output_file)
        with open(args.output_file, "w", encoding="utf-8") as f:
            _ = f.write("[") if args.output_format == "json" else f.write("")
    elif args.output_format == "json":
        print("[", end="")


def _write_output(args: argparse.Namespace, txt: str) -> None:
    """Append *txt* to the output file or stdout."""
    if args.output_file:
        with open(args.output_file, "a", encoding="utf-8") as f:
            f.write(txt)
    else:
        print(txt)


def _csv_header() -> str:
    with io.StringIO() as f:
        writer = csv.DictWriter(f, fieldnames=settings.article_json_fields)
        writer.writeheader()
        return f.getvalue()


def _csv_string(article_dict: dict) -> str:
    with io.StringIO() as f:
        writer = csv.DictWriter(f, fieldnames=settings.article_json_fields)
        writer.writerow(article_dict)
        return f.getvalue()


def _emit_article(args: argparse.Namespace, article: Any, idx: int, total: int) -> None:
    """Serialise *article* and write it to the configured output."""
    if not args.skip_nlp:
        article.nlp()
    else:
        logger.info("Skipping NLP step.")

    output = article.to_json(as_string=args.output_format == "json")
    if args.output_format == "json":
        if idx < total - 1:
            output += ","
        _write_output(args, output)
    elif args.output_format == "csv":
        if idx == 0:
            _write_output(args, _csv_header())
        _write_output(args, _csv_string(output))
    elif args.output_format == "text":
        _write_output(args, f"{article.title}\n\n")
        _write_output(args, article.text)
    else:
        raise ValueError(f"Unknown output format: {args.output_format}")


def _close_output(args: argparse.Namespace) -> None:
    """Write the JSON closing bracket."""
    if args.output_file and args.output_format == "json":
        with open(args.output_file, "a", encoding="utf-8") as f:
            f.write("]")
    elif args.output_format == "json":
        print("]")


def _run_sync(args: argparse.Namespace, urls: list[str], kwargs: dict) -> None:
    """Legacy sync execution path (used when ``--sync`` is passed)."""
    for idx, url in enumerate(urls):
        logger.info("[sync] Parsing article %d of %d: %s", idx + 1, len(urls), url)
        article = newspaper.article(url=url, **kwargs)
        _emit_article(args, article, idx, len(urls))
        if "input_html" in kwargs:
            del kwargs["input_html"]
    _close_output(args)


async def _run_async(args: argparse.Namespace, urls: list[str], kwargs: dict) -> None:
    """Default async execution path."""
    try:
        from newspaper.async_func.api import async_article  # pylint: disable=import-outside-toplevel
    except ImportError:
        logger.warning(
            "httpx is not installed; falling back to sync mode. Install it with: pip install newspaper4k[async]"
        )
        return _run_sync(args, urls, kwargs)

    input_html = kwargs.pop("input_html", None)
    for idx, url in enumerate(urls):
        logger.info("[async] Parsing article %d of %d: %s", idx + 1, len(urls), url)
        # Only the first URL gets the pre-loaded HTML
        html = input_html if idx == 0 else None
        article = await async_article(url=url.strip(), input_html=html, **kwargs)
        _emit_article(args, article, idx, len(urls))
    _close_output(args)


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

    urls = _collect_urls(args)
    kwargs = get_kwargs(args)
    _open_output(args)

    use_sync = getattr(args, "sync", False)
    if use_sync:
        _run_sync(args, urls, kwargs)
    else:
        asyncio.run(_run_async(args, urls, kwargs))


def main(argv: list | None = None):
    """Run the newspaper CLI command."""
    parser = get_arparse()

    args = parser.parse_args(argv)

    try:
        run(args)
    except KeyboardInterrupt:
        sys.exit("\nERROR: Interrupted by user, exiting...\n")


__all__ = ["main"]
