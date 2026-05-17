"""
services/enrichment.py — Company data enrichment pipeline.

Strategy (tried in order, results merged):
  1. Scrape homepage + /about
  2. Clearbit Company API (if key available)
  3. DuckDuckGo Instant Answer
  4. LinkedIn page (best-effort, graceful on block)
  5. NewsAPI / Google News RSS
  6. Tech-stack detection
"""

from __future__ import annotations

import logging
from typing import Optional
from urllib.parse import urlparse

import httpx

import config
from utils.helpers import extract_domain, safe_scrape, truncate_for_llm
from utils.scraper import (
    detect_tech_stack,
    scrape_duckduckgo,
    scrape_google_news_rss,
    scrape_homepage,
)

logger = logging.getLogger(__name__)


class EnrichmentService:
    async def enrich(self, lead_data: dict) -> dict:
        """
        Run all enrichment steps and return a merged dict.
        Never raises — failures are logged and skipped.
        """
        company_name: str = lead_data.get("company_name", "")
        website: Optional[str] = lead_data.get("company_website")
        domain: Optional[str] = extract_domain(website) if website else None

        enriched: dict = {
            "company_name": company_name,
            "domain": domain,
            "description": None,
            "industry": lead_data.get("industry"),
            "founded_year": None,
            "employee_count": lead_data.get("company_size"),
            "hq_location": None,
            "key_products_services": [],
            "recent_news": [],
            "tech_stack": [],
            "social_media": {},
            "competitors": [],
            "funding_stage": None,
            "logo_url": None,
            "website_data": {},
            "data_confidence": "low",
        }

        # ── Logo URL (Clearbit Logo API — always free) ─────────────────────
        if domain:
            enriched["logo_url"] = f"https://logo.clearbit.com/{domain}"

        # ── Step 1: Scrape homepage ────────────────────────────────────────
        if website:
            try:
                website_data = await scrape_homepage(website)
                enriched["website_data"] = website_data
                if website_data.get("meta_description"):
                    enriched["description"] = website_data["meta_description"]
                logger.info("Homepage scrape succeeded for %s", website)
            except Exception as exc:
                logger.warning("Homepage scrape failed: %s", exc)

        # ── Step 2: Clearbit Autocomplete (always free) ────────────────────
        try:
            clearbit_data = await self._clearbit_autocomplete(company_name, domain)
            if clearbit_data:
                enriched = _merge(enriched, clearbit_data)
                logger.info("Clearbit autocomplete succeeded")
        except Exception as exc:
            logger.warning("Clearbit autocomplete failed: %s", exc)

        # ── Step 2b: Clearbit full Company API (requires key) ──────────────
        if config.CLEARBIT_API_KEY and domain:
            try:
                full_data = await self._clearbit_company_api(domain)
                if full_data:
                    enriched = _merge(enriched, full_data)
                    logger.info("Clearbit Company API succeeded")
            except Exception as exc:
                logger.warning("Clearbit Company API failed: %s", exc)

        # ── Step 3: DuckDuckGo Instant Answer ─────────────────────────────
        if not enriched.get("description"):
            try:
                ddg = await scrape_duckduckgo(f"{company_name} company")
                if ddg:
                    enriched["description"] = ddg
                    logger.info("DuckDuckGo description found")
            except Exception as exc:
                logger.warning("DuckDuckGo failed: %s", exc)

        # ── Step 4: LinkedIn (best-effort) ────────────────────────────────
        try:
            li_data = await self._scrape_linkedin(company_name, domain)
            if li_data:
                enriched = _merge(enriched, li_data)
                logger.info("LinkedIn scrape returned data")
        except Exception as exc:
            logger.warning("LinkedIn scrape failed: %s", exc)

        # ── Step 5: News ───────────────────────────────────────────────────
        try:
            news = await self._fetch_news(company_name)
            if news:
                enriched["recent_news"] = news
                logger.info("Fetched %d news items", len(news))
        except Exception as exc:
            logger.warning("News fetch failed: %s", exc)

        # ── Step 6: Tech stack ─────────────────────────────────────────────
        if website:
            try:
                tech = await detect_tech_stack(website)
                if tech:
                    enriched["tech_stack"] = tech
                    logger.info("Tech stack detected: %s", tech)
            except Exception as exc:
                logger.warning("Tech stack detection failed: %s", exc)

        # ── Confidence scoring ─────────────────────────────────────────────
        enriched["data_confidence"] = _score_confidence(enriched)

        return enriched

    # ── Private helpers ────────────────────────────────────────────────────

    async def _clearbit_autocomplete(
        self, company_name: str, domain: Optional[str]
    ) -> Optional[dict]:
        """
        Use Clearbit's free autocomplete endpoint to get basic company info.
        """
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(
                "https://autocomplete.clearbit.com/v1/companies/suggest",
                params={"query": company_name},
            )
            resp.raise_for_status()
            results = resp.json()

        if not results:
            return None

        # Pick the best match: prefer domain match, else first result
        match = results[0]
        if domain:
            for r in results:
                if domain in r.get("domain", ""):
                    match = r
                    break

        return {
            "description": match.get("name"),
            "domain": match.get("domain"),
            "logo_url": match.get("logo"),
        }

    async def _clearbit_company_api(self, domain: str) -> Optional[dict]:
        """
        Call Clearbit's paid Company API for full enrichment.
        Requires CLEARBIT_API_KEY.
        """
        async with httpx.AsyncClient(
            timeout=10.0,
            auth=(config.CLEARBIT_API_KEY, ""),
        ) as client:
            resp = await client.get(
                "https://company.clearbit.com/v2/companies/find",
                params={"domain": domain},
            )
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            data = resp.json()

        result: dict = {}
        if data.get("description"):
            result["description"] = data["description"]
        if data.get("foundedYear"):
            result["founded_year"] = data["foundedYear"]
        if data.get("metrics", {}).get("employees"):
            result["employee_count"] = str(data["metrics"]["employees"])
        if data.get("geo", {}).get("city"):
            city = data["geo"]["city"]
            country = data["geo"].get("country", "")
            result["hq_location"] = f"{city}, {country}".strip(", ")
        if data.get("category", {}).get("industry"):
            result["industry"] = data["category"]["industry"]
        if data.get("tags"):
            result["key_products_services"] = data["tags"][:5]
        if data.get("linkedin", {}).get("handle"):
            result.setdefault("social_media", {})["linkedin"] = (
                f"https://linkedin.com/company/{data['linkedin']['handle']}"
            )
        if data.get("twitter", {}).get("handle"):
            result.setdefault("social_media", {})["twitter"] = (
                f"https://twitter.com/{data['twitter']['handle']}"
            )
        if data.get("crunchbase", {}).get("handle"):
            result["funding_stage"] = "See Crunchbase: " + data["crunchbase"]["handle"]

        return result or None

    async def _scrape_linkedin(
        self, company_name: str, domain: Optional[str]
    ) -> Optional[dict]:
        """
        Attempt to scrape a LinkedIn company page.
        LinkedIn aggressively blocks bots — we handle failure gracefully.
        """
        slug = company_name.lower().replace(" ", "-").replace(",", "")
        li_url = f"https://www.linkedin.com/company/{slug}"
        html = await safe_scrape(li_url, timeout=8.0)
        if not html or "authwall" in html.lower() or "join linkedin" in html.lower():
            return None

        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "lxml")
        result: dict = {"social_media": {"linkedin": li_url}}

        # Try to extract tagline / description
        desc_tag = soup.find("p", class_=lambda c: c and "description" in c.lower())
        if desc_tag:
            result["description"] = truncate_for_llm(
                desc_tag.get_text(strip=True), 500
            )

        return result if len(result) > 1 else None

    async def _fetch_news(self, company_name: str) -> list[dict]:
        """
        Fetch recent news via NewsAPI (if key set) or Google News RSS fallback.
        """
        if config.NEWS_API_KEY:
            try:
                async with httpx.AsyncClient(timeout=8.0) as client:
                    resp = await client.get(
                        "https://newsapi.org/v2/everything",
                        params={
                            "q": f'"{company_name}"',
                            "sortBy": "publishedAt",
                            "pageSize": 5,
                            "apiKey": config.NEWS_API_KEY,
                        },
                    )
                    resp.raise_for_status()
                    articles = resp.json().get("articles", [])
                    return [
                        {
                            "title": a.get("title", ""),
                            "source": a.get("source", {}).get("name", ""),
                            "published": a.get("publishedAt", ""),
                            "url": a.get("url", ""),
                        }
                        for a in articles[:5]
                    ]
            except Exception as exc:
                logger.debug("NewsAPI failed, falling back to RSS: %s", exc)

        # Fallback: Google News RSS
        return await scrape_google_news_rss(company_name)


# ── Helpers ────────────────────────────────────────────────────────────────

def _merge(base: dict, update: dict) -> dict:
    """
    Merge update into base, only overwriting None/empty values.
    Lists are extended (deduplicated). Dicts are recursively merged.
    """
    for key, value in update.items():
        if value is None or value == "" or value == [] or value == {}:
            continue
        existing = base.get(key)
        if isinstance(existing, list) and isinstance(value, list):
            combined = existing + [v for v in value if v not in existing]
            base[key] = combined
        elif isinstance(existing, dict) and isinstance(value, dict):
            base[key] = {**existing, **value}
        elif not existing:
            base[key] = value
    return base


def _score_confidence(data: dict) -> str:
    """
    Score enrichment confidence based on how many fields were populated.
    """
    scored_fields = [
        "description",
        "industry",
        "founded_year",
        "employee_count",
        "hq_location",
        "key_products_services",
        "recent_news",
        "tech_stack",
        "social_media",
    ]
    filled = sum(1 for f in scored_fields if data.get(f))
    if filled >= 6:
        return "high"
    if filled >= 3:
        return "medium"
    return "low"
