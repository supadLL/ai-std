import socket

import httpx
import pytest

from app.web_page_fetcher import WebPageFetchError, fetch_web_page, validate_web_page_url


def _public_dns(*args, **kwargs):
    return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))]


def test_fetch_web_page_downloads_html(monkeypatch):
    monkeypatch.setattr(socket, "getaddrinfo", _public_dns)

    def handler(request):
        assert str(request.url) == "https://example.com/docs/intro"
        return httpx.Response(
            200,
            headers={"content-type": "text/html; charset=utf-8"},
            content=b"<html><body><main><h1>Intro</h1></main></body></html>",
        )

    client = httpx.Client(transport=httpx.MockTransport(handler), follow_redirects=True)

    fetched = fetch_web_page(
        url="https://example.com/docs/intro",
        client=client,
        max_bytes=1024,
    )

    assert fetched.final_url == "https://example.com/docs/intro"
    assert fetched.content_type == "text/html"
    assert fetched.filename.endswith(".html")
    assert b"Intro" in fetched.content


def test_validate_web_page_url_rejects_localhost():
    with pytest.raises(WebPageFetchError):
        validate_web_page_url("http://localhost/admin")


def test_validate_web_page_url_rejects_private_resolved_host(monkeypatch):
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *args, **kwargs: [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.0.0.5", 80))],
    )

    with pytest.raises(WebPageFetchError):
        validate_web_page_url("https://internal.example.com/wiki")


def test_validate_web_page_url_rejects_non_http_scheme():
    with pytest.raises(WebPageFetchError):
        validate_web_page_url("file:///etc/passwd")


def test_fetch_web_page_rejects_non_html(monkeypatch):
    monkeypatch.setattr(socket, "getaddrinfo", _public_dns)
    client = httpx.Client(
        transport=httpx.MockTransport(
            lambda request: httpx.Response(
                200,
                headers={"content-type": "application/json"},
                content=b'{"ok": true}',
            )
        ),
        follow_redirects=True,
    )

    with pytest.raises(WebPageFetchError):
        fetch_web_page(url="https://example.com/data.json", client=client)


def test_fetch_web_page_rejects_large_response(monkeypatch):
    monkeypatch.setattr(socket, "getaddrinfo", _public_dns)
    client = httpx.Client(
        transport=httpx.MockTransport(
            lambda request: httpx.Response(
                200,
                headers={"content-type": "text/html", "content-length": "99"},
                content=b"<html></html>",
            )
        ),
        follow_redirects=True,
    )

    with pytest.raises(WebPageFetchError):
        fetch_web_page(url="https://example.com/large", client=client, max_bytes=10)
