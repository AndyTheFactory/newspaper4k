"""Selector-based HTML filtering inspired by uBlock static cosmetic filters."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from lxml.html import HtmlElement

import newspaper.parsers as parsers

log = logging.getLogger(__name__)


@dataclass
class FilterRule:
    """Represents one selector filter rule."""

    hosts: tuple[str, ...]
    selector: str
    action: str
    value: str | None = None

    @property
    def dedupe_key(self) -> tuple[tuple[str, ...], str]:
        return (self.hosts, self.selector)


class HtmlFilterExtractor:
    """Loads and applies selector rules to an HTML element tree.

    Rule syntax (subset inspired by uBlock cosmetic filters):
      - `##.ad-banner` (global remove)
      - `example.com##.promo` (domain/host remove)
      - `example.com##.promo:replace(<span>replacement</span>)`
      - `example.com##.promo:func(custom_name)`

    File scoping:
      - `all.txt` / `global.txt` / `*.txt` -> global
      - `<domain-or-host>.txt` -> rules default to that host/domain when host part is omitted.
    """

    _RE_REPLACE = re.compile(r"^(?P<selector>.+):replace\((?P<value>.*)\)\s*$")
    _RE_FUNC = re.compile(r"^(?P<selector>.+):func\((?P<value>.*)\)\s*$")
    _RE_REMOVE = re.compile(r"^(?P<selector>.+):remove\s*$")

    def __init__(
        self,
        default_rules_folder: str | Path | None,
        custom_rule_folders: list[str] | None = None,
        custom_functions: dict | None = None,
    ):
        self.default_rules_folder = Path(default_rules_folder) if default_rules_folder else None
        self.custom_rule_folders = [Path(folder) for folder in (custom_rule_folders or []) if folder]
        self.custom_functions = custom_functions or {}
        self._rules = self._load_rules()

    def apply(self, doc: HtmlElement, source_url: str | None = None) -> HtmlElement:
        """Apply matching rules to the document and return filtered doc."""
        if not self._rules:
            return doc

        host = self._get_host(source_url)
        matching_rules = [rule for rule in self._rules if self._matches_host(host, rule.hosts)]
        if not matching_rules:
            return doc

        soup = BeautifulSoup(parsers.node_to_string(doc), "html.parser")
        for rule in matching_rules:
            for element in soup.select(rule.selector):
                self._apply_rule_to_element(element, rule, soup)

        filtered_doc = parsers.fromstring(str(soup))
        return filtered_doc if filtered_doc is not None else doc

    def _load_rules(self) -> list[FilterRule]:
        rules_by_key: dict[tuple[tuple[str, ...], str], FilterRule] = {}
        folders = []
        if self.default_rules_folder:
            folders.append(self.default_rules_folder)
        folders.extend(self.custom_rule_folders)

        for folder in folders:
            if not folder.exists() or not folder.is_dir():
                continue
            for rule_file in sorted(path for path in folder.iterdir() if path.is_file()):
                file_scope_hosts = self._hosts_from_filename(rule_file.stem)
                for rule in self._parse_rule_file(rule_file, file_scope_hosts):
                    rules_by_key[rule.dedupe_key] = rule
        return list(rules_by_key.values())

    def _parse_rule_file(self, file_path: Path, file_scope_hosts: tuple[str, ...]) -> list[FilterRule]:
        rules: list[FilterRule] = []
        content = file_path.read_text(encoding="utf-8")
        for raw_line in content.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("!") or (line.startswith("#") and not line.startswith("##")):
                continue
            if "##" not in line:
                continue

            host_part, raw_selector = line.split("##", 1)
            selector, action, value = self._parse_selector_action(raw_selector.strip())
            if not selector:
                continue

            hosts = self._parse_hosts(host_part.strip())
            if not hosts:
                hosts = file_scope_hosts
            if not hosts:
                hosts = ("*",)

            rules.append(FilterRule(hosts=hosts, selector=selector, action=action, value=value))
        return rules

    def _parse_selector_action(self, raw_selector: str) -> tuple[str, str, str | None]:
        for pattern, action in ((self._RE_REPLACE, "replace"), (self._RE_FUNC, "func"), (self._RE_REMOVE, "remove")):
            match = pattern.match(raw_selector)
            if match:
                value = match.groupdict().get("value")
                return match.group("selector").strip(), action, value.strip() if value else None
        return raw_selector.strip(), "remove", None

    def _parse_hosts(self, host_part: str) -> tuple[str, ...]:
        if not host_part:
            return ()
        hosts = []
        for host in host_part.split(","):
            normalized = self._normalize_host(host)
            if normalized:
                hosts.append(normalized)
        return tuple(hosts)

    def _normalize_host(self, host: str) -> str:
        value = host.strip().lower()
        if not value or value in {"*", "all", "global"}:
            return "*"
        value = value.removeprefix("||").removesuffix("^")
        value = value.strip(".")
        return value

    def _hosts_from_filename(self, filename_stem: str) -> tuple[str, ...]:
        normalized = self._normalize_host(filename_stem)
        if normalized == "*":
            return ("*",)
        if normalized and "." in normalized:
            return (normalized,)
        return ("*",)

    def _get_host(self, source_url: str | None) -> str:
        if not source_url:
            return ""
        parsed = urlparse(source_url)
        return (parsed.hostname or "").lower()

    def _matches_host(self, host: str, rule_hosts: tuple[str, ...]) -> bool:
        if "*" in rule_hosts:
            return True
        if not host:
            return False
        for rule_host in rule_hosts:
            if host == rule_host or host.endswith(f".{rule_host}"):
                return True
        return False

    def _apply_rule_to_element(self, element, rule: FilterRule, soup: BeautifulSoup):
        if rule.action == "remove":
            element.decompose()
            return

        if rule.action == "replace":
            replacement_html = rule.value or ""
            replacement_nodes = BeautifulSoup(replacement_html, "html.parser").contents
            if not replacement_nodes:
                element.decompose()
                return
            element.insert_before(*replacement_nodes)
            element.decompose()
            return

        if rule.action == "func":
            function_name = (rule.value or "").strip()
            callback = self.custom_functions.get(function_name)
            if not callable(callback):
                log.debug("No custom filter function found for %s", function_name)
                return
            result = callback(element)
            if isinstance(result, str):
                replacement_nodes = BeautifulSoup(result, "html.parser").contents
                if replacement_nodes:
                    element.insert_before(*replacement_nodes)
                    element.decompose()
