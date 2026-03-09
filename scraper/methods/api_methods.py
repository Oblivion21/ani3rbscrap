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
# Step 10 — Apify: macheta/universal-bypasser
# Cloudflare Bypasser — returns clean HTML + cookies after solving
# challenges automatically.  Simple input: just a URL.
# Free $5/month, no credit card.
# ────────────────────────────────────────────────────────────────

async def scrape_apify_bypasser(episode_url: str) -> Optional[str]:
    """Use macheta/universal-bypasser to bypass Cloudflare and extract video URL.

    Two-phase approach:
      Phase 1: Bypass Cloudflare on the anime3rb episode page, get HTML,
               extract the vid3rb player iframe URL.
      Phase 2: Fetch the player page (usually no CF) to get video_sources MP4 URLs.
    """
    if not config.APIFY_TOKEN:
        raise SkipMethod("apify_bypasser: no token in config.py (APIFY_TOKEN) — "
                         "sign up free at https://apify.com")

    try:
        from apify_client import ApifyClient
    except ImportError:
        raise SkipMethod("apify_bypasser: pip install apify-client")

    ACTOR_ID = "macheta/universal-bypasser"
    print(f"  [apify_bypasser] Running universal-bypasser on Apify cloud")

    client = ApifyClient(config.APIFY_TOKEN)

    # ── Phase 1: Bypass Cloudflare on the episode page ──
    try:
        run = client.actor(ACTOR_ID).call(
            run_input={"url": episode_url},
            max_items=1,
            timeout_secs=config.PAGE_LOAD_TIMEOUT + 60,
            wait_secs=config.PAGE_LOAD_TIMEOUT + 60,
            logger=None,
        )
    except Exception as e:
        print(f"  [apify_bypasser] Actor run failed: {e}")
        return None

    print(f"  [apify_bypasser] Phase 1 done, status: {run.get('status')}")

    dataset_id = run.get("defaultDatasetId")
    if not dataset_id:
        print(f"  [apify_bypasser] No dataset returned")
        return None

    items = _take_dataset_items(client.dataset(dataset_id))
    if not items:
        print(f"  [apify_bypasser] Dataset is empty")
        return None

    # The actor returns items with HTML body content
    html_content = _extract_html_from_apify_items(items)
    if not html_content:
        print(f"  [apify_bypasser] No HTML in response")
        return None

    print(f"  [apify_bypasser] Got HTML: {len(html_content)} chars")

    if is_cloudflare_challenge(html_content):
        print(f"  [apify_bypasser] Still got Cloudflare challenge")
        return None

    # Extract player iframe URL first (most likely to be in the page)
    player_iframe_url = extract_player_iframe_url(html_content)
    if player_iframe_url:
        print(f"  [apify_bypasser] Found player iframe: {player_iframe_url[:80]}...")
        return _fetch_player_and_extract(
            player_iframe_url,
            episode_url,
            "apify_bypasser",
            client=client,
            actor_id=ACTOR_ID,
        )

    # Fallback: try direct .mp4 URL in HTML (rare but possible)
    video_url = extract_video_url(html_content)
    if video_url:
        print(f"  [apify_bypasser] Found video URL directly in HTML")
        return video_url

    print(f"  [apify_bypasser] No player iframe or video URL found")
    _debug_response("apify_bypasser", html_content)
    return None


# ────────────────────────────────────────────────────────────────
# Step 11 — Apify: zfcsoftware/scraper-api
# Cheap ($0.10/1000 results), fast, uses trusted proxies.
# Handles Cloudflare-protected sites automatically.
# ────────────────────────────────────────────────────────────────

async def scrape_apify_scraper(episode_url: str) -> Optional[str]:
    """Use zfcsoftware/scraper-api to bypass Cloudflare and extract video URL.

    Same two-phase approach as apify_bypasser.
    """
    if not config.APIFY_TOKEN:
        raise SkipMethod("apify_scraper: no token in config.py (APIFY_TOKEN) — "
                         "sign up free at https://apify.com")

    try:
        from apify_client import ApifyClient
    except ImportError:
        raise SkipMethod("apify_scraper: pip install apify-client")

    ACTOR_ID = "zfcsoftware/scraper-api"
    print(f"  [apify_scraper] Running scraper-api on Apify cloud")

    client = ApifyClient(config.APIFY_TOKEN)

    # ── Phase 1: Scrape the episode page ──
    try:
        run = client.actor(ACTOR_ID).call(
            run_input={"url": episode_url},
            max_items=1,
            timeout_secs=config.PAGE_LOAD_TIMEOUT + 60,
            wait_secs=config.PAGE_LOAD_TIMEOUT + 60,
            logger=None,
        )
    except Exception as e:
        print(f"  [apify_scraper] Actor run failed: {e}")
        return None

    print(f"  [apify_scraper] Phase 1 done, status: {run.get('status')}")

    dataset_id = run.get("defaultDatasetId")
    if not dataset_id:
        print(f"  [apify_scraper] No dataset returned")
        return None

    items = _take_dataset_items(client.dataset(dataset_id))
    if not items:
        print(f"  [apify_scraper] Dataset is empty")
        return None

    html_content = _extract_html_from_apify_items(items)
    if not html_content:
        print(f"  [apify_scraper] No HTML in response")
        return None

    print(f"  [apify_scraper] Got HTML: {len(html_content)} chars")

    if is_cloudflare_challenge(html_content):
        print(f"  [apify_scraper] Still got Cloudflare challenge")
        return None

    player_iframe_url = extract_player_iframe_url(html_content)
    if player_iframe_url:
        print(f"  [apify_scraper] Found player iframe: {player_iframe_url[:80]}...")
        return _fetch_player_and_extract(
            player_iframe_url,
            episode_url,
            "apify_scraper",
            client=client,
            actor_id=ACTOR_ID,
        )

    video_url = extract_video_url(html_content)
    if video_url:
        print(f"  [apify_scraper] Found video URL directly in HTML")
        return video_url

    print(f"  [apify_scraper] No player iframe or video URL found")
    _debug_response("apify_scraper", html_content)
    return None


# ────────────────────────────────────────────────────────────────
# Shared helpers for Apify methods
# ────────────────────────────────────────────────────────────────

def _extract_html_from_apify_items(items: list) -> Optional[str]:
    """Extract HTML body content from Apify actor dataset items.

    Different actors return HTML in different fields. We check common ones.
    """
    for item in items:
        # Common field names used by various Apify actors
        for key in ("body", "html", "content", "text", "page_content", "result"):
            val = item.get(key)
            if val and isinstance(val, str) and len(val) > 100:
                return val

        # Some actors nest it under data.body or similar
        data = item.get("data")
        if isinstance(data, dict):
            for key in ("body", "html", "content"):
                val = data.get(key)
                if val and isinstance(val, str) and len(val) > 100:
                    return val

        # If the item itself looks like it has HTML (e.g., contains <html)
        item_str = str(item)
        if "<html" in item_str.lower() and len(item_str) > 500:
            # Try to find the largest string value in the item
            best = ""
            for v in item.values():
                if isinstance(v, str) and len(v) > len(best):
                    best = v
            if best and len(best) > 100:
                return best

    return None


def _take_dataset_items(dataset_client, limit: int = 3) -> list[dict]:
    """Read only the first few dataset items instead of materializing the whole dataset."""
    items: list[dict] = []
    for item in dataset_client.iterate_items(clean=True):
        items.append(item)
        if len(items) >= limit:
            break
    return items


def _fetch_player_and_extract(
    player_url: str,
    referer_url: str,
    method_name: str,
    client=None,
    actor_id: Optional[str] = None,
) -> Optional[str]:
    """Phase 2: Fetch the vid3rb player page and extract MP4 video_sources.

    The player page usually does not have Cloudflare, so a direct HTTP fetch is
    enough and avoids a second paid actor run. On server IPs that get challenged
    by Cloudflare, fall back to the same Apify actor used in phase 1.
    """
    print(f"  [{method_name}] Phase 2: Fetching player page via HTTP...")
    video_url = _fetch_player_video_sources(player_url, referer_url)
    if video_url:
        return video_url

    if not client or not actor_id:
        return None

    print(f"  [{method_name}] Phase 2 fallback: Fetching player page via Apify...")
    player_html = _fetch_url_via_apify(client, actor_id, player_url, method_name, "Phase 2 fallback")
    if not player_html:
        return None

    print(f"  [{method_name}] Apify player HTML: {len(player_html)} chars")

    video_url = _parse_video_sources_from_html(player_html, method_name)
    if video_url:
        return video_url

    video_url = extract_video_url(player_html)
    if video_url:
        print(f"  [{method_name}] Found video URL in Apify player HTML")
        return video_url

    if is_cloudflare_challenge(player_html):
        print(f"  [{method_name}] Player page is still challenged after Apify fallback")

    _debug_response(f"{method_name}-player", player_html)
    return None


def _fetch_url_via_apify(
    client,
    actor_id: str,
    target_url: str,
    method_name: str,
    phase_label: str,
) -> Optional[str]:
    """Fetch a URL through an Apify actor and return the extracted HTML."""
    try:
        run = client.actor(actor_id).call(
            run_input={"url": target_url},
            max_items=1,
            timeout_secs=config.PAGE_LOAD_TIMEOUT + 60,
            wait_secs=config.PAGE_LOAD_TIMEOUT + 60,
            logger=None,
        )
    except Exception as e:
        print(f"  [{method_name}] {phase_label} actor run failed: {e}")
        return None

    print(f"  [{method_name}] {phase_label} actor status: {run.get('status')}")

    dataset_id = run.get("defaultDatasetId")
    if not dataset_id:
        print(f"  [{method_name}] {phase_label} returned no dataset")
        return None

    items = _take_dataset_items(client.dataset(dataset_id))
    if not items:
        print(f"  [{method_name}] {phase_label} dataset is empty")
        return None

    html_content = _extract_html_from_apify_items(items)
    if not html_content:
        print(f"  [{method_name}] {phase_label} returned no HTML")
        return None

    return html_content


def _parse_video_sources_from_html(html: str, method_name: str) -> Optional[str]:
    """Extract the best MP4 URL from video_sources = [...] in HTML."""
    import re as _re
    import json as _json

    matches = _re.findall(r'video_sources\s*=\s*(\[.*?\]);', html, _re.DOTALL)
    for raw in reversed(matches):
        if len(raw) <= 5:
            continue
        try:
            sources = _json.loads(raw)
            valid = [s for s in sources if s.get("src") and not s.get("premium")]
            valid.sort(key=lambda s: int(s.get("res", 0)), reverse=True)
            if valid:
                best = valid[0]["src"].replace("\\/", "/")
                print(f"  [{method_name}] Found {len(valid)} sources, "
                      f"best: {valid[0].get('label', '?')}")
                return best
        except Exception as e:
            print(f"  [{method_name}] Failed to parse video_sources: {e}")
    return None


def _fetch_player_video_sources(player_url: str, referer_url: str) -> Optional[str]:
    """Fetch the vid3rb player page via direct HTTP and extract video_sources.

    The player page (video.vid3rb.com) typically doesn't have Cloudflare.
    When fetched with the right Referer header, the HTML contains:
        video_sources = [{src: "https://files.vid3rb.com/.../1080p.mp4?...", ...}, ...]
    The second match is the real one (first is often an empty []).
    """
    import requests as _requests

    def _build_session() -> _requests.Session:
        session = _requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                           "AppleWebKit/537.36 (KHTML, like Gecko) "
                           "Chrome/120.0.0.0 Safari/537.36",
            "Referer": referer_url,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
        })
        return session

    def _proxy_config() -> Optional[dict]:
        if not config.PROXY_SERVER:
            return None

        proxy_url = config.PROXY_SERVER
        if config.PROXY_USERNAME:
            proxy_url = proxy_url.replace(
                "://",
                f"://{config.PROXY_USERNAME}:{config.PROXY_PASSWORD}@",
                1,
            )
        return {"http": proxy_url, "https": proxy_url}

    def _extract_from_player_html(text: str, log_name: str) -> Optional[str]:
        if is_cloudflare_challenge(text):
            print(f"  [{log_name}] Player page looks challenged by Cloudflare")
            _debug_response("apify-player", text)
            return None

        video_url = _parse_video_sources_from_html(text, log_name)
        if video_url:
            return video_url

        video_url = extract_video_url(text)
        if video_url:
            print(f"  [{log_name}] Found video URL in player page HTML")
            return video_url

        print(f"  [{log_name}] No video_sources found in player page HTML")
        _debug_response("apify-player", text)
        return None

    def _fetch_html(proxies: Optional[dict], label: str) -> Optional[str]:
        session = _build_session()
        try:
            print(f"  [{label}] Fetching player page: {player_url[:80]}...")
            resp = session.get(player_url, timeout=30, proxies=proxies)
            print(f"  [{label}] Player page status: {resp.status_code}, {len(resp.text)} chars")
        except Exception as e:
            print(f"  [{label}] Player page fetch failed: {e}")
            return None

        if resp.status_code != 200:
            return None

        return resp.text

    proxies = _proxy_config()
    if proxies:
        print("  [apify] Fetching player page through configured proxy...")
        text = _fetch_html(proxies=proxies, label="apify-proxy")
        if text:
            video_url = _extract_from_player_html(text, "apify-proxy")
            if video_url:
                return video_url
        print("  [apify] Proxy fetch did not yield sources, trying direct fetch...")

    text = _fetch_html(proxies=None, label="apify")
    if not text:
        return None

    return _extract_from_player_html(text, "apify")
