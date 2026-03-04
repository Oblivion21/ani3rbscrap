"""Shared utilities for scraper methods."""

import re
from typing import Optional

import config


class SkipMethod(Exception):
    """Raised when a method cannot run at all (not installed, no API key, etc.).

    The chain catches this and moves to the next method immediately — no retries.
    """
    pass


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


# ────────────────────────────────────────────────────────────────
# Cloudflare Turnstile solver (Playwright API — works with
# camoufox, patchright, and vanilla playwright)
# ────────────────────────────────────────────────────────────────

async def solve_turnstile_playwright(page, method_name: str, max_wait: int = 30) -> bool:
    """
    Detect and click the Cloudflare Turnstile checkbox, then wait for the
    challenge to resolve and the real page to load.

    Args:
        page:        Playwright Page object (works with Patchright and Camoufox too).
        method_name: Label for log messages.
        max_wait:    Max seconds to wait for challenge resolution after clicking.

    Returns True if the challenge was solved, False otherwise.
    """
    import asyncio
    import random

    # Give the Turnstile widget time to render
    await asyncio.sleep(2)

    content = await page.content()
    if not is_cloudflare_challenge(content):
        print(f"  [{method_name}] No Cloudflare challenge detected, continuing")
        return True  # no challenge = success

    print(f"  [{method_name}] Cloudflare Turnstile detected, attempting to solve...")

    clicked = False

    # --- Approach 1: find the challenge iframe and click the checkbox inside ---
    for frame in page.frames:
        url = frame.url or ""
        if "challenges.cloudflare.com" not in url:
            continue

        print(f"  [{method_name}] Found Turnstile iframe")

        # Try the checkbox input
        try:
            checkbox = await frame.wait_for_selector(
                "input[type='checkbox']", timeout=8000,
            )
            if checkbox:
                await asyncio.sleep(random.uniform(0.3, 1.0))
                await checkbox.click()
                print(f"  [{method_name}] Clicked Turnstile checkbox")
                clicked = True
                break
        except Exception:
            pass

        # Try any clickable label
        try:
            label = await frame.query_selector("label")
            if label:
                await asyncio.sleep(random.uniform(0.3, 1.0))
                await label.click()
                print(f"  [{method_name}] Clicked Turnstile label")
                clicked = True
                break
        except Exception:
            pass

        # Try the body of the frame (fallback)
        try:
            body = await frame.query_selector("body")
            if body:
                await asyncio.sleep(random.uniform(0.3, 1.0))
                await body.click()
                print(f"  [{method_name}] Clicked Turnstile frame body")
                clicked = True
                break
        except Exception:
            pass

    # --- Approach 2: click the iframe element directly on the parent page ---
    if not clicked:
        for selector in [
            "iframe[src*='challenges.cloudflare.com']",
            ".cf-turnstile iframe",
            "#turnstile-wrapper iframe",
            "iframe[id*='cf-chl']",
        ]:
            try:
                iframe_el = await page.query_selector(selector)
                if iframe_el:
                    bbox = await iframe_el.bounding_box()
                    if bbox:
                        # The checkbox is on the left side of the widget
                        x = bbox["x"] + 32
                        y = bbox["y"] + bbox["height"] / 2
                        await asyncio.sleep(random.uniform(0.3, 1.0))
                        await page.mouse.click(x, y)
                        print(f"  [{method_name}] Clicked Turnstile iframe at ({x:.0f}, {y:.0f})")
                        clicked = True
                        break
            except Exception:
                continue

    if not clicked:
        print(f"  [{method_name}] Could not find Turnstile widget to click")
        return False

    # --- Wait for the challenge to resolve and page to navigate ---
    print(f"  [{method_name}] Waiting for challenge to resolve (up to {max_wait}s)...")
    for i in range(max_wait):
        await asyncio.sleep(1)
        try:
            content = await page.content()
            if not is_cloudflare_challenge(content):
                print(f"  [{method_name}] Challenge solved after {i + 1}s")
                return True
        except Exception:
            # Page might be navigating
            pass

    print(f"  [{method_name}] Challenge did not resolve within {max_wait}s")
    return False
