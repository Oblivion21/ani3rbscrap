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
    """Use Apify's Cloudflare Scraper Actor (ChNuXurElMWvpbJB9) to bypass
    Turnstile and get page HTML.

    Two-phase approach:
      Phase 1: Scrape the episode page to extract the vid3rb player iframe URL.
      Phase 2: Scrape the player iframe URL with a JS script that clicks play
               and captures the .mp4 file URL from network requests or video src.
    """
    if not config.APIFY_TOKEN:
        raise SkipMethod("apify: no token in config.py (APIFY_TOKEN) — "
                         "sign up free at https://apify.com")

    try:
        from apify_client import ApifyClient
    except ImportError:
        raise SkipMethod("apify: install the client first → pip install apify-client")

    ACTOR_ID = "ChNuXurElMWvpbJB9"

    print(f"  [apify] Running Cloudflare Scraper Actor on Apify cloud")

    client = ApifyClient(config.APIFY_TOKEN)

    # ── Phase 1: Get the episode page HTML to find the player iframe ──
    run_input = {
        "urls": [episode_url],
        "js_script": (
            "var iframe = document.querySelector('iframe[src*=\"vid3rb\"]');"
            "if (iframe) return iframe.src;"
            "var video = document.querySelector('video');"
            "if (video && video.src) return video.src;"
            "var source = document.querySelector('video source');"
            "if (source && source.src) return source.src;"
            "return null;"
        ),
        "retrieve_result_from_js_script": True,
        "page_is_loaded_before_running_script": True,
        "execute_js_async": False,
        "retrieve_html_from_url_after_loaded": True,
        "js_timeout": 15,
        "max_retries_per_url": 2,
        "proxy": {"useApifyProxy": False},
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
        # Check JS script result first (returns the iframe src directly)
        js_result = item.get("js_result") or item.get("result")
        if js_result and isinstance(js_result, str) and "vid3rb" in js_result:
            # If it's already a .mp4 URL, return directly
            if ".mp4" in js_result or "files.vid3rb.com" in js_result:
                print(f"  [apify] Found video URL from JS: {js_result[:80]}...")
                return js_result
            player_iframe_url = js_result
            print(f"  [apify] Found player iframe from JS: {player_iframe_url[:80]}...")
            break

        # Fallback: parse the returned HTML
        html = item.get("html") or item.get("body") or item.get("content") or ""
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

    # Async JS that clicks play and polls for the .mp4 src
    player_js = (
        "var selectors = ["
        "  'button.plyr__control--overlaid',"
        "  '[data-plyr=\"play\"]',"
        "  '.plyr__control--overlaid',"
        "  '.vjs-big-play-button',"
        "  'button[aria-label*=\"Play\"]',"
        "  'video',"
        "  '.play-button'"
        "];"
        "for (var i = 0; i < selectors.length; i++) {"
        "  try {"
        "    var el = document.querySelector(selectors[i]);"
        "    if (el) { el.click(); break; }"
        "  } catch(e) {}"
        "}"
        "var vid = document.querySelector('video');"
        "if (vid) try { vid.play(); } catch(e) {}"
        ""
        "return new Promise(function(resolve) {"
        "  var checks = 0;"
        "  var interval = setInterval(function() {"
        "    checks++;"
        "    var v = document.querySelector('video');"
        "    if (v && v.src && (v.src.includes('.mp4') || v.src.includes('files.vid3rb.com'))) {"
        "      clearInterval(interval);"
        "      resolve(v.src);"
        "      return;"
        "    }"
        "    var s = document.querySelector('video source');"
        "    if (s && s.src && (s.src.includes('.mp4') || s.src.includes('files.vid3rb.com'))) {"
        "      clearInterval(interval);"
        "      resolve(s.src);"
        "      return;"
        "    }"
        "    var entries = performance.getEntriesByType('resource');"
        "    for (var j = 0; j < entries.length; j++) {"
        "      if (entries[j].name.includes('.mp4') || entries[j].name.includes('files.vid3rb.com')) {"
        "        clearInterval(interval);"
        "        resolve(entries[j].name);"
        "        return;"
        "      }"
        "    }"
        "    if (checks >= 15) {"
        "      clearInterval(interval);"
        "      var fallback = v ? (v.src || (v.querySelector('source') ? v.querySelector('source').src : null)) : null;"
        "      resolve(fallback);"
        "    }"
        "  }, 1000);"
        "});"
    )

    run_input_phase2 = {
        "urls": [player_iframe_url],
        "js_script": player_js,
        "retrieve_result_from_js_script": True,
        "page_is_loaded_before_running_script": True,
        "execute_js_async": True,
        "retrieve_html_from_url_after_loaded": True,
        "js_timeout": 20,
        "max_retries_per_url": 2,
        "proxy": {"useApifyProxy": False},
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
        # Check JS result for the .mp4 URL
        js_result = item.get("js_result") or item.get("result")
        if js_result and isinstance(js_result, str) and ("vid3rb" in js_result or ".mp4" in js_result):
            print(f"  [apify] Captured .mp4 URL from JS: {js_result[:80]}...")
            return js_result

        # Fallback: check HTML content
        html = item.get("html") or item.get("body") or item.get("content") or ""
        if html:
            video_url = extract_video_url(html)
            if video_url:
                print(f"  [apify] Found video URL in player page HTML")
                return video_url

    print(f"  [apify] Phase 2: no .mp4 URL captured")
    return None
