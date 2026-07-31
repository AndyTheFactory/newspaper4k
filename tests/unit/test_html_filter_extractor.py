from pathlib import Path

from newspaper import parsers
from newspaper.cleaners import DocumentCleaner
from newspaper.configuration import Configuration
from newspaper.extractors.html_filter_extractor import HtmlFilterExtractor


def _write_rule_file(folder: Path, name: str, content: str):
    folder.mkdir(parents=True, exist_ok=True)
    (folder / name).write_text(content, encoding="utf-8")


def test_rule_loading_order_and_deduplication(tmp_path):
    default_rules = tmp_path / "default"
    custom_rules = tmp_path / "custom"

    _write_rule_file(default_rules, "a.txt", "##.promo:remove\n")
    _write_rule_file(default_rules, "z.txt", "##.promo:replace(<span>from-default</span>)\n")
    _write_rule_file(custom_rules, "a.txt", "##.promo:replace(<span>from-custom</span>)\n")

    extractor = HtmlFilterExtractor(default_rules, [str(custom_rules)])
    html = "<div><div class='promo'>old</div></div>"
    doc = parsers.fromstring(html)

    filtered = extractor.apply(doc, source_url="https://example.com/news")
    assert "from-custom" in parsers.node_to_string(filtered)
    assert "from-default" not in parsers.node_to_string(filtered)


def test_file_scope_host_and_global_rules(tmp_path):
    default_rules = tmp_path / "default"

    _write_rule_file(default_rules, "all.txt", "##.global-banner\n")
    _write_rule_file(default_rules, "example.com.txt", "##.host-banner\n")

    extractor = HtmlFilterExtractor(default_rules)
    html = "<div><div class='global-banner'>g</div><div class='host-banner'>h</div></div>"

    doc_for_host = parsers.fromstring(html)
    host_filtered = extractor.apply(doc_for_host, source_url="https://www.example.com/story")
    host_text = parsers.get_text(host_filtered)
    assert "g" not in host_text
    assert "h" not in host_text

    doc_for_other = parsers.fromstring(html)
    other_filtered = extractor.apply(doc_for_other, source_url="https://other.org/story")
    other_text = parsers.get_text(other_filtered)
    assert "g" not in other_text
    assert "h" in other_text


def test_custom_function_rule_application(tmp_path):
    default_rules = tmp_path / "default"
    _write_rule_file(default_rules, "all.txt", "##.widget:func(mark_widget)\n")

    def mark_widget(tag):
        tag["data-filtered"] = "1"
        return None

    extractor = HtmlFilterExtractor(default_rules, custom_functions={"mark_widget": mark_widget})
    doc = parsers.fromstring("<div><span class='widget'>content</span></div>")
    filtered = extractor.apply(doc, source_url="https://example.com")
    output = parsers.node_to_string(filtered)
    assert 'data-filtered="1"' in output


def test_document_cleaner_integration_with_rules(tmp_path):
    rule_dir = tmp_path / "rules"
    _write_rule_file(rule_dir, "all.txt", "##.remove-me\n")

    config = Configuration()
    config.html_filter_rules_default_folder = str(rule_dir)
    config.html_filter_rules_custom_folders = []
    cleaner = DocumentCleaner(config)

    doc = parsers.fromstring("<html><body><div class='remove-me'>ad</div><p>keep</p></body></html>")
    cleaned = cleaner.clean(doc, source_url="https://example.com/article")
    text = parsers.get_text(cleaned)

    assert "ad" not in text
    assert "keep" in text
