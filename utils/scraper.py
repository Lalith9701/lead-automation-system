"""
utils/scraper.py — Web scraping utilities built on httpx + BeautifulSoup4.
"""

from __future__ import annotations

import logging
import re
from typing import Optional
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from utils.helpers import safe_scrape, truncate_for_llm

logger = logging.getLogger(__name__)


async def scrape_homepage(url: str) -> dict:
    """
    Scrape a company homepage and /about page.
    Returns a dict with title, meta_description, headings, body_text, about_text.
    """
    result: dict = {
        "title": None,
        "meta_description": None,
        "headings": [],
        "body_text": "",
        "about_text": "",
    }

    # ── Homepage ──────────────────────────────────────────────────────────
    html = await safe_scrape(url)
    if html:
        soup = BeautifulSoup(html, "lxml")

        # Title
        title_tag = soup.find("title")
        result["title"] = title_tag.get_text(strip=True) if title_tag else None

        # Meta description
        meta = soup.find("meta", attrs={"name": re.compile(r"description", re.I)})
        if meta and meta.get("content"):
            result["meta_description"] = meta["content"].strip()

        # H1 / H2 headings
        headings = []
        for tag in soup.find_all(["h1", "h2"]):
            text = tag.get_text(strip=True)
            if text:
                headings.append(text)
        result["headings"] = headings[:10]  # cap at 10

        # Body text (strip scripts/styles)
        for unwanted in soup(["script", "style", "nav", "footer", "header"]):
            unwanted.decompose()
        body_text = soup.get_text(separator=" ", strip=True)
        result["body_text"] = truncate_for_llm(body_text, max_chars=2000)

    # ── /about page ───────────────────────────────────────────────────────
    about_url = _build_about_url(url)
    if about_url:
        about_html = await safe_scrape(about_url)
        if about_html:
            about_soup = BeautifulSoup(about_html, "lxml")
            for unwanted in about_soup(["script", "style", "nav", "footer", "header"]):
                unwanted.decompose()
            about_text = about_soup.get_text(separator=" ", strip=True)
            result["about_text"] = truncate_for_llm(about_text, max_chars=2000)

    return result


def _build_about_url(base_url: str) -> Optional[str]:
    """Construct a likely /about URL from a base URL."""
    try:
        parsed = urlparse(base_url)
        return urljoin(f"{parsed.scheme}://{parsed.netloc}", "/about")
    except Exception:
        return None


async def scrape_duckduckgo(query: str) -> Optional[str]:
    """
    Use DuckDuckGo Instant Answer API to get a short description.
    Returns the AbstractText field or None.
    """
    try:
        import httpx

        params = {
            "q": query,
            "format": "json",
            "no_html": "1",
            "skip_disambig": "1",
        }
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(
                "https://api.duckduckgo.com/", params=params
            )
            resp.raise_for_status()
            data = resp.json()
            abstract = data.get("AbstractText", "").strip()
            return abstract if abstract else None
    except Exception as exc:
        logger.debug("DuckDuckGo scrape failed: %s", exc)
        return None


async def scrape_google_news_rss(company_name: str) -> list[dict]:
    """
    Scrape Google News RSS feed for recent mentions of the company.
    Returns a list of {title, link, published} dicts (up to 5).
    """
    results: list[dict] = []
    try:
        import urllib.parse

        query = urllib.parse.quote(f'"{company_name}"')
        rss_url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
        html = await safe_scrape(rss_url)
        if not html:
            return results

        soup = BeautifulSoup(html, "lxml-xml")
        for item in soup.find_all("item")[:5]:
            title_tag = item.find("title")
            link_tag = item.find("link")
            pub_tag = item.find("pubDate")
            results.append(
                {
                    "title": title_tag.get_text(strip=True) if title_tag else "",
                    "link": link_tag.get_text(strip=True) if link_tag else "",
                    "published": pub_tag.get_text(strip=True) if pub_tag else "",
                }
            )
    except Exception as exc:
        logger.debug("Google News RSS scrape failed: %s", exc)
    return results


async def detect_tech_stack(url: str) -> list[str]:
    """
    Lightweight tech-stack detection by inspecting HTML source for known
    fingerprints (script src, meta generators, link hrefs, etc.).
    """
    tech: list[str] = []
    html = await safe_scrape(url)
    if not html:
        return tech

    lower = html.lower()

    fingerprints = {
        "WordPress": ["wp-content", "wp-includes", "wordpress"],
        "Shopify": ["cdn.shopify.com", "shopify.com/s/files"],
        "Wix": ["wix.com", "wixstatic.com"],
        "Squarespace": ["squarespace.com", "squarespace-cdn.com"],
        "Webflow": ["webflow.com", "webflow.io"],
        "React": ["react.development.js", "react.production.min.js", "__react"],
        "Next.js": ["_next/static", "__next"],
        "Vue.js": ["vue.min.js", "vue.js", "__vue__"],
        "Angular": ["ng-version", "angular.min.js"],
        "jQuery": ["jquery.min.js", "jquery-"],
        "Bootstrap": ["bootstrap.min.css", "bootstrap.min.js"],
        "Tailwind CSS": ["tailwind"],
        "Google Analytics": ["google-analytics.com/analytics.js", "gtag("],
        "Google Tag Manager": ["googletagmanager.com/gtm.js"],
        "HubSpot": ["hs-scripts.com", "hubspot.com"],
        "Intercom": ["intercom.io", "widget.intercom.io"],
        "Stripe": ["js.stripe.com"],
        "Cloudflare": ["cloudflare"],
        "AWS": ["amazonaws.com", "cloudfront.net"],
        "Vercel": ["vercel.app", "_vercel"],
        "Netlify": ["netlify.app", "netlify.com"],
    }

    for name, patterns in fingerprints.items():
        if any(p in lower for p in patterns):
            tech.append(name)

    return tech
