"""
services/report_generator.py — AI report generation (Claude) + PDF rendering (WeasyPrint).
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

import anthropic
from jinja2 import Environment, FileSystemLoader

import config
from utils.helpers import truncate_for_llm

logger = logging.getLogger(__name__)

# Jinja2 environment pointing at the templates/ directory
_jinja_env = Environment(
    loader=FileSystemLoader(str(config.TEMPLATES_DIR)),
    autoescape=True,
)


class ReportGenerator:
    def __init__(self) -> None:
        self._client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

    # ── Public API ─────────────────────────────────────────────────────────

    async def generate(self, lead_data: dict, enrichment_data: dict) -> dict:
        """
        Call Claude to produce structured report JSON.
        Retries once with a stricter prompt if JSON parsing fails.
        """
        prompt = self._build_prompt(lead_data, enrichment_data)
        raw = await self._call_claude(prompt)
        report = self._parse_json(raw)

        if report is None:
            logger.warning("First JSON parse failed — retrying with strict prompt")
            strict_prompt = prompt + (
                "\n\nIMPORTANT: Your previous response could not be parsed as JSON. "
                "Respond with ONLY a valid JSON object. No markdown fences, no commentary."
            )
            raw2 = await self._call_claude(strict_prompt)
            report = self._parse_json(raw2)

        if report is None:
            logger.error("Claude did not return parseable JSON after retry")
            report = self._fallback_report(lead_data)

        return report

    async def render_pdf(
        self, lead_data: dict, enrichment_data: dict, report_content: dict
    ) -> str:
        """
        Render the Jinja2 HTML template → PDF via WeasyPrint.
        Returns the absolute path to the saved PDF file.
        """
        from weasyprint import HTML, CSS

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = re.sub(r"[^\w\-]", "_", lead_data.get("company_name", "report"))
        filename = f"{safe_name}_{timestamp}.pdf"
        output_path = config.OUTPUT_DIR / filename

        # Build template context
        context = {
            "lead": lead_data,
            "enrichment": enrichment_data,
            "report": report_content,
            "generated_at": datetime.now().strftime("%B %d, %Y"),
            "logo_url": enrichment_data.get("logo_url", ""),
            "static_dir": str(config.STATIC_DIR),
        }

        template = _jinja_env.get_template("report_template.html")
        html_content = template.render(**context)

        # Load CSS
        css_path = config.STATIC_DIR / "styles.css"
        css = CSS(filename=str(css_path)) if css_path.exists() else None

        # Render PDF
        html_obj = HTML(string=html_content, base_url=str(config.BASE_DIR))
        if css:
            html_obj.write_pdf(str(output_path), stylesheets=[css])
        else:
            html_obj.write_pdf(str(output_path))

        logger.info("PDF saved to %s", output_path)
        return str(output_path)

    # ── Private helpers ────────────────────────────────────────────────────

    def _build_prompt(self, lead_data: dict, enrichment_data: dict) -> str:
        # Truncate enrichment to avoid token overflow
        enrichment_str = truncate_for_llm(
            json.dumps(enrichment_data, indent=2), max_chars=4000
        )

        return f"""Generate a comprehensive business audit report for the following prospect.

Name: {lead_data.get('full_name')} | Role: {lead_data.get('role', 'N/A')}
Company: {lead_data.get('company_name')}
Website: {lead_data.get('company_website', 'N/A')}
Industry: {lead_data.get('industry', 'N/A')}
Size: {lead_data.get('company_size', 'N/A')}

Enriched Data:
{enrichment_str}

Additional context from prospect: {lead_data.get('message', 'None provided')}

Data confidence level: {enrichment_data.get('data_confidence', 'low')}
{"NOTE: Data confidence is low. Make reasonable, clearly-labeled assumptions based on the company name and industry." if enrichment_data.get('data_confidence') == 'low' else ""}

Generate the report in the following JSON structure (respond ONLY with valid JSON, no markdown fences):
{{
  "executive_summary": "2-3 paragraph personalized summary of the company and why this audit matters for them specifically",
  "company_overview": {{
    "what_they_do": "...",
    "market_position": "...",
    "key_strengths": ["...", "...", "..."],
    "notable_achievements": "..."
  }},
  "digital_presence_audit": {{
    "website_analysis": "detailed analysis of their web presence",
    "seo_observations": "observations about their likely SEO posture",
    "content_strategy": "assessment of their content and messaging",
    "score": "X/10",
    "recommendations": ["...", "...", "..."]
  }},
  "competitive_landscape": {{
    "market_overview": "...",
    "key_competitors": ["...", "...", "..."],
    "differentiators": "what makes this company unique",
    "threats_and_opportunities": "..."
  }},
  "growth_opportunities": [
    {{
      "title": "Opportunity title",
      "description": "Detailed description",
      "impact": "High",
      "effort": "Medium",
      "recommended_action": "Specific actionable step"
    }}
  ],
  "tech_and_operations": {{
    "current_stack_observations": "...",
    "automation_gaps": "...",
    "recommended_tools": ["...", "..."]
  }},
  "action_plan": {{
    "immediate_actions": ["...", "...", "..."],
    "short_term_30_60_days": ["...", "..."],
    "long_term_90_plus_days": ["...", "..."]
  }},
  "closing_note": "A warm, personalized closing paragraph addressed to {lead_data.get('full_name')} specifically, mentioning something specific about their company"
}}

Generate 3-4 growth opportunities. Tailor every section specifically to {lead_data.get('company_name')} — never use generic filler text."""

    async def _call_claude(self, prompt: str) -> str:
        """Send prompt to Claude and return the text response."""
        message = self._client.messages.create(
            model=config.CLAUDE_MODEL,
            max_tokens=4096,
            system=(
                "You are a senior business analyst and consultant. You write professional, "
                "insightful business audit reports that help companies understand their digital "
                "presence, competitive position, and growth opportunities. Your tone is "
                "authoritative but approachable. You must tailor every section specifically to "
                "the company provided — never use generic filler text."
            ),
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text

    def _parse_json(self, text: str) -> Optional[dict]:
        """
        Extract and parse JSON from Claude's response.
        Handles markdown code fences if present.
        """
        # Strip markdown fences
        text = re.sub(r"```(?:json)?\s*", "", text).strip()
        text = text.rstrip("`").strip()

        # Try direct parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try to find the outermost { ... } block
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                pass

        return None

    def _fallback_report(self, lead_data: dict) -> dict:
        """Minimal fallback report when Claude fails entirely."""
        company = lead_data.get("company_name", "Your Company")
        name = lead_data.get("full_name", "there")
        return {
            "executive_summary": (
                f"This audit report was prepared for {company}. "
                "Due to a temporary processing issue, some sections contain placeholder content. "
                "Please contact us for a full analysis."
            ),
            "company_overview": {
                "what_they_do": "Information not available",
                "market_position": "Information not available",
                "key_strengths": ["To be determined"],
                "notable_achievements": "Information not available",
            },
            "digital_presence_audit": {
                "website_analysis": "Analysis pending",
                "seo_observations": "Analysis pending",
                "content_strategy": "Analysis pending",
                "score": "N/A",
                "recommendations": ["Please contact us for a detailed analysis"],
            },
            "competitive_landscape": {
                "market_overview": "Analysis pending",
                "key_competitors": [],
                "differentiators": "Analysis pending",
                "threats_and_opportunities": "Analysis pending",
            },
            "growth_opportunities": [
                {
                    "title": "Full Analysis Available",
                    "description": "Contact us for a complete growth opportunity analysis.",
                    "impact": "High",
                    "effort": "Low",
                    "recommended_action": "Schedule a consultation call",
                }
            ],
            "tech_and_operations": {
                "current_stack_observations": "Analysis pending",
                "automation_gaps": "Analysis pending",
                "recommended_tools": [],
            },
            "action_plan": {
                "immediate_actions": ["Contact us to discuss your goals"],
                "short_term_30_60_days": ["Schedule a strategy session"],
                "long_term_90_plus_days": ["Develop a comprehensive growth plan"],
            },
            "closing_note": (
                f"Thank you, {name}, for your interest. We look forward to helping "
                f"{company} achieve its goals."
            ),
        }
