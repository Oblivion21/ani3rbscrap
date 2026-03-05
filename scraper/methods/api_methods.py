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
      Phase 1: Scrape the episode page.  The player URL lives inside a
               Livewire wire:snapshot JSON attribute (video_url field).
               The pageFunction uses $ (Cheerio/jQuery) to parse it.
      Phase 2: Scrape the vid3rb player page.  The player page contains a
               video_sources JS array with signed MP4 URLs for each quality.
               We extract them with a regex on the HTML.
    """
    if not config.APIFY_TOKEN:
        raise SkipMethod("apify: no token in config.py (APIFY_TOKEN) — "
                         "sign up free at https://apify.com")

    try:
        from apify_client import ApifyClient
    except ImportError:
        raise SkipMethod("apify: install the client first → pip install apify-client")

    import json as _json

    # Cloudflare Bypass Actor — handles Turnstile automatically.
    # pageFunction receives $ (Cheerio) — NOT browser document.
    ACTOR_ID = "24MaNvUH2R4RioZ6W"

    print(f"  [apify] Running Cloudflare Bypass Actor on Apify cloud")

    client = ApifyClient(config.APIFY_TOKEN)

    # ── Phase 1: Get the episode page to find the player iframe URL ──
    # The player URL is in a Livewire wire:snapshot JSON attribute on the
    # episode page (server-rendered, no JS needed).  Fallback: regex HTML.
    phase1_page_fn = """($) => {
        var result = {};
        var html = $('html').html() || '';

        // 1. Parse wire:snapshot attributes for video_url
        var snapRe = /wire:snapshot="(\\{.*?\\})"/g;
        var match;
        while ((match = snapRe.exec(html)) !== null) {
            try {
                // Decode HTML entities (&quot; etc.)
                var decoded = match[1].replace(/&quot;/g, '"').replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>');
                var snap = JSON.parse(decoded);
                var url = snap && snap.data && snap.data.video_url;
                if (url && url.indexOf('vid3rb') !== -1) {
                    return { playerUrl: url.replace(/\\\\\\//g, '/') };
                }
            } catch(e) {}
        }

        // 2. Regex for video_url in any JSON-like structure
        var m = html.match(/"video_url"\\s*[=:]\\s*"(https?:[^"]*vid3rb[^"]*)"/i);
        if (m) {
            return { playerUrl: m[1].replace(/\\\\\\//g, '/').replace(/&amp;/g, '&') };
        }

        // 3. iframe src with vid3rb (may be set if Alpine ran)
        var iframeSrc = $('iframe[src*="vid3rb"]').attr('src');
        if (iframeSrc) return { playerUrl: iframeSrc.replace(/&amp;/g, '&') };

        // 4. Return HTML snippet for fallback parsing
        return { html: html.substring(0, 50000) };
    }"""

    run_input = {
        "startUrls": [{"url": episode_url}],
        "waitForSeconds": 10,
        "waitForTitle": "Security Check",
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
            player_url = player_url.replace("&amp;", "&")
            if ".mp4" in player_url or "files.vid3rb.com" in player_url:
                print(f"  [apify] Found video URL directly: {player_url[:80]}...")
                return player_url
            player_iframe_url = player_url
            print(f"  [apify] Found player iframe: {player_iframe_url[:80]}...")
            break

        # Fallback: parse HTML returned by pageFunction
        html_content = item.get("html") or ""
        if not html_content:
            continue

        print(f"  [apify] Got HTML: {len(html_content)} chars")

        if is_cloudflare_challenge(html_content):
            print(f"  [apify] Still got Cloudflare challenge")
            continue

        video_url = extract_video_url(html_content)
        if video_url:
            print(f"  [apify] Found video URL directly in HTML")
            return video_url

        player_iframe_url = extract_player_iframe_url(html_content)
        if player_iframe_url:
            print(f"  [apify] Found player iframe in HTML: {player_iframe_url[:80]}...")
            break

        _debug_response("apify", html_content)

    if not player_iframe_url:
        print(f"  [apify] No video URL or player iframe found")
        return None

    # ── Phase 2: Scrape the vid3rb player page for video_sources ──
    # The player page HTML contains a JS variable:
    #   video_sources = [{src: "https://files.vid3rb.com/.../1080p.mp4?...", ...}, ...]
    # The second occurrence is the real one (first is an empty []).
    # We extract it with regex — no need to click play or intercept network.
    print(f"  [apify] Phase 2: Scraping player page for video_sources...")

    phase2_page_fn = """($) => {
        var html = $('html').html() || '';
        var result = { title: $('title').text(), bodyLength: html.length };

        // 1. Extract video_sources = [...] from inline scripts
        //    There may be two matches: first is empty [], second has real URLs
        var allMatches = [];
        var re = /video_sources\\s*=\\s*(\\[.*?\\]);/gs;
        var m;
        while ((m = re.exec(html)) !== null) {
            allMatches.push(m[1]);
        }
        if (allMatches.length > 0) {
            // Take the last (non-empty) match
            for (var i = allMatches.length - 1; i >= 0; i--) {
                if (allMatches[i].length > 5) {
                    result.videoSources = allMatches[i];
                    break;
                }
            }
        }

        // 2. Look for files.vid3rb.com MP4 URLs directly
        var mp4Urls = html.match(/https?:\\/\\/files\\.vid3rb\\.com[^"'\\s<>]+\\.mp4[^"'\\s<>]*/g);
        if (mp4Urls) result.mp4Urls = [...new Set(mp4Urls)];

        // 3. video.vid3rb.com/video/ API URLs
        var apiUrls = html.match(/https?:\\/\\/video\\.vid3rb\\.com\\/video\\/[^"'\\s<>]+/g);
        if (apiUrls) result.apiUrls = [...new Set(apiUrls)];

        // 4. Check video element src (in case autoplay worked)
        result.videoSrc = $('video').attr('src') || null;

        // 5. source elements
        var sources = [];
        $('video source').each(function() { sources.push($(this).attr('src')); });
        if (sources.length) result.sourceTags = sources;

        return result;
    }"""

    run_input_phase2 = {
        "startUrls": [{"url": player_iframe_url}],
        "waitForSeconds": 8,
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
        # 1. Parse video_sources JSON array — best quality first
        video_sources_raw = item.get("videoSources")
        if video_sources_raw:
            try:
                sources = _json.loads(video_sources_raw)
                # Filter to non-premium sources with actual URLs, sort by resolution
                valid = [s for s in sources if s.get("src") and not s.get("premium")]
                valid.sort(key=lambda s: int(s.get("res", 0)), reverse=True)
                if valid:
                    best = valid[0]["src"].replace("\\/", "/")
                    print(f"  [apify] Got {len(valid)} sources, best: {valid[0].get('label', '?')}")
                    print(f"  [apify] Video URL: {best[:80]}...")
                    return best
            except Exception as e:
                print(f"  [apify] Failed to parse video_sources: {e}")

        # 2. Direct MP4 URLs from regex
        mp4_urls = item.get("mp4Urls") or []
        if mp4_urls:
            print(f"  [apify] Found {len(mp4_urls)} MP4 URL(s)")
            return mp4_urls[0]

        # 3. API URLs (video.vid3rb.com/video/...)
        api_urls = item.get("apiUrls") or []
        if api_urls:
            print(f"  [apify] Found video API URL: {api_urls[0][:80]}...")
            return api_urls[0]

        # 4. Video element src
        video_src = item.get("videoSrc")
        if video_src and "vid3rb" in video_src:
            print(f"  [apify] Found video src: {video_src[:80]}...")
            return video_src

        # 5. Source tags
        source_tags = item.get("sourceTags") or []
        for src in source_tags:
            if src and "vid3rb" in src:
                print(f"  [apify] Found source tag: {src[:80]}...")
                return src

        print(f"  [apify] Phase 2 debug: title={item.get('title')}, "
              f"bodyLength={item.get('bodyLength')}")

    print(f"  [apify] Phase 2: no video URL found")
    return None
