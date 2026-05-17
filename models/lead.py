"""
models/lead.py — Pydantic v2 models for lead validation.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
from pydantic import AnyHttpUrl


class CompanySize(str, Enum):
    micro = "1-10"
    small = "11-50"
    medium = "51-200"
    large = "201-500"
    enterprise = "500+"


class LeadSubmission(BaseModel):
    full_name: str = Field(..., min_length=2, description="Prospect's full name")
    email: EmailStr = Field(..., description="Prospect's business email")
    company_name: str = Field(..., min_length=1, description="Company name")
    company_website: Optional[str] = Field(
        None, description="Company website URL (optional)"
    )
    industry: Optional[str] = Field(None, description="Industry or sector")
    company_size: Optional[CompanySize] = Field(
        None, description="Approximate employee count range"
    )
    role: Optional[str] = Field(
        None, description="Prospect's role, e.g. CEO, Marketing Head"
    )
    message: Optional[str] = Field(
        None, description="Free-text pain points or goals"
    )

    @field_validator("company_website", mode="before")
    @classmethod
    def validate_website(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v.strip() == "":
            return None
        v = v.strip()
        # Prepend scheme if missing so AnyHttpUrl can parse it
        if not v.startswith(("http://", "https://")):
            v = "https://" + v
        # Validate via pydantic's URL type
        try:
            AnyHttpUrl(v)
        except Exception:
            raise ValueError(f"'{v}' is not a valid URL")
        return v

    @field_validator("full_name", mode="before")
    @classmethod
    def strip_name(cls, v: str) -> str:
        return v.strip()

    @field_validator("company_name", mode="before")
    @classmethod
    def strip_company(cls, v: str) -> str:
        return v.strip()

    model_config = {"str_strip_whitespace": True}


class LeadResponse(BaseModel):
    status: str
    message: str


class WorkflowStatus(BaseModel):
    """Internal tracking object passed between pipeline stages."""

    lead: LeadSubmission
    enrichment_data: dict = Field(default_factory=dict)
    report_content: dict = Field(default_factory=dict)
    pdf_path: Optional[str] = None
    drive_url: Optional[str] = None
    sheets_row: Optional[int] = None
    errors: list[str] = Field(default_factory=list)
