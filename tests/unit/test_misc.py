import newspaper


def test_popular_urls():
    popular_urls = newspaper.popular_urls()
    assert len(popular_urls) > 0


def test_languages():
    language_list = newspaper.valid_languages()
    assert len(language_list) > 20
