"""
Steps 6–9 — Paid Scraping APIs

Each service handles Cloudflare/Turnstile server-side — there's nothing to
click. The key is sending the right parameters so each service enables its
full JS-rendering + challenge-solving pipeline.
"""

from typing import Optional

import config
from scraper.utils import extract_video_url, extract_player_iframe_url, is_cloudflare_challenge, SkipMethod


def _debug_response(name: str, text: str):
    """Print a snippet of the response to help diagnose failures."""
    snippet = text.replace("\n", " ")[:400]
    print(f"  [{name}] Response snippet: {snippet}")


# ────────────────────────────────────────────────────────────────
# Step 6 — ScrapeOps
# ────────────────────────────────────────────────────────────────

async def scrape_scrapeops(episode_url: str) -> Optional[str]:
    """Use ScrapeOps with Cloudflare level-3 bypass (Turnstile-capable)."""
    if not config.SCRAPEOPS_API_KEY:
        raise SkipMethod("scrapeops: no API key in config.py (SCRAPEOPS_API_KEY)")

    import requests

    print(f"  [scrapeops] Fetching via ScrapeOps API")

    resp = requests.get(
        "https://proxy.scrapeops.io/v1/",
        params={
            "api_key": config.SCRAPEOPS_API_KEY,
            "url": episode_url,
            "render_js": "true",
            # level_3 uses a real browser + Turnstile solver
            "bypass": "cloudflare_level_3",
            "residential": "true",
            "country": "us",
        },
        timeout=config.PAGE_LOAD_TIMEOUT + 60,
    )

    print(f"  [scrapeops] Status: {resp.status_code}, body: {len(resp.text)} chars")

    if resp.status_code != 200:
        print(f"  [scrapeops] Non-200 status")
        _debug_response("scrapeops", resp.text)
        return None

    if is_cloudflare_challenge(resp.text):
        print(f"  [scrapeops] Still got Cloudflare challenge")
        return None

    video_url = extract_video_url(resp.text)
    if video_url:
        print(f"  [scrapeops] Found video URL")
        return video_url

    print(f"  [scrapeops] Page loaded but no video URL found")
    _debug_response("scrapeops", resp.text)
    return None


# ────────────────────────────────────────────────────────────────
# Step 7 — Scrapfly
# ────────────────────────────────────────────────────────────────

async def scrape_scrapfly(episode_url: str) -> Optional[str]:
    """Use Scrapfly with ASP (Anti Scraping Protection) + JS rendering."""
    if not config.SCRAPFLY_API_KEY:
        raise SkipMethod("scrapfly: no API key in config.py (SCRAPFLY_API_KEY)")

    import requests

    print(f"  [scrapfly] Fetching via Scrapfly API")

    resp = requests.get(
        "https://api.scrapfly.io/scrape",
        params={
            "key": config.SCRAPFLY_API_KEY,
            "url": episode_url,
            # asp=true enables Cloudflare/Turnstile bypass
            "asp": "true",
            "render_js": "true",
            "country": "us",
            # Wait for video player element before returning HTML
            "wait_for_selector": "video,#player,.episode-player,[class*='player']",
            # Give JS 10s to execute after page load
            "wait": "10000",
        },
        timeout=config.PAGE_LOAD_TIMEOUT + 60,
    )

    print(f"  [scrapfly] Status: {resp.status_code}")

    if resp.status_code != 200:
        print(f"  [scrapfly] Non-200 status")
        try:
            _debug_response("scrapfly", resp.text)
        except Exception:
            pass
        return None

    data = resp.json()
    content = data.get("result", {}).get("content", "")

    if is_cloudflare_challenge(content):
        print(f"  [scrapfly] Still got Cloudflare challenge")
        return None

    video_url = extract_video_url(content)
    if video_url:
        print(f"  [scrapfly] Found video URL")
        return video_url

    print(f"  [scrapfly] Page loaded but no video URL found (content: {len(content)} chars)")
    _debug_response("scrapfly", content)
    return None


# ────────────────────────────────────────────────────────────────
# Step 8 — Crawlbase
# NOTE: You must use a JavaScript API token, not a regular token.
#       Get yours at: https://crawlbase.com/dashboard
# ────────────────────────────────────────────────────────────────

async def scrape_crawlbase(episode_url: str) -> Optional[str]:
    """Use Crawlbase JS API (requires JavaScript token) with full page rendering."""
    if not config.CRAWLBASE_TOKEN:
        raise SkipMethod("crawlbase: no token in config.py (CRAWLBASE_TOKEN)")

    import requests

    print(f"  [crawlbase] Fetching via Crawlbase JS API")

    resp = requests.get(
        "https://api.crawlbase.com/",
        params={
            # Must be a JavaScript API token (not a normal token)
            "token": config.CRAWLBASE_TOKEN,
            "url": episode_url,
            # Wait for all AJAX/XHR requests to complete
            "ajax_wait": "true",
            # Wait 8 seconds after page load (time for Turnstile + player init)
            "page_wait": "8000",
        },
        timeout=config.PAGE_LOAD_TIMEOUT + 60,
    )

    print(f"  [crawlbase] Status: {resp.status_code}, body: {len(resp.text)} chars")

    if resp.status_code != 200:
        print(f"  [crawlbase] Non-200 status")
        _debug_response("crawlbase", resp.text)
        return None

    if is_cloudflare_challenge(resp.text):
        print(f"  [crawlbase] Still got Cloudflare challenge")
        return None

    video_url = extract_video_url(resp.text)
    if video_url:
        print(f"  [crawlbase] Found video URL")
        return video_url

    print(f"  [crawlbase] Page loaded but no video URL found")
    _debug_response("crawlbase", resp.text)
    return None


# ────────────────────────────────────────────────────────────────
# Step 9 — ScraperAPI
# ────────────────────────────────────────────────────────────────

async def scrape_scraperapi(episode_url: str) -> Optional[str]:
    """Use ScraperAPI with JS rendering, premium proxies, and Cloudflare bypass."""
    if not config.SCRAPERAPI_KEY:
        raise SkipMethod("scraperapi: no API key in config.py (SCRAPERAPI_KEY)")

    import requests

    print(f"  [scraperapi] Fetching via ScraperAPI")

    resp = requests.get(
        "https://api.scraperapi.com",
        params={
            "api_key": config.SCRAPERAPI_KEY,
            "url": episode_url,
            # render=true runs a real headless Chrome browser
            "render": "true",
            # premium proxies have higher Cloudflare bypass success rate
            "premium": "true",
            "country_code": "us",
            # Wait for video player element before capturing HTML
            "wait_for_selector": "video,#player,[class*='player']",
        },
        timeout=config.PAGE_LOAD_TIMEOUT + 60,
    )

    print(f"  [scraperapi] Status: {resp.status_code}, body: {len(resp.text)} chars")

    if resp.status_code != 200:
        print(f"  [scraperapi] Non-200 status")
        _debug_response("scraperapi", resp.text)
        return None

    if is_cloudflare_challenge(resp.text):
        print(f"  [scraperapi] Still got Cloudflare challenge")
        return None

    video_url = extract_video_url(resp.text)
    if video_url:
        print(f"  [scraperapi] Found video URL")
        return video_url

    print(f"  [scraperapi] Page loaded but no video URL found")
    _debug_response("scraperapi", resp.text)
    return None


# ────────────────────────────────────────────────────────────────
# Step 10 — Apify (free $5/month, no credit card)
# Uses the "neatrat/cloudflare-scraper" Actor which handles
# Cloudflare Turnstile automatically on Apify's cloud.
# Sign up: https://apify.com   Token: https://console.apify.com/account/integrations
# ────────────────────────────────────────────────────────────────

async def scrape_apify(episode_url: str) -> Optional[str]:
    """Use Apify's Cloudflare Bypass Actor (24MaNvUH2R4RioZ6W) to bypass
    Turnstile and extract the video URL.

    Two-phase approach:
      Phase 1: Scrape the episode page. The page uses Alpine.js to bind the
               iframe src dynamically (:src="currentVideoUrl"), so we wait
               for it to render, then extract the vid3rb player iframe URL.
      Phase 2: Scrape the player iframe URL to capture the .mp4 file URL.
    """
    if not config.APIFY_TOKEN:
        raise SkipMethod("apify: no token in config.py (APIFY_TOKEN) — "
                         "sign up free at https://apify.com")

    try:
        from apify_client import ApifyClient
    except ImportError:
        raise SkipMethod("apify: install the client first → pip install apify-client")

    # Cloudflare Bypass Actor — handles Turnstile automatically
    ACTOR_ID = "24MaNvUH2R4RioZ6W"

    print(f"  [apify] Running Cloudflare Bypass Actor on Apify cloud")

    client = ApifyClient(config.APIFY_TOKEN)

    # ── Phase 1: Get the episode page to find the player iframe ──
    # pageFunction runs in the browser after waitForSeconds.
    # Alpine.js binds :src="currentVideoUrl" on the iframe at runtime,
    # so the raw HTML has no src — we must wait for Alpine to init.
    phase1_page_fn = """($) => {
        // 1. Check iframe with vid3rb src (set by Alpine.js after init)
        var iframe = document.querySelector('iframe[src*="vid3rb"]');
        if (iframe && iframe.src) return { playerUrl: iframe.src };

        // 2. Livewire wire:snapshot JSON
        var snapshots = document.querySelectorAll('[wire\\\\:snapshot]');
        for (var i = 0; i < snapshots.length; i++) {
            try {
                var snap = JSON.parse(snapshots[i].getAttribute('wire:snapshot'));
                var url = snap && snap.data && snap.data.video_url;
                if (url && url.indexOf('vid3rb') !== -1)
                    return { playerUrl: url.replace(/\\\\\\//g, '/') };
            } catch(e) {}
        }

        // 3. Regex the rendered HTML for video_url pattern
        var html = document.documentElement.innerHTML;
        var m = html.match(/"video_url"\\s*:\\s*"(https?:[^"]+vid3rb[^"]+)"/i);
        if (m) return { playerUrl: m[1].replace(/\\\\\\//g, '/') };

        // 4. Direct video element
        var video = document.querySelector('video');
        if (video && video.src) return { playerUrl: video.src };

        // 5. Return full HTML for fallback parsing
        return { html: html.substring(0, 50000) };
    }"""

    run_input = {
        "startUrls": [{"url": episode_url}],
        "waitForSeconds": 10,
        "pageFunction": phase1_page_fn,
        "proxyConfig": {"useApifyProxy": True},
    }

    try:
        run = client.actor(ACTOR_ID).call(
            run_input=run_input,
            timeout_secs=config.PAGE_LOAD_TIMEOUT + 60,
        )
    except Exception as e:
        print(f"  [apify] Actor run failed: {e}")
        return None

    print(f"  [apify] Phase 1 done, status: {run.get('status')}")

    dataset_id = run.get("defaultDatasetId")
    if not dataset_id:
        print(f"  [apify] No dataset returned")
        return None

    items = list(client.dataset(dataset_id).iterate_items())
    if not items:
        print(f"  [apify] Dataset is empty — page may not have loaded")
        return None

    player_iframe_url = None
    for item in items:
        # pageFunction returns {playerUrl: ...} or {html: ...}
        player_url = item.get("playerUrl")
        if player_url and "vid3rb" in player_url:
            # Unescape HTML entities
            player_url = player_url.replace("&amp;", "&")
            if ".mp4" in player_url or "files.vid3rb.com" in player_url:
                print(f"  [apify] Found video URL directly: {player_url[:80]}...")
                return player_url
            player_iframe_url = player_url
            print(f"  [apify] Found player iframe: {player_iframe_url[:80]}...")
            break

        # Fallback: parse HTML returned by pageFunction
        html = item.get("html") or ""
        if not html:
            continue

        print(f"  [apify] Got HTML: {len(html)} chars")

        if is_cloudflare_challenge(html):
            print(f"  [apify] Still got Cloudflare challenge")
            continue

        video_url = extract_video_url(html)
        if video_url:
            print(f"  [apify] Found video URL directly in HTML")
            return video_url

        player_iframe_url = extract_player_iframe_url(html)
        if player_iframe_url:
            print(f"  [apify] Found player iframe in HTML: {player_iframe_url[:80]}...")
            break

        _debug_response("apify", html)

    if not player_iframe_url:
        print(f"  [apify] No video URL or player iframe found")
        return None

    # ── Phase 2: Navigate to the player iframe and capture the .mp4 URL ──
    print(f"  [apify] Phase 2: Scraping player iframe to capture .mp4 URL...")

    phase2_page_fn = """($) => {
        // Click play button
        var selectors = [
            'button.plyr__control--overlaid',
            '[data-plyr="play"]',
            '.plyr__control--overlaid',
            '.vjs-big-play-button',
            'button[aria-label*="Play"]',
            'video',
            '.play-button'
        ];
        for (var i = 0; i < selectors.length; i++) {
            try {
                var el = document.querySelector(selectors[i]);
                if (el) { el.click(); break; }
            } catch(e) {}
        }

        // Try to play video directly
        var vid = document.querySelector('video');
        if (vid) try { vid.play(); } catch(e) {}

        // Check video src
        if (vid && vid.src && (vid.src.includes('.mp4') || vid.src.includes('files.vid3rb.com')))
            return { videoUrl: vid.src };

        // Check source element
        var source = vid ? vid.querySelector('source') : null;
        if (source && source.src && (source.src.includes('.mp4') || source.src.includes('files.vid3rb.com')))
            return { videoUrl: source.src };

        // Check performance entries for .mp4 network requests
        var entries = performance.getEntriesByType('resource');
        for (var j = 0; j < entries.length; j++) {
            if (entries[j].name.includes('.mp4') || entries[j].name.includes('files.vid3rb.com'))
                return { videoUrl: entries[j].name };
        }

        // Return video src even if it doesn't match patterns (fallback)
        if (vid && vid.src) return { videoUrl: vid.src };
        if (source && source.src) return { videoUrl: source.src };

        // Return HTML for fallback parsing
        return { html: document.documentElement.innerHTML.substring(0, 50000) };
    }"""

    run_input_phase2 = {
        "startUrls": [{"url": player_iframe_url}],
        "waitForSeconds": 12,
        "pageFunction": phase2_page_fn,
        "proxyConfig": {"useApifyProxy": True},
    }

    try:
        run2 = client.actor(ACTOR_ID).call(
            run_input=run_input_phase2,
            timeout_secs=config.PAGE_LOAD_TIMEOUT + 60,
        )
    except Exception as e:
        print(f"  [apify] Phase 2 actor run failed: {e}")
        return None

    print(f"  [apify] Phase 2 done, status: {run2.get('status')}")

    dataset_id2 = run2.get("defaultDatasetId")
    if not dataset_id2:
        print(f"  [apify] Phase 2: no dataset returned")
        return None

    items2 = list(client.dataset(dataset_id2).iterate_items())
    for item in items2:
        video_url = item.get("videoUrl")
        if video_url and ("vid3rb" in video_url or ".mp4" in video_url):
            print(f"  [apify] Captured video URL: {video_url[:80]}...")
            return video_url

        # Fallback: check HTML content
        html = item.get("html") or ""
        if html:
            video_url = extract_video_url(html)
            if video_url:
                print(f"  [apify] Found video URL in player page HTML")
                return video_url

    print(f"  [apify] Phase 2: no .mp4 URL captured")
    return None
