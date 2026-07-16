"""SSRF hardening for the admin ingest fetcher (issue #44).

The fetcher must refuse non-https URLs, hosts that resolve to private / loopback
/ link-local (cloud-metadata) addresses, and — when configured — hosts outside
the domain allowlist. Redirects are followed manually so each hop is checked.
"""
import socket

import pytest

from ingest import fetch


def _resolve_to(monkeypatch, ip: str):
    """Force DNS resolution to a fixed IP so tests never touch the network."""
    def fake_getaddrinfo(host, port, *args, **kwargs):
        return [(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", (ip, port or 443))]
    monkeypatch.setattr(fetch.socket, "getaddrinfo", fake_getaddrinfo)


def test_rejects_non_https():
    with pytest.raises(fetch.FetchError):
        fetch._assert_url_safe("http://carleton.ca/page")


@pytest.mark.parametrize("ip", ["127.0.0.1", "10.0.0.5", "192.168.1.1", "169.254.169.254", "::1"])
def test_rejects_private_and_metadata_ips(monkeypatch, ip):
    _resolve_to(monkeypatch, ip)
    with pytest.raises(fetch.FetchError):
        fetch._assert_url_safe("https://internal.example.com/whatever")


def test_allows_public_ip(monkeypatch):
    _resolve_to(monkeypatch, "142.130.1.1")  # a public address
    # Should not raise.
    fetch._assert_url_safe("https://carleton.ca/courses")


def test_domain_allowlist_blocks_offlist_host(monkeypatch):
    monkeypatch.setattr(fetch, "_ALLOWED_DOMAINS", ["carleton.ca"])
    _resolve_to(monkeypatch, "142.130.1.1")
    with pytest.raises(fetch.FetchError):
        fetch._assert_url_safe("https://evil.example.com/x")


def test_domain_allowlist_allows_subdomain(monkeypatch):
    monkeypatch.setattr(fetch, "_ALLOWED_DOMAINS", ["carleton.ca"])
    _resolve_to(monkeypatch, "142.130.1.1")
    fetch._assert_url_safe("https://calendar.carleton.ca/deadlines")  # no raise


def test_ip_is_public_helper():
    assert fetch._ip_is_public("142.130.1.1") is True
    assert fetch._ip_is_public("127.0.0.1") is False
    assert fetch._ip_is_public("169.254.169.254") is False
    assert fetch._ip_is_public("not-an-ip") is False


def test_get_follows_redirect_and_revalidates(monkeypatch):
    """A public host that 302-redirects to a metadata IP is blocked mid-chain."""
    _resolve_to(monkeypatch, "142.130.1.1")  # first host resolves public
    monkeypatch.setattr(fetch, "_polite_wait", lambda url: None)

    class FakeResp:
        def __init__(self, status, location=None):
            self.status_code = status
            self.headers = {"location": location} if location else {}
            self.is_redirect = status in (301, 302, 303, 307, 308) and status != 308
            self.is_permanent_redirect = status == 308

    def fake_get(url, **kwargs):
        # Always 302 to the metadata host.
        return FakeResp(302, location="https://169.254.169.254/latest/meta-data/")

    monkeypatch.setattr(fetch.requests, "get", fake_get)

    # When the redirect target resolves to the metadata address, revalidation
    # must reject it. Point resolution at the metadata IP for the second hop.
    def resolve_meta(host, port, *a, **k):
        ip = "169.254.169.254" if "169.254" in host else "142.130.1.1"
        return [(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", (ip, port or 443))]
    monkeypatch.setattr(fetch.socket, "getaddrinfo", resolve_meta)

    with pytest.raises(fetch.FetchError):
        fetch._get("https://carleton.ca/redirector", retries=0)
