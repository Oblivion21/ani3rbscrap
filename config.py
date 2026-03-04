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
PROXY_SERVER = os.environ.get("https://geo.iproyal.com:12321")  # e.g. "http://proxy.iproyal.com:12321"
PROXY_USERNAME = os.environ.get("zjAfVmcBG4oxZVuc")
PROXY_PASSWORD = os.environ.get("kBie3DT0JM6Dfbqb")

# ─── Paid API keys (Phase 3: Steps 6–9) ───────────────────────
SCRAPEOPS_API_KEY = os.environ.get("2be635e7-d1a2-4043-adf0-4b1aef27ad6a"
)
SCRAPFLY_API_KEY = os.environ.get("scp-live-c1d72453a9034f8ba2f8669dbe77c8ad")
CRAWLBASE_TOKEN = os.environ.get("Uxa3140A7nPCNvQMcgNwmg")
SCRAPERAPI_KEY = os.environ.get("29e43c18d4b6d6e4b0e37c1758ef57eb")

# ─── Timeouts & retries ───────────────────────────────────────
PAGE_LOAD_TIMEOUT = 30  # seconds to wait for page load
CHALLENGE_WAIT = 10     # seconds to wait for Cloudflare challenge
NETWORK_IDLE_TIMEOUT = 15  # seconds to wait for network requests to settle
MAX_RETRIES = 2         # retries per method before moving to fallback
