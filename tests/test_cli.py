import os
import json
import pytest
from newspaper.cli import main


@pytest.fixture
def output_file(tmp_path):
    return {
        "json": tmp_path / "output_file.json",
        "csv": tmp_path / "output_file.csv",
    }


class TestCLI:
    def test_cli_no_args(self):
        with pytest.raises(SystemExit):
            main([])

    def test_input_html(self, output_file):
        main(
            [
                "--url=http://www.test.com",
                "--html-from-file=tests/data/html/cnn_001.html",
                "--output-format=json",
                "--output-file",
                str(output_file["json"]),
                "--max-nr-keywords",
                "35",
            ]
        )

        assert output_file["json"].exists()

        json_data = json.loads(output_file["json"].read_text())[0]

        json_data2 = json.load(
            open("tests/data/metadata/cnn_001.json", "r", encoding="utf-8")
        )

        for key in json_data2:
            if key in ["url", "text_cleaned", "images"]:
                continue
            if isinstance(json_data[key], list):
                json_data[key] = sorted(json_data[key])
            if isinstance(json_data2[key], list):
                json_data2[key] = sorted(json_data2[key])

            if key == "publish_date":
                json_data[key] = json_data[key][:10]
                json_data2[key] = json_data2[key][:10]

            assert json_data[key] == json_data2[key], f"Test failed on key: {key}"

    def test_nlp(self, output_file):
        main(
            [
                "--url=http://www.test.com",
                "--html-from-file=tests/data/html/cnn_001.html",
                "--output-format=json",
                "--output-file",
                str(output_file["json"]),
                "--max-nr-keywords",
                "35",
                "--skip-nlp",
            ]
        )

        assert output_file["json"].exists()

        json_data = json.loads(output_file["json"].read_text())[0]

        assert json_data["keywords"] == []
        assert json_data["summary"] == ""

    # Skip if GITHUB_ACTIONS
    @pytest.mark.skipif("GITHUB_ACTIONS" in os.environ, reason="Skip if GITHUB_ACTIONS")
    def test_cli_output_format(self, output_file):
        with pytest.raises(SystemExit):
            main(["--output-format", "invalid"])

        main(
            [
                "--url=https://edition.cnn.com/2023/11/16/entertainment/robert-pattinson-inflatable-boat-intl-scli/index.html",
                "--output-format=json",
                "--output-file",
                str(output_file["json"]),
            ]
        )

        assert output_file["json"].exists()

        json_data = json.loads(output_file["json"].read_text())[0]

        assert (
            json_data["url"]
            == "https://edition.cnn.com/2023/11/16/entertainment/robert-pattinson-inflatable-boat-intl-scli/index.html"
        )
        assert json_data["language"] == "en"
        assert len(json_data["authors"]) > 0
        assert json_data["top_image"]
        assert len(json_data["keywords"]) == 10
        assert json_data["publish_date"][:10] == "2023-11-16"
        assert len(json_data["summary"]) > 100
        assert len(json_data["text"]) > 1000

        main(
            [
                "--url=https://edition.cnn.com/2023/11/16/entertainment/robert-pattinson-inflatable-boat-intl-scli/index.html",
                "--output-format=csv",
                "--output-file",
                str(output_file["csv"]),
            ]
        )

        assert output_file["csv"].exists()
        assert len(output_file["csv"].read_text().splitlines()) > 2
