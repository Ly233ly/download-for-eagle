from __future__ import annotations

import ipaddress
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from .constants import TRACKING_QUERY_KEYS


class InvalidPageUrl(ValueError):
    pass


def normalize_domain(value: str) -> str:
    candidate = value.strip().lower().rstrip(".")
    if "://" in candidate:
        candidate = urlsplit(candidate).hostname or ""
    elif "/" in candidate:
        candidate = urlsplit(f"https://{candidate}").hostname or ""
    elif ":" in candidate and not candidate.startswith("["):
        candidate = candidate.split(":", 1)[0]

    if not candidate:
        raise InvalidPageUrl("网站域名为空")

    try:
        ipaddress.ip_address(candidate)
        return candidate
    except ValueError:
        pass

    try:
        ascii_domain = candidate.encode("idna").decode("ascii")
    except UnicodeError as exc:
        raise InvalidPageUrl("网站域名格式无效") from exc

    labels = ascii_domain.split(".")
    if any(not label or len(label) > 63 for label in labels):
        raise InvalidPageUrl("网站域名格式无效")
    if any(label.startswith("-") or label.endswith("-") for label in labels):
        raise InvalidPageUrl("网站域名格式无效")
    return ascii_domain


def clean_page_url(raw_url: str) -> str:
    raw_url = raw_url.strip()
    parts = urlsplit(raw_url)
    if parts.scheme.lower() not in {"http", "https"}:
        raise InvalidPageUrl("只支持 http 或 https 网页地址")
    if not parts.hostname:
        raise InvalidPageUrl("网页地址缺少网站域名")
    if parts.username or parts.password:
        raise InvalidPageUrl("网页地址不能包含账号信息")

    domain = normalize_domain(parts.hostname)
    port = parts.port
    default_port = (parts.scheme.lower() == "http" and port == 80) or (
        parts.scheme.lower() == "https" and port == 443
    )
    netloc = domain if port is None or default_port else f"{domain}:{port}"

    filtered_query = []
    for key, value in parse_qsl(parts.query, keep_blank_values=True):
        lowered = key.lower()
        if lowered.startswith("utm_") or lowered in TRACKING_QUERY_KEYS:
            continue
        filtered_query.append((key, value))

    path = parts.path or "/"
    return urlunsplit(
        (parts.scheme.lower(), netloc, path, urlencode(filtered_query, doseq=True), "")
    )


def domain_from_url(url: str) -> str:
    parts = urlsplit(url)
    if not parts.hostname:
        raise InvalidPageUrl("网页地址缺少网站域名")
    return normalize_domain(parts.hostname)
