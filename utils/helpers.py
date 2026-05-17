"""
utils/helpers.py — Retry logic, safe HTTP helpers, and text utilities.
"""

from __future__ import annotations

import asyncio
import logging
import re
from functools import wraps
from typing import Any, Callable, Optional
from urllib.parse import urlparse

import httpx

logger = logging.getLogger(__name__)

# ── Browser-like headers to reduce scraping blocks ────────────────────────
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}


def async_retry(retries: int = 3, delay: float = 1.0, exceptions=(Exception,)):
    """
    Decorator that retries an async function with exponential back-off.

    Usage:
        @async_retry(retries=3, delay=1.0)
        async def my_func(): ...
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exc: Optional[Exception] = None
            for attempt in range(1, retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as exc:
                    last_exc = exc
                    wait = delay * (2 ** (attempt - 1))
                    logger.warning(
                        "Attempt %d/%d for %s failed: %s. Retrying in %.1fs…",
                        attempt,
                        retries,
                        func.__name__,
                        exc,
                        wait,
                    )
                    if attempt < retries:
                        await asyncio.sleep(wait)
            raise last_exc  # type: ignore[misc]

        return wrapper

    return decorator


async def safe_scrape(
    url: str,
    timeout: float = 10.0,
    headers: Optional[dict] = None,
) -> Optional[str]:
    """
    Perform an HTTP GET and return the response text.
    Returns None on any failure — never raises.
    """
    try:
        hdrs = {**DEFAULT_HEADERS, **(headers or {})}
        async with httpx.AsyncClient(
            follow_redirects=True, timeout=timeout, headers=hdrs
        ) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return resp.text
    except Exception as exc:
        logger.debug("safe_scrape(%s) failed: %s", url, exc)
        return None


def truncate_for_llm(text: str, max_chars: int = 3000) -> str:
    """
    Truncate text to max_chars, breaking at a word boundary.
    Appends an ellipsis marker when truncated.
    """
    if len(text) <= max_chars:
        return text
    truncated = text[:max_chars]
    # Walk back to the last whitespace so we don't cut mid-word
    last_space = truncated.rfind(" ")
    if last_space > max_chars // 2:
        truncated = truncated[:last_space]
    return truncated + " … [truncated]"


def extract_domain(url: str) -> Optional[str]:
    """Return the bare domain (e.g. 'example.com') from a URL string."""
    try:
        parsed = urlparse(url if "://" in url else "https://" + url)
        domain = parsed.netloc or parsed.path
        # Strip www.
        domain = re.sub(r"^www\.", "", domain)
        return domain.lower() or None
    except Exception:
        return None


def first_name(full_name: str) -> str:
    """Return the first token of a full name."""
    return full_name.strip().split()[0] if full_name.strip() else full_name
