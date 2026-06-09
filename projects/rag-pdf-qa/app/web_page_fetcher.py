from dataclasses import dataclass
from hashlib import sha256
import ipaddress
import re
import socket
from urllib.parse import urlparse

import httpx


HTML_CONTENT_TYPES = {"text/html", "application/xhtml+xml"}
BLOCKED_HOSTNAMES = {"localhost"}


@dataclass(frozen=True)
class FetchedWebPage:
    url: str
    final_url: str
    filename: str
    content: bytes
    content_type: str
    status_code: int


class WebPageFetchError(RuntimeError):
    pass


def fetch_web_page(
    *,
    url: str,
    timeout_seconds: float = 10.0,
    max_bytes: int = 2 * 1024 * 1024,
    allow_private_hosts: bool = False,
    client: httpx.Client | None = None,
) -> FetchedWebPage:
    normalized_url = validate_web_page_url(url, allow_private_hosts=allow_private_hosts)
    close_client = client is None
    http_client = client or httpx.Client(
        timeout=timeout_seconds,
        follow_redirects=True,
        max_redirects=3,
        headers={"User-Agent": "rag-pdf-qa-web-fetcher/1.0"},
    )
    try:
        with http_client.stream("GET", normalized_url) as response:
            final_url = validate_web_page_url(
                str(response.url),
                allow_private_hosts=allow_private_hosts,
            )
            if response.status_code >= 400:
                raise WebPageFetchError(f"Web page returned HTTP {response.status_code}")

            content_type = _content_type(response.headers.get("content-type", ""))
            if content_type not in HTML_CONTENT_TYPES:
                raise WebPageFetchError("Only HTML web pages can be indexed from URLs")

            content_length = _parse_content_length(response.headers.get("content-length"))
            if content_length is not None and content_length > max_bytes:
                raise WebPageFetchError(f"Web page is too large; max size is {max_bytes} bytes")

            content = _read_limited_response(response, max_bytes=max_bytes)
            if not content.strip():
                raise WebPageFetchError("Web page response is empty")

            return FetchedWebPage(
                url=normalized_url,
                final_url=final_url,
                filename=_filename_from_url(final_url),
                content=content,
                content_type=content_type,
                status_code=response.status_code,
            )
    except httpx.HTTPError as exc:
        raise WebPageFetchError(f"Failed to fetch web page: {exc}") from exc
    finally:
        if close_client:
            http_client.close()


def validate_web_page_url(url: str, *, allow_private_hosts: bool = False) -> str:
    parsed = urlparse((url or "").strip())
    if parsed.scheme not in {"http", "https"}:
        raise WebPageFetchError("Only http and https URLs are supported")
    if not parsed.hostname:
        raise WebPageFetchError("URL host is required")

    host = parsed.hostname.strip().lower()
    if not allow_private_hosts:
        _reject_unsafe_host(host)

    return parsed.geturl()


def _reject_unsafe_host(host: str) -> None:
    if host in BLOCKED_HOSTNAMES or host.endswith(".localhost"):
        raise WebPageFetchError("Private or local URLs are not allowed")

    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        address = None
    if address is not None:
        _reject_unsafe_ip(address)
        return

    try:
        resolved_addresses = socket.getaddrinfo(host, None, proto=socket.IPPROTO_TCP)
    except socket.gaierror as exc:
        raise WebPageFetchError(f"Could not resolve URL host {host!r}") from exc

    if not resolved_addresses:
        raise WebPageFetchError(f"Could not resolve URL host {host!r}")

    for address_info in resolved_addresses:
        sockaddr = address_info[4]
        if not sockaddr:
            continue
        ip_text = str(sockaddr[0])
        try:
            _reject_unsafe_ip(ipaddress.ip_address(ip_text))
        except ValueError as exc:
            raise WebPageFetchError(f"Could not validate resolved address {ip_text!r}") from exc


def _reject_unsafe_ip(address: ipaddress.IPv4Address | ipaddress.IPv6Address) -> None:
    if (
        address.is_loopback
        or address.is_private
        or address.is_link_local
        or address.is_multicast
        or address.is_reserved
        or address.is_unspecified
    ):
        raise WebPageFetchError("Private or local URLs are not allowed")


def _content_type(value: str) -> str:
    return value.split(";", 1)[0].strip().lower()


def _parse_content_length(value: str | None) -> int | None:
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _read_limited_response(response: httpx.Response, *, max_bytes: int) -> bytes:
    chunks: list[bytes] = []
    total = 0
    for chunk in response.iter_bytes():
        total += len(chunk)
        if total > max_bytes:
            raise WebPageFetchError(f"Web page is too large; max size is {max_bytes} bytes")
        chunks.append(chunk)
    return b"".join(chunks)


def _filename_from_url(url: str) -> str:
    parsed = urlparse(url)
    host = parsed.hostname or "web-page"
    path = parsed.path.strip("/") or "index"
    stem = f"{host}-{path}"
    if parsed.query:
        stem = f"{stem}-{sha256(parsed.query.encode('utf-8')).hexdigest()[:8]}"
    slug = re.sub(r"[^a-zA-Z0-9._-]+", "-", stem).strip("-._")
    if not slug:
        slug = "web-page"
    digest = sha256(url.encode("utf-8")).hexdigest()[:12]
    return f"{slug[:120]}-{digest}.html"
