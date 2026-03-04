"""
Steps 6–9 — Paid Scraping APIs

Each function fetches the page via a paid API service and extracts the video URL.
These services handle proxies, browsers, and challenge solving behind a single API call.
"""

from typing import Optional

import config
from scraper.utils import extract_video_url, is_cloudflare_challenge


# ────────────────────────────────────────────────────────────────
# Step 6 — ScrapeOps (free tier: 1,000 credits/month)
# ────────────────────────────────────────────────────────────────

async def scrape_scrapeops(episode_url: str) -> Optional[str]:
    """Use ScrapeOps proxy API with JS rendering and Cloudflare bypass."""
    if not config.SCRAPEOPS_API_KEY:
        print("  [scrapeops] No API key configured, skipping")
        return None

    try:
        import requests
    except ImportError:
        print("  [scrapeops] requests not installed, skipping")
        return None

    print(f"  [scrapeops] Fetching via ScrapeOps API")

    try:
        resp = requests.get(
            "https://proxy.scrapeops.io/v1/",
            params={
                "api_key": config.SCRAPEOPS_API_KEY,
                "url": episode_url,
                "render_js": "true",
                "bypass": "cloudflare",
            },
            timeout=config.PAGE_LOAD_TIMEOUT + 30,
        )

        print(f"  [scrapeops] Status: {resp.status_code}, body: {len(resp.text)} chars")

        if resp.status_code != 200:
            print(f"  [scrapeops] Non-200 status, failing")
            return None

        if is_cloudflare_challenge(resp.text):
            print(f"  [scrapeops] Still got Cloudflare challenge, failing")
            return None

        video_url = extract_video_url(resp.text)
        if video_url:
            print(f"  [scrapeops] Found video URL")
            return video_url

        print(f"  [scrapeops] Page loaded but no video URL found")
        return None

    except Exception as e:
        print(f"  [scrapeops] Error: {e}")
        return None


# ────────────────────────────────────────────────────────────────
# Step 7 — Scrapfly (highest success rate, 98.8%)
# ────────────────────────────────────────────────────────────────

async def scrape_scrapfly(episode_url: str) -> Optional[str]:
    """Use Scrapfly API with Anti Scraping Protection bypass."""
    if not config.SCRAPFLY_API_KEY:
        print("  [scrapfly] No API key configured, skipping")
        return None

    try:
        import requests
    except ImportError:
        print("  [scrapfly] requests not installed, skipping")
        return None

    print(f"  [scrapfly] Fetching via Scrapfly API")

    try:
        resp = requests.get(
            "https://api.scrapfly.io/scrape",
            params={
                "key": config.SCRAPFLY_API_KEY,
                "url": episode_url,
                "asp": "true",
                "render_js": "true",
                "country": "us",
            },
            timeout=config.PAGE_LOAD_TIMEOUT + 30,
        )

        print(f"  [scrapfly] Status: {resp.status_code}")

        if resp.status_code != 200:
            print(f"  [scrapfly] Non-200 status, failing")
            return None

        data = resp.json()
        content = data.get("result", {}).get("content", "")

        if is_cloudflare_challenge(content):
            print(f"  [scrapfly] Still got Cloudflare challenge, failing")
            return None

        video_url = extract_video_url(content)
        if video_url:
            print(f"  [scrapfly] Found video URL")
            return video_url

        print(f"  [scrapfly] Page loaded but no video URL found")
        return None

    except Exception as e:
        print(f"  [scrapfly] Error: {e}")
        return None


# ────────────────────────────────────────────────────────────────
# Step 8 — Crawlbase (true pay-as-you-go, no monthly fee)
# ────────────────────────────────────────────────────────────────

async def scrape_crawlbase(episode_url: str) -> Optional[str]:
    """Use Crawlbase API with JS token."""
    if not config.CRAWLBASE_TOKEN:
        print("  [crawlbase] No token configured, skipping")
        return None

    try:
        import requests
    except ImportError:
        print("  [crawlbase] requests not installed, skipping")
        return None

    print(f"  [crawlbase] Fetching via Crawlbase API")

    try:
        resp = requests.get(
            "https://api.crawlbase.com/",
            params={
                "token": config.CRAWLBASE_TOKEN,
                "url": episode_url,
            },
            timeout=config.PAGE_LOAD_TIMEOUT + 30,
        )

        print(f"  [crawlbase] Status: {resp.status_code}, body: {len(resp.text)} chars")

        if resp.status_code != 200:
            print(f"  [crawlbase] Non-200 status, failing")
            return None

        if is_cloudflare_challenge(resp.text):
            print(f"  [crawlbase] Still got Cloudflare challenge, failing")
            return None

        video_url = extract_video_url(resp.text)
        if video_url:
            print(f"  [crawlbase] Found video URL")
            return video_url

        print(f"  [crawlbase] Page loaded but no video URL found")
        return None

    except Exception as e:
        print(f"  [crawlbase] Error: {e}")
        return None


# ────────────────────────────────────────────────────────────────
# Step 9 — ScraperAPI (most documented, large community)
# ────────────────────────────────────────────────────────────────

async def scrape_scraperapi(episode_url: str) -> Optional[str]:
    """Use ScraperAPI with JS rendering and premium residential proxies."""
    if not config.SCRAPERAPI_KEY:
        print("  [scraperapi] No API key configured, skipping")
        return None

    try:
        import requests
    except ImportError:
        print("  [scraperapi] requests not installed, skipping")
        return None

    print(f"  [scraperapi] Fetching via ScraperAPI")

    try:
        resp = requests.get(
            "https://api.scraperapi.com",
            params={
                "api_key": config.SCRAPERAPI_KEY,
                "url": episode_url,
                "render": "true",
                "premium": "true",
            },
            timeout=config.PAGE_LOAD_TIMEOUT + 30,
        )

        print(f"  [scraperapi] Status: {resp.status_code}, body: {len(resp.text)} chars")

        if resp.status_code != 200:
            print(f"  [scraperapi] Non-200 status, failing")
            return None

        if is_cloudflare_challenge(resp.text):
            print(f"  [scraperapi] Still got Cloudflare challenge, failing")
            return None

        video_url = extract_video_url(resp.text)
        if video_url:
            print(f"  [scraperapi] Found video URL")
            return video_url

        print(f"  [scraperapi] Page loaded but no video URL found")
        return None

    except Exception as e:
        print(f"  [scraperapi] Error: {e}")
        return None
