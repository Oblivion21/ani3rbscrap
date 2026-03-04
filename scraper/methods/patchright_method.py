"""
Step 4 — Patchright

Drop-in Playwright replacement with stealth patches.
Intercepts network requests to capture the video mp4 URL.
"""

import asyncio
from typing import Optional

import config
from scraper.utils import (
    extract_video_url, is_cloudflare_challenge, get_proxy_dict,
    SkipMethod, solve_turnstile_playwright,
)


METHOD_NAME = "patchright"


async def scrape(episode_url: str) -> Optional[str]:
    """
    Launch a patched Chromium browser, navigate to the episode page,
    solve the Cloudflare Turnstile challenge, and capture the mp4 video URL.
    """
    try:
        from patchright.async_api import async_playwright
    except ImportError:
        raise SkipMethod(f"{METHOD_NAME}: patchright not installed")

    print(f"  [{METHOD_NAME}] Launching patched Chromium browser")

    captured_urls: list[str] = []

    try:
        async with async_playwright() as p:
            launch_kwargs = {
                "headless": False,  # Non-headless is more likely to pass
                "channel": "chrome",  # Use system Chrome if available
            }

            proxy = get_proxy_dict()
            if proxy:
                launch_kwargs["proxy"] = proxy

            try:
                browser = await p.chromium.launch(**launch_kwargs)
            except Exception:
                # Fallback: try without system chrome channel
                launch_kwargs.pop("channel", None)
                browser = await p.chromium.launch(**launch_kwargs)

            page = await browser.new_page()

            # Intercept network responses to capture video URLs
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
                await browser.close()
                return None

            # Check if we already captured a video URL
            if captured_urls:
                await browser.close()
                return captured_urls[0]

            print(f"  [{METHOD_NAME}] Page loaded ({len(await page.content())} chars)")

            # Try to find and click play button
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

            # Wait for video network request
            print(f"  [{METHOD_NAME}] Waiting for video network request...")
            for _ in range(config.NETWORK_IDLE_TIMEOUT):
                if captured_urls:
                    await browser.close()
                    return captured_urls[0]
                await asyncio.sleep(1)

            # Last resort: check page source
            content = await page.content()
            video_url = extract_video_url(content)
            await browser.close()

            if video_url:
                print(f"  [{METHOD_NAME}] Found video URL in page source")
                return video_url

            print(f"  [{METHOD_NAME}] No video URL captured")
            return None

    except Exception as e:
        print(f"  [{METHOD_NAME}] Error: {e}")
        return None
