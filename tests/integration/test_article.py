# pytest file for testing the article class


from newspaper.article import Article


class TestArticle:
    def test_follow_read_more_button(self, read_more_fixture):
        for test_case in read_more_fixture:
            article = Article(
                url=test_case["url"],
                fetch_images=False,
                read_more_link=test_case["selector_button"],
                browser_user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                    " (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                ),
                header={
                    "Referer": test_case["url"],
                    "Accept": (
                        "text/html,application/xhtml+xml,"
                        "application/xml;q=0.9,image/avif,"
                        "image/webp,image/apng,*/*;q=0.8,"
                        "application/signed-exchange;v=b3;q=0.7"
                    ),
                },
            )
            article.download()
            article.parse()

            assert len(article.text) > test_case["min_text_length"], (
                f"Button for {test_case['url']} not followed correctly"
            )

    def test_redirect_url(self):
        url = "https://shotcut.in/YrVZ"
        article = Article(url=url)
        article.download()

        assert len(article.history) > 0
