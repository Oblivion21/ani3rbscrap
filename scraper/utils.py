"""Shared utilities for scraper methods."""

import re
from typing import Optional

import config


def is_cloudflare_challenge(html: str) -> bool:
    """Return True if the HTML is a Cloudflare challenge page, not real content."""
    challenge_markers = [
        "Just a moment",
        "Checking your browser",
        "cf-browser-verification",
        "challenge-platform",
        "cf-turnstile",
    ]
    return any(marker in html for marker in challenge_markers)


def extract_video_url(text: str) -> Optional[str]:
    """Extract the vid3rb mp4 URL from raw text (HTML, HAR, network log, etc.)."""
    pattern = rf'https?://[^\s"\'<>]*{re.escape(config.VIDEO_HOST_PATTERN)}[^\s"\'<>]*{re.escape(config.VIDEO_FILE_EXTENSION)}[^\s"\'<>]*'
    match = re.search(pattern, text)
    return match.group(0) if match else None


def extract_all_video_urls(text: str) -> list[str]:
    """Extract all vid3rb mp4 URLs from text."""
    pattern = rf'https?://[^\s"\'<>]*{re.escape(config.VIDEO_HOST_PATTERN)}[^\s"\'<>]*{re.escape(config.VIDEO_FILE_EXTENSION)}[^\s"\'<>]*'
    return list(set(re.findall(pattern, text)))


def get_proxy_dict() -> Optional[dict]:
    """Build a proxy config dict from config.py settings. Returns None if unset."""
    if not config.PROXY_SERVER:
        return None
    proxy = {"server": config.PROXY_SERVER}
    if config.PROXY_USERNAME:
        proxy["username"] = config.PROXY_USERNAME
    if config.PROXY_PASSWORD:
        proxy["password"] = config.PROXY_PASSWORD
    return proxy
