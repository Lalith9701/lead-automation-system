"""
config.py — Centralised settings loaded from environment variables.
All other modules import from here; never read os.environ directly.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Anthropic ──────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL: str = "claude-sonnet-4-20250514"

# ── Clearbit ───────────────────────────────────────────────────────────────
CLEARBIT_API_KEY: str = os.getenv("CLEARBIT_API_KEY", "")

# ── NewsAPI ────────────────────────────────────────────────────────────────
NEWS_API_KEY: str = os.getenv("NEWS_API_KEY", "")

# ── SendGrid ───────────────────────────────────────────────────────────────
SENDGRID_API_KEY: str = os.getenv("SENDGRID_API_KEY", "")
FROM_EMAIL: str = os.getenv("FROM_EMAIL", "noreply@example.com")
FROM_NAME: str = os.getenv("FROM_NAME", "Lead Automation")

# ── SMTP fallback ──────────────────────────────────────────────────────────
SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER: str = os.getenv("SMTP_USER", "")
SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")

# ── Google ─────────────────────────────────────────────────────────────────
GOOGLE_SERVICE_ACCOUNT_JSON: str = os.getenv(
    "GOOGLE_SERVICE_ACCOUNT_JSON", "./credentials/service_account.json"
)
GOOGLE_SHEET_ID: str = os.getenv("GOOGLE_SHEET_ID", "")
GOOGLE_DRIVE_FOLDER_ID: str = os.getenv("GOOGLE_DRIVE_FOLDER_ID", "")

# ── App ────────────────────────────────────────────────────────────────────
PORT: int = int(os.getenv("PORT", "8000"))
OUTPUT_DIR: Path = Path(os.getenv("OUTPUT_DIR", "./output/reports"))
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Base directory of the project (used for template resolution)
BASE_DIR: Path = Path(__file__).resolve().parent
TEMPLATES_DIR: Path = BASE_DIR / "templates"
STATIC_DIR: Path = BASE_DIR / "static"
