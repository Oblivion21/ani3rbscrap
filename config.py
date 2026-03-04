"""
Configuration for the anime3rb scraper.

Set your API keys and proxy credentials here, or via environment variables.
"""

import os

# ─── Target site ───────────────────────────────────────────────
BASE_URL = "https://anime3rb.com"
VIDEO_HOST_PATTERN = "files.vid3rb.com"
VIDEO_FILE_EXTENSION = ".mp4"

# ─── Proxy settings (Phase 2: Step 5) ─────────────────────────
PROXY_SERVER = os.environ.get("PROXY_SERVER", "")  # e.g. "http://proxy.iproyal.com:12321"
PROXY_USERNAME = os.environ.get("PROXY_USERNAME", "")
PROXY_PASSWORD = os.environ.get("PROXY_PASSWORD", "")

# ─── Paid API keys (Phase 3: Steps 6–9) ───────────────────────
SCRAPEOPS_API_KEY = os.environ.get("SCRAPEOPS_API_KEY", "")
SCRAPFLY_API_KEY = os.environ.get("SCRAPFLY_API_KEY", "")
CRAWLBASE_TOKEN = os.environ.get("CRAWLBASE_TOKEN", "")
SCRAPERAPI_KEY = os.environ.get("SCRAPERAPI_KEY", "")

# ─── Timeouts & retries ───────────────────────────────────────
PAGE_LOAD_TIMEOUT = 30  # seconds to wait for page load
CHALLENGE_WAIT = 10     # seconds to wait for Cloudflare challenge
NETWORK_IDLE_TIMEOUT = 15  # seconds to wait for network requests to settle
MAX_RETRIES = 2         # retries per method before moving to fallback
