from newspaper.google_news import GoogleNewsSource


class FakeFeedData:
    status = 200
    entries = []


def test_google_news_proxy_format(mocker):
    """GoogleNewsSource should pass the full proxies dict to gnews.GNews, not just the address string."""
    proxy_dict = {"http": "http://proxy.example.com:8080"}

    source = GoogleNewsSource(proxies=proxy_dict)

    assert source.gnews._proxy == proxy_dict


def test_google_news_proxy_used_in_feedparser(mocker):
    """When proxies are provided, feedparser should be called with a ProxyHandler."""
    import urllib.request

    proxy_dict = {"http": "http://proxy.example.com:8080"}

    mock_feedparser = mocker.patch("gnews.gnews.feedparser.parse", return_value=FakeFeedData())

    source = GoogleNewsSource(proxies=proxy_dict)
    source.build(top_news=True)

    assert mock_feedparser.called
    call_kwargs = mock_feedparser.call_args
    handlers = call_kwargs.kwargs.get("handlers") or (call_kwargs.args[2] if len(call_kwargs.args) > 2 else None)
    assert handlers is not None
    assert any(isinstance(h, urllib.request.ProxyHandler) for h in handlers)


def test_google_news_no_proxy(mocker):
    """When no proxies are provided, gnews._proxy should be None."""
    source = GoogleNewsSource()
    assert source.gnews._proxy is None
