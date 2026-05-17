"""
services/email_sender.py — Email delivery via SendGrid (primary) or SMTP (fallback).
"""

from __future__ import annotations

import logging
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Optional

from jinja2 import Environment, FileSystemLoader

import config
from utils.helpers import first_name

logger = logging.getLogger(__name__)

_jinja_env = Environment(
    loader=FileSystemLoader(str(config.TEMPLATES_DIR)),
    autoescape=True,
)


class EmailSender:
    async def send_report(
        self,
        lead_data: dict,
        report_content: dict,
        pdf_path: str,
        drive_url: Optional[str] = None,
    ) -> bool:
        """
        Send the audit report email with PDF attachment.
        Returns True on success, False on failure (never raises).
        """
        try:
            subject = f"Your Personalized Business Audit Report — {lead_data.get('company_name', '')}"
            html_body = self._render_email_body(lead_data, report_content, drive_url)

            if config.SENDGRID_API_KEY:
                success = await self._send_sendgrid(
                    to_email=lead_data["email"],
                    subject=subject,
                    html_body=html_body,
                    pdf_path=pdf_path,
                )
                if success:
                    return True
                logger.warning("SendGrid failed — falling back to SMTP")

            # SMTP fallback
            return self._send_smtp(
                to_email=lead_data["email"],
                subject=subject,
                html_body=html_body,
                pdf_path=pdf_path,
            )

        except Exception as exc:
            logger.error("Email send failed: %s", exc)
            return False

    # ── SendGrid ───────────────────────────────────────────────────────────

    async def _send_sendgrid(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        pdf_path: str,
    ) -> bool:
        try:
            import base64

            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import (
                Attachment,
                ContentId,
                Disposition,
                FileContent,
                FileName,
                FileType,
                Mail,
            )

            message = Mail(
                from_email=(config.FROM_EMAIL, config.FROM_NAME),
                to_emails=to_email,
                subject=subject,
                html_content=html_body,
            )

            # Attach PDF
            pdf_bytes = Path(pdf_path).read_bytes()
            encoded = base64.b64encode(pdf_bytes).decode()
            attachment = Attachment(
                FileContent(encoded),
                FileName(Path(pdf_path).name),
                FileType("application/pdf"),
                Disposition("attachment"),
            )
            message.attachment = attachment

            sg = SendGridAPIClient(config.SENDGRID_API_KEY)
            response = sg.send(message)
            logger.info("SendGrid response: %s", response.status_code)
            return response.status_code in (200, 202)

        except Exception as exc:
            logger.error("SendGrid error: %s", exc)
            return False

    # ── SMTP fallback ──────────────────────────────────────────────────────

    def _send_smtp(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        pdf_path: str,
    ) -> bool:
        try:
            msg = MIMEMultipart("mixed")
            msg["From"] = f"{config.FROM_NAME} <{config.FROM_EMAIL}>"
            msg["To"] = to_email
            msg["Subject"] = subject

            # HTML body
            msg.attach(MIMEText(html_body, "html"))

            # PDF attachment
            pdf_bytes = Path(pdf_path).read_bytes()
            part = MIMEBase("application", "pdf")
            part.set_payload(pdf_bytes)
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f'attachment; filename="{Path(pdf_path).name}"',
            )
            msg.attach(part)

            with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT) as server:
                server.ehlo()
                server.starttls()
                server.login(config.SMTP_USER, config.SMTP_PASSWORD)
                server.sendmail(config.FROM_EMAIL, to_email, msg.as_string())

            logger.info("SMTP email sent to %s", to_email)
            return True

        except Exception as exc:
            logger.error("SMTP error: %s", exc)
            return False

    # ── Template rendering ─────────────────────────────────────────────────

    def _render_email_body(
        self,
        lead_data: dict,
        report_content: dict,
        drive_url: Optional[str],
    ) -> str:
        """Render the HTML email body using the Jinja2 email template."""
        # Extract a teaser insight from the report
        opportunities = report_content.get("growth_opportunities", [])
        teaser_opportunity = opportunities[0] if opportunities else None

        digital_score = (
            report_content.get("digital_presence_audit", {}).get("score", "")
        )

        context = {
            "first_name": first_name(lead_data.get("full_name", "")),
            "full_name": lead_data.get("full_name", ""),
            "company_name": lead_data.get("company_name", ""),
            "executive_summary_snippet": (
                report_content.get("executive_summary", "")[:300] + "…"
                if report_content.get("executive_summary")
                else ""
            ),
            "teaser_opportunity": teaser_opportunity,
            "digital_score": digital_score,
            "drive_url": drive_url,
            "from_name": config.FROM_NAME,
            "from_email": config.FROM_EMAIL,
        }

        try:
            template = _jinja_env.get_template("email_template.html")
            return template.render(**context)
        except Exception as exc:
            logger.warning("Email template render failed, using plain fallback: %s", exc)
            return self._plain_email_fallback(context)

    def _plain_email_fallback(self, ctx: dict) -> str:
        cta = (
            f'<a href="{ctx["drive_url"]}">View Your Full Report</a>'
            if ctx.get("drive_url")
            else "Please find your report attached."
        )
        return f"""
        <html><body>
        <p>Hi {ctx['first_name']},</p>
        <p>Your personalized Business Audit Report for <strong>{ctx['company_name']}</strong>
        is ready.</p>
        <p>{ctx.get('executive_summary_snippet', '')}</p>
        <p>{cta}</p>
        <p>Best regards,<br>{ctx['from_name']}</p>
        </body></html>
        """
