#!/usr/bin/env python3
"""
Test script to verify multiple proxies from a file and report successes.

- Reads proxies from "Webshare 10 proxies.txt" (one proxy per line).
- Normalizes lines like "ip:port" -> "http://ip:port" (assumes HTTP if scheme missing).
- Tests each proxy against test URLs and records successes.
- Writes successes to "successful_proxies.txt" and failures to "failed_proxies.txt".
"""
import logging
import requests
from urllib.parse import urlparse

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

PROXY_FILE = "Webshare 10 proxies.txt"
SUCCESS_FILE = "successful_proxies.txt"
FAIL_FILE = "failed_proxies.txt"

# URLs to test (می‌توانید این لیست را تغییر دهید)
TEST_URLS = [
    "https://elevenlab-test.vercel.app/assistant/chat",
    "https://api.ipify.org?format=json",
]

TIMEOUT = 12.0  # ثانیه


def normalize_proxy_line(line: str) -> str:
    """
    Normalize proxy string:
    - strip whitespace and newlines
    - if scheme missing, assume http and prepend 'http://'
    - returns normalized proxy string (e.g. 'http://1.2.3.4:8080' or 'http://user:pass@1.2.3.4:8080')
    """
    s = line.strip()
    if not s:
        return ""
    parsed = urlparse(s)
    if parsed.scheme:
        return s  # already has scheme (http, https, socks5, ...)
    # no scheme -> assume http
    return "http://" + s


def test_single_proxy(proxy_url: str) -> bool:
    """
    Test a single proxy by trying all TEST_URLS.
    Returns True if at least one test URL succeeds (status_code in 200-399).
    """
    proxies = {"http": proxy_url, "https": proxy_url}
    logger.info(f"Testing proxy: {proxy_url}")
    for url in TEST_URLS:
        try:
            logger.info(f"  -> requesting {url}")
            resp = requests.get(url, proxies=proxies, timeout=TIMEOUT)
            logger.info(f"     status: {resp.status_code}")
            if 200 <= resp.status_code < 400:
                # optional extra validation: if ipify, inspect json
                if "ipify" in url:
                    try:
                        logger.info(f"     response body: {resp.json()}")
                    except Exception:
                        logger.debug("     couldn't parse json from ipify response")
                return True
        except requests.exceptions.RequestException as e:
            logger.debug(f"     request failed: {e}")
    return False


def main():
    try:
        with open(PROXY_FILE, "r", encoding="utf-8") as f:
            raw_lines = f.readlines()
    except FileNotFoundError:
        logger.error(f"Proxy file not found: {PROXY_FILE}")
        return

    proxies = [normalize_proxy_line(l) for l in raw_lines]
    proxies = [p for p in proxies if p]  # drop empty lines

    logger.info(f"Loaded {len(proxies)} proxies from {PROXY_FILE}")

    successful = []
    failed = []

    for p in proxies:
        ok = test_single_proxy(p)
        if ok:
            logger.info(f"SUCCESS: {p}")
            successful.append(p)
        else:
            logger.info(f"FAILED:  {p}")
            failed.append(p)

    # Summary
    logger.info("=== Summary ===")
    logger.info(f"Total tested: {len(proxies)}")
    logger.info(f"Successful:   {len(successful)}")
    logger.info(f"Failed:       {len(failed)}")

    # Write results to files
    with open(SUCCESS_FILE, "w", encoding="utf-8") as f:
        for s in successful:
            f.write(s + "\n")
    with open(FAIL_FILE, "w", encoding="utf-8") as f:
        for s in failed:
            f.write(s + "\n")

    logger.info(f"Successful proxies saved to: {SUCCESS_FILE}")
    logger.info(f"Failed proxies saved to: {FAIL_FILE}")


if __name__ == "__main__":
    main()
