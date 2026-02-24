import json

import pytest

from newspaper.cli import main


class TestCLI:
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
