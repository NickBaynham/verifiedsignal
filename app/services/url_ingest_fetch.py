"""HTTP GET with size limits (used by the URL ingest worker).

Security: the intake API validates the *initial* URL (scheme, host resolution, private IP block).
When ``URL_FETCH_FOLLOW_REDIRECTS`` is true, ``httpx`` may follow redirects to hosts that were
**not** re-validated — a known SSRF class (redirect to metadata IP, loopback, etc.). For strict
network boundaries set ``URL_FETCH_FOLLOW_REDIRECTS=false`` or run URL ingest only for trusted
catalogs; long-term hardening is per-hop validation or a same-connection DNS re-check.
"""

from __future__ import annotations

import logging

import httpx

from app.core.config import Settings

log = logging.getLogger("verifiedsignal.url_fetch")


def fetch_url_bytes(
    url: str,
    settings: Settings,
    *,
    client: httpx.Client | None = None,
) -> tuple[bytes, str | None]:
    """
    Stream GET `url` into memory up to `url_fetch_max_bytes`.

    Returns (body, content_type) where content_type is from the final response header.
    """
    own_client = client is None
    max_b = settings.url_fetch_max_bytes
    timeout = httpx.Timeout(
        settings.url_fetch_timeout_s, connect=min(10.0, settings.url_fetch_timeout_s)
    )

    if client is None:
        client = httpx.Client(
            timeout=timeout,
            follow_redirects=settings.url_fetch_follow_redirects,
            max_redirects=settings.url_fetch_max_redirects,
        )

    try:
        chunks: list[bytes] = []
        total = 0
        content_type: str | None = None
        with client.stream("GET", url) as resp:
            resp.raise_for_status()
            content_type = resp.headers.get("content-type")
            if content_type and ";" in content_type:
                content_type = content_type.split(";", 1)[0].strip() or None
            for block in resp.iter_bytes(chunk_size=64 * 1024):
                total += len(block)
                if total > max_b:
                    raise ValueError(f"response exceeds max size of {max_b} bytes")
                chunks.append(block)
        return b"".join(chunks), content_type
    except httpx.HTTPStatusError as e:
        log.warning("url_fetch_http_error url=%s status=%s", url, e.response.status_code)
        raise ValueError(f"HTTP {e.response.status_code}") from e
    except httpx.RequestError as e:
        log.warning("url_fetch_request_error url=%s err=%s", url, e)
        raise ValueError(f"request failed: {e}") from e
    finally:
        if own_client:
            client.close()
