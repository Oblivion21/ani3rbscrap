"""
Configuration for the anime3rb scraper.

Set your API keys and proxy credentials below.
Environment variables override the values here if set.
"""

import os

# ─── Target site ───────────────────────────────────────────────
BASE_URL = "https://anime3rb.com"
VIDEO_HOST_PATTERN = "files.vid3rb.com"
VIDEO_HOST_PATTERN_ALT = "video.vid3rb.com/video/"
VIDEO_FILE_EXTENSION = ".mp4"

# ─── Proxy settings (Phase 2: Step 5) ─────────────────────────
PROXY_SERVER = os.environ.get("PROXY_SERVER") or "https://geo.iproyal.com:12321"
PROXY_USERNAME = os.environ.get("PROXY_USERNAME") or "zjAfVmcBG4oxZVuc"
PROXY_PASSWORD = os.environ.get("PROXY_PASSWORD") or "kBie3DT0JM6Dfbqb"

# Apify — free $5/month, no credit card needed
# Get your token at: https://console.apify.com/account/integrations
APIFY_TOKEN = os.environ.get("APIFY_TOKEN") or ""

# ─── Timeouts & retries ───────────────────────────────────────
PAGE_LOAD_TIMEOUT = 60  # seconds to wait for page load
CHALLENGE_WAIT = 15     # seconds to wait for Cloudflare challenge
NETWORK_IDLE_TIMEOUT = 20  # seconds to wait for network requests to settle
MAX_RETRIES = 2         # retries per method (only for transient errors)
