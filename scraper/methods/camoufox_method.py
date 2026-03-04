"""
Step 2 — Camoufox

Firefox-based, immune to the Feb 2025 CDP Chrome detection bug.
Highest stealth of any free tool. Handles JS challenges and Turnstile.
Intercepts network requests to capture the video mp4 URL.
"""

import asyncio
from typing import Optional

import config
from scraper.utils import (
    extract_video_url, is_cloudflare_challenge, get_proxy_dict,
    SkipMethod, solve_turnstile_playwright,
)


METHOD_NAME = "camoufox"


async def scrape(episode_url: str) -> Optional[str]:
    """
    Launch a stealth Firefox browser, navigate to the episode page,
    solve the Cloudflare Turnstile challenge, and capture the mp4 video URL.
    """
    try:
        from camoufox.async_api import AsyncCamoufox
    except ImportError:
        raise SkipMethod(f"{METHOD_NAME}: camoufox not installed")

    print(f"  [{METHOD_NAME}] Launching stealth Firefox browser")

    captured_urls: list[str] = []
    proxy = get_proxy_dict()

    kwargs = {"headless": True}
    if proxy:
        kwargs["proxy"] = proxy

    try:
        async with AsyncCamoufox(**kwargs) as browser:
            page = await browser.new_page()

            # Intercept network requests to capture video URLs
            async def on_response(response):
                url = response.url
                if config.VIDEO_HOST_PATTERN in url and config.VIDEO_FILE_EXTENSION in url:
                    captured_urls.append(url)
                    print(f"  [{METHOD_NAME}] Captured video URL from network: {url[:80]}...")

            page.on("response", on_response)

            print(f"  [{METHOD_NAME}] Navigating to {episode_url}")
            await page.goto(episode_url, wait_until="domcontentloaded",
                            timeout=config.PAGE_LOAD_TIMEOUT * 1000)

            # Solve Cloudflare Turnstile if present
            solved = await solve_turnstile_playwright(page, METHOD_NAME, max_wait=config.CHALLENGE_WAIT)
            if not solved:
                print(f"  [{METHOD_NAME}] Failed to solve Turnstile challenge")
                return None

            # Check if we already captured a URL from network requests
            if captured_urls:
                return captured_urls[0]

            print(f"  [{METHOD_NAME}] Page loaded ({len(await page.content())} chars)")

            # Try to find and click the play button to trigger video loading
            play_selectors = [
                "button.play-button",
                ".plyr__control--overlaid",
                "[data-plyr='play']",
                ".vjs-big-play-button",
                "video",
                ".player-container",
                ".btn-play",
                "#player",
            ]

            for selector in play_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        print(f"  [{METHOD_NAME}] Clicking play element: {selector}")
                        await element.click()
                        break
                except Exception:
                    continue

            # Wait for video network request after clicking play
            print(f"  [{METHOD_NAME}] Waiting for video network request...")
            for _ in range(config.NETWORK_IDLE_TIMEOUT):
                if captured_urls:
                    return captured_urls[0]
                await asyncio.sleep(1)

            # Last resort: check page source for video URL
            content = await page.content()
            video_url = extract_video_url(content)
            if video_url:
                print(f"  [{METHOD_NAME}] Found video URL in page source")
                return video_url

            print(f"  [{METHOD_NAME}] No video URL captured")
            return None

    except Exception as e:
        print(f"  [{METHOD_NAME}] Error: {e}")
        return None
