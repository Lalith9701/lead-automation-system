# Lead Automation System

An end-to-end lead automation pipeline built with FastAPI. When a prospect submits a form, the system automatically enriches their company data, generates a personalised PDF audit report using Claude AI, and emails it — all without human intervention.

---

## Architecture

```
Browser (index.html)
        │
        │  POST /api/v1/submit-lead
        ▼
┌───────────────────────────────────────────────────────────┐
│                     FastAPI (main.py)                     │
│                                                           │
│  ① Validate lead (Pydantic)                               │
│  ② Return 200 immediately                                 │
│  ③ Kick off BackgroundTask ──────────────────────────┐    │
└──────────────────────────────────────────────────────┼────┘
                                                       │
                    Background Pipeline                │
                    ───────────────────                ▼
          ┌──────────────────────────────────────────────┐
          │  EnrichmentService                           │
          │  ├─ Scrape homepage + /about (httpx + BS4)   │
          │  ├─ Clearbit Autocomplete API (free)         │
          │  ├─ Clearbit Company API (if key set)        │
          │  ├─ DuckDuckGo Instant Answer                │
          │  ├─ LinkedIn (best-effort)                   │
          │  ├─ NewsAPI / Google News RSS                │
          │  └─ Tech-stack fingerprinting                │
          └──────────────────┬───────────────────────────┘
                             │ enrichment_data
                             ▼
          ┌──────────────────────────────────────────────┐
          │  ReportGenerator — Claude claude-sonnet-4    │
          │  ├─ Build dynamic prompt                     │
          │  ├─ Call Anthropic API                       │
          │  ├─ Parse JSON response (retry once)         │
          │  └─ Render HTML → PDF (Jinja2 + WeasyPrint)  │
          └──────────────────┬───────────────────────────┘
                             │ pdf_path
                             ▼
          ┌──────────────────────────────────────────────┐
          │  DriveUploader (bonus)                       │
          │  └─ Upload PDF → Google Drive (shareable URL)│
          └──────────────────┬───────────────────────────┘
                             │ drive_url
                             ▼
          ┌──────────────────────────────────────────────┐
          │  EmailSender                                 │
          │  ├─ SendGrid (primary)                       │
          │  └─ SMTP / Gmail (fallback)                  │
          └──────────────────┬───────────────────────────┘
                             │
                             ▼
          ┌──────────────────────────────────────────────┐
          │  SheetsLogger (bonus)                        │
          │  └─ Append / update row in Google Sheet      │
          └──────────────────────────────────────────────┘
```

---

## Prerequisites

- Python 3.10+
- [WeasyPrint system dependencies](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#installation) (Pango, Cairo, GDK-PixBuf)
- API keys (see Configuration)

### WeasyPrint on Windows

```
pip install weasyprint
```

WeasyPrint on Windows requires GTK3 runtime libraries. The easiest path is the
[GTK3 runtime installer](https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases).

---

## Installation

```bash
# 1. Clone / download the project
cd lead-automation

# 2. Create a virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux

# 3. Install dependencies
pip install -r requirements.txt
```

---

## Configuration

Copy `.env.example` to `.env` and fill in your keys:

```bash
copy .env.example .env   # Windows
# cp .env.example .env   # macOS / Linux
```

| Variable | Required | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | ✅ | Claude API key from console.anthropic.com |
| `SENDGRID_API_KEY` | ✅ (or SMTP) | SendGrid API key |
| `FROM_EMAIL` | ✅ | Verified sender email |
| `FROM_NAME` | ✅ | Sender display name |
| `SMTP_HOST/PORT/USER/PASSWORD` | Fallback | Gmail SMTP credentials |
| `CLEARBIT_API_KEY` | Optional | Enables full Clearbit enrichment |
| `NEWS_API_KEY` | Optional | Enables NewsAPI (free tier: 100 req/day) |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Bonus | Path to service account JSON |
| `GOOGLE_SHEET_ID` | Bonus | Google Sheet ID for logging |
| `GOOGLE_DRIVE_FOLDER_ID` | Bonus | Drive folder ID for PDF uploads |

### Google Service Account Setup (Bonus features)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project → Enable **Google Sheets API** and **Google Drive API**
3. Create a Service Account → Download the JSON key
4. Save the JSON to `./credentials/service_account.json`
5. Share your Google Sheet with the service account email (Editor role)
6. Share your Drive folder with the service account email (Editor role)

---

## Running

```bash
uvicorn main:app --reload --port 8000
```

Open [http://localhost:8000](http://localhost:8000) to see the lead intake form.

API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## API Documentation

### `POST /api/v1/submit-lead`

Accepts a lead form submission and triggers the automation pipeline.

**Request body (JSON):**

```json
{
  "full_name":       "Jane Smith",
  "email":           "jane@acme.com",
  "company_name":    "Acme Corp",
  "company_website": "https://acme.com",
  "industry":        "SaaS",
  "company_size":    "51-200",
  "role":            "CEO",
  "message":         "We want to improve our SEO and lead generation."
}
```

**Required fields:** `full_name`, `email`, `company_name`

**`company_size` enum values:** `1-10` · `11-50` · `51-200` · `201-500` · `500+`

**Success response (200):**

```json
{
  "status": "processing",
  "message": "Your report is being generated and will be emailed shortly."
}
```

**Validation error (422):**

```json
{
  "detail": [
    { "loc": ["body", "email"], "msg": "value is not a valid email address", "type": "value_error.email" }
  ]
}
```

---

## Assumptions

1. **Clearbit free autocomplete** is always called (no key needed). The paid Company API is only called when `CLEARBIT_API_KEY` is set.
2. **LinkedIn scraping** is best-effort — LinkedIn blocks most bots. The pipeline continues gracefully if it fails.
3. **WeasyPrint** renders the PDF server-side. The report template uses inline CSS for maximum WeasyPrint compatibility (WeasyPrint has limited CSS support compared to browsers).
4. **Claude model** is `claude-sonnet-4-20250514`. Update `CLAUDE_MODEL` in `config.py` if you want a different model.
5. The **output directory** (`./output/reports/`) is created automatically on startup.
6. Google Sheets / Drive features are **opt-in** — the pipeline works without them.

---

## Tradeoffs & Limitations

| Area | Decision | Tradeoff |
|---|---|---|
| PDF rendering | WeasyPrint (server-side) | No headless Chrome needed, but CSS support is limited |
| AI content | Single Claude call + 1 retry | Fast, but complex JSON can occasionally fail parsing |
| Enrichment | Multi-source with fallbacks | More data but slower (3–8 s); all steps are async |
| Email | SendGrid → SMTP fallback | Reliable delivery; SMTP requires app password for Gmail |
| Background tasks | FastAPI `BackgroundTasks` | Simple, in-process; use Celery/Redis for production scale |
| LinkedIn | httpx scraping | Frequently blocked; treat as best-effort only |

---

## Extending the System

### Add a new enrichment source

1. Add a method to `EnrichmentService` in `services/enrichment.py`
2. Call it inside `enrich()` and merge results with `_merge()`

### Add a different email provider

1. Add a `_send_<provider>()` method to `EmailSender`
2. Update the `send_report()` dispatch logic

### Scale to production

- Replace `BackgroundTasks` with **Celery + Redis** for distributed task processing
- Add a **PostgreSQL** database to persist lead and report state
- Use **S3** instead of local filesystem for PDF storage
- Add **rate limiting** (e.g., `slowapi`) to the `/submit-lead` endpoint
- Add **webhook support** to notify CRMs (HubSpot, Salesforce) on completion

### Add more report sections

1. Extend the JSON schema in `ReportGenerator._build_prompt()`
2. Add the corresponding section to `templates/report_template.html`
