"""Validate submitted URLs before persisting rows or fetching (SSRF mitigation)."""

from __future__ import annotations

import ipaddress
import re
import socket
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from app.core.config import Settings
from app.services.exceptions import IntakeValidationError


def _normalize_url_parts(scheme: str, netloc: str, path: str, query: str) -> str:
    """Rebuild URL with sorted query keys for stable storage (fragment stripped for intake)."""
    pairs = parse_qsl(query, keep_blank_values=True)
    pairs.sort(key=lambda x: x[0])
    q = urlencode(pairs, doseq=True)
    return urlunsplit((scheme.lower(), netloc, path or "", q, ""))


def validate_url_for_ingest(raw: str, settings: Settings) -> str:
    """
    Parse URL, reject unsafe schemes and embedded credentials, resolve host to IPs
    and block private/link-local/loopback when `url_fetch_block_private_networks` is on.

    Returns a normalized URL string suitable for storage in `document_sources.locator`.
    """
    if not raw or not raw.strip():
        raise IntakeValidationError("url is required")

    text = raw.strip()
    if len(text) > 8192:
        raise IntakeValidationError("url is too long")

    parts = urlsplit(text)
    scheme = (parts.scheme or "").lower()
    if scheme not in ("http", "https"):
        raise IntakeValidationError("URL scheme must be http or https")
    if scheme == "http" and not settings.allow_http_url_ingest:
        raise IntakeValidationError(
            "http URLs are disabled (set ALLOW_HTTP_URL_INGEST=true for dev)"
        )

    if parts.username is not None or parts.password is not None:
        raise IntakeValidationError("URL must not contain embedded credentials")

    host = parts.hostname
    if not host:
        raise IntakeValidationError("URL host is required")

    port = parts.port
    if port is None:
        port = 443 if scheme == "https" else 80

    # Literal IP first. IntakeValidationError subclasses ValueError; only catch parse failures.
    try:
        parsed_ip = ipaddress.ip_address(host)
    except ValueError:
        if settings.url_fetch_block_private_networks:
            _assert_hostname_resolves_to_allowed_ips(host, port)
    else:
        if settings.url_fetch_block_private_networks and _ip_disallowed(parsed_ip):
            raise IntakeValidationError("URL target address is not allowed")

    normalized = _normalize_url_parts(scheme, parts.netloc, parts.path, parts.query)
    return normalized


def _ip_disallowed(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    return bool(
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
        or (ip.version == 4 and ip.compressed.startswith("0."))
    )


def _assert_hostname_resolves_to_allowed_ips(host: str, port: int) -> None:
    try:
        infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except socket.gaierror as e:
        raise IntakeValidationError(f"could not resolve URL host: {e}") from e

    if not infos:
        raise IntakeValidationError("could not resolve URL host")

    for info in infos:
        sockaddr = info[4]
        ip_str = sockaddr[0]
        if not isinstance(ip_str, str):
            continue
        if ":" in ip_str and re.match(r"^[0-9a-fA-F:.]+$", ip_str):
            try:
                ip = ipaddress.ip_address(ip_str)
            except ValueError:
                continue
        else:
            try:
                ip = ipaddress.ip_address(ip_str)
            except ValueError:
                continue
        if _ip_disallowed(ip):
            raise IntakeValidationError("URL resolves to a disallowed address")
