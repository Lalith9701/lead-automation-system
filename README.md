<div align="center">

# 🚀 Lead Automation System

**Submit a form. Get a personalized AI audit report in your inbox. Automatically.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.136-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Claude AI](https://img.shields.io/badge/Claude-claude--sonnet--4-blueviolet?logo=anthropic&logoColor=white)](https://anthropic.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

---

## What Is This?

Lead Automation System is a fully automated pipeline that:

1. **Captures** a prospect's company details via a web form
2. **Enriches** the data from multiple sources (Clearbit, DuckDuckGo, LinkedIn, NewsAPI, tech-stack detection)
3. **Generates** a personalized 7-section business audit report using Claude AI
4. **Renders** it as a professional PDF (WeasyPrint + Jinja2)
5. **Emails** the PDF directly to the prospect (SendGrid or SMTP)
6. **Logs** every step to Google Sheets and uploads the PDF to Google Drive *(optional)*

Zero human intervention required after the form is submitted.

---

## Live Demo Flow

```
Prospect fills form  →  POST /api/v1/submit-lead
        │
        └──▶  Instant 200 response: "Your report is being prepared…"
                        │
              ┌─────────▼──────────┐
              │  Enrich Company    │  Clearbit · DuckDuckGo · LinkedIn
              │  Data              │  NewsAPI · Homepage scrape · Tech stack
              └─────────┬──────────┘
                        │
              ┌─────────▼──────────┐
              │  Generate Report   │  Claude claude-sonnet-4
              │  Content (AI)      │  7-section JSON → parsed & validated
              └─────────┬──────────┘
                        │
              ┌─────────▼──────────┐
              │  Render PDF        │  Jinja2 HTML template → WeasyPrint
              └─────────┬──────────┘
                        │
              ┌─────────▼──────────┐
              │  Upload to Drive   │  Google Drive (shareable link) [bonus]
              └─────────┬──────────┘
                        │
              ┌─────────▼──────────┐
              │  Send Email        │  SendGrid (primary) → SMTP (fallback)
              └─────────┬──────────┘
                        │
              ┌─────────▼──────────┐
              │  Log to Sheets     │  Google Sheets row updated [bonus]
              └────────────────────┘
```

---

## Project Structure

```
lead-automation/
│
├── main.py                   # FastAPI app entry point
├── config.py                 # All environment variables & settings
├── requirements.txt
├── .env.example              # Template for your .env file
│
├── api/
│   └── routes.py             # POST /api/v1/submit-lead endpoint
│
├── models/
│   └── lead.py               # Pydantic v2 models & validation
│
├── services/
│   ├── enrichment.py         # Multi-source company data enrichment
│   ├── report_generator.py   # Claude AI report + WeasyPrint PDF
│   ├── email_sender.py       # SendGrid / SMTP email delivery
│   ├── sheets_logger.py      # Google Sheets logging  [bonus]
│   └── drive_uploader.py     # Google Drive upload    [bonus]
│
├── templates/
│   ├── report_template.html  # Jinja2 PDF report template
│   ├── email_template.html   # HTML email body template
│   └── index.html            # Lead intake form (vanilla HTML/CSS/JS)
│
├── static/
│   └── styles.css            # WeasyPrint print overrides
│
└── utils/
    ├── scraper.py            # httpx + BeautifulSoup4 scrapers
    └── helpers.py            # Retry logic, safe HTTP, text utilities
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Web framework | FastAPI |
| AI / LLM | Anthropic Claude (`claude-sonnet-4-20250514`) |
| PDF generation | WeasyPrint + Jinja2 |
| Web scraping | httpx + BeautifulSoup4 |
| Data enrichment | Clearbit API · DuckDuckGo · NewsAPI · LinkedIn |
| Email | SendGrid (primary) · smtplib/SMTP (fallback) |
| Google integrations | gspread · google-api-python-client |
| Validation | Pydantic v2 |
| Config | python-dotenv |

---

## Prerequisites

- **Python 3.10+**
- **API keys** — Anthropic (required), SendGrid or SMTP (required for email), others optional
- **WeasyPrint system libraries** — see below

### WeasyPrint on Windows

WeasyPrint needs GTK3 runtime libraries. Install them first:

👉 [GTK3 Runtime Installer for Windows](https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases)

Then:
```bash
pip install weasyprint
```

### WeasyPrint on macOS / Linux

```bash
# macOS
brew install pango

# Ubuntu / Debian
sudo apt-get install libpango-1.0-0 libpangoft2-1.0-0
```

---

## Installation

```bash
# 1. Clone the repository
git clone https://github.com/Lalith9701/lead-automation-system.git
cd lead-automation-system

# 2. Create and activate a virtual environment
python -m venv .venv

.venv\Scripts\activate        # Windows
source .venv/bin/activate     # macOS / Linux

# 3. Install dependencies
pip install -r requirements.txt
```

---

## Configuration

Copy the example env file and fill in your keys:

```bash
copy .env.example .env    # Windows
cp .env.example .env      # macOS / Linux
```

### Environment Variables

| Variable | Required | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | ✅ Required | Get from [console.anthropic.com](https://console.anthropic.com) |
| `SENDGRID_API_KEY` | ✅ or SMTP | Get from [sendgrid.com](https://sendgrid.com) |
| `FROM_EMAIL` | ✅ | Verified sender email address |
| `FROM_NAME` | ✅ | Sender display name |
| `SMTP_HOST` | Fallback | e.g. `smtp.gmail.com` |
| `SMTP_PORT` | Fallback | e.g. `587` |
| `SMTP_USER` | Fallback | Your Gmail address |
| `SMTP_PASSWORD` | Fallback | Gmail app password |
| `CLEARBIT_API_KEY` | Optional | Enables full Clearbit enrichment |
| `NEWS_API_KEY` | Optional | [newsapi.org](https://newsapi.org) — free tier: 100 req/day |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Bonus | Path to service account JSON file |
| `GOOGLE_SHEET_ID` | Bonus | ID of your Google Sheet for logging |
| `GOOGLE_DRIVE_FOLDER_ID` | Bonus | Drive folder ID for PDF uploads |
| `PORT` | Optional | Server port (default: `8000`) |
| `OUTPUT_DIR` | Optional | PDF output path (default: `./output/reports`) |

> **Tip:** The system works without Clearbit, NewsAPI, and Google keys. Those features degrade gracefully.

---

### Google Service Account Setup *(Bonus features only)*

Only needed if you want Google Sheets logging and Drive uploads.

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project → Enable **Google Sheets API** and **Google Drive API**
3. Go to **IAM & Admin → Service Accounts** → Create a service account
4. Download the JSON key → save it to `./credentials/service_account.json`
5. Share your Google Sheet with the service account email *(Editor role)*
6. Share your Drive folder with the service account email *(Editor role)*

---

## Running the Server

```bash
uvicorn main:app --reload --port 8000
```

| URL | Description |
|---|---|
| http://localhost:8000 | Lead intake form |
| http://localhost:8000/docs | Interactive API docs (Swagger UI) |
| http://localhost:8000/redoc | API docs (ReDoc) |
| http://localhost:8000/health | Health check |

---

## API Reference

### `POST /api/v1/submit-lead`

Submits a lead and triggers the full automation pipeline in the background.

**Request Body**

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

| Field | Type | Required | Notes |
|---|---|---|---|
| `full_name` | string | ✅ | Min 2 characters |
| `email` | string | ✅ | Must be a valid email |
| `company_name` | string | ✅ | |
| `company_website` | string | Optional | Must be a valid URL if provided |
| `industry` | string | Optional | Free text |
| `company_size` | enum | Optional | `1-10` · `11-50` · `51-200` · `201-500` · `500+` |
| `role` | string | Optional | e.g. `CEO`, `Marketing Head` |
| `message` | string | Optional | Pain points or goals |

**Success Response — 200**

```json
{
  "status": "processing",
  "message": "Your report is being generated and will be emailed shortly."
}
```

The response is immediate. The pipeline runs in the background.

**Validation Error — 422**

```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    }
  ]
}
```

---

## Report Sections

Every generated PDF report contains these 7 sections:

| # | Section | What's Inside |
|---|---|---|
| 01 | Executive Summary | Personalized 2–3 paragraph overview |
| 02 | Company Overview | What they do, market position, key strengths |
| 03 | Digital Presence Audit | Website, SEO, content strategy, score out of 10 |
| 04 | Competitive Landscape | Market overview, key competitors, differentiators |
| 05 | Growth Opportunities | 3–4 cards with Impact/Effort tags and action steps |
| 06 | Tech & Operations | Stack observations, automation gaps, tool recommendations |
| 07 | Action Plan | Immediate · 30–60 days · 90+ days timeline |

---

## Pipeline Status Tracking *(Google Sheets)*

When Sheets logging is enabled, each lead gets a row that updates in real time:

```
processing → enriched → report_generated → pdf_ready → uploaded → emailed → complete
```

If any step fails, the status updates to `<step>_failed` with an error note — the pipeline always continues to the next step.

---

## Assumptions & Design Decisions

| Topic | Decision |
|---|---|
| **Clearbit free tier** | Autocomplete endpoint is always called (no key needed). Full API only runs when `CLEARBIT_API_KEY` is set. |
| **LinkedIn scraping** | Best-effort only — LinkedIn blocks most bots. The pipeline continues gracefully if blocked. |
| **PDF rendering** | WeasyPrint renders server-side. Inline CSS is used throughout for maximum compatibility. |
| **Claude model** | `claude-sonnet-4-20250514`. Change `CLAUDE_MODEL` in `config.py` to use a different model. |
| **Output directory** | `./output/reports/` is created automatically on startup. |
| **Google features** | Fully opt-in. The core pipeline works without any Google credentials. |
| **Background tasks** | Uses FastAPI's built-in `BackgroundTasks`. For production scale, replace with Celery + Redis. |

---

## Extending the System

### Add a new enrichment source
1. Add a method to `EnrichmentService` in `services/enrichment.py`
2. Call it inside `enrich()` and merge results using `_merge()`

### Add a new email provider
1. Add a `_send_<provider>()` method to `EmailSender` in `services/email_sender.py`
2. Update the dispatch logic in `send_report()`

### Add a new report section
1. Extend the JSON schema in `ReportGenerator._build_prompt()` in `services/report_generator.py`
2. Add the corresponding HTML block to `templates/report_template.html`

### Scale to production
- Replace `BackgroundTasks` with **Celery + Redis** for distributed workers
- Add **PostgreSQL** to persist lead and report state
- Use **AWS S3** instead of local filesystem for PDF storage
- Add **rate limiting** with `slowapi` on the submit endpoint
- Add **webhook support** to push completion events to HubSpot, Salesforce, etc.

---

## Troubleshooting

**WeasyPrint fails with a font/library error**
→ Install the GTK3 runtime (Windows) or Pango (macOS/Linux). See [Prerequisites](#prerequisites).

**Claude returns invalid JSON**
→ The system retries once automatically with a stricter prompt. If it still fails, a minimal fallback report is used.

**Email not sending**
→ Check `SENDGRID_API_KEY` and that `FROM_EMAIL` is a verified sender in SendGrid. Or configure SMTP fallback credentials.

**LinkedIn scraping returns nothing**
→ Expected. LinkedIn blocks automated requests. The pipeline continues without it.

---

## License

MIT — free to use, modify, and distribute.

---

<div align="center">
Built with FastAPI · Claude AI · WeasyPrint · SendGrid
</div>
