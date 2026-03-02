"""
PRAVA — HTTP client utility.
Shared requests session with retry logic and rate limiting.
"""
import time
import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "fr-FR,fr;q=0.9,nl-NL,nl;q=0.9",
}

# Seconds between requests (be a polite scraper)
DEFAULT_REQUEST_DELAY = 1.5


def get_session(
    retries: int = 3,
    backoff_factor: float = 1.0,
    status_forcelist: tuple = (429, 500, 502, 503, 504),
    headers: dict | None = None,
) -> requests.Session:
    """
    Create a requests.Session with automatic retry and sensible defaults.

    Args:
        retries: Number of retries on failure.
        backoff_factor: Multiplier for retry delays (1s, 2s, 4s...).
        status_forcelist: HTTP status codes that trigger a retry.
        headers: Additional headers to merge with defaults.

    Returns:
        Configured requests.Session
    """
    session = requests.Session()

    retry_strategy = Retry(
        total=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        allowed_methods=["GET"],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    merged_headers = {**DEFAULT_HEADERS, **(headers or {})}
    session.headers.update(merged_headers)

    return session


def get_page(url: str, session: requests.Session | None = None, delay: float = DEFAULT_REQUEST_DELAY) -> requests.Response:
    """
    Fetch a page with optional rate limiting delay.

    Args:
        url: URL to fetch.
        session: Existing session (creates one if None).
        delay: Seconds to wait before the request.

    Returns:
        requests.Response

    Raises:
        requests.HTTPError: If the response status is 4xx/5xx.
    """
    if session is None:
        session = get_session()

    if delay > 0:
        time.sleep(delay)

    logger.debug(f"GET {url}")
    response = session.get(url, timeout=30)
    response.raise_for_status()
    return response
