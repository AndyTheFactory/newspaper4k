# ruff: noqa: D100, D103
import pytest
import requests

from newspaper import network
from newspaper.configuration import Configuration
from newspaper.exceptions import PrivateHostError


@pytest.fixture(autouse=True)
def fake_dns(mocker):
    names = {"internal.test": "10.0.0.5", "localhost": "127.0.0.1"}

    def getaddrinfo(host, port, *args, **kwargs):
        ip = names.get(host, host if host[0].isdigit() or ":" in host else "93.184.216.34")
        return [(2, 1, 6, "", (ip, port))]

    mocker.patch("newspaper.network.socket.getaddrinfo", side_effect=getaddrinfo)


def make_config(allow_private=False):
    config = Configuration()
    config.allow_binary_content = True
    config.allow_private_hosts = allow_private
    return config


@pytest.mark.parametrize(
    "url",
    ["http://127.0.0.1:8000/", "http://localhost/", "http://169.254.169.254/latest/", "http://internal.test/"],
)
def test_do_request_blocks_private_hosts(mocker, url):
    session = mocker.patch("newspaper.network.session")

    with pytest.raises(PrivateHostError):
        network.do_request(url, make_config())
    session.get.assert_not_called()


def test_do_request_allows_private_hosts_when_enabled(mocker):
    session = mocker.patch("newspaper.network.session")

    network.do_request("http://127.0.0.1:8000/", make_config(allow_private=True))
    session.get.assert_called_once()
    assert "hooks" not in session.get.call_args.kwargs


def test_do_request_registers_redirect_guard(mocker):
    session = mocker.patch("newspaper.network.session")

    network.do_request("http://example.com/", make_config())
    hooks = session.get.call_args.kwargs["hooks"]["response"]
    assert hooks == [network._block_private_redirect]


def test_redirect_hook_blocks_private_target():
    redirect = requests.Response()
    redirect.status_code = 302
    redirect.url = "http://example.com/a"
    redirect.headers["Location"] = "http://169.254.169.254/latest/meta-data/"

    with pytest.raises(PrivateHostError):
        network._block_private_redirect(redirect)


def test_redirect_hook_allows_relative_redirect_to_public_host():
    redirect = requests.Response()
    redirect.status_code = 302
    redirect.url = "http://example.com/a"
    redirect.headers["Location"] = "/b"

    assert network._block_private_redirect(redirect) is redirect


def test_multithread_request_returns_none_for_private_urls(mocker):
    mocker.patch("newspaper.network.session")

    results = network.multithread_request(["http://127.0.0.1/", "http://internal.test/"], make_config())
    assert results == [None, None]
