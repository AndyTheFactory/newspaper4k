# pytest file for testing the article class


from newspaper.article import Article


class TestArticle:
    def test_issue_457_googleblog(self):
        """Test that research.googleblog.com articles are parsed correctly.

        Originally reported at https://github.com/codelucas/newspaper/issues/457
        Articles from research.googleblog.com (now blog.research.google.com)
        were only returning "The latest news from Research at Google" instead
        of the actual article content.
        """
        urls = [
            "https://blog.research.google.com/2017/08/launching-speech-commands-dataset.html",
            "https://blog.research.google.com/2017/08/transformer-novel-neural-network.html",
        ]
        for url in urls:
            article = Article(url=url, fetch_images=False)
            article.download()
            article.parse()

            assert len(article.text) > 200, (
                f"Article text for {url} is too short: {article.text!r}"
            )
            assert "The latest news from Research at Google" not in article.text, (
                f"Article text for {url} only contains the site tagline, "
                "not the actual article content"
            )

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
        url = "https://nyti.ms/4K9g6u"  # New York Times link shortener
        article = Article(url=url)
        article.download()

        assert len(article.history) > 0
