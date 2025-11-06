import newspaper
from newspaper import Source
from newspaper.article import ArticleDownloadState


class TestSource:
    def test_download_all_articles(self, cnn_source):
        source = Source(cnn_source["url"], verbose=False, memorize_articles=False)
        source.clean_memo_cache()

        source.html = cnn_source["html_content"]
        source.parse()
        source.set_feeds()
        source.download_feeds()  # mthread

        source.generate_articles(limit=30)
        articles = source.download_articles()

        assert len(articles) == 30
        assert all([a.download_state == ArticleDownloadState.SUCCESS for a in articles])  # noqa: C419

    def test_only_homepage(self, cnn_source):
        source = newspaper.build(
            cnn_source["url"],
            only_homepage=True,
            input_html=cnn_source["html_content"],
            memorize_articles=False,
        )

        assert len(source.articles) > 250
