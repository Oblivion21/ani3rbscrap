"""
Step 3 — Nodriver

Successor to undetected-chromedriver. Simpler API.
May work if the site's Cloudflare config doesn't use CDP detection.
Intercepts network requests to capture the video mp4 URL.
"""

import asyncio
from typing import Optional

import config
from scraper.utils import extract_video_url, is_cloudflare_challenge, SkipMethod


METHOD_NAME = "nodriver"


async def scrape(episode_url: str) -> Optional[str]:
    """
    Launch a stealth Chrome browser via nodriver, navigate to the episode page,
    and capture the mp4 video URL via CDP network events.
    """
    try:
        import nodriver as uc
    except ImportError:
        raise SkipMethod(f"{METHOD_NAME}: nodriver not installed")

    print(f"  [{METHOD_NAME}] Launching stealth Chrome browser")

    captured_urls: list[str] = []
    browser = None

    try:
        browser_args = []
        if config.PROXY_SERVER:
            browser_args.append(f"--proxy-server={config.PROXY_SERVER}")

        browser = await uc.start(browser_args=browser_args if browser_args else None)

        # Enable network domain for request interception via CDP
        page = await browser.get("about:blank")

        # Set up network request monitoring via CDP
        await page.send(uc.cdp.network.enable())

        # Listen for network responses containing our video pattern
        async def monitor_network():
            """Monitor network events for video URLs in the background."""
            # nodriver uses CDP events; we'll check periodically via JS instead
            pass

        print(f"  [{METHOD_NAME}] Navigating to {episode_url}")
        page = await browser.get(episode_url)

        # Wait for Cloudflare challenge to resolve
        print(f"  [{METHOD_NAME}] Waiting for challenge resolution...")
        await asyncio.sleep(config.CHALLENGE_WAIT)

        content = await page.get_content()
        if is_cloudflare_challenge(content):
            print(f"  [{METHOD_NAME}] Still on challenge page, waiting more...")
            await asyncio.sleep(config.CHALLENGE_WAIT)
            content = await page.get_content()
            if is_cloudflare_challenge(content):
                print(f"  [{METHOD_NAME}] Challenge not resolved, failing")
                return None

        print(f"  [{METHOD_NAME}] Page loaded ({len(content)} chars)")

        # Check page source for video URL
        video_url = extract_video_url(content)
        if video_url:
            print(f"  [{METHOD_NAME}] Found video URL in page source")
            return video_url

        # Use JavaScript to monitor for video elements and network requests
        # Inject a PerformanceObserver to capture resource URLs
        await page.evaluate("""
            window.__captured_video_urls = [];
            const observer = new PerformanceObserver((list) => {
                for (const entry of list.getEntries()) {
                    if (entry.name.includes('vid3rb.com') && entry.name.includes('.mp4')) {
                        window.__captured_video_urls.push(entry.name);
                    }
                }
            });
            observer.observe({ entryTypes: ['resource'] });

            // Also check existing performance entries
            performance.getEntriesByType('resource').forEach(entry => {
                if (entry.name.includes('vid3rb.com') && entry.name.includes('.mp4')) {
                    window.__captured_video_urls.push(entry.name);
                }
            });
        """)

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

        # Wait for video request to appear
        print(f"  [{METHOD_NAME}] Waiting for video network request...")
        for _ in range(config.NETWORK_IDLE_TIMEOUT):
            await asyncio.sleep(1)

            # Check via JS PerformanceObserver
            try:
                urls = await page.evaluate("window.__captured_video_urls || []")
                if urls:
                    print(f"  [{METHOD_NAME}] Captured video URL via PerformanceObserver")
                    return urls[0]
            except Exception:
                pass

            # Check for video element src
            try:
                video_src = await page.evaluate("""
                    (() => {
                        const video = document.querySelector('video');
                        if (video && video.src && video.src.includes('vid3rb.com'))
                            return video.src;
                        const source = document.querySelector('video source');
                        if (source && source.src && source.src.includes('vid3rb.com'))
                            return source.src;
                        return null;
                    })()
                """)
                if video_src:
                    print(f"  [{METHOD_NAME}] Found video URL in <video> element")
                    return video_src
            except Exception:
                pass

        # Final check on full page content
        content = await page.get_content()
        video_url = extract_video_url(content)
        if video_url:
            print(f"  [{METHOD_NAME}] Found video URL in final page source")
            return video_url

        print(f"  [{METHOD_NAME}] No video URL captured")
        return None

    except Exception as e:
        print(f"  [{METHOD_NAME}] Error: {e}")
        return None
    finally:
        if browser:
            try:
                browser.stop()
            except Exception:
                pass
