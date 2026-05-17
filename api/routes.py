"""
api/routes.py — FastAPI router for the lead submission endpoint.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse

from models.lead import LeadResponse, LeadSubmission, WorkflowStatus
from services.enrichment import EnrichmentService
from services.report_generator import ReportGenerator
from services.email_sender import EmailSender
from services.sheets_logger import SheetsLogger
from services.drive_uploader import DriveUploader

logger = logging.getLogger(__name__)
router = APIRouter()

# Singletons — instantiated once at import time
_enrichment = EnrichmentService()
_report_gen = ReportGenerator()
_email = EmailSender()
_sheets = SheetsLogger()
_drive = DriveUploader()


@router.post("/submit-lead", response_model=LeadResponse, status_code=200)
async def submit_lead(
    lead: LeadSubmission,
    background_tasks: BackgroundTasks,
) -> LeadResponse:
    """
    Accept a lead form submission, immediately acknowledge it, and kick off
    the enrichment → report → email pipeline as a background task.
    """
    logger.info("Lead received: %s <%s>", lead.full_name, lead.email)

    # Log to Sheets immediately (status = "processing")
    lead_dict = lead.model_dump()
    row_index = _sheets.append_lead(lead_dict)

    background_tasks.add_task(
        _run_pipeline,
        lead_dict=lead_dict,
        row_index=row_index,
    )

    return LeadResponse(
        status="processing",
        message="Your report is being generated and will be emailed shortly.",
    )


async def _run_pipeline(lead_dict: dict, row_index: int | None) -> None:
    """
    Full automation pipeline:
      1. Enrich company data
      2. Generate AI report content
      3. Render PDF
      4. Upload to Drive (bonus)
      5. Send email
      6. Update Sheets status
    """
    errors: list[str] = []
    enrichment_data: dict = {}
    report_content: dict = {}
    pdf_path: str | None = None
    drive_url: str | None = None

    company = lead_dict.get("company_name", "Unknown")
    logger.info("Pipeline started for: %s", company)

    # ── Step 1: Enrichment ─────────────────────────────────────────────
    try:
        enrichment_data = await _enrichment.enrich(lead_dict)
        _sheets.update_status(
            row_index,
            status="enriched",
            confidence=enrichment_data.get("data_confidence", ""),
        )
        logger.info("Enrichment complete (confidence=%s)", enrichment_data.get("data_confidence"))
    except Exception as exc:
        msg = f"Enrichment failed: {exc}"
        logger.error(msg)
        errors.append(msg)
        _sheets.update_status(row_index, status="enrichment_failed", error_notes=msg)

    # ── Step 2: AI Report Generation ──────────────────────────────────
    try:
        report_content = await _report_gen.generate(lead_dict, enrichment_data)
        _sheets.update_status(row_index, status="report_generated")
        logger.info("Report content generated for %s", company)
    except Exception as exc:
        msg = f"Report generation failed: {exc}"
        logger.error(msg)
        errors.append(msg)
        _sheets.update_status(row_index, status="report_failed", error_notes=msg)

    # ── Step 3: PDF Rendering ──────────────────────────────────────────
    try:
        pdf_path = await _report_gen.render_pdf(lead_dict, enrichment_data, report_content)
        _sheets.update_status(row_index, status="pdf_ready", pdf_path=pdf_path)
        logger.info("PDF rendered: %s", pdf_path)
    except Exception as exc:
        msg = f"PDF rendering failed: {exc}"
        logger.error(msg)
        errors.append(msg)
        _sheets.update_status(row_index, status="pdf_failed", error_notes=msg)

    # ── Step 4: Google Drive Upload (bonus) ────────────────────────────
    if pdf_path:
        try:
            drive_url = _drive.upload(pdf_path, company)
            if drive_url:
                _sheets.update_status(row_index, status="uploaded", drive_url=drive_url)
                logger.info("Drive upload complete: %s", drive_url)
        except Exception as exc:
            msg = f"Drive upload failed: {exc}"
            logger.warning(msg)
            errors.append(msg)

    # ── Step 5: Email ──────────────────────────────────────────────────
    if pdf_path:
        try:
            sent = await _email.send_report(
                lead_data=lead_dict,
                report_content=report_content,
                pdf_path=pdf_path,
                drive_url=drive_url,
            )
            if sent:
                _sheets.update_status(row_index, status="emailed")
                logger.info("Email sent to %s", lead_dict.get("email"))
            else:
                _sheets.update_status(row_index, status="email_failed")
                errors.append("Email delivery failed")
        except Exception as exc:
            msg = f"Email failed: {exc}"
            logger.error(msg)
            errors.append(msg)
            _sheets.update_status(row_index, status="email_failed", error_notes=msg)
    else:
        logger.warning("Skipping email — no PDF was generated")
        errors.append("Email skipped: no PDF available")

    # ── Final status ───────────────────────────────────────────────────
    final_status = "complete" if not errors else f"complete_with_warnings"
    _sheets.update_status(
        row_index,
        status=final_status,
        error_notes="; ".join(errors) if errors else "",
    )
    logger.info(
        "Pipeline finished for %s — status=%s errors=%d",
        company,
        final_status,
        len(errors),
    )
